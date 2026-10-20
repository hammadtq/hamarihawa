#!/usr/bin/env python3
"""Link-preview card (og:image, 1200x630) for the Two Punjabs report, in the same style as build-og.py:
the headline numbers on the left and the two season lines on the right.

Usage: python3 -I scripts/build-og-report.py <Kalam-Bold.ttf> <Inter.ttf>
Reads site/public/report/two-punjabs/seasons.json, writes site/public/og/two-punjabs.png. Needs Pillow.
"""
import importlib.util, json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("build_og", os.path.join(HERE, "build-og.py"))
og = importlib.util.module_from_spec(spec)
spec.loader.exec_module(og)

PK_GREEN, IN_SAFFRON = (31, 122, 77), (217, 130, 43)


def main():
    kalam, inter = sys.argv[1], sys.argv[2]
    S = json.load(open(os.path.join(HERE, "..", "site", "public", "report", "two-punjabs", "seasons.json"), encoding="utf-8"))["seasons"]
    years = sorted(int(y) for y in S)
    tot = lambda k, y: S[str(y)][k]["total"]
    pk, inn = [tot("PK|Punjab", y) for y in years], [tot("IN|Punjab", y) for y in years]
    peak = max(years, key=lambda y: tot("IN|Punjab", y))
    fall = round((1 - inn[-1] / tot("IN|Punjab", peak)) * 100)
    ratio = pk[-1] / inn[-1]

    img = Image.new("RGB", (og.W, og.H), "white")
    d = ImageDraw.Draw(img)
    # Chart panel on the right: the two Punjabs' season totals.
    mx, my, mw, mh = 620, 60, 540, 470
    d.rectangle((mx, my, mx + mw, my + mh), fill=og.PAPER)
    px, py, pw, ph = mx + 36, my + 50, mw - 210, mh - 110
    top = max(inn + pk) * 1.08
    X = lambda i: px + i * pw / (len(years) - 1)
    Y = lambda v: py + ph - v / top * ph
    d.line((px, py + ph, px + pw, py + ph), fill=(200, 196, 188), width=2)
    for i, y in enumerate(years):
        if i % 2 == 0 or i == len(years) - 1:
            d.text((X(i), py + ph + 12), str(y), font=og.font(inter, 18, 400), fill=og.INK2, anchor="ma")
    for vals, col, label in ((inn, IN_SAFFRON, "Indian Punjab"), (pk, PK_GREEN, "Pakistani Punjab")):
        pts = [(X(i), Y(v)) for i, v in enumerate(vals)]
        d.line(pts, fill=col, width=6, joint="curve")
        for x, y in pts:
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=col)
        lx, ly = pts[-1]
        d.text((lx + 14, ly - (34 if col == PK_GREEN else -4)), label, font=og.font(inter, 19, 600), fill=col)
    d.text((px, my + 18), "Crop-fire spots seen by NASA's Suomi NPP, Oct–Nov", font=og.font(inter, 18, 400), fill=og.INK2)
    og.pencil_rect(d, (mx, my, mx + mw, my + mh), 11)
    # Left column: brand, title, the three numbers.
    og.flame(d, 52, 54, 58)
    d.text((122, 58), "HamariHawa", font=og.font(kalam, 52), fill=og.INK)
    d.text((56, 170), "Two Punjabs", font=og.font(kalam, 66), fill=og.FIRE)
    d.text((58, 248), "seven seasons of crop fires", font=og.font(kalam, 40), fill=og.INK)
    y = 330
    for big, small in ((f"−{fall}%", f"Indian Punjab, {peak} to {years[-1]}"),
                       (f"{ratio:.1f}×", f"more in Pakistani Punjab, {years[-1]}")):
        d.text((58, y), big, font=og.font(kalam, 54), fill=og.INK)
        d.text((250, y + 18), small, font=og.font(inter, 24, 400), fill=og.INK2)
        y += 78
    d.rectangle((0, og.H - 78, og.W, og.H), fill=og.INK)
    d.text((56, og.H - 64), "hamarihawa.org", font=og.font(kalam, 44), fill=(255, 179, 168))
    d.text((og.W - 56, og.H - 50), "NASA FIRMS · checked against India's official counts", font=og.font(inter, 20, 400), fill=(170, 170, 175), anchor="ra")
    out = os.path.join(og.OUT, "two-punjabs.png")
    img.save(out, optimize=True)
    print("wrote", os.path.relpath(out), os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
