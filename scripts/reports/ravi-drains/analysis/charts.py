# Charts for the Ravi drains report. python3 charts.py [en|ur|hi]   (run build_evidence.py first)
# Writes strip.svg, profile.svg and map.svg into site/public/report/ravi-drains/ (name.ur.svg / name.hi.svg for the other
# languages). Labels go through T(); translations are in strings.<lang>.json, keyed by the English text.
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "ravi-drains")
LANG = sys.argv[1] if len(sys.argv) > 1 else "en"
_S = {} if LANG == "en" else json.load(open(os.path.join(HERE, f"strings.{LANG}.json"), encoding="utf-8"))
MISSING = []
def T(s, **k):
    t = s if LANG == "en" else _S.get(s)
    if t is None: MISSING.append(s); t = s
    t = t.format(**k) if k else t
    return f"⁧{t}⁩" if LANG == "ur" else t  # isolate Urdu runs as right-to-left
FONT = {"en": "Helvetica, Arial, sans-serif",
        "ur": "'Noto Naskh Arabic', 'Geeza Pro', Tahoma, Arial, sans-serif",
        "hi": "'Noto Sans Devanagari', 'Kohinoor Devanagari', Mangal, 'Nirmala UI', Arial, sans-serif"}[LANG]
SUFFIX = "" if LANG == "en" else "." + LANG
INK, INK3, HAIR, BLANK = "#1d1d1b", "#7c7c80", "#e6e6e6", "#f3f3f1"
EV = {e["id"]: e["value"] for e in json.load(open(os.path.join(OUT, "data.json"), encoding="utf-8"))["evidence"]}
def save(n, parts):
    if MISSING: sys.exit(f"{n}: missing {LANG} strings: {sorted(set(MISSING))}")
    open(os.path.join(OUT, n + SUFFIX + ".svg"), "w", encoding="utf-8").write("\n".join(parts + ["</svg>"]))
def head(W, H, label, title, sub, **k):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" aria-label="{T(label, **k).strip(chr(0x2067) + chr(0x2069))}">',
            '<rect width="100%" height="100%" fill="#fff"/>',
            f'<text x="16" y="20" font-size="14" font-weight="700" fill="{INK}">{T(title, **k)}</text>',
            f'<text x="16" y="36" font-size="10.5" fill="{INK3}">{T(sub, **k)}</text>']
LIGHT, DARK = (236, 217, 176), (52, 34, 20)   # as bright as upstream -> half as bright
def colour(v):
    f = min(1.0, max(0.0, (1.02 - v) / 0.55))
    return "#%02x%02x%02x" % tuple(int(a + (b - a) * f + 0.5) for a, b in zip(LIGHT, DARK))
LM = EV["landmarks"]["points"]; CMP = EV["comparison"]; SH = EV["shape"]; YR = EV["years"]
MARKS = [("Old Ravi Bridge", LM["Old Ravi Bridge"]["km_below_siphon"]), ("Saggian bypass bridge", LM["Saggian bypass bridge"]["km_below_siphon"]), ("M-2 motorway bridge", LM["M-2 motorway bridge"]["km_below_siphon"])]
K0, K1 = -10, 78   # kilometres below the siphon shown
MOUTHS = EV["mouths"]["km_below_siphon"]; JN = EV["junction"]["km_below_siphon"]

# 1. The strips: one row a year, one cell for every 2 km of river.
W, X0, X1, RH = 720, 86, 704, 17
def kx(k): return X0 + (X1 - X0) * (k - K0) / (K1 - K0)
blocks = [("October", YR["october"]), ("March and April", YR["spring"])]
H = 96 + sum(len(b[1]) * RH + 58 for b in blocks) + 78
o = head(W, H, "Two blocks of coloured strips, one row for each year from 2018 to 2026, showing the brightness of the Ravi's water along about 90 km of river. Every row is pale above Lahore and turns darker from about {k} km below the Ravi Siphon.",
         "The Ravi turns darker as it passes Lahore, year after year", "Each row is one year; each cell is 2 km of river, coloured by how bright the water is compared with the stretch above the city", k=SH["onset_km_below_siphon"])
