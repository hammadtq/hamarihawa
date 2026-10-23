#!/usr/bin/env python3
"""Build the compact place-name index the Worker uses to name fire locations.

Usage: python3 -I scripts/build-places.py <geonames dir> <geoboundaries dir> data/places
  geonames dir: PK.zip IN.zip admin1CodesASCII.txt admin2Codes.txt (download.geonames.org/export/dump)
  geoboundaries dir: {PAK,IND}-{ADM0,ADM2}.geojson, the gbOpen *_simplified.geojson files

Writes one JSON file per 0.25-degree cell (<floor(lat*4)>_<floor(lon*4)>.json), so the feed builder
loads only the cells under current fires instead of every place. Also writes:
  borders.json    the Pakistan and India outlines, for telling which country a fire is in
  countries.json  each cell of the region as "PK", "IN", "PK+IN" (Kashmir, claimed by both outlines) or
                  "mix" (a border runs through it); cells outside both countries are left out
  site/src/towns.json (places over 100k people) for the "km from <town>" context.

Sources: GeoNames (CC BY 4.0) for places and their districts; geoBoundaries gbOpen for the country
outlines and, for the few places GeoNames gives no district, the district they fall in.
Keeps populated places (feature class P) in Pakistan and India.
"""
import importlib.util, io, json, math, os, re, sys, unicodedata, zipfile

