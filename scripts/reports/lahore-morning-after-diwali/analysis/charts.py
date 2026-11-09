# Charts for the Diwali report. python3 charts.py [en|ur|hi]
# Writes the season, hourly, cities, delhi and map charts into site/public/report/lahore-morning-after-diwali/
# (name.svg for English, name.ur.svg / name.hi.svg). Labels go through T(); translations are in strings.<lang>.json,
# keyed by the English text ({n}, {v} are filled in after translation).
import json, os, sys, math, datetime as D
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "lahore-morning-after-diwali")
ROOT = os.path.join(HERE, "..", "..", "..", "..")
LANG = sys.argv[1] if len(sys.argv) > 1 else "en"
_S = {} if LANG == "en" else json.load(open(os.path.join(HERE, f"strings.{LANG}.json"), encoding="utf-8"))
MISSING = []
def T(s, **k):
    t = s if LANG == "en" else _S.get(s)
    if t is None: MISSING.append(s); t = s
    t = t.format(**k) if k else t
    return f"\u2067{t}\u2069" if LANG == "ur" else t  # isolate Urdu runs as right-to-left
MON = {"en": ["Oct", "Nov"], "ur": ["اکتوبر", "نومبر"], "hi": ["अक्टूबर", "नवंबर"]}[LANG]
def dm(d): return f"{d.day} {MON[d.month - 10]}" if LANG != "ur" else f"\u2067{d.day} {MON[d.month - 10]}\u2069"
FONT = {"en": "Helvetica, Arial, sans-serif",
        "ur": "'Noto Naskh Arabic', 'Geeza Pro', Tahoma, Arial, sans-serif",  # Naskh: Nastaliq is too tall for chart labels
        "hi": "'Noto Sans Devanagari', 'Kohinoor Devanagari', Mangal, 'Nirmala UI', Arial, sans-serif"}[LANG]
SUFFIX = "" if LANG == "en" else "." + LANG
INK, INK3, HAIR, FIRE = "#1d1d1b", "#7c7c80", "#eeeeee", "#d62d20"
J = lambda f: json.load(open(os.path.join(HERE, "data", f)))
def save(n, parts):
    if MISSING: sys.exit(f"{n}: missing {LANG} strings: {sorted(set(MISSING))}")
    open(os.path.join(OUT, n + SUFFIX + ".svg"), "w", encoding="utf-8").write("\n".join(parts))
def head(W, H, label, title, sub):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" aria-label="{T(label).strip(chr(0x2067) + chr(0x2069))}">',
            '<rect width="100%" height="100%" fill="#fff"/>',
            f'<text x="16" y="20" font-size="14" font-weight="700" fill="{INK}">{T(title)}</text>',
            f'<text x="16" y="36" font-size="10.5" fill="{INK3}">{T(sub)}</text>']

# 0. The collision: the season's daily fire detections with Diwali marked, and Diwali against each season's busiest day.
import glob
DY = {os.path.basename(f)[:10]: json.load(open(f))["summary"] for f in glob.glob(os.path.join(HERE, "data", "day-summaries", "20*.json"))}
PUN = lambda s, i=0: s["states"].get("PK|Punjab", [0] * 4)[i] + s["states"].get("IN|Punjab", [0] * 4)[i]
DIWALI = {2019: "2019-10-27", 2020: "2020-11-14", 2021: "2021-11-04", 2022: "2022-10-24", 2023: "2023-11-12", 2024: "2024-10-31", 2025: "2025-10-20", 2026: "2026-11-08"}
PKC, INC, GOLD = "#2f5d8a", "#e8a29b", "#8a6a1e"
days = [k for k in sorted(DY) if "2026-10-01" <= k <= "2026-11-08"]
W, H, l, r, top, h = 720, 572, 46, 16, 64, 190
o = head(W, H, "Daily satellite fire spots in Pakistani and Indian Punjab from 1 October to 8 November 2026, highest on Diwali; and Diwali against each season’s busiest day since 2019",
         "In the two Punjabs, the season’s busiest fire day so far fell on Diwali",
         "Satellite fire spots per Pakistan-time day, Pakistani and Indian Punjab, 1 Oct to 8 Nov 2026, all satellites")