y = 96
for name, block in blocks:
    o.append(f'<text x="16" y="{y-26}" font-size="11.5" font-weight="700" fill="{INK}">{T(name)}</text>')
    for lab, k in MARKS:
        anchor = "end" if lab == "Old Ravi Bridge" else "start"; dx = -3 if anchor == "end" else 3
        if name == "October":
            o.append(f'<text x="{kx(k)+dx:.1f}" y="{y-8 - (11 if lab == "Saggian bypass bridge" else 0)}" font-size="9" text-anchor="{anchor}" fill="{INK}">{T(lab)}</text>')
    for i, (yr, row) in enumerate(block.items()):
        yy = y + i * RH
        o.append(f'<text x="16" y="{yy+12}" font-size="10.5" fill="{INK}">{yr}</text><text x="{X0-6}" y="{yy+12}" font-size="9" text-anchor="end" fill="{INK3}">{T("{n} dates", n=row["dates"]) if row["dates"] > 1 else (T("1 date") if row["dates"] else T("none"))}</text>')
        for k in range(K0, K1, 2):
            v = row["by_km_below_siphon"].get(str(k))
            o.append(f'<rect x="{kx(k):.1f}" y="{yy}" width="{kx(k+2)-kx(k)+0.3:.1f}" height="{RH-2}" fill="{colour(v) if v is not None else BLANK}"/>')
    yb = y + len(block) * RH
    for lab, k in MARKS: o.append(f'<line x1="{kx(k):.1f}" x2="{kx(k):.1f}" y1="{y-6 - (11 if lab == "Saggian bypass bridge" and name == "October" else 0)}" y2="{yb}" stroke="{INK}" stroke-width="0.9"/>')
    for k in MOUTHS: o.append(f'<path d="M {kx(k)-4.5:.1f} {yb+9} l 4.5 -9 l 4.5 9 z" fill="{INK}"/>')
    o.append(f'<path d="M {kx(JN)-4.5:.1f} {yb+9} l 4.5 -9 l 4.5 9 z" fill="#fff" stroke="{INK}" stroke-width="1"/>')
    for k in range(-10, 71, 10): o.append(f'<text x="{kx(k):.1f}" y="{yb+21}" font-size="9" text-anchor="middle" fill="{INK3}">{k}</text>')
    y = yb + 58 + 18
ly = H - 46
o.append(f'<text x="{X1}" y="{ly-24}" font-size="9" text-anchor="end" fill="{INK3}">{T("km below the Ravi Siphon (0); the river flows left to right")}</text>')
for i in range(40): o.append(f'<rect x="{16+i*4}" y="{ly-8}" width="4.2" height="10" fill="{colour(1.02 - 0.55 * i / 39)}"/>')
o.append(f'<text x="16" y="{ly+14}" font-size="9" fill="{INK}">{T("as bright as above the city")}</text><text x="196" y="{ly+1}" font-size="9" fill="{INK}">{T("half as bright")}</text>')
o.append(f'<rect x="290" y="{ly-8}" width="14" height="10" fill="{BLANK}" stroke="{HAIR}"/><text x="309" y="{ly+1}" font-size="9" fill="{INK}">{T("no usable water (river too narrow, or cloud)")}</text>')
o.append(f'<path d="M 506 {ly+2} l 4.5 -9 l 4.5 9 z" fill="{INK}"/><text x="520" y="{ly+1}" font-size="9" fill="{INK}">{T("a waterway mapped as a drain meets the river")}</text>'
         f'<path d="M 506 {ly+16} l 4.5 -9 l 4.5 9 z" fill="#fff" stroke="{INK}" stroke-width="1"/><text x="520" y="{ly+15}" font-size="9" fill="{INK}">{T("dark channel from Mehmood Booti (in images)")}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">{T("Source: Copernicus Sentinel-2, red light reflected by water at least 40 m wide; HamariHawa analysis. Each row is the middle value of that year’s selected low-cloud dates.")}</text>')
save("strip", o)