_spec = importlib.util.spec_from_file_location("geo", os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo.py"))
geo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(geo)
R = geo.REGION
SKIP_CODES = {"PPLX", "PPLH", "PPLQ", "PPLW", "PPLCH"}  # sections, historical, abandoned, destroyed

UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
NUM_RE = re.compile(r"\b(?:(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)(?:[- ]|\b))+", re.I)


def words_to_digits(name):
    """GeoNames spells Punjab chak numbers out ("Chak One Hundred Eighty"); locals write "Chak 180"."""
    def conv(m):
        nums, total, cur, last = [], 0, 0, None
        for w in re.split(r"[- ]+", m.group(0).strip().lower()):
            # "Eighty-seven Twelve" is chak 87/12: a new number starts after a unit or after a bare tens word.
            if (w in UNITS and last in ("unit", "tens") and not (last == "tens" and UNITS[w] < 10)) or (w in TENS and last in ("unit", "tens")):
                nums.append(total + cur); total, cur = 0, 0
            if w in UNITS: cur += UNITS[w]; last = "unit"
            elif w in TENS: cur += TENS[w]; last = "tens"
            elif w == "hundred": cur = (cur or 1) * 100; last = "big"
            elif w == "thousand": total += (cur or 1) * 1000; cur = 0; last = "big"
        nums.append(total + cur)
        trail = " " if m.group(0).endswith((" ", "-")) else ""
        return "/".join(map(str, nums)) + trail
    return NUM_RE.sub(conv, name) if re.search(r"\b(chak|chakk|no\.?)\b", name, re.I) else name


src, gbdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
plain = lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
ISO = {"PK": "PAK", "IN": "IND"}
adm0 = {cc: geo.geojson_polys(json.load(open(f"{gbdir}/{iso}-ADM0.geojson"))["features"]) for cc, iso in ISO.items()}
# District outlines, only as a fallback name for places GeoNames gives no district.
adm2 = {}
for cc, iso in ISO.items():
    for f in json.load(open(f"{gbdir}/{iso}-ADM2.geojson"))["features"]:
        adm2[f"{cc}|{plain(f['properties']['shapeName'])}"] = geo.geojson_polys([f])
adm2_b = geo.Borders(adm2)

admin1, admin2 = {}, {}
for line in open(f"{src}/admin1CodesASCII.txt", encoding="utf-8"):
    code, name, ascii_name, _ = line.rstrip("\n").split("\t")
    admin1[code] = ascii_name.replace("Islamabad Capital Territory", "Islamabad").replace("National Capital Territory of Delhi", "Delhi")
for line in open(f"{src}/admin2Codes.txt", encoding="utf-8"):
    code, name, ascii_name, _ = line.rstrip("\n").split("\t")
    if code[:2] in ("PK", "IN"):
        # GeoNames writes some Indian districts as "District Jalaun"; locals say "Jalaun".
        admin2[code] = re.sub(r"^District\s+", "", ascii_name.replace(" District", ""))

cells = {}  # "lat4_lon4" -> {"regions": [...], "idx": {...}, "p": [...]}
towns = []

for cc in ("PK", "IN"):
    with zipfile.ZipFile(f"{src}/{cc}.zip") as z:
        for line in io.TextIOWrapper(z.open(f"{cc}.txt"), encoding="utf-8"):
            f = line.rstrip("\n").split("\t")
            if f[6] != "P" or f[7] in SKIP_CODES:
                continue
            la, lo = float(f[4]), float(f[5])
            if not geo.in_box(R, la, lo):
                continue
            name = words_to_digits(f[2] or f[1])
            if not name or len(name) > 40:
                continue
            a1 = admin1.get(f"{cc}.{f[10]}", "")
            a2 = admin2.get(f"{cc}.{f[10]}.{f[11]}", "")
            if not a2:
                hit = [n for n in adm2_b.which(la, lo) if n.startswith(cc + "|")]
                a2 = hit[0].split("|", 1)[1] if hit else ""
            key = f"{a2}|{a1}|{cc}"
            cell = cells.setdefault(f"{math.floor(la * 4)}_{math.floor(lo * 4)}", {"regions": [], "idx": {}, "p": [], "seen": set()})
            dedupe = (name, round(la, 2), round(lo, 2))
            if dedupe in cell["seen"]:
                continue
            cell["seen"].add(dedupe)
            if key not in cell["idx"]:
                cell["idx"][key] = len(cell["regions"])
                cell["regions"].append(key)
            p = int(f[14] or 0)
            cell["p"].append([round(la, 4), round(lo, 4), name, cell["idx"][key]])
            if p >= 100000:
                towns.append([round(la, 4), round(lo, 4), name, a2, a1, cc, p])

os.makedirs(out, exist_ok=True)
total = 0
for k, c in cells.items():
    total += len(c["p"])
    json.dump({"r": c["regions"], "p": c["p"]}, open(f"{out}/{k}.json", "w"), separators=(",", ":"), ensure_ascii=False)
json.dump(towns, open(os.path.join(os.path.dirname(__file__), "..", "site", "src", "towns.json"), "w"), separators=(",", ":"), ensure_ascii=False)
# A small copy for the page (wind "from X towards Y"): lat, lon, name, country.
json.dump([[t[0], t[1], t[2], t[5]] for t in towns], open(os.path.join(os.path.dirname(__file__), "..", "site", "public", "sources", "towns.json"), "w"),
          separators=(",", ":"), ensure_ascii=False)
print(f"{len(towns)} towns over 100k")

# Country outlines and which country each cell of the region is in.
json.dump(adm0, open(f"{out}/borders.json", "w"), separators=(",", ":"))
b0 = geo.Borders(adm0)
mixed = set()
for cc, polys in adm0.items():
    for poly in polys:
        for ring in poly:
            for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
                for a in range(math.floor(min(y1, y2) * 4), math.floor(max(y1, y2) * 4) + 1):
                    for b in range(math.floor(min(x1, x2) * 4), math.floor(max(x1, x2) * 4) + 1):
                        mixed.add(f"{a}_{b}")
countries = {}
for a in range(math.floor(R["s"] * 4), math.floor(R["n"] * 4) + 1):
    for b in range(math.floor(R["w"] * 4), math.floor(R["e"] * 4) + 1):
        k = f"{a}_{b}"
        if k in mixed:
            countries[k] = "mix"
            continue
        inside = b0.which((a + 0.5) / 4, (b + 0.5) / 4)
        if inside:
            countries[k] = "+".join(sorted(inside, key=["PK", "IN"].index))
json.dump(countries, open(f"{out}/countries.json", "w"), separators=(",", ":"), sort_keys=True)
from collections import Counter
print("cells by country:", dict(Counter(countries.values())))
print(f"{total} places in {len(cells)} cells -> {out}")