ymax = 3000; y = lambda v: top + h - v / ymax * h; bw = (W - l - r) / len(days)
for g in (1000, 2000, 3000):
    o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{HAIR}"/><text x="{l-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{g:,}</text>')
for i, k in enumerate(days):
    p, n = DY[k]["states"].get("PK|Punjab", [0])[0], DY[k]["states"].get("IN|Punjab", [0])[0]; x = l + i * bw + 1
    o.append(f'<rect x="{x:.1f}" y="{y(p):.1f}" width="{bw-2:.1f}" height="{top+h-y(p):.1f}" fill="{PKC}"/>')
    o.append(f'<rect x="{x:.1f}" y="{y(p+n):.1f}" width="{bw-2:.1f}" height="{y(p)-y(p+n):.1f}" fill="{FIRE if k == "2026-11-08" else INC}"/>')
    if k[8:] in ("01", "15"):
        o.append(f'<text x="{x+bw/2:.1f}" y="{top+h+13}" font-size="9.5" text-anchor="middle" fill="{INK3}">{dm(D.date.fromisoformat(k))}</text>')
    if k == "2026-11-08":
        o.append(f'<text x="{x+bw/2-4:.1f}" y="{y(p+n)-6:.1f}" font-size="11" font-weight="700" text-anchor="end" fill="{FIRE}">{T("Diwali, 8 Nov: {n}", n=f"{p+n:,}")}</text>')
o.append(f'<rect x="{l+10}" y="70" width="10" height="10" fill="{PKC}"/><text x="{l+24}" y="79" font-size="10" fill="{INK}">{T("Pakistani Punjab")}</text>')
o.append(f'<rect x="{l+130}" y="70" width="10" height="10" fill="{INC}"/><text x="{l+144}" y="79" font-size="10" fill="{INK}">{T("Indian Punjab")}</text>')
# Lower panel: one row per season, 15 Oct to 20 Nov; ring = Diwali, filled dot = that season's busiest day.
t2 = top + h + 52
o.append(f'<text x="16" y="{t2}" font-size="13" font-weight="700" fill="{INK}">{T("Diwali and each season’s busiest fire day")}</text>')
o.append(f'<text x="16" y="{t2+15}" font-size="10.5" fill="{INK3}">{T("Two Punjabs, all satellites. Filled dot: the busiest recorded day of October–November. Ring: Diwali. 2026: to 8 November.")}</text>')
a0, a1 = D.date(2000, 10, 15), D.date(2000, 11, 20); xl, xr = 70, W - 150
X = lambda d: xl + (D.date(2000, d.month, d.day) - a0).days / (a1 - a0).days * (xr - xl)
for j, yr in enumerate(range(2019, 2027)):
    ry = t2 + 38 + j * 22
    ds = {k: v for k, v in DY.items() if k.startswith(str(yr)) and k[5:7] in ("10", "11")}
    ds = {k: v for k, v in ds.items() if k <= "2026-11-08"}; pk = max(ds, key=lambda k: PUN(ds[k])); dv = DIWALI[yr]
    o.append(f'<text x="{xl-10}" y="{ry+4}" font-size="10.5" text-anchor="end" fill="{INK}" font-weight="{700 if yr == 2026 else 400}">{yr}</text>')
    o.append(f'<line x1="{xl}" x2="{xr}" y1="{ry}" y2="{ry}" stroke="{HAIR}"/>')
    xp, xd = X(D.date.fromisoformat(pk)), X(D.date.fromisoformat(dv))
    o.append(f'<circle cx="{xp:.1f}" cy="{ry}" r="5" fill="{FIRE}"/>')
    o.append(f'<circle cx="{xd:.1f}" cy="{ry}" r="8" fill="none" stroke="{GOLD}" stroke-width="2"/>')
    gap = (D.date.fromisoformat(dv) - D.date.fromisoformat(pk)).days
    lab = T("Diwali same day") if gap == 0 else T("Diwali 1 day before" if gap == -1 else "Diwali 1 day after" if gap == 1 else "Diwali {n} days after" if gap > 0 else "Diwali {n} days before", n=abs(gap))
    o.append(f'<text x="{xr+10}" y="{ry+4}" font-size="9.5" fill="{FIRE if gap == 0 else INK3}" font-weight="{700 if gap == 0 else 400}">{lab}</text>')
for d in (D.date(2000, 10, 15), D.date(2000, 11, 1), D.date(2000, 11, 15)):
    o.append(f'<text x="{X(d):.1f}" y="{t2+38+8*22+2}" font-size="9.5" text-anchor="middle" fill="{INK3}">{dm(d)}</text>')
o.append(f'<text x="16" y="{H-20}" font-size="9" fill="{INK3}">{T("NASA FIRMS VIIRS and MODIS via HamariHawa’s daily archive (2019–2025 final processing, 2026 near real time); a spot seen by several satellites in a day counts once.")}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">{T("The 2026 Diwali coincidence also holds using NOAA-20 alone. Busiest recorded days; days with missing satellite data are gaps, not zero fires.")}</text>')
o.append("</svg>"); save("season", o)

# 1. Lahore hour by hour: sensors (bars) against the CAMS model (line), PM2.5.
L = J("iqair-lahore-hourly.json")["rows"]
cams = {t.replace("T", " "): v for t, v in zip(J("dw-lahore.json")["a"]["time"], J("dw-lahore.json")["a"]["pm2_5"])}
W, H, l, r, top, h = 720, 330, 46, 16, 56, 220
o = head(W, H, "Lahore hourly PM2.5 from ground monitors and the CAMS model, 7 to 9 November 2026",
         "Lahore, hour by hour: IQAir’s city figure against the CAMS model, PM2.5 µg/m³",
         "IQAir city figure (median of stations; bars) and CAMS model series retrieved 9 Nov (line), Saturday 6 pm to Monday 4 pm, Pakistan time")
ymax = 420; y = lambda v: top + h - v / ymax * h; n = len(L); bw = (W - l - r) / n
for g in (100, 200, 300, 400):
    o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{HAIR}"/><text x="{l-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{g}</text>')
# Diwali evening band: Sunday 6 pm to midnight
i0 = next(i for i, x in enumerate(L) if x["pkt"] == "2026-11-08 18:00")
o.append(f'<rect x="{l+i0*bw:.1f}" y="{top}" width="{6*bw:.1f}" height="{h}" fill="#f6e7c8" opacity=".7"/>')
o.append(f'<text x="{l+i0*bw+3:.1f}" y="{top+12}" font-size="10" fill="#8a6a1e">{T("Diwali evening")}</text>')
for i, x in enumerate(L):
    v = x["pm25"]; peak = x["pkt"] == "2026-11-09 09:00"
    o.append(f'<rect x="{l+i*bw+1:.1f}" y="{y(v):.1f}" width="{bw-2:.1f}" height="{top+h-y(v):.1f}" fill="{FIRE if peak else "#e8a29b"}" rx="1"/>')
    if peak: o.append(f'<text x="{l+i*bw+bw/2:.1f}" y="{y(v)-5:.1f}" font-size="11" font-weight="700" text-anchor="middle" fill="{FIRE}">{v:g}</text>')
    if x["pkt"][11:13] in ("00", "06", "12", "18"):
        hh = int(x["pkt"][11:13]); lab = T({0: "midnight", 6: "6 am", 12: "noon", 18: "6 pm"}[hh])
        o.append(f'<text x="{l+i*bw+bw/2:.1f}" y="{top+h+13}" font-size="9.5" text-anchor="middle" fill="{INK3}">{lab}</text>')
    if x["pkt"][11:13] == "00":
        day = T(D.date.fromisoformat(x["pkt"][:10]).strftime("%A"))
        o.append(f'<text x="{l+i*bw+bw/2:.1f}" y="{top+h+26}" font-size="10" font-weight="700" text-anchor="middle" fill="{INK}">{day}</text>')
pts = " ".join(f"{l+i*bw+bw/2:.1f},{y(cams[x['pkt']]):.1f}" for i, x in enumerate(L) if cams.get(x["pkt"]) is not None)
o.append(f'<polyline points="{pts}" fill="none" stroke="#2f5d8a" stroke-width="2"/>')
o.append(f'<rect x="{W-r-250}" y="44" width="10" height="10" fill="#e8a29b"/><text x="{W-r-236}" y="53" font-size="10" fill="{INK}">{T("IQAir city figure")}</text>')
o.append(f'<line x1="{W-r-120}" x2="{W-r-106}" y1="49" y2="49" stroke="#2f5d8a" stroke-width="2"/><text x="{W-r-102}" y="53" font-size="10" fill="{INK}">{T("CAMS model")}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">{T("IQAir hourly city figure, captured 5 pm PKT 9 Nov; IQAir later revised some hours (9 am: AQI 648). CAMS via Open-Meteo, grid point nearest central Lahore. HamariHawa")}</text>')
o.append("</svg>"); save("hourly", o)

# 2. Five Pakistani cities, US AQI, same hours (IQAir city averages; Lahore's checked station by station).
O = J("iqair-others-hourly.json")["cities"]
series = {"Lahore": [x["us_aqi"] for x in L[1:]]}  # L starts 18:00; others start 19:00
for c in ("faisalabad", "multan", "gujranwala", "islamabad"):
    series[c.title()] = [x["us_aqi"] for x in O[c]["rows"]]
order = ["Multan", "Faisalabad", "Lahore", "Gujranwala", "Islamabad"]
W, H = 720, 262; cols, cw, ch = 5, 138, 150; x0, y0 = 16, 64
o = head(W, H, "Hourly US AQI in five Pakistani cities, Saturday evening to Monday afternoon",
         "Five Pakistani cities, same hours: Multan, Faisalabad and Lahore rose overnight",
         "IQAir hourly city figures (median of stations), US AQI+, Saturday 7 pm to Monday 4 pm Pakistan time. Shaded: Sunday 6 pm to midnight")
ym = 720
for k, c in enumerate(order):
    s = series[c][:46]; gx = x0 + k * (cw + 4); gy = y0
    yy = lambda v: gy + ch - v / ym * ch; step = (cw - 10) / (len(s) - 1)
    o.append(f'<text x="{gx}" y="{gy-6}" font-size="12" font-weight="700" fill="{INK}">{T(c)}</text>')
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
    o.append(f'<text x="{gx}" y="{gy+ch+14}" font-size="9.5" fill="{INK3}">{T("highest {v}", v=mx)}</text>')
    for i, lab in ((5, "Sun"), (29, "Mon")):
        o.append(f'<line x1="{gx+i*step:.1f}" x2="{gx+i*step:.1f}" y1="{gy+ch}" y2="{gy+ch+3}" stroke="{INK3}"/><text x="{gx+i*step+2:.1f}" y="{gy+ch+26}" font-size="9" fill="{INK3}">{T(lab)}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">{T("Ticks mark midnight. HamariHawa")}</text>')
o.append("</svg>"); save("cities", o)

# 2b. Delhi: five IQAir feeds by attribution, US AQI+, India time (data/iqair-delhi-stations-recapture.json).
DR = {r[0]: (r[1], [int(x) if x else None for x in r[5].split(",")]) for r in J("iqair-delhi-stations-recapture.json")["rows"]}
W, H, l, r, top, h = 720, 340, 46, 190, 56, 220
o = head(W, H, "Hourly US AQI+ at five Delhi feeds on IQAir, Saturday night to Monday evening: three private sensors and a DPCC feed rise above 1,000 on Diwali night; a CPCB-attributed feed for Anand Vihar stays near 190",
         "Delhi on Diwali night, as IQAir displayed it",
         "US AQI+, IQAir station histories, hours from Saturday 10:30 pm to Monday 8:30 pm India time. Shaded: Sunday 6:30 pm to 12:30 am")
n = 47; ymax = 2200; y = lambda v: top + h - v / ymax * h; step = (W - l - r) / (n - 1)
for g in (500, 1000, 1500, 2000):
    o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{HAIR}"/><text x="{l-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{g:,}</text>')
o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(500):.1f}" y2="{y(500):.1f}" stroke="{INK3}" stroke-dasharray="3 3"/><text x="{W-r}" y="{y(500)-4:.1f}" font-size="9" text-anchor="end" fill="{INK3}">{T("AQI 500 = PM2.5 325.4 µg/m³")}</text>')
o.append(f'<rect x="{l+20*step:.1f}" y="{top}" width="{6*step:.1f}" height="{h}" fill="#f6e7c8" opacity=".7"/>')  # 18:30 to 00:30 IST
feeds = [("vv-block-c-station", "VV Block C", "private (Luca)", "#d62d20"), ("safdarjung-enclave", "Safdarjung Enclave", "private (TL)", "#7b1d2f"),
         ("poorvi-marg-d-block-market", "Poorvi Marg", "private (Daniel I)", "#ec8a2b"), ("anand-vihar", "Anand Vihar", "Delhi Pollution Control Cttee", "#8b3fa8"),
         ("anand-vihar-delhi-dpcc", "Anand Vihar, Delhi - DPCC", "Central Pollution Control Board", "#2f5d8a")]
ly = top + 4
for slug, name, attr, col in feeds:
    v = DR[slug][1][:n]; segs, cur = [], []
    for i, x in enumerate(v):
        if x is None:
            if cur: segs.append(cur); cur = []
        else: cur.append(f"{l+i*step:.1f},{y(x):.1f}")
    if cur: segs.append(cur)
    cp = slug.endswith("-dpcc"); DASH = ' stroke-dasharray="6 3"' if cp else ""
    for sg in segs: o.append(f'<polyline points="{" ".join(sg)}" fill="none" stroke="{col}" stroke-width="{2.6 if cp else 1.8}"{DASH}/>')
    o.append(f'<line x1="{W-r+10}" x2="{W-r+26}" y1="{ly:.0f}" y2="{ly:.0f}" stroke="{col}" stroke-width="2"{DASH}/><text x="{W-r+30}" y="{ly+3:.0f}" font-size="9.5" fill="{INK}">{T(name)}</text>')
    o.append(f'<text x="{W-r+30}" y="{ly+15:.0f}" font-size="8.5" fill="{INK3}">{T(attr)}</text>'); ly += 32
for i, lab in ((1.5, "midnight"), (13.5, "noon"), (25.5, "midnight"), (37.5, "noon")):  # series starts 22:30 IST, so 00:00 is index 1.5
    o.append(f'<line x1="{l+i*step:.1f}" x2="{l+i*step:.1f}" y1="{top+h}" y2="{top+h+3}" stroke="{INK3}"/><text x="{l+i*step:.1f}" y="{top+h+13}" font-size="9.5" text-anchor="middle" fill="{INK3}">{T(lab)}</text>')
for i, lab in ((1.5, "Sunday"), (25.5, "Monday")):
    o.append(f'<text x="{l+i*step:.1f}" y="{top+h+26}" font-size="10" font-weight="700" text-anchor="middle" fill="{INK}">{T(lab)}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">{T("Gaps: hours with no reading. Attribution as shown on each IQAir page, 9 Nov. Not checked against CPCB or DPCC records. HamariHawa")}</text>')
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
         "Modelled 24-hour back-paths of air arriving at 9 am Monday (10 m and 925 hPa winds, GFS), over Sunday's fire spots")
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
TJ = J("traj.json")
for c, col in (("Lahore", FIRE), ("Faisalabad", "#7b1d2f"), ("Multan", "#8b3fa8")):
    for lev, dash in (("10m", ""), ("925hPa", ' stroke-dasharray="4 3"')):
        p = TJ[f"{c}|2026-11-09T09|{lev}"]["path"]
        pts = " ".join(f"{X(b):.1f},{Y(a):.1f}" for a, b, t in p)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.2"{dash}/>')
        a, b, t = p[-1]; o.append(f'<circle cx="{X(b):.1f}" cy="{Y(a):.1f}" r="2.5" fill="{col}"/>')
o.append("</g>")
CITIES = {"Lahore": (31.5497, 74.3436), "Faisalabad": (31.418, 73.079), "Multan": (30.1978, 71.4711), "Gujranwala": (32.1617, 74.1883),
          "Amritsar": (31.634, 74.8723), "Ludhiana": (30.901, 75.8573), "Jalandhar": (31.326, 75.576), "Bathinda": (30.211, 74.945), "Islamabad": (33.6938, 73.0652)}
for c, (a, b) in CITIES.items():
    if not (lo0 < b < lo1 and la0 < a < la1): continue
    o.append(f'<circle cx="{X(b):.1f}" cy="{Y(a):.1f}" r="3.5" fill="{INK}"/><text x="{X(b)+6:.1f}" y="{Y(a)-5:.1f}" font-size="11.5" font-weight="700" fill="{INK}" stroke="#fff" stroke-width="3" paint-order="stroke">{T(c)}</text>')
o.append(f'<text x="{X(72.2):.0f}" y="{Y(32.75):.0f}" font-size="12" fill="#8f8a80" font-weight="700">{T("PAKISTAN")}</text><text x="{X(75.9):.0f}" y="{Y(29.55):.0f}" font-size="12" fill="#8f8a80" font-weight="700">{T("INDIA")}</text>')
ly = my0 + mh + 16
o.append(f'<circle cx="22" cy="{ly-3:.0f}" r="3" fill="#f08a24"/><text x="30" y="{ly:.0f}" font-size="10" fill="{INK}">{T("fire detection, 8 Nov (NASA FIRMS)")}</text>')
o.append(f'<line x1="210" x2="232" y1="{ly-3:.0f}" y2="{ly-3:.0f}" stroke="{INK}" stroke-width="2"/><text x="236" y="{ly:.0f}" font-size="10" fill="{INK}">{T("path near the ground")}</text>')
o.append(f'<line x1="350" x2="372" y1="{ly-3:.0f}" y2="{ly-3:.0f}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 3"/><text x="376" y="{ly:.0f}" font-size="10" fill="{INK}">{T("path at 925 hPa")}</text>')
o.append(f'<text x="490" y="{ly:.0f}" font-size="10" fill="{INK}"><tspan fill="{FIRE}" font-weight="700">{T("Lahore")}</tspan> · <tspan fill="#7b1d2f" font-weight="700">{T("Faisalabad")}</tspan> · <tspan fill="#8b3fa8" font-weight="700">{T("Multan")}</tspan>{T("; dot = 24 h earlier")}</text>')
o.append(f'<text x="16" y="{ly+14:.0f}" font-size="9" fill="{INK3}">{T("Paths from GFS winds (Open-Meteo, 0.5°), horizontal only: a guide to direction, not a dispersion model. Dashed line: Pakistan–India boundary. HamariHawa")}</text>')
o.append("</svg>")
o[0] = o[0].replace('viewBox="0 0 720 470"', f'viewBox="0 0 720 {H}"'); save("map", o)
print("ok")
