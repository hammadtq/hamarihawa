#!/usr/bin/env python3
"""Fresh link-preview images (og:image, 1200x630) for the live map and every city page, drawn from the
site's own live data in the style of scripts/build-og.py.

Each city card shows that city's last 24 hours of fires within 250 km, the upwind wedge and the wind,
counted as the city page counts them (src/air.js: wind from the hourly grid, upwind = within 45 degrees, calm below
3 km/h). The live map's card is build-og.py's map with today's fires and counts.

All images go to KV as ONE value, "og-live" (so the hourly refresh costs 24 of the free plan's 1,000 daily
writes), laid out as b"HHOG1", a 4-byte big-endian header length, a JSON header
{"generated": ms, "items": {id: [offset, length]}}, then the JPEGs. The Worker serves /og/live/<id>.jpg
from it. Nothing here takes input from visitors.

Usage: python3 -I scripts/build-og-live.py [--out DIR] [--upload]
Fonts: scripts/fonts/ (Kalam and Inter, SIL Open Font License). Needs Pillow.
"""
import argparse, importlib.util, io, json, math, os, random, struct, sys, time, urllib.request
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITE = "https://hamarihawa.org"
FONTS = os.path.join(ROOT, "scripts", "fonts")
KALAM, INTER = os.path.join(FONTS, "Kalam-Bold.ttf"), os.path.join(FONTS, "Inter.ttf")
spec = importlib.util.spec_from_file_location("og", os.path.join(ROOT, "scripts", "build-og.py"))
og = importlib.util.module_from_spec(spec)
spec.loader.exec_module(og)
W, H, INK, INK2, FIRE, PAPER = og.W, og.H, og.INK, og.INK2, og.FIRE, og.PAPER
GREY, BLUE = (178, 178, 182), (47, 111, 159)
KM, UPWIND, CALM, BIN = 250, 45, 3, 5
DIRS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]


