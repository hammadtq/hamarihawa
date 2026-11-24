# People living near the open drains that OpenStreetMap has mapped around Lahore.
# python population_near_drains.py   -> inputs/population_near_drains.json   (needs numpy and rasterio; reads one window of a public file)
# Population: Meta / Data for Good "High Resolution Population Density Maps", general population, 1 arc-second (about 30 m),
# public bucket dataforgood-fb-data (CC BY 4.0). Drains: inputs/osm_waterways.json. Distances use the grid's own cells (about 31 m by 26 m).
import json, math, os, collections
import numpy as np, rasterio
from rasterio.windows import from_bounds
HERE = os.path.dirname(os.path.abspath(__file__)); INP = os.path.join(HERE, "inputs")
URL = "https://dataforgood-fb-data.s3.amazonaws.com/hrsl-cogs/hrsl_general/v1.5/cog_globallat_30_lon_70_general-v1.5.2.tif"
W_, S_, E_, N_ = 74.05, 31.30, 74.55, 31.75
with rasterio.open("/vsicurl/" + URL) as ds:
    w = from_bounds(W_, S_, E_, N_, ds.transform).round_offsets().round_lengths()
    pop = ds.read(1, window=w).astype("float64"); tr = ds.window_transform(w)
pop = np.where(np.isnan(pop) | (pop < 0), 0, pop)
X0, Y0, R = tr.c, tr.f, tr.a; H, W = pop.shape
IRR = ("distribut", "minor", "canal road", "brb", "doab", "chenab", "bedian", "branch", "hayr", "نہر", "برانچ")  # irrigation channels, left out
def klass(t):
    n = (t.get("name") or t.get("name:en") or "").lower(); w = t.get("waterway")
    if t.get("tunnel") in ("culvert", "yes", "covered") or t.get("covered") == "yes": return None
    if any(k in n for k in IRR): return None
    if w == "drain": return n or "(unnamed drain)"
    if w == "canal" and "drain" in n: return n
    if w == "stream" and ("نالہ" in n or "nala" in n or "nullah" in n): return n
    return None
my = 110946.0; mx = 111320.0 * math.cos(math.radians((S_ + N_) / 2))
mask = np.zeros((H, W), bool); length = collections.Counter(); kept = []
for e in json.load(open(os.path.join(INP, "osm_waterways.json"), encoding="utf-8"))["elements"]:
    k = klass(e["tags"])
    if not k: continue
    kept.append(e["id"]); g = e["geometry"]
    for a, b in zip(g[:-1], g[1:]):
        L = math.hypot((b["lon"] - a["lon"]) * mx, (b["lat"] - a["lat"]) * my); n = max(1, int(L / 10))
        for i in range(n + 1):
            lo = a["lon"] + (b["lon"] - a["lon"]) * i / n; la = a["lat"] + (b["lat"] - a["lat"]) * i / n
            c, r = int((lo - X0) / R), int((Y0 - la) / R)
            if 0 <= r < H and 0 <= c < W: mask[r, c] = True; length[k] += L / (n + 1)
cy, cx = R * my, R * mx; dist = np.full((H, W), 1e9); ry, rx = int(1000 / cy) + 1, int(1000 / cx) + 1
for dy in range(-ry, ry + 1):
    for dx in range(-rx, rx + 1):
        d = math.hypot(dy * cy, dx * cx)
        if d > 1000: continue
        sh = np.zeros_like(mask)
        ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
        xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
        sh[yd, xd] = mask[ys, xs]; dist[sh & (dist > d)] = d
out = {"population_file": URL, "window_w_s_e_n": [W_, S_, E_, N_], "population_in_window": int(round(pop.sum())),
       "drain_km_by_name": {k: round(v / 1000, 1) for k, v in length.most_common()}, "drain_km_total": round(sum(length.values()) / 1000, 1),
       "osm_way_ids_used": kept, "within_m": {str(r): int(round(pop[dist <= r].sum())) for r in (100, 250, 500, 1000)}}
json.dump(out, open(os.path.join(INP, "population_near_drains.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: v for k, v in out.items() if k != "osm_way_ids_used"})
