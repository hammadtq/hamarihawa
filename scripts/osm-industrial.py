#!/usr/bin/env python3
"""Extract industrial areas from Geofabrik OpenStreetMap extracts (.osm.pbf).

The public Overpass servers can't answer region-wide industrial queries reliably, so this
reads the country extracts directly. Needs pyosmium (`pip install osmium`).

Usage: python3 -I scripts/osm-industrial.py <out.json> <extract.osm.pbf> [more.osm.pbf ...]
Get extracts from https://download.geofabrik.de/asia/ (pakistan, india/northern-zone,
india/central-zone, india/eastern-zone).

Output matches build-sources.py: {"items": [[lat, lon, name, radius_m, osm_ref], ...]}.
Keeps named estates, and unnamed ones larger than ~5 ha (radius >= 130 m).
"""
import json, math, sys, time
import osmium

BBOX = (25.0, 66.0, 35.5, 88.5)  # s, w, n, e


class Industrial(osmium.SimpleHandler):
    def __init__(self, seen):
        super().__init__()
        self.items, self.seen = [], seen

    def way(self, w):
        if w.tags.get("landuse") != "industrial" or w.id in self.seen:
            return
        try:
            lats = [n.lat for n in w.nodes]
            lons = [n.lon for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        if not lats:
            return
        la, lo = (min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2
        if not (BBOX[0] <= la <= BBOX[2] and BBOX[1] <= lo <= BBOX[3]):
            return
        dy = (max(lats) - min(lats)) * 111_000
        dx = (max(lons) - min(lons)) * 111_000 * math.cos(math.radians(la))
        r = max(60, round(math.hypot(dx, dy) / 2))
        name = w.tags.get("name:en") or w.tags.get("name") or ""
        if not name and r < 130:
            return
        self.seen.add(w.id)
        self.items.append([round(la, 5), round(lo, 5), name, r, f"w{w.id}"])


def main():
    out, files = sys.argv[1], sys.argv[2:]
    seen, items = set(), []
    for f in files:
        h = Industrial(seen)
        h.apply_file(f, locations=True, idx="flex_mem")
        items += h.items
        print(f"{f}: {len(h.items)} industrial areas")
    json.dump({"source": "© OpenStreetMap contributors (ODbL), via Geofabrik extracts", "built": time.strftime("%Y-%m-%d"),
               "items": items}, open(out, "w"), separators=(",", ":"), ensure_ascii=False)
    print(f"wrote {len(items)} -> {out}")


if __name__ == "__main__":
    main()
