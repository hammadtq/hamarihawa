# The two satellite pictures in the Ravi report. python make_images.py inputs <output folder>
# Writes ravi-2026-10-18.jpg (the river passing north-west Lahore) and ravi-above-below.jpg (two 4 km squares of the same
# image, above and below the city). True colour: bands 4, 3, 2 of the Sentinel-2 Level-2A scene, reflectance times 3.2,
# clipped, at 20 m a pixel, with the same scaling everywhere so the two squares can be compared.
# Needs numpy and rasterio, and macOS "sips" to write the JPEG files. The scenes are picked by select_dates.pick.
import json, math, os, subprocess, sys, urllib.request
import numpy as np, rasterio
from rasterio.enums import Resampling
from rasterio.warp import transform
from rasterio.windows import from_bounds
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from select_dates import pick, post, BBOX
INP, OUT = sys.argv[1], sys.argv[2]
DATE, GAIN = "2026-10-18", 3.2
WIDE = (74.215, 31.535, 74.375, 31.65)        # west, south, east, north
SQUARES, HALF = (64.0, 104.0), 2000.0         # line kilometres of the two close-ups; half their width in metres
F = post("https://planetarycomputer.microsoft.com/api/stac/v1/search", {"collections": ["sentinel-2-l2a"], "bbox": BBOX, "datetime": DATE + "T00:00:00Z/" + DATE + "T23:59:59Z", "limit": 50})["features"]
ITS = [pick([f for f in F if f["properties"]["s2:mgrs_tile"] == t]) for t in ("43RDQ", "43SDR")]   # southern tile first, as in measure_ravi.py
TOKEN = json.load(urllib.request.urlopen("https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-2-l2a", timeout=90))["token"]
def rgb(x0, y0, x1, y1):
    x0, y0, x1, y1 = [round(v / 20) * 20 for v in (x0, y0, x1, y1)]; H, W = int((y1 - y0) / 20), int((x1 - x0) / 20); out = []
    for b in ("B04", "B03", "B02"):
        a = np.zeros((H, W), "float32")
        for it in ITS:
            off = 1000.0 if float(it["properties"].get("s2:processing_baseline", "0")) >= 4 else 0.0
            with rasterio.open(it["assets"][b]["href"] + "?" + TOKEN) as src:
                v = src.read(1, window=from_bounds(x0, y0, x1, y1, src.transform), out_shape=(H, W), resampling=Resampling.nearest, boundless=True, fill_value=0).astype("float32")
            a = np.where(a > 0, a, np.where(v > 0, np.clip(v - off, 1, None), 0))
        out.append(np.clip(a / 1e4 * GAIN, 0, 1))
    return (np.stack(out) * 255).astype("uint8")
def save(a, name, width, height, quality):
    tmp = os.path.join(OUT, "_tmp.png")
    with rasterio.open(tmp, "w", driver="PNG", width=a.shape[2], height=a.shape[1], count=3, dtype="uint8") as o: o.write(a)
    subprocess.check_call(["sips", "-z", str(height), str(width), "-s", "format", "jpeg", "-s", "formatOptions", str(quality), tmp, "--out", os.path.join(OUT, name)], stdout=subprocess.DEVNULL)
    for f in (tmp, tmp + ".aux.xml"):
        if os.path.exists(f): os.remove(f)
xs, ys = transform("EPSG:4326", "EPSG:32643", [WIDE[0], WIDE[2]], [WIDE[1], WIDE[3]])
a = rgb(xs[0], ys[0], xs[1], ys[1]); save(a, "ravi-2026-10-18.jpg", 1300, int(round(1300.0 * a.shape[1] / a.shape[2])), 80)
LINE = json.load(open(os.path.join(INP, "ravi_line.json")))["points"]; parts = []
for km in SQUARES:
    p = min(LINE, key=lambda q: abs(q["km"] - km)); parts.append(rgb(p["x"] - HALF, p["y"] - HALF, p["x"] + HALF, p["y"] + HALF))
gap = np.full((3, parts[0].shape[1], 6), 255, "uint8"); a = np.concatenate([parts[0], gap, parts[1]], axis=2)
save(a, "ravi-above-below.jpg", a.shape[2] * 4, a.shape[1] * 4, 84)
print("images written for", DATE, [it["id"] for it in ITS])
