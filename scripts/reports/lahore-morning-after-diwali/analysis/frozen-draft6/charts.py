# Charts for "The morning after Diwali". python3 charts.py  (English; Urdu/Hindi after approval)
# Writes season.svg, hourly.svg, cities.svg, map.svg into site/public/report/lahore-morning-after-diwali/.
import json, os, math, datetime as D
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "lahore-morning-after-diwali")
ROOT = os.path.join(HERE, "..", "..", "..", "..")
FONT = "Helvetica, Arial, sans-serif"
INK, INK3, HAIR, FIRE = "#1d1d1b", "#7c7c80", "#eeeeee", "#d62d20"
J = lambda f: json.load(open(os.path.join(HERE, "data", f)))
def save(n, parts): open(os.path.join(OUT, n + ".svg"), "w", encoding="utf-8").write("\n".join(parts))
def head(W, H, label, title, sub):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" aria-label="{label}">',
            '<rect width="100%" height="100%" fill="#fff"/>',
            f'<text x="16" y="20" font-size="14" font-weight="700" fill="{INK}">{title}</text>',
            f'<text x="16" y="36" font-size="10.5" fill="{INK3}">{sub}</text>']

# 0. The collision: the season's daily fire detections with Diwali marked, and Diwali against each season's busiest day.
DY = J("days.json")
DIWALI = {2019: "2019-10-27", 2020: "2020-11-14", 2021: "2021-11-04", 2022: "2022-10-24", 2023: "2023-11-12", 2024: "2024-10-31", 2025: "2025-10-20", 2026: "2026-11-08"}
PKC, INC, GOLD = "#2f5d8a", "#e8a29b", "#8a6a1e"
days = [k for k in sorted(DY) if "2026-10-01" <= k <= "2026-11-08"]
W, H, l, r, top, h = 720, 560, 46, 16, 64, 190
o = head(W, H, "Daily satellite fire detections from 1 October to 8 November 2026, highest on Diwali; and Diwali against each season’s busiest fire day since 2019",
         "The season’s biggest fire day so far fell on Diwali",
         "Satellite fire detections per Pakistan-time day, 1 Oct to 8 Nov 2026, Pakistan and northern India")