# 2. The shape along the river across all dates.
W, H, X0, X1, Y0, Y1 = 720, 394, 60, 700, 70, 310
def ky(v): return Y1 - (Y1 - Y0) * (v - 0.4) / (1.15 - 0.4)
o = head(W, H, "Line chart of the brightness of the Ravi's water along the river in October, relative to the stretch above Lahore. It stays level for about 30 km, then falls from about {k} km below the Ravi Siphon and keeps falling.",
         "Level for 30 km, then a fall that starts near the city’s northern side", "Brightness relative to the stretch above the city (1.0). Line: middle value across dates; band: the middle half. Each date counts once", k=SH["onset_km_below_siphon"])
for v in (0.4, 0.6, 0.8, 1.0):
    o.append(f'<line x1="{X0}" x2="{X1}" y1="{ky(v):.1f}" y2="{ky(v):.1f}" stroke="{INK if v == 1.0 else HAIR}" stroke-width="{0.8 if v == 1.0 else 1}" stroke-dasharray="{"2 3" if v == 1.0 else "none"}"/><text x="{X0-6}" y="{ky(v)+3.5:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{v:.1f}</text>')
def kx(k): return X0 + (X1 - X0) * (k - K0) / (K1 - K0)
for k in range(-10, 71, 10): o.append(f'<text x="{kx(k):.1f}" y="{Y1+14}" font-size="9.5" text-anchor="middle" fill="{INK3}">{k}</text>')
o.append(f'<text x="{X1}" y="{Y1+28}" font-size="9" text-anchor="end" fill="{INK3}">{T("km below the Ravi Siphon (0); the river flows left to right")}</text>')
for i, (lab, k) in enumerate(MARKS):
    yt = Y0 - 6 + (i % 2) * 0
    o.append(f'<line x1="{kx(k):.1f}" x2="{kx(k):.1f}" y1="{Y0+ (12 if i == 1 else 0)}" y2="{Y1}" stroke="{INK}" stroke-width="0.8" stroke-dasharray="3 3"/><text x="{kx(k) + (-3 if i == 0 else 3):.1f}" y="{Y0 + 8 + (12 if i == 1 else 0)}" font-size="9" text-anchor="{"end" if i == 0 else "start"}" fill="{INK}" stroke="#fff" stroke-width="3" paint-order="stroke">{T(lab)}</text>')
for k in MOUTHS: o.append(f'<path d="M {kx(k)-4.5:.1f} {Y1} l 4.5 -9 l 4.5 9 z" fill="{INK}"/>')
o.append(f'<path d="M {kx(JN)-4.5:.1f} {Y1} l 4.5 -9 l 4.5 9 z" fill="#fff" stroke="{INK}" stroke-width="1"/>')
oc = {int(k): v for k, v in SH["october_by_km_below_siphon"].items() if K0 <= int(k) <= K1}; sp = {int(k): v for k, v in SH["spring_by_km_below_siphon"].items() if K0 <= int(k) <= K1}
ks = sorted(oc)
o.append('<polygon points="' + " ".join(f"{kx(k):.1f},{ky(oc[k]['q3']):.1f}" for k in ks) + " " + " ".join(f"{kx(k):.1f},{ky(oc[k]['q1']):.1f}" for k in reversed(ks)) + '" fill="#8a5a2b" opacity="0.18"/>')
o.append('<polyline points="' + " ".join(f"{kx(k):.1f},{ky(sp[k]['median']):.1f}" for k in sorted(sp)) + f'" fill="none" stroke="{INK3}" stroke-width="1.3" stroke-dasharray="4 3"/>')
o.append('<polyline points="' + " ".join(f"{kx(k):.1f},{ky(oc[k]['median']):.1f}" for k in ks) + '" fill="none" stroke="#6b3f17" stroke-width="2.2"/>')
o.append(f'<text x="{kx(-9):.1f}" y="{ky(1.06):.1f}" font-size="9.5" fill="{INK}">{T("as bright as above the city")}</text>')
ly = H - 26
o.append(f'<line x1="16" x2="40" y1="{ly-3}" y2="{ly-3}" stroke="#6b3f17" stroke-width="2.2"/><text x="45" y="{ly}" font-size="9.5" fill="{INK}">{T("October, {n} dates", n=SH["october_dates"])}</text>'
         f'<line x1="170" x2="194" y1="{ly-3}" y2="{ly-3}" stroke="{INK3}" stroke-width="1.3" stroke-dasharray="4 3"/><text x="199" y="{ly}" font-size="9.5" fill="{INK}">{T("March and April, {n} dates", n=SH["spring_dates"])}</text>'
         f'<path d="M 380 {ly+1} l 4.5 -9 l 4.5 9 z" fill="{INK}"/><text x="394" y="{ly}" font-size="9.5" fill="{INK}">{T("a waterway mapped as a drain meets the river")}</text>'
         f'<path d="M 380 {ly-13} l 4.5 -9 l 4.5 9 z" fill="#fff" stroke="{INK}" stroke-width="1"/><text x="394" y="{ly-14}" font-size="9.5" fill="{INK}">{T("dark channel from Mehmood Booti (in images)")}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">{T("Source: Copernicus Sentinel-2, 2018 to 2026; HamariHawa analysis. Distances follow OpenStreetMap’s centre line of the river and are approximate.")}</text>')
