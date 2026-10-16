#!/usr/bin/env python3
"""Build the traffic-pollution layer: a 14-day average of Sentinel-5P TROPOMI NO2 and its hotspots.

A single day of NO2 is patchy (clouds, orbit gaps) and noisy; two weeks averaged show where it
really piles up: city cores, highway corridors, power plants. NO2 in cities comes mostly from
vehicle engines, so the hotspots are a fair map of traffic pollution once power plants and
always-hot industrial sites are labelled separately.

Reads NASA GIBS tiles (TROPOMI_L2_Nitrogen_Dioxide_Tropospheric_Column, zoom 6), inverts the
published colour table back to molecules/cm2, averages per pixel, and writes:
  no2.png   Web Mercator image covering the tile block, our own colours, transparent where low
  no2.json  {"bounds": [[s, w], [n, e]], "days": [...], "median": v, "hotspots": [...]}
Uploads both to KV (keys no2-png, no2-json) with --upload. Needs Pillow.

Usage: python3 -I scripts/build-no2.py --out <dir> [--days 14] [--upload]
"""
import argparse, io, json, math, os, re, statistics, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LAYER = "TROPOMI_L2_Nitrogen_Dioxide_Tropospheric_Column"
CMAP = "https://gibs.earthdata.nasa.gov/colormaps/v1.3/OMI_Nitrogen_Dioxide_Tropo_Column.xml"
Z, X0, X1, Y0, Y1 = 6, 43, 47, 25, 27  # tile block covering 25-35.5 N, 66-88.5 E
BBOX = (25.0, 35.5, 66.0, 88.5)  # s, n, w, e: hotspots outside this are dropped
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--upload", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    table = colour_table()
    W, H = (X1 - X0 + 1) * 256, (Y1 - Y0 + 1) * 256
    total = [0.0] * (W * H)
    count = [0] * (W * H)
    days_used = []
    today = datetime.now(timezone.utc).date()
    for back in range(1, a.days + 1):  # start yesterday: today's tiles are usually still processing
        d = (today - timedelta(days=back)).isoformat()
        got = 0
        for tx in range(X0, X1 + 1):
            for ty in range(Y0, Y1 + 1):
                raw = get(f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{LAYER}/default/{d}/GoogleMapsCompatible_Level6/{Z}/{ty}/{tx}.png")
                if not raw:
                    continue
                im = Image.open(io.BytesIO(raw)).convert("RGBA")
                px = im.load()
                ox, oy = (tx - X0) * 256, (ty - Y0) * 256
                for y in range(256):
                    row = (oy + y) * W + ox
                    for x in range(256):
                        r, g, b, al = px[x, y]
                        if al == 0:
                            continue
                        v = table.get((r, g, b))
                        if v is None:
                            continue  # hatched "still processing" pixels and anything off-palette
                        total[row + x] += v
                        count[row + x] += 1
                        got += 1
        if got:
            days_used.append(d)
        print(f"{d}: {got} valid pixels")

    mean = [total[i] / count[i] if count[i] >= 3 else None for i in range(W * H)]

    def pix_latlon(x, y):
        return tile2lat(Y0 + (y + 0.5) / 256, Z), tile2lon(X0 + (x + 0.5) / 256, Z)

    # "Typical" level: median over the plains where people live (inside our region, below the
    # mountains), so ratios mean "times the usual air in Punjab/Haryana/UP", not "times the desert".
    plains = []
    for y in range(H):
        la = tile2lat(Y0 + (y + 0.5) / 256, Z)
        if not (BBOX[0] <= la <= 33.0):
            continue
        for x in range(W):
            v = mean[y * W + x]
            lo = tile2lon(X0 + (x + 0.5) / 256, Z)
            if v is not None and 70.0 <= lo <= BBOX[3]:
                plains.append(v)
    if not plains:
        sys.exit("no NO2 data")
    median = statistics.median(plains)

    # Our own palette: transparent near the regional background, then yellow -> red -> plum.
    stops = [(1.0, (255, 236, 140, 0)), (1.6, (255, 200, 80, 120)), (2.4, (240, 120, 40, 175)),
             (3.4, (205, 40, 30, 205)), (5.0, (120, 20, 70, 225))]

    def colour(ratio):
        if ratio <= stops[0][0]:
            return (0, 0, 0, 0)
        for (r0, c0), (r1, c1) in zip(stops, stops[1:]):
            if ratio <= r1:
                f = (ratio - r0) / (r1 - r0)
                return tuple(round(c0[i] + (c1[i] - c0[i]) * f) for i in range(4))
        return stops[-1][1]

    img = Image.new("RGBA", (W, H))
    out = img.load()
    for i, v in enumerate(mean):
        if v is not None:
            out[i % W, i // W] = colour(v / median)
    png = io.BytesIO()
    img.save(png, "PNG", optimize=True)
    open(os.path.join(a.out, "no2.png"), "wb").write(png.getvalue())

    # Hotspots: local maxima of a 5x5-smoothed field, at least 1.8x the regional median.
    def at(x, y):
        return mean[y * W + x] if 0 <= x < W and 0 <= y < H else None

    smooth = {}
    for y in range(2, H - 2):
        for x in range(2, W - 2):
            vs = [at(x + i, y + j) for i in range(-2, 3) for j in range(-2, 3)]
            vs = [v for v in vs if v is not None]
            if len(vs) >= 15:
                smooth[(x, y)] = sum(vs) / len(vs)
    peaks = []
    for (x, y), v in smooth.items():
        if v < 2.0 * median:
            continue
        if all(smooth.get((x + i, y + j), 0) <= v for i in range(-6, 7) for j in range(-6, 7) if (i, j) != (0, 0)):
            la, lo = pix_latlon(x, y)
            if BBOX[0] <= la <= BBOX[1] and BBOX[2] <= lo <= BBOX[3]:
                peaks.append((round(la, 3), round(lo, 3), round(v / median, 2)))
    peaks.sort(key=lambda p: -p[2])

    # Label each hotspot: power plant / industrial site if one is close, otherwise traffic in the nearest town.
    towns = json.load(open(os.path.join(ROOT, "site", "src", "towns.json"), encoding="utf-8"))
    # Our 17 named cities come first, so East Delhi reads "Delhi", not a suburb's name.
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
    for la, lo, ratio in peaks[:60]:
        town = min(towns, key=lambda t: km(la, lo, t[0], t[1]))
        tkm = km(la, lo, town[0], town[1])
        cc = town[5]  # country from the nearest big town (towns.json carries it)
        city = min(cities, key=lambda c: km(la, lo, c[0], c[1]))
        if km(la, lo, city[0], city[1]) < 35:
            town, tkm = [city[0], city[1], city[2], "", "", "", 0], km(la, lo, city[0], city[1])
        near_plant = min(plants, key=lambda p: km(la, lo, p[0], p[1]), default=None)
        pkm = km(la, lo, near_plant[0], near_plant[1]) if near_plant else 1e9
        in_city = town[6] == 0 and tkm < 15  # one of our 17 cities: NO2 there is mostly traffic
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
        get(f"{base}/no2-json", data=json.dumps(meta).encode(), method="PUT", headers={**auth, "Content-Type": "application/json"})
        print("uploaded to KV")


if __name__ == "__main__":
    main()
