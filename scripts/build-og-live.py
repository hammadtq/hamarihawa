#!/usr/bin/env python3
"""Fresh link-preview images (og:image, 1200x630) for the live map and every city page, drawn from the
site's own live data in the style of scripts/build-og.py.

Each city card shows that city's last 24 hours of fires within 250 km, the upwind wedge and the wind,
as the city page does (src/air.js: wind from the hourly grid, upwind = within 45 degrees, calm below
3 km/h). The live map's card is build-og.py's map with today's fires and counts.

All images go to KV as ONE value, "og-live" (so a refresh costs one of the free plan's 1,000 daily
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
KM, UPWIND, CALM = 250, 45, 3
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


def city_card(c, pts, wind, borders, towns, latest):
    F = lambda path, size, wt=None: og.font(path, size, wt)
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img, "RGBA")
    mx, my, mw, mh = 600, 46, 560, 470
    cx0, cy0 = mx + mw / 2, my + mh / 2
    k = min(mw, mh) / (2 * (KM + 15))  # px per km
    clat, clon = c["lat"], c["lon"]
    kx = 111.2 * math.cos(math.radians(clat))
    proj = lambda la, lo: (cx0 + (lo - clon) * kx * k, cy0 - (la - clat) * 111.2 * k)
    inside = lambda x, y: mx <= x <= mx + mw and my <= y <= my + mh
    panel = Image.new("RGB", (mw, mh), PAPER)
    pd = ImageDraw.Draw(panel, "RGBA")
    shift = lambda xy: (xy[0] - mx, xy[1] - my)
    # Countries, as in build-og.py; only polygons near this city.
    dlat, dlon = (KM + 60) / 111.2, (KM + 60) / kx
    for polys in borders.values():
        for poly in polys:
            ring = poly[0]
            los, las = [q[0] for q in ring], [q[1] for q in ring]
            if min(las) > clat + dlat or max(las) < clat - dlat or min(los) > clon + dlon or max(los) < clon - dlon:
                continue
            xy = [shift(proj(la, lo)) for lo, la in ring]
            if len(xy) > 2:
                pd.polygon(xy, fill=(238, 233, 222), outline=(176, 170, 160))
    w = wind_at(wind, clat, clon)
    calm = not w or w[0] < CALM
    near = [(p, dist(clat, clon, p[0], p[1])) for p in pts]
    near = [(p, km) for p, km in near if km <= KM]
    up = (lambda p: not calm and angle(bearing(clat, clon, p[0], p[1]), w[1]) <= UPWIND)
    if not calm:
        def toward(deg, km):
            r = math.radians(deg)
            return shift(proj(clat + km / 111.2 * math.cos(r), clon + km / kx * math.sin(r)))
        wedge = [shift(proj(clat, clon))] + [toward(w[1] + a, KM) for a in range(-UPWIND, UPWIND + 1, 5)]
        pd.polygon(wedge, fill=BLUE + (26,))
        # Wind streaks inside the wedge, all running the way the wind blows.
        rnd = random.Random(c["id"])
        go = math.radians(w[1] + 180)
        vx, vy = math.sin(go), -math.cos(go)
        L = 9 + min(14, w[0])
        for _ in range(140):
            a, rr = math.radians(w[1] + rnd.uniform(-UPWIND + 3, UPWIND - 3)), KM * math.sqrt(rnd.uniform(0.02, 0.95))
            x, y = shift(proj(clat + rr / 111.2 * math.cos(a), clon + rr / kx * math.sin(a)))
            pd.line([(x, y), (x + vx * L, y + vy * L)], fill=(38, 38, 52, 120), width=2)
    # 250 km ring, dashed.
    R = KM * k
    for i in range(0, 360, 6):
        a0, a1 = math.radians(i), math.radians(i + 3)
        pd.line([(cx0 - mx + R * math.sin(a0), cy0 - my - R * math.cos(a0)), (cx0 - mx + R * math.sin(a1), cy0 - my - R * math.cos(a1))], fill=(120, 120, 120), width=2)
    for p, km in sorted(near, key=lambda q: up(q[0])):
        x, y = shift(proj(p[0], p[1]))
        if up(p):
            pd.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(227, 50, 31), outline=(143, 20, 11))
        else:
            pd.ellipse((x - 3.5, y - 3.5, x + 3.5, y + 3.5), fill=(196, 196, 196), outline=(154, 154, 154))
    # The biggest towns on the panel, then the city itself.
    lab = F(INTER, 16, 600)
    shown = 0
    for la, lo, name, *_rest in sorted(towns, key=lambda t: -t[-1]):
        if shown >= 7 or dist(clat, clon, la, lo) < 40:
            continue
        x, y = shift(proj(la, lo))
        if 20 < x < mw - 90 and 14 < y < mh - 14:
            pd.ellipse((x - 2.5, y - 2.5, x + 2.5, y + 2.5), fill=INK2)
            pd.text((x + 6, y - 10), name, font=lab, fill=INK2, stroke_width=3, stroke_fill=PAPER)
            shown += 1
    x, y = cx0 - mx, cy0 - my
    pd.ellipse((x - 8, y - 8, x + 8, y + 8), fill=INK, outline="white", width=3)
    pd.text((x + 12, y - 14), c["name"]["en"], font=F(INTER, 22, 700), fill=INK, stroke_width=4, stroke_fill="white")
    img.paste(panel, (mx, my))
    og.pencil_rect(d, (mx, my, mx + mw, my + mh), hash(c["id"]) % 97)
    # Left column.
    og.flame(d, 52, 44, 52)
    d.text((116, 46), "HamariHawa", font=F(KALAM, 46), fill=INK)
    name = c["name"]["en"]
    big = F(KALAM, 60 if len(name) < 12 else 50)
    d.text((56, 140), f"{name}'s air", font=big, fill=FIRE)
    d.text((56, 208), "where the smoke", font=F(KALAM, 46), fill=INK)
    d.text((56, 262), "is coming from", font=F(KALAM, 46), fill=INK)
    body, bold = F(INTER, 25, 400), F(INTER, 25, 700)
    n_up, n_all = sum(1 for p, _ in near if up(p)), len(near)
    y = 350
    if calm:
        lines = [("Almost no wind right now,", body), (f"{n_all:,} fires within 250 km", bold), ("in the last 24 hours.", body)]
    elif n_up:
        lines = [(f"Wind from the {DIRS[round(w[1] / 45) % 8]}, {round(w[0])} km/h.", body),
                 (f"{n_up:,} fires upwind", bold), ("within 250 km in the last 24 hours.", body)]
    else:
        lines = [(f"Wind from the {DIRS[round(w[1] / 45) % 8]}, {round(w[0])} km/h.", body),
                 ("No fires upwind", bold), (f"of {n_all:,} within 250 km in 24 hours.", body)]
    for txt, f in lines:
        d.text((56, y), txt, font=f, fill=INK if f is bold else INK2)
        y += 38
    d.text((56, y + 8), f"Fires up to {stamp(latest)}", font=F(INTER, 19, 400), fill=(124, 124, 128))
    d.rectangle((0, H - 78, W, H), fill=INK)
    d.text((56, H - 64), f"hamarihawa.org/air/{c['id']}", font=F(KALAM, 40), fill=(255, 179, 168))
    d.text((W - 56, H - 50), "NASA FIRMS · Open-Meteo wind", font=F(INTER, 20, 400), fill=(170, 170, 175), anchor="ra")
    return img


def main_card(pts, stats, latest):
    img = og.card(["Live fire & air map", "of Pakistan", "and India"],
                  [f"{stats['spots']:,} fire spots in the last", f"24 hours: {stats['pk']:,} in Pakistan,", f"{stats['in']:,} in India, up to {stamp(latest)}."],
                  pts, (232, 120, 40), name=None, fonts=(KALAM, INTER))
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
    pts = [[r[0], r[1], r[2], r[3]] for r in feed["points"]]
    borders = json.load(open(os.path.join(ROOT, "data", "places", "borders.json"), encoding="utf-8"))
    towns = [t for t in json.load(open(os.path.join(ROOT, "site", "src", "towns.json"), encoding="utf-8")) if t[-1] >= 250000]
    cities = json.load(open(os.path.join(ROOT, "site", "src", "cities.json"), encoding="utf-8"))
    latest = feed.get("latest") or feed["generated"]
    items = {"main": jpeg(main_card(pts, feed["stats"], latest))}
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