save("profile", o)

# 3. The map: the river coloured by its October brightness, and the open drains that are mapped.
W, H = 720, 640; FR = EV["drain_map"]["map_frame"]; LON0, LON1, LAT0, LAT1 = FR["west"], FR["east"], FR["south"], FR["north"]
MX0, MY0, MW = 16, 50, 688; KXd = 111320.0 * math.cos(math.radians(31.54)); KYd = 110946.0
sc = MW / ((LON1 - LON0) * KXd); MH = (LAT1 - LAT0) * KYd * sc
def px(lon, lat): return MX0 + (lon - LON0) * KXd * sc, MY0 + (LAT1 - lat) * KYd * sc
H = int(MY0 + MH + 64)
POP = EV["drain_map"]
o = head(W, H, "Map of Lahore showing the Ravi, coloured from pale above the city to dark below it, and about {km} km of waterways tagged as drains or nalas in OpenStreetMap, running through and around the city.",
         "The Ravi, and the waterways mapped as drains around Lahore", "River coloured by its October brightness. Brown lines: waterways tagged as drains or nalas in OpenStreetMap, {km} km in this frame", km=POP["km_inside_the_map_frame"])
o.append(f'<clipPath id="m"><rect x="{MX0}" y="{MY0}" width="{MW}" height="{MH:.1f}"/></clipPath><rect x="{MX0}" y="{MY0}" width="{MW}" height="{MH:.1f}" fill="#f7f6f2" stroke="{HAIR}"/><g clip-path="url(#m)">')
USED = set(json.load(open(os.path.join(INP, "population_near_drains.json"), encoding="utf-8"))["osm_way_ids_used"])
for e in json.load(open(os.path.join(INP, "osm_waterways.json"), encoding="utf-8"))["elements"]:
    if e["id"] in USED:
        o.append('<polyline points="' + " ".join("%.1f,%.1f" % px(p["lon"], p["lat"]) for p in e["geometry"]) + '" fill="none" stroke="#7a4a1e" stroke-width="1.5" stroke-linejoin="round"/>')
