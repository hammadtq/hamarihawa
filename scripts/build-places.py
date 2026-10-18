#!/usr/bin/env python3
"""Build the compact place-name index the Worker uses to name fire locations.

Usage: python3 -I scripts/build-places.py <dir with PK.zip IN.zip admin1CodesASCII.txt admin2Codes.txt> site/public/places

Writes one JSON file per 0.25-degree cell (<floor(lat*4)>_<floor(lon*4)>.json), so the Worker
loads only the cells under current fires instead of all ~460k places. Also writes
site/src/towns.json (places over 100k people) for the "km from <town>" context.

Source: GeoNames (CC-BY 4.0), https://download.geonames.org/export/dump/
Keeps populated places (feature class P) inside the Indus-Gangetic Plain box.
"""
import io, json, math, os, re, sys, zipfile

BBOX = (24.5, 35.5, 66.0, 88.5)  # lat min, lat max, lon min, lon max
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


src, out = sys.argv[1], sys.argv[2]

admin1, admin2 = {}, {}
for line in open(f"{src}/admin1CodesASCII.txt", encoding="utf-8"):
    code, name, ascii_name, _ = line.rstrip("\n").split("\t")
    admin1[code] = ascii_name.replace("Islamabad Capital Territory", "Islamabad").replace("National Capital Territory of Delhi", "Delhi")
for line in open(f"{src}/admin2Codes.txt", encoding="utf-8"):
    code, name, ascii_name, _ = line.rstrip("\n").split("\t")
    if code[:2] in ("PK", "IN"):
        admin2[code] = ascii_name.replace(" District", "")

cells = {}  # "lat4_lon4" -> {"regions": [...], "idx": {...}, "p": [...]}
towns = []

for cc in ("PK", "IN"):
    with zipfile.ZipFile(f"{src}/{cc}.zip") as z:
        for line in io.TextIOWrapper(z.open(f"{cc}.txt"), encoding="utf-8"):
            f = line.rstrip("\n").split("\t")
            if f[6] != "P" or f[7] in SKIP_CODES:
                continue
            la, lo = float(f[4]), float(f[5])
            if not (BBOX[0] <= la <= BBOX[1] and BBOX[2] <= lo <= BBOX[3]):
                continue
            name = words_to_digits(f[2] or f[1])
            if not name or len(name) > 40:
                continue
            a1 = admin1.get(f"{cc}.{f[10]}", "")
            a2 = admin2.get(f"{cc}.{f[10]}.{f[11]}", "")
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
print(f"{total} places in {len(cells)} cells -> {out}")
