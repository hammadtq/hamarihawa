# One date: Sentinel-2 water colour along the Ravi by river kilometre (centre line in inputs/ravi_line.json).
# python measure_ravi.py inputs <YYYY-MM-DD>            -> inputs/profiles/<date>.csv (500 m bins)
# python measure_ravi.py inputs <YYYY-MM-DD> --north    -> inputs/profiles_northern_tile/<date>.csv: the northern tile wherever
#                                                          it has data, which moves the join between tiles 10 km downstream
# python measure_ravi.py inputs <YYYY-MM-DD> --checks   -> inputs/profiles_checks/<variant>/<date>.csv, three variants from one
#     read of the image: "rerun" (the standard measurement again), "near300" (water within 300 m of the centre line, not
#     700 m, which leaves out side channels) and "core" (only pixels with water for 20 m in every direction, which does
#     not depend on which way the river runs)
# Needs numpy and rasterio; about 4 minutes a date. Reads Sentinel-2 L2A from Microsoft Planetary Computer (public,
# signed links). The scenes used are written next to each profile as <date>.scenes.json.
import json, math, sys, os, time, urllib.request
for k_, v_ in {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR", "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES", "GDAL_HTTP_MULTIPLEX": "YES", "VSI_CACHE": "TRUE", "VSI_CACHE_SIZE": "100000000", "GDAL_CACHEMAX": "512", "GDAL_HTTP_MAX_RETRY": "5", "GDAL_HTTP_RETRY_DELAY": "3"}.items(): os.environ.setdefault(k_, v_)
import numpy as np, rasterio
from rasterio.windows import from_bounds
D, IDS = sys.argv[1], [a for a in sys.argv[2:] if not a.startswith("--")]
NORTH, CHECKS = "--north" in sys.argv, "--checks" in sys.argv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from select_dates import pick
K0, K1, CH, BUF, BIN = 45000.0, 135000.0, 4000.0, 900.0, 500.0
import urllib.parse
def getj(url, body=None):
    for a in range(6):
        try:
            rq = urllib.request.Request(url, body, {"Content-Type": "application/json"}) if body else url
            return json.load(urllib.request.urlopen(rq, timeout=90))
        except Exception: time.sleep(6)
    sys.exit("failed " + url[:80])
# Microsoft Planetary Computer's public copy (signed links, no account); argument is the date
DATE = IDS[0]
F = getj("https://planetarycomputer.microsoft.com/api/stac/v1/search", json.dumps({"collections": ["sentinel-2-l2a"], "bbox": [74.2, 31.45, 74.45, 31.7], "datetime": f"{DATE}T00:00:00Z/{DATE}T23:59:59Z", "limit": 20}).encode())["features"]
ITS = {}
_m = os.path.join(D, "scenes.json")
REC = next((x.get("planetary_computer", {}) for x in (json.load(open(_m))["dates"] if os.path.exists(_m) else []) if x["date"] == DATE), {})
for t in ("43RDQ", "43SDR"):
    its = [f for f in F if f["properties"]["s2:mgrs_tile"] == t]
    if not its: continue
    want = REC.get(t, {}).get("id")                         # the scene recorded in inputs/scenes.json, so a rerun reads the same one
    if want and "--latest" not in sys.argv:
        got = [f for f in its if f["id"] == want]
        if not got: sys.exit("%s %s: the recorded scene %s is no longer in the catalogue; run with --latest to apply the rule to what is there now" % (DATE, t, want))
        ITS[t] = got[0]
    else: ITS[t] = pick(its)                                # no record, or --latest: one scene per tile by the fixed rule (select_dates.pick)
ORDER = ("43SDR", "43RDQ") if NORTH else ("43RDQ", "43SDR")  # the first tile is used wherever it has data; the standard run takes the southern one, so the join is at its northern edge
ITS = [ITS[t] for t in ORDER if t in ITS]
if len(ITS) < 2: sys.exit(DATE + ": tiles found " + str(len(ITS)))
TOKEN = getj("https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-2-l2a")["token"]
VARIANTS = [("rerun", 700, False), ("near300", 300, False), ("core", 700, True)] if CHECKS else [("", 700, False)]
BASE = D + ("/profiles_checks" if CHECKS else "/profiles_northern_tile" if NORTH else "/profiles")
OUTS = {v[0]: (f"{BASE}/{v[0]}/{DATE}.csv" if v[0] else f"{BASE}/{DATE}.csv") for v in VARIANTS}
if all(os.path.exists(f) for f in OUTS.values()): sys.exit(0)
for f in OUTS.values(): os.makedirs(os.path.dirname(f), exist_ok=True)
SCENES = [{"tile": it["properties"]["s2:mgrs_tile"], "id": it["id"], "processing_baseline": it["properties"].get("s2:processing_baseline")} for it in ITS]
rv = [[p["x"], p["y"]] for p in json.load(open(D + "/ravi_line.json"))["points"]]
# densify the centre line to 25 m and keep the chainage of every point
px_, py_, pc_ = [], [], []; c = 0.0
for (ax, ay), (bx, by) in zip(rv, rv[1:]):
    L = math.hypot(bx - ax, by - ay); n = max(int(L // 25), 1)
    for k in range(n): px_.append(ax + (bx - ax) * k / n); py_.append(ay + (by - ay) * k / n); pc_.append(c + L * k / n)
    c += L
PX, PY, PC = np.array(px_), np.array(py_), np.array(pc_)
BANDS = ["B03", "B04", "B08", "B05", "B11", "SCL"]
SRC = [{b: rasterio.open(it["assets"][b]["href"] + "?" + TOKEN) for b in BANDS} for it in ITS]
OFF = [1000.0 if float(it["properties"].get("s2:processing_baseline", "0")) >= 4 else 0.0 for it in ITS]
# read each band once for the whole corridor box (one ranged read per tile), then cut the stretches out of memory
sel_ = (PC >= K0 - 1500) & (PC < K1 + 1500)
GX0 = math.floor((PX[sel_].min() - BUF - 100) / 20) * 20; GX1 = math.ceil((PX[sel_].max() + BUF + 100) / 20) * 20
GY0 = math.floor((PY[sel_].min() - BUF - 100) / 20) * 20; GY1 = math.ceil((PY[sel_].max() + BUF + 100) / 20) * 20
GH, GW = int((GY1 - GY0) / 10), int((GX1 - GX0) / 10)
def box(k):
    sel = (PC >= k - 1000) & (PC < k + CH + 1000); lx, ly = PX[sel], PY[sel]
    return (math.floor((lx.min() - BUF) / 20) * 20, math.floor((ly.min() - BUF) / 20) * 20, math.ceil((lx.max() + BUF) / 20) * 20, math.ceil((ly.max() + BUF) / 20) * 20)
BOXES = [box(K0 + i * CH) for i in range(int((K1 - K0) / CH))]
def readall(b):
    out = np.zeros((GH, GW), "uint16")
    for S_, off in zip(SRC, OFF):
        src = S_[b]; B_ = src.bounds; f = int(round(abs(src.transform.a) / 10))
        for (bx0, by0, bx1, by1) in BOXES:
            x0 = max(bx0, B_.left); x1 = min(bx1, B_.right); y0 = max(by0, B_.bottom); y1 = min(by1, B_.top)
            if x1 <= x0 or y1 <= y0: continue
            a = None
            for attempt in range(4):
                try: a = src.read(1, window=from_bounds(x0, y0, x1, y1, src.transform)); break
                except Exception: time.sleep(8)
            if a is None: sys.exit(DATE + ": read failed " + b)
            if f > 1: a = np.repeat(np.repeat(a, f, 0), f, 1)
            if b != "SCL" and off: a = np.where(a > 0, np.clip(a.astype("int32") - int(off), 1, None), 0).astype("uint16")
            r0 = int(round((GY1 - y1) / 10)); c0 = int(round((x0 - GX0) / 10)); h = min(a.shape[0], GH - r0); w = min(a.shape[1], GW - c0)
            blk = out[r0:r0+h, c0:c0+w]; out[r0:r0+h, c0:c0+w] = np.where(blk > 0, blk, a[:h, :w])
    return out
ALL = {b: readall(b) for b in BANDS}
def rd(b, bounds, shape):
    c0 = int(round((bounds[0] - GX0) / 10)); r0 = int(round((GY1 - bounds[3]) / 10))
    return ALL[b][r0:r0+shape[0], c0:c0+shape[1]].astype("float32")
def runlen(m):  # length of the run of True through each cell, along rows
    out = np.zeros(m.shape, "int32")
    for i in range(m.shape[0]):
        row = m[i]
        if not row.any(): continue
        d = np.diff(np.concatenate(([0], row.astype("int8"), [0]))); st = np.nonzero(d == 1)[0]; en = np.nonzero(d == -1)[0]
        for s, e in zip(st, en): out[i, s:e] = e - s
    return out
def core(m):   # True where every pixel within 20 m (a disc two pixels in radius) is water too
    out = m.copy(); H_, W_ = m.shape
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if (dy or dx) and dy * dy + dx * dx <= 4:
                sh = np.zeros_like(m); sh[max(dy, 0):H_ + min(dy, 0), max(dx, 0):W_ + min(dx, 0)] = m[max(-dy, 0):H_ + min(-dy, 0), max(-dx, 0):W_ + min(-dx, 0)]; out &= sh
    return out
ACC = {v[0]: {} for v in VARIANTS}
k = K0
while k < K1:
    sel = (PC >= k - 1000) & (PC < k + CH + 1000)
    lx, ly, lc = PX[sel], PY[sel], PC[sel]
    x0 = math.floor((lx.min() - BUF) / 20) * 20; x1 = math.ceil((lx.max() + BUF) / 20) * 20; y0 = math.floor((ly.min() - BUF) / 20) * 20; y1 = math.ceil((ly.max() + BUF) / 20) * 20
    H, W = int((y1 - y0) / 10), int((x1 - x0) / 10); bounds = (x0, y0, x1, y1)
    g, r, n, re1, sw, scl = [rd(b, bounds, (H, W)) for b in BANDS]
    valid = (g > 0) & (r > 0) & (sw > 0)
    g = np.clip(g, 1, None) / 1e4; r = np.clip(r, 1, None) / 1e4; n = np.clip(n, 1, None) / 1e4; re1 = np.clip(re1, 1, None) / 1e4; sw = np.clip(sw, 1, None) / 1e4
    cloudy = np.isin(scl, (3, 8, 9, 10))
    water = valid & ((g - sw) / (g + sw) > 0.0) & (n < 0.15) & ~cloudy
    rows, cols = np.nonzero(water)
    if len(rows):
        X = x0 + (cols + 0.5) * 10; Y = y1 - (rows + 0.5) * 10
        dist = np.empty(len(rows), "float32"); kc = np.empty(len(rows), "float32")
        for s in range(0, len(rows), 4000):
            d2 = (X[s:s+4000, None] - lx[None, :]) ** 2 + (Y[s:s+4000, None] - ly[None, :]) ** 2; j = d2.argmin(1)
            dist[s:s+4000] = np.sqrt(d2[np.arange(len(j)), j]); kc[s:s+4000] = lc[j]
        for vname, within, use_core in VARIANTS:
            near = dist <= within                              # the river and its braids, not ponds further off
            wm = np.zeros((H, W), bool); wm[rows[near], cols[near]] = True
            # width: the shorter of the east-west and north-south runs of water through the pixel; the "core" variant
            # instead marks a pixel as wide (40) only if the water reaches 20 m from it in every direction
            wid = np.where(core(wm), 40, 0) if use_core else np.minimum(runlen(wm), runlen(wm.T).T) * 10
            keep = near & (kc >= k) & (kc < k + CH); acc = ACC[vname]
            for rr, cc, kk in zip(rows[keep], cols[keep], kc[keep]):
                acc.setdefault(int(kk // BIN), []).append((wid[rr, cc], r[rr, cc], g[rr, cc], n[rr, cc], re1[rr, cc], sw[rr, cc]))
    # share of the chunk's corridor that had data and was not cloud, for the record
    k += CH
for vname, acc in ACC.items():
    rowsout = ["km,water_px,median_width_m,red,green,nir,rededge1,red_wide,ndti_wide,ndci_wide,wide_px"]
    for b in range(int(K0 // BIN), int(K1 // BIN)):
        v = np.array(acc.get(b, []), "float32")
        if len(v) < 10: rowsout.append(f"{b * BIN / 1000:.1f},{len(v)},,,,,,,,,"); continue
        wide = v[v[:, 0] >= 40]                                    # pixels in water at least 40 m across: little bank in them
        med = np.median(v, 0)
        if len(wide) >= 10:
            mw = np.median(wide, 0); extra = f"{mw[1]:.4f},{(mw[1]-mw[2])/(mw[1]+mw[2]):.3f},{(mw[4]-mw[1])/(mw[4]+mw[1]):.3f},{len(wide)}"
        else: extra = f",,,{len(wide)}"
        rowsout.append(f"{b * BIN / 1000:.1f},{len(v)},{med[0]:.0f},{med[1]:.4f},{med[2]:.4f},{med[3]:.4f},{med[4]:.4f},{extra}")
    open(OUTS[vname], "w").write("\n".join(rowsout) + "\n")
    json.dump(SCENES, open(OUTS[vname][:-4] + ".scenes.json", "w"))
print(DATE, "done", [(v, sum(1 for x in a.values() if len(x) >= 10)) for v, a in ACC.items()])