LINE = json.load(open(os.path.join(INP, "ravi_line.json")))["points"]; sip = EV["landmarks"]["ravi_siphon_line_km"]
ocm = {int(k): v["median"] for k, v in SH["october_by_km_below_siphon"].items()}
o.append('<polyline points="' + " ".join("%.1f,%.1f" % px(p["lon"], p["lat"]) for p in LINE) + '" fill="none" stroke="#fff" stroke-width="8.5" stroke-linejoin="round"/>')
o.append('<polyline points="' + " ".join("%.1f,%.1f" % px(p["lon"], p["lat"]) for p in LINE) + f'" fill="none" stroke="{INK3}" stroke-width="7" stroke-linejoin="round"/>')
for a, b in zip(LINE[:-1], LINE[1:]):
    v = ocm.get(int(math.floor(a["km"] - 56 + 0.5)))
    if v is None: continue
    (xa, ya), (xb, yb) = px(a["lon"], a["lat"]), px(b["lon"], b["lat"])
    o.append(f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="{colour(v)}" stroke-width="5.6" stroke-linecap="round"/>')
def dot(lon, lat, lab, dx=7, dy=3.5, anchor="start", bold=False):
    x, y = px(lon, lat)
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="#fff" stroke="{INK}" stroke-width="1.3"/><text x="{x+dx:.1f}" y="{y+dy:.1f}" font-size="9.5" text-anchor="{anchor}" fill="{INK}" stroke="#f7f6f2" stroke-width="2.6" paint-order="stroke"{" font-weight=\"700\"" if bold else ""}>{T(lab)}</text>'
def label(lon, lat, lab, size=9.5, fill=INK, anchor="middle", weight="400"):
    x, y = px(lon, lat)
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-weight="{weight}" stroke="#f7f6f2" stroke-width="2.6" paint-order="stroke">{T(lab)}</text>'
sp_pt = min(LINE, key=lambda p: abs(p["km"] - sip))
o.append(dot(sp_pt["lon"], sp_pt["lat"], "Ravi Siphon", dx=-7, anchor="end"))
o.append(dot(LM["Old Ravi Bridge"]["lon"], LM["Old Ravi Bridge"]["lat"], "Old Ravi Bridge", dx=-7, dy=-4, anchor="end"))
o.append(dot(LM["Saggian bypass bridge"]["lon"], LM["Saggian bypass bridge"]["lat"], "Saggian bypass bridge", dx=-7, anchor="end"))
o.append(dot(LM["M-2 motorway bridge"]["lon"], LM["M-2 motorway bridge"]["lat"], "M-2 motorway bridge", dx=-7, dy=10, anchor="end"))
o.append(label(74.335, 31.558, "LAHORE", size=13, fill=INK3, weight="700"))
for lon, lat, lab in ((74.445, 31.437, "Hudiara Drain"), (74.262, 31.428, "Sattu Katla Drain"), (74.425, 31.492, "Rohi Nala"), (74.345, 31.533, "Cantonment Drain"), (74.235, 31.672, "Bhed Nala")):
    o.append(label(lon, lat, lab, fill="#7a4a1e"))
x, y = px(74.3179, 31.4635)
o.append(f'<rect x="{x-4:.1f}" y="{y-4:.1f}" width="8" height="8" fill="{INK}"/>' + label(74.3179, 31.4575, "Quaid-e-Azam Industrial Estate", fill=INK))
o.append("</g>")
bx, by = MX0 + 14, MY0 + MH - 14
o.append(f'<line x1="{bx}" x2="{bx + 5000 * sc:.1f}" y1="{by}" y2="{by}" stroke="{INK}" stroke-width="1.4"/><text x="{bx}" y="{by-5}" font-size="9.5" fill="{INK}">{T("5 km")}</text>')
o.append(f'<text x="{MX0+MW-10}" y="{MY0+18}" font-size="9.5" text-anchor="end" fill="{INK3}">{T("North is up")}</text>')
ly = MY0 + MH + 20
for i in range(40): o.append(f'<rect x="{16+i*4}" y="{ly-8}" width="4.2" height="10" fill="{colour(1.02 - 0.55 * i / 39)}"/>')
o.append(f'<text x="184" y="{ly+1}" font-size="9" fill="{INK}">{T("river: as bright as above the city, to half as bright")}</text>')
o.append(f'<line x1="440" x2="464" y1="{ly-3}" y2="{ly-3}" stroke="#7a4a1e" stroke-width="1.5"/><text x="469" y="{ly+1}" font-size="9" fill="{INK}">{T("tagged as a drain or nala in OpenStreetMap")}</text>')
o.append(f'<text x="16" y="{H-22}" font-size="9" fill="{INK3}">{T("Drains, river line and bridges: OpenStreetMap contributors. River colour: Copernicus Sentinel-2, HamariHawa analysis.")}</text>')
o.append(f'<text x="16" y="{H-9}" font-size="9" fill="{INK3}">{T("Not every line reaches the Ravi, some may carry farm or storm water, and the map is incomplete, mainly in the north of the city.")}</text>')
save("map", o)
print("charts written", LANG)
