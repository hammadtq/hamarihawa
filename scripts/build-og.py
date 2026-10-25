#!/usr/bin/env python3
"""Draw the link-preview images (og:image, 1200x630) in the site's pencil-sketch style.

Usage: python3 -I scripts/build-og.py <fire-feed.json> <Kalam-Bold.ttf> <Inter.ttf>
Writes site/public/og/map-v3.png and site/public/og/sites-v3.png (a new name whenever the picture changes,
since link previews are cached by URL), plus apple-touch-icon.png.
Fonts: Kalam and Inter from Google Fonts (OFL). Needs Pillow.
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "site", "public", "og")
W, H = 1200, 630
INK, INK2, FIRE, PAPER = (29, 29, 31), (90, 90, 95), (214, 45, 32), (250, 248, 243)
BOX = (5.5, 37.5, 60.5, 97.5)  # s, n, w, e: all of Pakistan and India


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try:
            f.set_variation_by_axes([14, weight] if "opsz" in str(f.get_variation_axes()) else [weight])
        except Exception:
            pass
    return f


def pencil_rect(d, box, seed, width=3):
    """Two slightly wobbly passes, like rough.js."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(2):
        j = lambda: rnd.uniform(-2.5, 2.5)
        pts = [(x0 + j(), y0 + j()), (x1 + j(), y0 + j()), (x1 + j(), y1 + j()), (x0 + j(), y1 + j()), (x0 + j(), y0 + j())]
        d.line(pts, fill=(43, 43, 43), width=width, joint="curve")


def _bez(p0, p1, p2, p3, n=24):
    return [tuple((1 - t) ** 3 * p0[i] + 3 * (1 - t) ** 2 * t * p1[i] + 3 * (1 - t) * t ** 2 * p2[i] + t ** 3 * p3[i] for i in (0, 1))
            for t in (k / n for k in range(n + 1))]


def flame(d, x, y, s):
    """The site's flame logo: the same path as the SVG mark (32x32 viewBox), traced as curves."""
    pts = _bez((16, 3), (18, 9), (25, 12), (25, 20))
    pts += [(16 + 9 * math.cos(a), 20 + 9 * math.sin(a)) for a in (k / 24 * math.pi for k in range(25))]  # bottom half circle
    pts += _bez((7, 20), (7, 15), (10, 13), (11, 9))
    pts += _bez((11, 9), (12, 12), (13, 13), (14, 13))
    pts += _bez((14, 13), (14, 9), (14, 6), (16, 3))
    k = s / 32
    d.line([(x + px * k, y + py * k) for px, py in pts], fill=FIRE, width=max(3, round(2.2 * k)), joint="curve")
    wave = _bez((5, 24), (9, 22), (12, 26), (16, 24)) + _bez((16, 24), (20, 22), (23, 22), (27, 24))
    d.line([(x + px * k, y + py * k) for px, py in wave], fill=FIRE, width=max(2, round(1.8 * k)), joint="curve")


def project(lat, lon, x, y, w, h):
    k = math.cos(math.radians((BOX[0] + BOX[1]) / 2))
    sc = min(w / ((BOX[3] - BOX[2]) * k), h / (BOX[1] - BOX[0]))
    ox = x + (w - (BOX[3] - BOX[2]) * k * sc) / 2
    oy = y + (h - (BOX[1] - BOX[0]) * sc) / 2
    return ox + (lon - BOX[2]) * k * sc, oy + (BOX[1] - lat) * sc


def card(title, sub, points, pt_colour, kiln=False, name="map.png", fonts=None):
    kalam, inter = fonts
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    # map panel on the right
    mx, my, mw, mh = 600, 60, 560, 470
    d.rectangle((mx, my, mx + mw, my + mh), fill=PAPER)
    # Both countries' outlines (data/places/borders.json), filled a shade darker than the paper.
    borders = json.load(open(os.path.join(ROOT, "data", "places", "borders.json"), encoding="utf-8"))
    for polys in borders.values():
        for poly in polys:
            ring = [project(la, lo, mx, my, mw, mh) for lo, la in poly[0]]
            if len(ring) > 2:
                d.polygon(ring, fill=(238, 233, 222), outline=(176, 170, 160))
    for p in points:
        cx, cy = project(p[0], p[1], mx, my, mw, mh)
        if mx < cx < mx + mw and my < cy < my + mh:
            r = 2 if kiln else max(2.5, min(7, 2 + math.sqrt(p[3]) * 0.5))
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=pt_colour)
    for nm, la, lo in [("Lahore", 31.55, 74.34), ("Delhi", 28.61, 77.21), ("Karachi", 24.86, 67.0), ("Kolkata", 22.57, 88.36),
                       ("Mumbai", 19.08, 72.88), ("Bengaluru", 12.97, 77.59)]:
        cx, cy = project(la, lo, mx, my, mw, mh)
        d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=INK)
        d.text((cx + 8, cy - 12), nm, font=font(inter, 19, 600), fill=INK, stroke_width=3, stroke_fill="white")
    pencil_rect(d, (mx, my, mx + mw, my + mh), 7)
    # left column: brand, title, sub, url
    flame(d, 52, 54, 58)
    d.text((122, 58), "HamariHawa", font=font(kalam, 52), fill=INK)
    y = 190
    for line in title:
        d.text((56, y), line, font=font(kalam, 58), fill=FIRE if y == 190 else INK)
        y += 70
    y += 10
    for line in sub:
        d.text((58, y), line, font=font(inter, 26, 400), fill=INK2)
        y += 38
    d.rectangle((0, H - 78, W, H), fill=INK)
    d.text((56, H - 64), "hamarihawa.org", font=font(kalam, 44), fill=(255, 179, 168))
    d.text((W - 56, H - 50), "NASA FIRMS · Sentinel-5P · Copernicus", font=font(inter, 20, 400), fill=(170, 170, 175), anchor="ra")
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, name), optimize=True)
    print("wrote", name)


def main():
    feed, kalam, inter = sys.argv[1], sys.argv[2], sys.argv[3]
    pts = json.load(open(feed))["points"]
    card(["Live fire & air map", "of Pakistan", "and India"],
         ["Every fire NASA's satellites saw in the", "last day, the smoke and NO₂ in the air,", "and what it means for your health."],
         pts, (232, 120, 40), name="map-v3.png", fonts=(kalam, inter))
    kilns = json.load(open(os.path.join(ROOT, "site", "public", "sources", "kilns.json")))["items"]
    hot = json.load(open(os.path.join(ROOT, "site", "public", "sources", "hotspots.json")))["items"]
    card(["Pollution sites", "satellites keep", "catching"],
         ["Traffic hotspots, methane-leaking landfills,", "coal plants, flares and 50,000 brick kilns", "across Pakistan and India."],
         [[k[0], k[1], 0, 0] for k in kilns[::2] + hot], (122, 74, 42), kiln=True, name="sites-v3.png", fonts=(kalam, inter))
    # 180x180 touch icon: the flame on white
    icon = Image.new("RGB", (180, 180), "white")
    flame(ImageDraw.Draw(icon), 18, 14, 144)
    icon.save(os.path.join(ROOT, "site", "public", "apple-touch-icon.png"))
    print("wrote apple-touch-icon.png")


if __name__ == "__main__":
    main()
