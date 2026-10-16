#!/usr/bin/env python3
"""Build the known-pollution-sources layers: landfills and industrial areas from OpenStreetMap,
and brick kilns from two satellite-derived research datasets.

Usage: python3 -I scripts/build-sources.py [--only landfill|industrial]
       python3 -I scripts/build-sources.py --only kilns --skdb-labels <labels.json> --pk-kilns <csv>

Writes site/public/sources/osm-landfill.json and osm-industrial.json:
  {"source": ..., "items": [[lat, lon, name, radius_m, osm_ref], ...]}
radius_m is the approximate size of the site (from its bounding box), used to decide whether
a fire falls "at" it. OpenStreetMap data © OpenStreetMap contributors, ODbL.
"""
import argparse, json, math, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "site", "public", "sources")
BBOX = (25.0, 66.0, 35.5, 88.5)  # s, w, n, e
MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
UA = "hamarihawa.org source mapper (+https://hamarihawa.org/about/)"
QUERIES = {
    # amenity=waste_disposal is mostly street bins here, so only mapped landfill sites count.
    "landfill": '(nwr["landuse"="landfill"]({b}););',
    # Named estates only: the public Overpass servers can't serve every unnamed yard in the region,
    # and the named ones (Sundar, Kot Lakhpat, Okhla...) are what people recognise.
    "industrial": '(way["landuse"="industrial"]["name"]({b});relation["landuse"="industrial"]["name"]({b}););',
}