def get(path):
    req = urllib.request.Request(SITE + path, headers={"User-Agent": "hamarihawa.org og-live"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def wind_at(g, lat, lon):
    """[speed km/h, direction it comes from] at a point, bilinear on the grid, as src/air.js windAt."""
    if not g or not g.get("speed"):
        return None
    x, y = (lon - g["lon0"]) / g["step"], (lat - g["lat0"]) / g["step"]
    if x < 0 or y < 0 or x > g["nx"] - 1 or y > g["ny"] - 1:
        return None
    x0, y0 = min(g["nx"] - 2, int(x)), min(g["ny"] - 2, int(y))
    fx, fy = x - x0, y - y0
    u = v = 0.0
    for yy, xx, w in ((y0, x0, (1 - fx) * (1 - fy)), (y0, x0 + 1, fx * (1 - fy)), (y0 + 1, x0, (1 - fx) * fy), (y0 + 1, x0 + 1, fx * fy)):
        i = yy * g["nx"] + xx
        s, r = g["speed"][i], math.radians(g["dir"][i])
        u -= w * s * math.sin(r)
        v -= w * s * math.cos(r)
    return math.hypot(u, v), (math.degrees(math.atan2(-u, -v)) + 360) % 360


def distinct(rows):
    """Distinct fire spots, as scripts/build-feed.py distinct() counts them for the city pages: one row per
    ~400 m VIIRS spot (rows are newest first, so the newest detection is kept), plus MODIS detections no
    VIIRS satellite caught within about a kilometre. Row: [lat, lon, t, frp, sat]; sat 0-2 VIIRS, 3-4 MODIS."""
    spots, grid = {}, set()
    for r in rows:
        if r[4] < 3:
            spots.setdefault((round(r[0] / 0.004), round(r[1] / 0.004)), r)
            grid.add((round(r[0] / 0.01), round(r[1] / 0.01)))
    for r in rows:
        if r[4] >= 3:
            g = (round(r[0] / 0.01), round(r[1] / 0.01))
            if not any((g[0] + i, g[1] + j) in grid for i in (-1, 0, 1) for j in (-1, 0, 1)):
                spots.setdefault(("m",) + g, r)
    return list(spots.values())


def dist(a, b, c, d):
    p = math.radians
    return 2 * 6371 * math.asin(math.sqrt(math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2))


def bearing(a, b, c, d):
    p = math.radians
    y = math.sin(p(d - b)) * math.cos(p(c))
    x = math.cos(p(a)) * math.sin(p(c)) - math.sin(p(a)) * math.cos(p(c)) * math.cos(p(d - b))
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def angle(a, b):
    d = abs(a - b) % 360
    return 360 - d if d > 180 else d


def jpeg(img):
    b = io.BytesIO()
    img.save(b, "JPEG", quality=84, optimize=True, progressive=True)
    return b.getvalue()


def stamp(ms):
    t = time.gmtime(ms / 1000 + 5 * 3600)  # Pakistan time, as the daily pages
    return f"{t.tm_mday} {time.strftime('%B', t)}, {t.tm_hour:02d}:{t.tm_min:02d} PKT"


MAP_H = H - 78  # the map fills the card above the dark footer band


def text_box(img, d, lines, F):
    """The words, in a white box at the top left. The map's centre (the city) stays clear, so the square
    WhatsApp crops from the middle of the card shows the map."""
    x0, y0, x1 = 22, 22, 352
    y = y0 + 20
    rows = []
    for kind, txt in lines:
        f = {"brand": F(KALAM, 34), "big": F(KALAM, 46 if len(txt) < 16 else 38), "mid": F(KALAM, 30),
             "body": F(INTER, 19, 400), "bold": F(INTER, 21, 700), "small": F(INTER, 16, 400)}[kind]
        rows.append((kind, txt, f, y))
        y += {"brand": 52, "big": 58, "mid": 38, "body": 27, "bold": 29, "small": 24}[kind]
    d.rounded_rectangle((x0, y0, x1, y + 12), radius=12, fill=(255, 255, 255, 238), outline=(43, 43, 43), width=2)
    for kind, txt, f, yy in rows:
        if kind == "brand":
            og.flame(d, x0 + 18, yy - 2, 36)
            d.text((x0 + 62, yy - 4), txt, font=f, fill=INK)
        else:
            colour = FIRE if kind == "big" else INK if kind in ("mid", "bold") else (110, 110, 114) if kind == "small" else INK2
            d.text((x0 + 20, yy), txt, font=f, fill=colour)


def footer(d, F, left, right):
    d.rectangle((0, MAP_H, W, H), fill=INK)
    d.text((40, MAP_H + 14), left, font=F(KALAM, 40), fill=(255, 179, 168))
    d.text((W - 40, MAP_H + 28), right, font=F(INTER, 20, 400), fill=(170, 170, 175), anchor="ra")


def city_card(c, pts, wind, borders, towns, latest):
    F = lambda path, size, wt=None: og.font(path, size, wt)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img, "RGBA")
    cx0, cy0 = W / 2, MAP_H / 2
    k = (MAP_H / 2 - 12) / KM  # px per km: the 250 km ring just fits the map's height
    clat, clon = c["lat"], c["lon"]
    kx = 111.2 * math.cos(math.radians(clat))
    proj = lambda la, lo: (cx0 + (lo - clon) * kx * k, cy0 - (la - clat) * 111.2 * k)
    # Countries, as in build-og.py; only polygons that reach the card.
    dlat, dlon = (MAP_H / 2 / k + 50) / 111.2, (W / 2 / k + 50) / kx
    for polys in borders.values():
        for poly in polys:
            ring = poly[0]
            los, las = [q[0] for q in ring], [q[1] for q in ring]
            if min(las) > clat + dlat or max(las) < clat - dlat or min(los) > clon + dlon or max(los) < clon - dlon:
                continue
            xy = [proj(la, lo) for lo, la in ring]
            if len(xy) > 2:
                d.polygon(xy, fill=(238, 233, 222), outline=(176, 170, 160))
    w = wind_at(wind, clat, clon)
    calm = not w or w[0] < CALM
    # Counted exactly as the city page counts them (scripts/build-feed.py city_smoke, src/air.js smoke): every
    # detection 1-250 km away, its direction in 5-degree bins, upwind when the bin's centre is within 45 degrees.
    near = [(p, dist(clat, clon, p[0], p[1])) for p in pts]
    near = [(p, km) for p, km in near if 1 <= km <= KM]
    bin_deg = lambda p: int(bearing(clat, clon, p[0], p[1]) // BIN) * BIN + BIN / 2
    up = (lambda p: not calm and angle(bin_deg(p), w[1]) <= UPWIND)
    if not calm:
        def toward(deg, km):
            r = math.radians(deg)
            return proj(clat + km / 111.2 * math.cos(r), clon + km / kx * math.sin(r))
        d.polygon([proj(clat, clon)] + [toward(w[1] + a, KM) for a in range(-UPWIND, UPWIND + 1, 5)], fill=BLUE + (26,))
        # Wind streaks inside the wedge, all running the way the wind blows.
        rnd = random.Random(c["id"])
        go = math.radians(w[1] + 180)
        vx, vy = math.sin(go), -math.cos(go)
        L = 9 + min(14, w[0])
        for _ in range(140):
            a, rr = math.radians(w[1] + rnd.uniform(-UPWIND + 3, UPWIND - 3)), KM * math.sqrt(rnd.uniform(0.02, 0.95))
            x, y = proj(clat + rr / 111.2 * math.cos(a), clon + rr / kx * math.sin(a))
            d.line([(x, y), (x + vx * L, y + vy * L)], fill=(38, 38, 52, 120), width=2)
    R = KM * k
    for i in range(0, 360, 6):  # the 250 km ring, dashed
        a0, a1 = math.radians(i), math.radians(i + 3)
        d.line([(cx0 + R * math.sin(a0), cy0 - R * math.cos(a0)), (cx0 + R * math.sin(a1), cy0 - R * math.cos(a1))], fill=(120, 120, 120), width=2)
    for p, km in sorted(near, key=lambda q: up(q[0])):
        x, y = proj(p[0], p[1])
        if up(p):
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(227, 50, 31), outline=(143, 20, 11))
        else:
            d.ellipse((x - 3.5, y - 3.5, x + 3.5, y + 3.5), fill=(196, 196, 196), outline=(154, 154, 154))
    # The biggest towns on the card (clear of the text box), then the city itself.
    lab = F(INTER, 16, 600)
    shown = 0
    for la, lo, name, *_rest in sorted(towns, key=lambda t: -t[-1]):
        if shown >= 9 or dist(clat, clon, la, lo) < 40:
            continue
        x, y = proj(la, lo)
        if 20 < x < W - 100 and 14 < y < MAP_H - 14 and not (x < 380 and y < 340):
            d.ellipse((x - 2.5, y - 2.5, x + 2.5, y + 2.5), fill=INK2)
            d.text((x + 6, y - 10), name, font=lab, fill=INK2, stroke_width=3, stroke_fill=PAPER)
            shown += 1
    d.ellipse((cx0 - 9, cy0 - 9, cx0 + 9, cy0 + 9), fill=INK, outline="white", width=3)
    d.text((cx0 + 14, cy0 - 16), c["name"]["en"], font=F(INTER, 26, 700), fill=INK, stroke_width=4, stroke_fill="white")
    n_up, n_all = sum(1 for p, _ in near if up(p)), len(near)
    wind_line = "Almost no wind right now" if calm else f"Wind from the {DIRS[round(w[1] / 45) % 8]}, {round(w[0])} km/h"
    count = (f"{n_all:,} fires within 250 km" if calm else f"{n_up:,} fires upwind" if n_up else "No fires upwind")
    text_box(img, d, [("brand", "HamariHawa"), ("big", f"{c['name']['en']}'s air"), ("mid", "where the smoke"), ("mid", "is coming from"),
                      ("body", wind_line), ("bold", count), ("body", "within 250 km, last 24 hours"), ("small", f"Fires up to {stamp(latest)}")], F)
    footer(d, F, "hamarihawa.org", "NASA FIRMS · Open-Meteo wind")
    return img


def main_card(pts, stats, latest, borders):
    F = lambda path, size, wt=None: og.font(path, size, wt)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img, "RGBA")
    # Both countries, centred, as tall as the map area allows.
    rect = (W / 2 - 270, 8, 660, MAP_H - 16)  # a little right of centre, clear of the text box
    for polys in borders.values():
        for poly in polys:
            ring = [og.project(la, lo, *rect) for lo, la in poly[0]]
            if len(ring) > 2:
                d.polygon(ring, fill=(238, 233, 222), outline=(176, 170, 160))
    for p in pts:
        x, y = og.project(p[0], p[1], *rect)
        r = max(2.5, min(7, 2 + math.sqrt(p[3]) * 0.5))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(232, 120, 40))
    for nm, la, lo in [("Lahore", 31.55, 74.34), ("Delhi", 28.61, 77.21), ("Karachi", 24.86, 67.0), ("Kolkata", 22.57, 88.36),
                       ("Mumbai", 19.08, 72.88), ("Bengaluru", 12.97, 77.59)]:
        x, y = og.project(la, lo, *rect)
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=INK)
        d.text((x + 8, y - 12), nm, font=F(INTER, 19, 600), fill=INK, stroke_width=3, stroke_fill="white")
    text_box(img, d, [("brand", "HamariHawa"), ("big", "Live fire map"), ("mid", "of Pakistan and India"),
                      ("bold", f"{stats['spots']:,} fire spots, 24 hours"), ("body", f"{stats['pk']:,} in Pakistan, {stats['in']:,} in India"),
                      ("small", f"Fires up to {stamp(latest)}")], F)
    footer(d, F, "hamarihawa.org", "NASA FIRMS · Sentinel-5P · Copernicus")
    return img


