#!/usr/bin/env python3
"""Build the traffic-pollution layer: a 14-day average of Sentinel-5P TROPOMI NO2 and its hotspots.

A single day of NO2 is patchy (clouds, orbit gaps) and noisy; two weeks averaged show where it
really piles up: city cores, highway corridors, power plants. NO2 in cities comes mostly from
vehicle engines, so the hotspots are a fair map of traffic pollution once power plants and
always-hot industrial sites are labelled separately.

Reads NASA GIBS tiles (TROPOMI_L2_Nitrogen_Dioxide_Tropospheric_Column, zoom 6) over all of Pakistan and
India, inverts the published colour table back to molecules/cm2, averages per pixel, and writes:
  no2.png   Web Mercator image covering the tile block, our own colours, transparent where low
  no2.json  {"bounds": [[s, w], [n, e]], "days": [...], "median": v, "hotspots": [...]}
Uploads both to KV (keys no2-png, no2-json) with --upload. Needs Pillow and numpy.

Colours and hotspot ratios are against the usual level around each place: the median over land in each
5-degree block, smoothed between blocks, so a city in the south stands out against the south's cleaner air
rather than against the northern plains' smog. "median" in no2.json is still the northern plains' level.

Usage: python3 -I scripts/build-no2.py --out <dir> [--days 14] [--upload] [--cache <dir>]
"""
import argparse, io, json, math, os, re, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LAYER = "TROPOMI_L2_Nitrogen_Dioxide_Tropospheric_Column"
CMAP = "https://gibs.earthdata.nasa.gov/colormaps/v1.3/OMI_Nitrogen_Dioxide_Tropo_Column.xml"
Z, X0, X1, Y0, Y1 = 6, 42, 49, 24, 31  # tile block covering the region, 5.5-37.5 N, 60.5-97.5 E (64 tiles)
PLAINS = (25.0, 33.0, 70.0, 88.5)  # s, n, w, e: the northern plains, for the published "median"
BLOCK = 5.0  # degrees: the baseline is the median over land in blocks this size
FLOOR = 0.4  # baseline never below this share of the plains median, so ocean and desert noise stay quiet
UA = {"User-Agent": "hamarihawa.org NO2 builder (+https://hamarihawa.org/about/)"}