ymax = 6000; y = lambda v: top + h - v / ymax * h; bw = (W - l - r) / len(days)
for g in (2000, 4000, 6000):
    o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{HAIR}"/><text x="{l-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{g:,}</text>')
for i, k in enumerate(days):
    p, n = DY[k]["pk"], DY[k]["in"]; x = l + i * bw + 1
    o.append(f'<rect x="{x:.1f}" y="{y(p):.1f}" width="{bw-2:.1f}" height="{top+h-y(p):.1f}" fill="{PKC}"/>')
    o.append(f'<rect x="{x:.1f}" y="{y(p+n):.1f}" width="{bw-2:.1f}" height="{y(p)-y(p+n):.1f}" fill="{FIRE if k == "2026-11-08" else INC}"/>')
    if k[8:] in ("01", "15"):
        o.append(f'<text x="{x+bw/2:.1f}" y="{top+h+13}" font-size="9.5" text-anchor="middle" fill="{INK3}">{int(k[8:])} {D.date.fromisoformat(k).strftime("%b")}</text>')
    if k == "2026-11-08":
        o.append(f'<text x="{x+bw/2-4:.1f}" y="{y(p+n)-6:.1f}" font-size="11" font-weight="700" text-anchor="end" fill="{FIRE}">Diwali, 8 Nov: {p+n:,}</text>')
o.append(f'<rect x="{W-r-200}" y="52" width="10" height="10" fill="{PKC}"/><text x="{W-r-186}" y="61" font-size="10" fill="{INK}">Pakistan</text>')
o.append(f'<rect x="{W-r-130}" y="52" width="10" height="10" fill="{INC}"/><text x="{W-r-116}" y="61" font-size="10" fill="{INK}">India</text>')
# Lower panel: one row per season, 15 Oct to 20 Nov; ring = Diwali, filled dot = that season's busiest day.
t2 = top + h + 52
o.append(f'<text x="16" y="{t2}" font-size="13" font-weight="700" fill="{INK}">Diwali and each season’s busiest fire day</text>')
o.append(f'<text x="16" y="{t2+15}" font-size="10.5" fill="{INK3}">Filled dot: the season’s busiest day (October and November). Ring: Diwali. 2026 is the season so far.</text>')
a0, a1 = D.date(2000, 10, 15), D.date(2000, 11, 20); xl, xr = 70, W - 150
X = lambda d: xl + (D.date(2000, d.month, d.day) - a0).days / (a1 - a0).days * (xr - xl)
for j, yr in enumerate(range(2019, 2027)):
    ry = t2 + 38 + j * 22
    ds = {k: v for k, v in DY.items() if k.startswith(str(yr)) and k[5:7] in ("10", "11")}
    pk = max(ds, key=lambda k: ds[k]["spots"]); dv = DIWALI[yr]
    o.append(f'<text x="{xl-10}" y="{ry+4}" font-size="10.5" text-anchor="end" fill="{INK}" font-weight="{700 if yr == 2026 else 400}">{yr}</text>')
    o.append(f'<line x1="{xl}" x2="{xr}" y1="{ry}" y2="{ry}" stroke="{HAIR}"/>')
    xp, xd = X(D.date.fromisoformat(pk)), X(D.date.fromisoformat(dv))
    o.append(f'<circle cx="{xp:.1f}" cy="{ry}" r="5" fill="{FIRE}"/>')
    o.append(f'<circle cx="{xd:.1f}" cy="{ry}" r="8" fill="none" stroke="{GOLD}" stroke-width="2"/>')
    gap = (D.date.fromisoformat(dv) - D.date.fromisoformat(pk)).days
    lab = "same day" if gap == 0 else f"{abs(gap)} day{'s' if abs(gap) > 1 else ''} {'after' if gap > 0 else 'before'}"
    o.append(f'<text x="{xr+10}" y="{ry+4}" font-size="9.5" fill="{FIRE if gap == 0 else INK3}" font-weight="{700 if gap == 0 else 400}">Diwali {lab}</text>')
for d in (D.date(2000, 10, 15), D.date(2000, 11, 1), D.date(2000, 11, 15)):
    o.append(f'<text x="{X(d):.1f}" y="{t2+38+8*22+2}" font-size="9.5" text-anchor="middle" fill="{INK3}">{d.day} {d.strftime("%b")}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">NASA FIRMS VIIRS and MODIS detections via HamariHawa’s daily archive; heat detections, not confirmed fires. HamariHawa</text>')
o.append("</svg>"); save("season", o)

# 1. Lahore hour by hour: sensors (bars) against the CAMS model (line), PM2.5.
L = J("iqair-lahore-hourly.json")["rows"]
cams = {t.replace("T", " "): v for t, v in zip(J("dw-lahore.json")["a"]["time"], J("dw-lahore.json")["a"]["pm2_5"])}
W, H, l, r, top, h = 720, 330, 46, 16, 56, 220
o = head(W, H, "Lahore hourly PM2.5 from ground monitors and the CAMS model, 7 to 9 November 2026",
         "Lahore, hour by hour: ground monitors against the forecast model, PM2.5 µg/m³",
         "IQAir city average (bars) and Copernicus CAMS model (line), Saturday 6 pm to Monday 4 pm, Pakistan time")
ymax = 420; y = lambda v: top + h - v / ymax * h; n = len(L); bw = (W - l - r) / n
for g in (100, 200, 300, 400):
    o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{HAIR}"/><text x="{l-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{g}</text>')
# Diwali evening band: Sunday 6 pm to midnight
i0 = next(i for i, x in enumerate(L) if x["pkt"] == "2026-11-08 18:00")
o.append(f'<rect x="{l+i0*bw:.1f}" y="{top}" width="{6*bw:.1f}" height="{h}" fill="#f6e7c8" opacity=".7"/>')
o.append(f'<text x="{l+i0*bw+3:.1f}" y="{top+12}" font-size="10" fill="#8a6a1e">Diwali evening</text>')
for i, x in enumerate(L):
    v = x["pm25"]; peak = x["pkt"] == "2026-11-09 09:00"
    o.append(f'<rect x="{l+i*bw+1:.1f}" y="{y(v):.1f}" width="{bw-2:.1f}" height="{top+h-y(v):.1f}" fill="{FIRE if peak else "#e8a29b"}" rx="1"/>')
    if peak: o.append(f'<text x="{l+i*bw+bw/2:.1f}" y="{y(v)-5:.1f}" font-size="11" font-weight="700" text-anchor="middle" fill="{FIRE}">{v:g}</text>')
    if x["pkt"][11:13] in ("00", "06", "12", "18"):
        hh = int(x["pkt"][11:13]); lab = {0: "midnight", 6: "6 am", 12: "noon", 18: "6 pm"}[hh]
        o.append(f'<text x="{l+i*bw+bw/2:.1f}" y="{top+h+13}" font-size="9.5" text-anchor="middle" fill="{INK3}">{lab}</text>')
    if x["pkt"][11:13] == "00":
        day = D.date.fromisoformat(x["pkt"][:10]).strftime("%A")
        o.append(f'<text x="{l+i*bw+bw/2:.1f}" y="{top+h+26}" font-size="10" font-weight="700" text-anchor="middle" fill="{INK}">{day}</text>')
pts = " ".join(f"{l+i*bw+bw/2:.1f},{y(cams[x['pkt']]):.1f}" for i, x in enumerate(L) if cams.get(x["pkt"]) is not None)
o.append(f'<polyline points="{pts}" fill="none" stroke="#2f5d8a" stroke-width="2"/>')
o.append(f'<rect x="{W-r-250}" y="44" width="10" height="10" fill="#e8a29b"/><text x="{W-r-236}" y="53" font-size="10" fill="{INK}">ground monitors (IQAir)</text>')
o.append(f'<line x1="{W-r-120}" x2="{W-r-106}" y1="49" y2="49" stroke="#2f5d8a" stroke-width="2"/><text x="{W-r-102}" y="53" font-size="10" fill="{INK}">CAMS model</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">IQAir hourly city average of 53 stations, read 9 Nov 2026. CAMS via Open-Meteo, nearest grid point to central Lahore. HamariHawa</text>')
o.append("</svg>"); save("hourly", o)

# 2. Five Pakistani cities, US AQI, same hours (IQAir city averages; Lahore's checked station by station).
O = J("iqair-others-hourly.json")["cities"]
series = {"Lahore": [x["us_aqi"] for x in L[1:]]}  # L starts 18:00; others start 19:00
for c in ("faisalabad", "multan", "gujranwala", "islamabad"):
    series[c.title()] = [x["us_aqi"] for x in O[c]["rows"]]
order = ["Multan", "Faisalabad", "Lahore", "Gujranwala", "Islamabad"]
W, H = 720, 262; cols, cw, ch = 5, 138, 150; x0, y0 = 16, 64
o = head(W, H, "Hourly US AQI in five Pakistani cities, Saturday evening to Monday afternoon",
         "Five cities in Pakistan's Punjab, same hours: Multan, Faisalabad and Lahore spiked overnight",
         "IQAir hourly city averages, US AQI, Saturday 7 pm to Monday 4 pm Pakistan time. Shaded: Diwali evening, Sunday 6 pm to midnight")
ym = 720
for k, c in enumerate(order):
    s = series[c][:46]; gx = x0 + k * (cw + 4); gy = y0
    yy = lambda v: gy + ch - v / ym * ch; step = (cw - 10) / (len(s) - 1)
    o.append(f'<text x="{gx}" y="{gy-6}" font-size="12" font-weight="700" fill="{INK}">{c}</text>')
    for g in (200, 400, 600):
        o.append(f'<line x1="{gx}" x2="{gx+cw-10}" y1="{yy(g):.1f}" y2="{yy(g):.1f}" stroke="{HAIR}"/>')
        if k == cols - 1: o.append(f'<text x="{gx+cw-10}" y="{yy(g)-3:.1f}" font-size="8.5" text-anchor="end" fill="{INK3}">{g}</text>')
    o.append(f'<rect x="{gx+23*step:.1f}" y="{gy}" width="{6*step:.1f}" height="{ch}" fill="#f6e7c8" opacity=".7"/>')
    segs, cur = [], []
    for i, v in enumerate(s):
        if v is None:
            if cur: segs.append(cur); cur = []
        else: cur.append(f"{gx+i*step:.1f},{yy(v):.1f}")
    if cur: segs.append(cur)
    rose = c in ("Multan", "Faisalabad", "Lahore")
    for sg in segs: o.append(f'<polyline points="{" ".join(sg)}" fill="none" stroke="{FIRE if rose else "#6b6b70"}" stroke-width="{2 if rose else 1.5}"/>')
    mx = max(v for v in s if v is not None)
    o.append(f'<text x="{gx}" y="{gy+ch+14}" font-size="9.5" fill="{INK3}">highest {mx}</text>')
    for i, lab in ((5, "Sun"), (29, "Mon")):
        o.append(f'<line x1="{gx+i*step:.1f}" x2="{gx+i*step:.1f}" y1="{gy+ch}" y2="{gy+ch+3}" stroke="{INK3}"/><text x="{gx+i*step+2:.1f}" y="{gy+ch+26}" font-size="9" fill="{INK3}">{lab}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">Ticks mark midnight. HamariHawa</text>')
o.append("</svg>"); save("cities", o)

# 2b. Delhi: independent sensors against a government station as shown by IQAir, US AQI, India time.
Ds = J("iqair-delhi-sensors-hourly.json")["series"]
W, H, l, r, top, h = 720, 330, 46, 150, 56, 220
o = head(W, H, "Hourly US AQI at four independent Delhi sensors and one government station, 7 to 9 November",
         "Delhi on Diwali night: independent sensors against a government station",
         "US AQI, IQAir station history, Saturday 7:30 pm to Monday 5:30 pm India time. Shaded: Diwali evening")
ymax = 2200; y = lambda v: top + h - v / ymax * h; n = 47; step = (W - l - r) / (n - 1)
for g in (500, 1000, 1500, 2000):
    o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{HAIR}"/><text x="{l-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{g:,}</text>')
o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(500):.1f}" y2="{y(500):.1f}" stroke="{INK3}" stroke-dasharray="3 3"/><text x="{W-r}" y="{y(500)-4:.1f}" font-size="9" text-anchor="end" fill="{INK3}">top of the US AQI scale</text>')
o.append(f'<rect x="{l+23*step:.1f}" y="{top}" width="{6*step:.1f}" height="{h}" fill="#f6e7c8" opacity=".7"/>')
cols_ = {"VV Block C": "#d62d20", "Safdarjung Enclave": "#7b1d2f", "Poorvi Marg": "#ec8a2b", "Anand Vihar": "#8b3fa8", "Anand Vihar (DPCC, government)": "#2f5d8a"}
ly = top + 4
for name, col in cols_.items():
    s = Ds[name]; segs, cur = [], []
    for i, v in enumerate(s):
        if v is None:
            if cur: segs.append(cur); cur = []
        else: cur.append(f"{l+i*step:.1f},{y(v):.1f}")
    if cur: segs.append(cur)
    gov = "DPCC" in name; DASH = ' stroke-dasharray="6 3"' if gov else ""
    for sg in segs: o.append(f'<polyline points="{" ".join(sg)}" fill="none" stroke="{col}" stroke-width="{2.6 if gov else 1.8}"{DASH}/>')
    o.append(f'<line x1="{W-r+10}" x2="{W-r+26}" y1="{ly:.0f}" y2="{ly:.0f}" stroke="{col}" stroke-width="2"{DASH}/><text x="{W-r+30}" y="{ly+3:.0f}" font-size="9.5" fill="{INK}">{name.replace(" (DPCC, government)", "")}</text>')
    if gov: o.append(f'<text x="{W-r+30}" y="{ly+15:.0f}" font-size="9" fill="{INK3}">government (DPCC)</text>'); ly += 12
    ly += 18
for i, lab in ((4, "midnight"), (16, "noon"), (28, "midnight"), (40, "noon")):
    o.append(f'<text x="{l+i*step:.1f}" y="{top+h+13}" font-size="9.5" text-anchor="middle" fill="{INK3}">{lab}</text>')
for i, lab in ((4, "Sunday"), (28, "Monday")):
    o.append(f'<text x="{l+i*step:.1f}" y="{top+h+26}" font-size="10" font-weight="700" text-anchor="middle" fill="{INK}">{lab}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">Gaps: hours with no reading. Above 500, IQAir extends the US AQI scale. HamariHawa</text>')
o.append("</svg>"); save("delhi", o)

# 3. Map: Sunday's fire detections, the border, and where Monday 9 am air came from.
B = json.load(open(os.path.join(ROOT, "data", "places", "borders.json")))
lo0, lo1, la0, la1 = 70.6, 77.0, 29.3, 33.0
W, H = 720, 470; mx0, my0, mw, mh = 16, 44, 688, 400
kx = mw / (lo1 - lo0); ky = kx / math.cos(math.radians(31.2)); mh = (la1 - la0) * ky
X = lambda lo: mx0 + (lo - lo0) * kx; Y = lambda la: my0 + (la1 - la) * ky
H = int(my0 + mh + 34)
o = head(W, H, "Map of fire detections on 8 November and the paths of air reaching Lahore, Faisalabad and Multan on Monday morning",
         "Where Monday morning's air came from",
         "Approximate 24-hour paths of air arriving at 9 am Monday (near the ground and at about 800 m), over Sunday's fire detections")
o.append(f'<clipPath id="m"><rect x="{mx0}" y="{my0}" width="{mw}" height="{mh:.0f}"/></clipPath><g clip-path="url(#m)">')
o.append(f'<rect x="{mx0}" y="{my0}" width="{mw}" height="{mh:.0f}" fill="#faf8f3"/>')
for poly in B["PK"]:
    ring = poly[0]
    if not any(lo0 - 3 < p[0] < lo1 + 3 and la0 - 3 < p[1] < la1 + 3 for p in ring[::20]): continue
    if len(ring) < 200: continue
    d = "M" + "L".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in ring[::3]) + "Z"
    o.append(f'<path d="{d}" fill="#f1ede4" stroke="#8f8a80" stroke-width="1.2" stroke-dasharray="5 3"/>')
day = J("day-2026-11-08.json")
for s in day["spots"]:
    if lo0 < s[1] < lo1 and la0 < s[0] < la1:
        o.append(f'<circle cx="{X(s[1]):.1f}" cy="{Y(s[0]):.1f}" r="1.6" fill="#f08a24" opacity=".75"/>')
T = J("traj.json")
for c, col in (("Lahore", FIRE), ("Faisalabad", "#7b1d2f"), ("Multan", "#8b3fa8")):
    for lev, dash in (("10m", ""), ("925hPa", ' stroke-dasharray="4 3"')):
        p = T[f"{c}|2026-11-09T09|{lev}"]["path"]
        pts = " ".join(f"{X(b):.1f},{Y(a):.1f}" for a, b, t in p)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.2"{dash}/>')
        a, b, t = p[-1]; o.append(f'<circle cx="{X(b):.1f}" cy="{Y(a):.1f}" r="2.5" fill="{col}"/>')
o.append("</g>")
CITIES = {"Lahore": (31.5497, 74.3436), "Faisalabad": (31.418, 73.079), "Multan": (30.1978, 71.4711), "Gujranwala": (32.1617, 74.1883),
          "Amritsar": (31.634, 74.8723), "Ludhiana": (30.901, 75.8573), "Jalandhar": (31.326, 75.576), "Bathinda": (30.211, 74.945), "Islamabad": (33.6938, 73.0652)}
for c, (a, b) in CITIES.items():
    if not (lo0 < b < lo1 and la0 < a < la1): continue
    o.append(f'<circle cx="{X(b):.1f}" cy="{Y(a):.1f}" r="3.5" fill="{INK}"/><text x="{X(b)+6:.1f}" y="{Y(a)-5:.1f}" font-size="11.5" font-weight="700" fill="{INK}" stroke="#fff" stroke-width="3" paint-order="stroke">{c}</text>')
o.append(f'<text x="{X(72.2):.0f}" y="{Y(32.75):.0f}" font-size="12" fill="#8f8a80" font-weight="700">PAKISTAN</text><text x="{X(75.9):.0f}" y="{Y(29.55):.0f}" font-size="12" fill="#8f8a80" font-weight="700">INDIA</text>')
ly = my0 + mh + 16
o.append(f'<circle cx="22" cy="{ly-3:.0f}" r="3" fill="#f08a24"/><text x="30" y="{ly:.0f}" font-size="10" fill="{INK}">fire detection, 8 Nov (NASA FIRMS)</text>')
o.append(f'<line x1="210" x2="232" y1="{ly-3:.0f}" y2="{ly-3:.0f}" stroke="{INK}" stroke-width="2"/><text x="236" y="{ly:.0f}" font-size="10" fill="{INK}">path near the ground</text>')
o.append(f'<line x1="350" x2="372" y1="{ly-3:.0f}" y2="{ly-3:.0f}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 3"/><text x="376" y="{ly:.0f}" font-size="10" fill="{INK}">path at about 800 m</text>')
o.append(f'<text x="490" y="{ly:.0f}" font-size="10" fill="{INK}"><tspan fill="{FIRE}" font-weight="700">Lahore</tspan> · <tspan fill="#7b1d2f" font-weight="700">Faisalabad</tspan> · <tspan fill="#8b3fa8" font-weight="700">Multan</tspan>; dot = 24 h earlier</text>')
o.append(f'<text x="16" y="{ly+14:.0f}" font-size="9" fill="{INK3}">Paths from GFS winds (Open-Meteo, 0.5°), horizontal only: a guide to direction, not a dispersion model. Dashed line: Pakistan–India boundary. HamariHawa</text>')
o.append("</svg>")
o[0] = o[0].replace('viewBox="0 0 720 470"', f'viewBox="0 0 720 {H}"'); save("map", o)
print("ok")