def bundle(items, generated):
    head, off, blobs = {}, 0, []
    for k, b in items.items():
        head[k] = [off, len(b)]
        off += len(b)
        blobs.append(b)
    h = json.dumps({"generated": generated, "items": head}, separators=(",", ":")).encode()
    return b"HHOG1" + struct.pack(">I", len(h)) + h + b"".join(blobs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="also write the JPEGs here, for a look")
    ap.add_argument("--upload", action="store_true")
    a = ap.parse_args()
    feed, wind = get("/api/fires?hours=24&v=2"), get("/api/wind")
    pts = distinct([[r[0], r[1], r[2], r[3], r[4]] for r in feed["points"]])
    borders = json.load(open(os.path.join(ROOT, "data", "places", "borders.json"), encoding="utf-8"))
    towns = [t for t in json.load(open(os.path.join(ROOT, "site", "src", "towns.json"), encoding="utf-8")) if t[-1] >= 250000]
    cities = json.load(open(os.path.join(ROOT, "site", "src", "cities.json"), encoding="utf-8"))
    latest = feed.get("latest") or feed["generated"]
    items = {"main": jpeg(main_card(pts, feed["stats"], latest, borders))}
    for c in cities:
        items[c["id"]] = jpeg(city_card(c, pts, wind, borders, towns, latest))
    data = bundle(items, int(time.time() * 1000))
    print(f"{len(items)} images, {len(data) / 1e6:.1f} MB")
    if len(data) > 24 * 2 ** 20:
        sys.exit("bundle over 24 MiB; not uploading")
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        for k, b in items.items():
            open(os.path.join(a.out, f"{k}.jpg"), "wb").write(b)
    if a.upload:
        acct, ns, tok = os.environ["CLOUDFLARE_ACCOUNT_ID"], os.environ["KV_NAMESPACE_ID"], os.environ["CLOUDFLARE_API_TOKEN"]
        req = urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{acct}/storage/kv/namespaces/{ns}/values/og-live",
                                     data=data, method="PUT", headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/octet-stream"})
        urllib.request.urlopen(req, timeout=120).read()
        print("uploaded og-live")


if __name__ == "__main__":
    main()