def get(url, data=None, method="GET", headers=None):
    req = urllib.request.Request(url, data=data, method=method, headers={**UA, **(headers or {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return None
            if attempt == 2:
                raise
        except urllib.error.URLError:
            if attempt == 2:
                raise
        time.sleep(3 * (attempt + 1))


def colour_table():
    """rgb -> NO2 value (molecules/cm2), using the middle of each published band."""
    xml = get(CMAP).decode()
    table = {}
    for e in re.findall(r"<ColorMapEntry ([^>]*)/>", xml):
        if "nodata" in e:
            continue
        rgb = tuple(int(v) for v in re.search(r'rgb="([^"]+)"', e).group(1).split(","))
        lo, hi = re.search(r'value="[\[(]([^,]+),([^)\]]+)[)\]]"', e).groups()
        lo = 0.0 if "INF" in lo else float(lo)
        hi = 2.2e16 if "INF" in hi else float(hi)
        table[rgb] = max(0.0, (lo + hi) / 2)
    return table


def tile2lat(y, z):
    n = math.pi - 2 * math.pi * y / 2 ** z
    return math.degrees(math.atan(math.sinh(n)))


def tile2lon(x, z):
    return x / 2 ** z * 360 - 180


def countries():
    """0.25-degree cells inside Pakistan or India (data/places/countries.json): {(lat4, lon4): "PK" | "IN" | "PK+IN" | "mix"}."""
    cells = json.load(open(os.path.join(ROOT, "data", "places", "countries.json")))
    return {tuple(int(v) for v in k.split("_")): c for k, c in cells.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--cache", help="keep downloaded tiles here and reuse them (for local reruns)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    table = colour_table()
    keys = np.array([(r << 16) | (g << 8) | b for r, g, b in table], dtype=np.int64)
    vals = np.array(list(table.values()))
    order = np.argsort(keys)
    keys, vals = keys[order], vals[order]
    W, H = (X1 - X0 + 1) * 256, (Y1 - Y0 + 1) * 256
    total = np.zeros((H, W))
    count = np.zeros((H, W), dtype=np.int32)
    days_used = []
    today = datetime.now(timezone.utc).date()
    for back in range(1, a.days + 1):  # start yesterday: today's tiles are usually still processing
        d = (today - timedelta(days=back)).isoformat()
        got = 0
        for tx in range(X0, X1 + 1):
            for ty in range(Y0, Y1 + 1):
                cached = os.path.join(a.cache, f"{d}_{tx}_{ty}.png") if a.cache else None
                if cached and os.path.exists(cached):
                    raw = open(cached, "rb").read() or None
                else:
                    raw = get(f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{LAYER}/default/{d}/GoogleMapsCompatible_Level6/{Z}/{ty}/{tx}.png")
                    if cached:
                        os.makedirs(a.cache, exist_ok=True)
                        open(cached, "wb").write(raw or b"")
                if not raw:
                    continue
                px = np.asarray(Image.open(io.BytesIO(raw)).convert("RGBA"), dtype=np.int64)
                k = (px[..., 0] << 16) | (px[..., 1] << 8) | px[..., 2]
                i = np.clip(np.searchsorted(keys, k), 0, len(keys) - 1)
                # Hatched "still processing" pixels and anything off-palette don't match a table entry.
                ok = (px[..., 3] > 0) & (keys[i] == k)
                oy, ox = (ty - Y0) * 256, (tx - X0) * 256
                total[oy:oy + 256, ox:ox + 256] += np.where(ok, vals[i], 0.0)
                count[oy:oy + 256, ox:ox + 256] += ok
                got += int(ok.sum())
        if got:
            days_used.append(d)
        print(f"{d}: {got} valid pixels", flush=True)

    mean = np.where(count >= 3, total / np.maximum(count, 1), np.nan)
    lat = np.array([tile2lat(Y0 + (y + 0.5) / 256, Z) for y in range(H)])
    lon = np.array([tile2lon(X0 + (x + 0.5) / 256, Z) for x in range(W)])
    LA, LO = np.meshgrid(lat, lon, indexing="ij")
    cells = countries()
    c4 = np.array(sorted(cells))
    la4, lo4 = np.floor(LA * 4).astype(int), np.floor(LO * 4).astype(int)
    grid = np.zeros((c4[:, 0].max() - c4[:, 0].min() + 1, c4[:, 1].max() - c4[:, 1].min() + 1), dtype=bool)
    grid[c4[:, 0] - c4[:, 0].min(), c4[:, 1] - c4[:, 1].min()] = True
    gi, gj = la4 - c4[:, 0].min(), lo4 - c4[:, 1].min()
    inb = (gi >= 0) & (gi < grid.shape[0]) & (gj >= 0) & (gj < grid.shape[1])
    land = np.zeros((H, W), dtype=bool)
    land[inb] = grid[gi[inb], gj[inb]]
    # Cells a border runs through: test each pixel against the country outlines, so Bangladesh, Nepal and the
    # sea stay out without a blocky edge.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import geo
    borders = geo.Borders.load(os.path.join(ROOT, "data", "places", "borders.json"))
    mix = np.zeros_like(grid)
    for (a4, o4), c in cells.items():
        if c == "mix":
            mix[a4 - c4[:, 0].min(), o4 - c4[:, 1].min()] = True
    edge = np.zeros((H, W), dtype=bool)
    edge[inb] = mix[gi[inb], gj[inb]]
    for y, x in zip(*np.where(edge)):
        land[y, x] = bool(borders.which(float(lat[y]), float(lon[x])))
    valid = land & ~np.isnan(mean)

    plains = valid & (LA >= PLAINS[0]) & (LA <= PLAINS[1]) & (LO >= PLAINS[2]) & (LO <= PLAINS[3])
    if not plains.any():
        sys.exit("no NO2 data")
    median = float(np.median(mean[plains]))

    # The usual level around each place: the median over land in each 5-degree block (blocks with little
    # land take their neighbours' level), interpolated between block centres so there are no seams.
    bs, bw = math.floor(lat.min() / BLOCK), math.floor(lon.min() / BLOCK)
    nb_la, nb_lo = math.floor(lat.max() / BLOCK) - bs + 1, math.floor(lon.max() / BLOCK) - bw + 1
    bi, bj = (np.floor(LA / BLOCK) - bs).astype(int), (np.floor(LO / BLOCK) - bw).astype(int)
    blocks = np.full((nb_la, nb_lo), np.nan)
    for i in range(nb_la):
        for j in range(nb_lo):
            m = valid & (bi == i) & (bj == j)
            if m.sum() >= 2000:
                blocks[i, j] = np.median(mean[m])
    for _ in range(nb_la + nb_lo):
        if not np.isnan(blocks).any():
            break
        fill = blocks.copy()
        for i, j in zip(*np.where(np.isnan(blocks))):
            nb = [blocks[x, y] for x, y in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1))
                  if 0 <= x < nb_la and 0 <= y < nb_lo and not np.isnan(blocks[x, y])]
            if nb:
                fill[i, j] = sum(nb) / len(nb)
        blocks = fill
    blocks = np.where(np.isnan(blocks), median, blocks)
    fy = np.clip(LA / BLOCK - bs - 0.5, 0, nb_la - 1)
    fx = np.clip(LO / BLOCK - bw - 0.5, 0, nb_lo - 1)
    y0, x0 = np.floor(fy).astype(int), np.floor(fx).astype(int)
    y1, x1 = np.minimum(y0 + 1, nb_la - 1), np.minimum(x0 + 1, nb_lo - 1)
    wy, wx = fy - y0, fx - x0
    base = (blocks[y0, x0] * (1 - wy) * (1 - wx) + blocks[y0, x1] * (1 - wy) * wx
            + blocks[y1, x0] * wy * (1 - wx) + blocks[y1, x1] * wy * wx)
    base = np.maximum(base, FLOOR * median)
    ratio = mean / base

    # Our own palette: transparent near the local background, then yellow -> red -> plum.
    stops = [(1.0, (255, 236, 140, 0)), (1.6, (255, 200, 80, 120)), (2.4, (240, 120, 40, 175)),
             (3.4, (205, 40, 30, 205)), (5.0, (120, 20, 70, 225))]
    xs = [r for r, _ in stops]
    r_ = np.nan_to_num(ratio, nan=0.0)
    rgba = np.stack([np.interp(r_, xs, [c[i] for _, c in stops]) for i in range(4)], axis=-1)
    rgba[(r_ <= 1.0) | np.isnan(ratio) | ~land] = 0  # only Pakistan and India
    img = Image.fromarray(np.round(rgba).astype(np.uint8), "RGBA")
    png = io.BytesIO()
    img.save(png, "PNG", optimize=True)
    open(os.path.join(a.out, "no2.png"), "wb").write(png.getvalue())

    # The same picture in plain lat/lon rows for Google Earth, whose ground overlays assume an
    # equirectangular image (the Mercator one would sit up to ~30 km off).
    s_, n_ = tile2lat(Y1 + 1, Z), tile2lat(Y0, Z)
    geo = Image.new("RGBA", (W, H))
    for r in range(H):
        la = math.radians(n_ - (n_ - s_) * (r + 0.5) / H)
        ty = (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * 2 ** Z
        src = min(H - 1, max(0, int((ty - Y0) * 256)))
        geo.paste(img.crop((0, src, W, src + 1)), (0, r))
    geo_png = io.BytesIO()
    geo.save(geo_png, "PNG", optimize=True)
    open(os.path.join(a.out, "no2-geo.png"), "wb").write(geo_png.getvalue())

    # Hotspots: local maxima (13x13 pixels) of a 5x5-smoothed ratio field, on land, at least 2x the usual level.
    v = np.nan_to_num(ratio, nan=0.0)
    n = (~np.isnan(ratio)).astype(float)
    box5 = lambda f: np.lib.stride_tricks.sliding_window_view(np.pad(f, 2), (5, 5)).sum(axis=(2, 3))
    sums, cnt = box5(v), box5(n)
    smooth = np.where(cnt >= 15, sums / np.maximum(cnt, 1), 0.0)
    peak = np.lib.stride_tricks.sliding_window_view(np.pad(smooth, 6), (13, 13)).max(axis=(2, 3))
    ys, xs_ = np.where((smooth >= 2.0) & (smooth >= peak) & land)
    peaks = sorted(((round(float(lat[y]), 3), round(float(lon[x]), 3), round(float(smooth[y, x]), 2)) for y, x in zip(ys, xs_)),
                   key=lambda p: -p[2])

    # Label each hotspot: power plant / industrial site if one is close, otherwise traffic in the nearest town.
    towns = json.load(open(os.path.join(ROOT, "site", "src", "towns.json"), encoding="utf-8"))
    CELLS = json.load(open(os.path.join(ROOT, "data", "places", "countries.json")))
    # Our named cities come first, so East Delhi reads "Delhi", not a suburb's name.
    cities = [(float(m[1]), float(m[2]), m[3]) for m in re.finditer(
        r'lat: ([\d.]+), lon: ([\d.]+),.*?en: "([^"]+)"', open(os.path.join(ROOT, "site", "public", "cities.js"), encoding="utf-8").read())]
    plants = []
    src = os.path.join(ROOT, "site", "public", "sources")
    if os.path.exists(os.path.join(src, "carbonmapper.json")):
        for it in json.load(open(os.path.join(src, "carbonmapper.json")))["items"]:
            if it[3] in ("power", "industry"):
                plants.append((it[0], it[1], "Power plant" if it[3] == "power" else "Industrial plant"))
    coal = []
    if os.path.exists(os.path.join(src, "plants.json")):
        for it in json.load(open(os.path.join(src, "plants.json"), encoding="utf-8"))["items"]:
            plants.append((it[0], it[1], it[3]))
            if it[2] == "coal":
                coal.append((it[0], it[1]))
    if os.path.exists(os.path.join(src, "hotspots.json")):
        for it in json.load(open(os.path.join(src, "hotspots.json"), encoding="utf-8"))["items"]:
            if it[4] and it[4] != "Brick kiln" and it[2] >= 30:
                plants.append((it[0], it[1], it[4]))

    estates, kilns = [], []
    if os.path.exists(os.path.join(src, "osm-industrial.json")):
        estates = [it for it in json.load(open(os.path.join(src, "osm-industrial.json"), encoding="utf-8"))["items"] if it[3] >= 300]
    if os.path.exists(os.path.join(src, "kilns.json")):
        kilns = json.load(open(os.path.join(src, "kilns.json")))["items"]

    def km(a1, o1, a2, o2):
        return math.hypot(a1 - a2, (o1 - o2) * math.cos(math.radians(a1))) * 111.2

    hotspots = []
    for la, lo, ratio in peaks[:100]:
        town = min(towns, key=lambda t: km(la, lo, t[0], t[1]))
        tkm = km(la, lo, town[0], town[1])
        # Country from the country outlines' cell, or from the nearest big town where a border runs through it.
        cc = CELLS.get(f"{math.floor(la * 4)}_{math.floor(lo * 4)}")
        cc = cc if cc in ("PK", "IN") else town[5]
        city = min(cities, key=lambda c: km(la, lo, c[0], c[1]))
        if km(la, lo, city[0], city[1]) < 35:
            town, tkm = [city[0], city[1], city[2], "", "", "", 0], km(la, lo, city[0], city[1])
        near_plant = min(plants, key=lambda p: km(la, lo, p[0], p[1]), default=None)
        pkm = km(la, lo, near_plant[0], near_plant[1]) if near_plant else 1e9
        in_city = town[6] == 0 and tkm < 15  # one of our named cities: NO2 there is mostly traffic
        box = lambda it, d: abs(it[0] - la) < d / 111 and abs(it[1] - lo) < d / 95
        big_estates = [it for it in estates if box(it, 8) and km(la, lo, it[0], it[1]) < 8]
        n_kilns = sum(1 for it in kilns if box(it, 10) and km(la, lo, it[0], it[1]) < 10)
        coal_near = any(km(la, lo, p[0], p[1]) < 8 for p in coal)
        if in_city and not coal_near:
            kind, site = "traffic", town[2]  # big-city cores: traffic first unless a coal plant sits right there
        elif pkm < 12 and (tkm > 8 or pkm < tkm):
            kind, site = "plant", near_plant[2]
        elif in_city:
            kind, site = "traffic", town[2]
        elif big_estates:
            best = max(big_estates, key=lambda it: it[3])
            kind, site = "industry", best[2] or town[2]
        elif n_kilns >= 80:
            kind, site = "kilns", f"{n_kilns} kilns"
        elif tkm < 25:
            kind, site = "traffic", town[2]
        else:
            kind, site = "corridor", town[2]
        hotspots.append([la, lo, ratio, kind, site, round(tkm), town[2], cc])

    s, n = tile2lat(Y1 + 1, Z), tile2lat(Y0, Z)
    w, e = tile2lon(X0, Z), tile2lon(X1 + 1, Z)
    meta = {"source": "Sentinel-5P TROPOMI tropospheric NO2 via NASA GIBS; 14-day average by HamariHawa",
            "built": datetime.now(timezone.utc).isoformat(timespec="minutes"), "days": sorted(days_used),
            "baseline": "median over land in 5-degree blocks, smoothed; ratios are against it",
            "bounds": [[round(s, 4), round(w, 4)], [round(n, 4), round(e, 4)]], "median": median, "hotspots": hotspots}
    open(os.path.join(a.out, "no2.json"), "w").write(json.dumps(meta, ensure_ascii=False))
    print(f"{len(days_used)} days, median {median:.2e}, {len(hotspots)} hotspots, png {len(png.getvalue()) // 1024} KB")
    for h in hotspots[:12]:
        print("  ", h)

    if a.upload:
        acct, ns, tok = os.environ["CLOUDFLARE_ACCOUNT_ID"], os.environ["KV_NAMESPACE_ID"], os.environ["CLOUDFLARE_API_TOKEN"]
        base = f"https://api.cloudflare.com/client/v4/accounts/{acct}/storage/kv/namespaces/{ns}/values"
        auth = {"Authorization": f"Bearer {tok}"}
        get(f"{base}/no2-png", data=png.getvalue(), method="PUT", headers={**auth, "Content-Type": "application/octet-stream"})
        get(f"{base}/no2-geo-png", data=geo_png.getvalue(), method="PUT", headers={**auth, "Content-Type": "application/octet-stream"})
        get(f"{base}/no2-json", data=json.dumps(meta).encode(), method="PUT", headers={**auth, "Content-Type": "application/json"})
        print("uploaded to KV")


if __name__ == "__main__":
    main()
