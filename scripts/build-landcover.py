#!/usr/bin/env python3
"""Cropland and tree-cover share for every 0.01-degree cell (about 1 km) of the region, from ESA WorldCover
2021 (10 m, CC BY 4.0, https://esa-worldcover.org). build-feed.py uses it to say what kind of ground a fire
is on, instead of guessing from the month.

One-time, on a laptop: needs rasterio and numpy (not in the standard library), and reads each 3-degree
WorldCover tile at 1/16 resolution over HTTP (the files are cloud-optimised, so only that level is fetched,
about 150 MB in all, about 6 minutes).

Usage: python3 scripts/build-landcover.py data/landcover.bin.gz
Writes two planes of uint8, cropland % then tree-cover %, row 0 at the region's south edge, gzip-compressed,
and data/landcover.json describing the grid.
"""
import gzip, json, math, os, sys, time
import numpy as np
import rasterio
from rasterio.enums import Resampling

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo  # noqa: E402

STEP = 0.01
PX = 5  # WorldCover pixels sampled per output cell side (25 samples)
URL = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{}_Map.tif"
CROP, TREE = 40, 10  # WorldCover classes: 40 cropland, 10 tree cover (20 shrub, 30 grass, 50 built-up, 60 bare, 80 water...)

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
R = geo.REGION
s, w = R["s"], R["w"]
rows, cols = round((R["n"] - s) / STEP), round((R["e"] - w) / STEP)
crop = np.zeros((rows, cols), np.uint8)
tree = np.zeros((rows, cols), np.uint8)
per_tile = round(3 / STEP)  # output cells per tile side

t0 = time.time()
done = missing = 0
for la in range(math.floor(s / 3) * 3, math.ceil(R["n"] / 3) * 3, 3):
    for lo in range(math.floor(w / 3) * 3, math.ceil(R["e"] / 3) * 3, 3):
        name = f"{'N' if la >= 0 else 'S'}{abs(la):02d}E{lo:03d}"
        try:
            with rasterio.open(URL.format(name)) as r:
                a = r.read(1, out_shape=(per_tile * PX, per_tile * PX), resampling=Resampling.nearest)
        except rasterio.errors.RasterioIOError:
            missing += 1  # open sea: WorldCover has no tile
            continue
        # Row 0 of the image is the tile's north edge; flip so row 0 is south, like the output grid.
        a = a[::-1].reshape(per_tile, PX, per_tile, PX)
        c = np.rint((a == CROP).mean(axis=(1, 3)) * 100).astype(np.uint8)
        t = np.rint((a == TREE).mean(axis=(1, 3)) * 100).astype(np.uint8)
        # Place the tile in the output grid, clipped to the region.
        r0, c0 = round((la - s) / STEP), round((lo - w) / STEP)
        rs, cs = max(0, r0), max(0, c0)
        re, ce = min(rows, r0 + per_tile), min(cols, c0 + per_tile)
        if rs < re and cs < ce:
            crop[rs:re, cs:ce] = c[rs - r0:re - r0, cs - c0:ce - c0]
            tree[rs:re, cs:ce] = t[rs - r0:re - r0, cs - c0:ce - c0]
        done += 1
        print(f"  {name} ({done} tiles, {time.time() - t0:.0f}s)", file=sys.stderr)

out = sys.argv[1]
with gzip.open(out, "wb", compresslevel=9) as f:
    f.write(crop.tobytes() + tree.tobytes())
json.dump({"source": "ESA WorldCover 2021 v200 (CC BY 4.0), sampled 5x5 per cell from the 1/16 overview",
           "s": s, "w": w, "step": STEP, "rows": rows, "cols": cols, "planes": ["cropland_pct", "tree_pct"],
           "order": "row-major, row 0 at the south edge"},
          open(os.path.join(os.path.dirname(out), "landcover.json"), "w"), indent=1)
print(f"{done} tiles, {missing} missing (sea), {os.path.getsize(out) / 2**20:.1f} MB -> {out}")
