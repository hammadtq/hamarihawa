# The close-up of the place where the fall in brightness begins. python make_onset_image.py <output folder>
# Writes ravi-onset-2022-03-13.jpg: true colour (bands 4, 3, 2) of the Sentinel-2 Level-2A scene of the northern tile, reflectance
# times 3.2, clipped, at 10 m a pixel. A white ring marks where the dark channel meets the river and a white square the place
# where the 2020 study sampled the Mehmood Booti drain; both positions are in data.json under 'junction'.
# Needs numpy and rasterio, and macOS "sips" to write the JPEG. The scene is picked by select_dates.pick.
import json, math, os, subprocess, sys, urllib.request
import numpy as np, rasterio
from rasterio.enums import Resampling
from rasterio.warp import transform
from rasterio.windows import from_bounds
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from select_dates import pick, post, BBOX
OUT, DATE, GAIN = sys.argv[1], "2022-03-13", 3.2
BOX = (74.306, 31.604, 74.366, 31.646)                  # west, south, east, north
JUNCTION, SAMPLED = (74.3347, 31.6264), (74.3344, 31.6194)
F = post("https://planetarycomputer.microsoft.com/api/stac/v1/search", {"collections": ["sentinel-2-l2a"], "bbox": BBOX, "datetime": DATE + "T00:00:00Z/" + DATE + "T23:59:59Z", "limit": 50})["features"]
it = pick([f for f in F if f["properties"]["s2:mgrs_tile"] == "43SDR"])
TOKEN = json.load(urllib.request.urlopen("https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-2-l2a", timeout=90))["token"]
xs, ys = transform("EPSG:4326", "EPSG:32643", [BOX[0], BOX[2]], [BOX[1], BOX[3]])
x0, y0, x1, y1 = [round(v / 10) * 10 for v in (xs[0], ys[0], xs[1], ys[1])]; H, W = int((y1 - y0) / 10), int((x1 - x0) / 10)
off = 1000.0 if float(it["properties"].get("s2:processing_baseline", "0")) >= 4 else 0.0
out = []
for b in ("B04", "B03", "B02"):
    with rasterio.open(it["assets"][b]["href"] + "?" + TOKEN) as src:
        v = src.read(1, window=from_bounds(x0, y0, x1, y1, src.transform), out_shape=(H, W), resampling=Resampling.nearest, boundless=True, fill_value=0).astype("float32")
    out.append(np.clip(np.clip(v - off, 0, None) / 1e4 * GAIN, 0, 1))
a = np.repeat(np.repeat((np.stack(out) * 255).astype("uint8"), 2, axis=1), 2, axis=2)   # 5 m a pixel on the page, so the marks can be thin
def spot(p):
    mx, my = transform("EPSG:4326", "EPSG:32643", [p[0]], [p[1]]); return (mx[0] - x0) / 5.0, (y1 - my[0]) / 5.0
rr, cc = np.mgrid[0:2 * H, 0:2 * W]
c, r = spot(JUNCTION); d = np.hypot(cc - c, rr - r); a[:, (d > 44) & (d < 47.5)] = 255
c, r = spot(SAMPLED); e = np.maximum(abs(cc - c), abs(rr - r)); a[:, (e > 9) & (e < 12.5)] = 255
tmp = os.path.join(OUT, "_tmp.png")
with rasterio.open(tmp, "w", driver="PNG", width=2 * W, height=2 * H, count=3, dtype="uint8") as o: o.write(a)
subprocess.check_call(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "84", tmp, "--out", os.path.join(OUT, "ravi-onset-" + DATE + ".jpg")], stdout=subprocess.DEVNULL)
for f in (tmp, tmp + ".aux.xml"):
    if os.path.exists(f): os.remove(f)
print("image written for", DATE, it["id"], 2 * W, 2 * H)
