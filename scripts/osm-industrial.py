#!/usr/bin/env python3
"""Extract industrial areas from Geofabrik OpenStreetMap extracts (.osm.pbf).

The public Overpass servers can't answer region-wide industrial queries reliably, so this
reads the country extracts directly. Needs pyosmium (`pip install osmium`).

Usage: python3 -I scripts/osm-industrial.py <out.json> <extract.osm.pbf> [more.osm.pbf ...]
       python3 -I scripts/osm-industrial.py --power <plants.json> <extract.osm.pbf> [...]   (named fossil power plants)
       python3 -I scripts/osm-industrial.py --roads <roads.json> <extract.osm.pbf> [...]    (major roads, under the NO2 layer)
Get extracts from https://download.geofabrik.de/asia/ (pakistan, india/northern-zone,
india/central-zone, india/eastern-zone).

Output matches build-sources.py: {"items": [[lat, lon, name, radius_m, osm_ref], ...]}.
Keeps named estates, and unnamed ones larger than ~5 ha (radius >= 130 m).
"""
import json, math, sys, time
import osmium

BBOX = (25.0, 66.0, 35.5, 88.5)  # s, w, n, e


FOSSIL = {"coal", "gas", "oil", "diesel", "lignite", "furnace_oil"}


class PowerPlants(osmium.SimpleHandler):
    """Named fossil-fuel power plants (power=plant), the big point sources of NO2 and SO2."""

    def __init__(self, seen):
        super().__init__()
        self.items, self.seen = [], seen

    def _add(self, kind, oid, tags, la, lo):
        if tags.get("power") != "plant" or (kind, oid) in self.seen:
            return
        src = (tags.get("plant:source") or tags.get("generator:source") or "").lower()
        if "bio" in src or not any(f in src for f in FOSSIL):  # biogas is not a fossil plant
            return
        name = tags.get("name:en") or tags.get("name") or ""
        if not name or not (BBOX[0] <= la <= BBOX[2] and BBOX[1] <= lo <= BBOX[3]):
            return
        self.seen.add((kind, oid))
        fuel = "coal" if ("coal" in src or "lignite" in src) else "gas" if "gas" in src else "oil"
        mw = tags.get("plant:output:electricity", "")
        self.items.append([round(la, 5), round(lo, 5), fuel, name, mw])

    def node(self, n):
        if n.tags.get("power") == "plant":
            self._add("n", n.id, n.tags, n.location.lat, n.location.lon)

    def way(self, w):
        if w.tags.get("power") != "plant":
            return
        try:
            lats = [n.lat for n in w.nodes]; lons = [n.lon for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        if lats:
            self._add("w", w.id, w.tags, (min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2)


ROAD_CLASSES = {"motorway": 0, "trunk": 1, "primary": 2}


def simplify(pts, tol):
    """Douglas-Peucker on (lon, lat) pairs; tol in degrees."""
    if len(pts) < 3:
        return pts
    keep, stack = {0, len(pts) - 1}, [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1e-12
        best, bi = 0, None
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / n
            if d > best:
                best, bi = d, i
        if bi is not None and best > tol:
            keep.add(bi)
            stack += [(a, bi), (bi, b)]
    return [pts[i] for i in sorted(keep)]


def chain(items):
    """Join road pieces of the same class that meet end to start, so the file holds long lines."""
    by_start = {}
    for i, (c, f) in enumerate(items):
        by_start.setdefault((c, f[0], f[1]), []).append(i)
    used, out = set(), []
    for i, (c, f) in enumerate(items):
        if i in used:
            continue
        used.add(i)
        line = list(f)
        while True:
            nxt = [j for j in by_start.get((c, line[-2], line[-1]), []) if j not in used]
            if not nxt:
                break
            used.add(nxt[0])
            line += items[nxt[0]][1][2:]
        out.append([c, line])
    return out


class Roads(osmium.SimpleHandler):
    """Motorways, trunk and primary roads, simplified, as context under the NO2 layer."""

    def __init__(self, seen):
        super().__init__()
        self.items, self.seen = [], seen

    def way(self, w):
        c = ROAD_CLASSES.get(w.tags.get("highway"))
        if c is None or w.id in self.seen:
            return
        try:
            pts = [(n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        pts = [p for p in pts if BBOX[0] - 0.2 <= p[1] <= BBOX[2] + 0.2 and BBOX[1] - 0.2 <= p[0] <= BBOX[3] + 0.2]
        if len(pts) < 2:
            return
        self.seen.add(w.id)
        flat = []
        for lon, lat in simplify(pts, 0.0015):
            flat += [round(lon, 3), round(lat, 3)]
        self.items.append([c, flat])


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
    if sys.argv[1] == "--power":
        out, files = sys.argv[2], sys.argv[3:]
        seen, items = set(), []
        for f in files:
            h = PowerPlants(seen)
            h.apply_file(f, locations=True, idx="flex_mem")
            items += h.items
            print(f"{f}: {len(h.items)} fossil power plants")
        json.dump({"source": "© OpenStreetMap contributors (ODbL); power=plant with coal/gas/oil source",
                   "fields": ["lat", "lon", "fuel", "name", "output"], "built": time.strftime("%Y-%m-%d"), "items": items},
                  open(out, "w"), separators=(",", ":"), ensure_ascii=False)
        print(f"wrote {len(items)} -> {out}")
        return
    if sys.argv[1] == "--roads":
        out, files = sys.argv[2], sys.argv[3:]
        seen, items = set(), []
        for f in files:
            h = Roads(seen)
            h.apply_file(f, locations=True, idx="flex_mem")
            items += h.items
            print(f"{f}: {len(h.items)} road segments")
        items = chain(items)
        json.dump({"source": "© OpenStreetMap contributors (ODbL); highway=motorway/trunk/primary, simplified",
                   "fields": ["class (0 motorway, 1 trunk, 2 primary)", "flat [lon, lat, ...]"],
                   "built": time.strftime("%Y-%m-%d"), "items": items},
                  open(out, "w"), separators=(",", ":"))
        print(f"wrote {len(items)} -> {out}")
        return
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
