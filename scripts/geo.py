"""Shared geography for the build scripts: the region we cover and which country a point is in.

Country outlines come from geoBoundaries (gbOpen ADM0: Pakistan from OpenStreetMap, ODbL; India from
DataMeet, CC BY 2.5 IN). Both outlines claim Kashmir, so where they overlap the caller decides by the
nearest village's country, which follows who administers the place rather than either claim.
"""
import json, math

# Everything we may cover, as named bounds (the old scripts used tuples in different orders).
REGION = {"s": 5.5, "n": 37.5, "w": 60.5, "e": 97.5}
# What the live feed covers today. Stage 4 of the all-India plan switches this to REGION.
FEED_BOX = {"s": 25.0, "n": 35.5, "w": 66.0, "e": 88.5}

BAND = 4  # edges are indexed by latitude band, 1/4 degree


def in_box(box, lat, lon):
    return box["s"] <= lat <= box["n"] and box["w"] <= lon <= box["e"]


def cell_key(lat, lon):
    """The 0.25-degree cell a point is in, as used by the place index (data/places/<key>.json)."""
    return f"{math.floor(lat * 4)}_{math.floor(lon * 4)}"


class Borders:
    """Point-in-polygon for a few large polygons. Every edge is filed under each latitude band it crosses,
    so a test looks only at the edges in its band. Uses the even-odd rule over all rings, which handles
    holes and multi-part countries."""

    def __init__(self, polys):
        """polys: {name: [polygon, ...]}, a polygon being [ring, ...] and a ring [[lon, lat], ...]."""
        self.names = list(polys)
        self.band = {}
        for name, ps in polys.items():
            for poly in ps:
                for ring in poly:
                    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
                        if y1 == y2:
                            continue
                        for r in range(math.floor(min(y1, y2) * BAND), math.floor(max(y1, y2) * BAND) + 1):
                            self.band.setdefault((name, r), []).append((x1, y1, x2, y2))

    def inside(self, name, lat, lon):
        c = False
        for x1, y1, x2, y2 in self.band.get((name, math.floor(lat * BAND)), ()):
            if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                c = not c
        return c

    def which(self, lat, lon):
        return [n for n in self.names if self.inside(n, lat, lon)]

    @classmethod
    def load(cls, path):
        return cls(json.load(open(path, encoding="utf-8")))


def geojson_polys(features):
    """GeoJSON (Multi)Polygon features -> [polygon, ...] with coordinates rounded to ~10 m."""
    out = []
    for f in features:
        g = f["geometry"]
        for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            out.append([[[round(x, 4), round(y, 4)] for x, y in ring] for ring in poly])
    return out