def overpass(q):
    body = urllib.parse.urlencode({"data": f"[out:json][timeout:240];{q}out center tags bb;"}).encode()
    last = None
    for attempt in range(6):
        for url in MIRRORS:
            try:
                req = urllib.request.Request(url, data=body, headers={"User-Agent": UA, "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=300) as r:
                    return json.load(r)["elements"]
            except Exception as e:  # busy mirror, timeout, HTML error page
                last = e
                print(f"  {url.split('/')[2]}: {str(e)[:80]}", file=sys.stderr)
        time.sleep(30 * (attempt + 1))
    raise SystemExit(f"all Overpass mirrors failed: {last}")


def tiles(step):
    s, w, n, e = BBOX
    lat = s
    while lat < n:
        lon = w
        while lon < e:
            yield (lat, lon, min(lat + step, n), min(lon + step, e))
            lon += step
        lat += step


def to_item(el):
    c = el.get("center") or ({"lat": el["lat"], "lon": el["lon"]} if "lat" in el else None)
    if not c and "bounds" in el:  # with "bb", Overpass returns the box but not the centre
        b = el["bounds"]
        c = {"lat": (b["minlat"] + b["maxlat"]) / 2, "lon": (b["minlon"] + b["maxlon"]) / 2}
    if not c:
        return None
    tags = el.get("tags", {})
    name = tags.get("name:en") or tags.get("name") or ""
    r = 150
    if "bounds" in el:
        b = el["bounds"]
        dy = (b["maxlat"] - b["minlat"]) * 111_000
        dx = (b["maxlon"] - b["minlon"]) * 111_000 * math.cos(math.radians(c["lat"]))
        r = max(100, round(math.hypot(dx, dy) / 2))
    return [round(c["lat"], 5), round(c["lon"], 5), name, r, f"{el['type'][0]}{el['id']}"]


KILN_TYPES = ["CFCBK", "FCBK", "Zigzag"]  # SentinelKilnDB class ids 0, 1, 2 (checked against its DOTA labels)


def build_kilns(skdb_labels, pk_csv):
    """Merge SentinelKilnDB (whole IGP, CC BY-NC 4.0) with the Pakistan IGP kiln dataset (CC BY 4.0).

    skdb_labels: JSON list of [split, "lat_lon.png", [yolo_aa labels]] read from the dataset's parquet
    (128 px chips at 10 m/px; the file name is the chip centre). pk_csv: Brick_Kilns_IGP_PK_emission_estimates.csv.
    Output items: [lat, lon, type_index, pm25_kg_per_day or null].
    """
    import csv
    s_, w_, n_, e_ = BBOX
    grid, items = {}, []

    def key(la, lo):
        return (round(la / 0.0006), round(lo / 0.0006))  # ~60 m: overlapping chips see the same kiln twice

    def add(la, lo, t, pm):
        if not (s_ <= la <= n_ and w_ <= lo <= e_):
            return
        k = key(la, lo)
        for dk in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            hit = grid.get((k[0] + dk[0], k[1] + dk[1]))
            if hit is not None:
                if pm is not None and items[hit][3] is None:
                    items[hit][3] = pm
                return
        grid[k] = len(items)
        items.append([round(la, 5), round(lo, 5), t, pm])

    # Pakistan first, so its emission estimates attach to the merged points.
    for r in csv.DictReader(open(pk_csv, encoding="utf-8-sig")):
        t = 2 if r["type"].strip().lower().startswith("zig") else 1
        add(float(r["lat"]), float(r["lon"]), t, round(float(r["pm2.5d(kg)"]), 1))
    for _, name, labels in json.load(open(skdb_labels)):
        la0, lo0 = map(float, name[:-4].split("_"))
        for lab in labels:
            c, cx, cy = lab.split()[:3]
            dy, dx = (0.5 - float(cy)) * 1280, (float(cx) - 0.5) * 1280
            add(la0 + dy / 111_000, lo0 + dx / (111_000 * math.cos(math.radians(la0))), int(c), None)
    path = os.path.join(OUT, "kilns.json")
    json.dump({"source": "SentinelKilnDB (CC BY-NC 4.0); Brick Kiln Dataset for Pakistan's IGP Region (CC BY 4.0)",
               "types": KILN_TYPES, "built": time.strftime("%Y-%m-%d"), "items": items},
              open(path, "w"), separators=(",", ":"))
    print(f"wrote {len(items)} kilns ({sum(1 for i in items if i[3] is not None)} with emission estimates) -> {path}")


# IPCC sector codes Carbon Mapper uses.
CM_SECTORS = {"6A": "landfill", "1A1": "power", "1A2": "industry", "1B2": "oilgas", "1B1": "coal", "4B": "livestock"}


def build_carbonmapper():
    """Methane and CO2 point sources seen by Carbon Mapper's satellites and aircraft (cite Carbon Mapper)."""
    s_, w_, n_, e_ = BBOX
    url = f"https://api.carbonmapper.org/api/v1/catalog/sources.geojson?bbox={w_}&bbox={s_}&bbox={e_}&bbox={n_}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        feats = json.load(r)["features"]
    items = []
    for f in feats:
        p, (lon, lat) = f["properties"], f["geometry"]["coordinates"]
        items.append([round(lat, 5), round(lon, 5), p["gas"], CM_SECTORS.get(p["sector"], "other"),
                      round(p.get("emission_auto") or 0), p.get("plume_count") or 0,
                      round((p.get("persistence") or 0) * 100), p.get("timestamp_min"), p.get("timestamp_max")])
    path = os.path.join(OUT, "carbonmapper.json")
    json.dump({"source": "Carbon Mapper (carbonmapper.org), satellite and airborne plume detections",
               "fields": ["lat", "lon", "gas", "sector", "emission_kg_per_h", "plumes", "persistence_pct", "first", "last"],
               "built": time.strftime("%Y-%m-%d"), "items": items}, open(path, "w"), separators=(",", ":"))
    print(f"wrote {len(items)} Carbon Mapper sources -> {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(QUERIES) + ["kilns", "carbonmapper"])
    ap.add_argument("--skdb-labels", help="SentinelKilnDB labels JSON (for --only kilns)")
    ap.add_argument("--pk-kilns", help="Pakistan kiln emission CSV (for --only kilns)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.only == "kilns":
        build_kilns(a.skdb_labels, a.pk_kilns)
        return
    if a.only == "carbonmapper":
        build_carbonmapper()
        return
    for kind, q in QUERIES.items():
        if a.only and kind != a.only:
            continue
        seen, items = set(), []
        step = 2.0 if kind == "industrial" else 12.0
        for t in tiles(step):
            b = ",".join(f"{x:.2f}" for x in t)
            els = overpass(q.replace("{b}", b))
            for el in els:
                key = (el["type"], el["id"])
                if key in seen:
                    continue
                seen.add(key)
                it = to_item(el)
                if it:
                    items.append(it)
            print(f"{kind} {b}: {len(els)} (total {len(items)})")
            time.sleep(2)
        if kind == "industrial":
            items = [i for i in items if i[3] >= 120]  # drop single workshops; keep estates and plants
        path = os.path.join(OUT, f"osm-{kind}.json")
        json.dump({"source": "© OpenStreetMap contributors (ODbL)", "built": time.strftime("%Y-%m-%d"), "items": items},
                  open(path, "w"), separators=(",", ":"), ensure_ascii=False)
        print(f"wrote {len(items)} {kind} sites -> {path}")


if __name__ == "__main__":
    main()
