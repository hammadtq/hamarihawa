# Charts for the rain-spell report. python3 charts.py [en|ur|hi]   (run build_evidence.py first)
# Writes lahore, cities and fires charts into site/public/report/punjab-rain-nov-2026/ (name.svg for English,
# name.ur.svg / name.hi.svg). Labels go through T(); translations are in strings.<lang>.json, keyed by the English text.
import json, os, sys, datetime as D
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "punjab-rain-nov-2026")
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
INK, INK3, HAIR, FIRE, PKC, INC, BAND = "#1d1d1b", "#7c7c80", "#eeeeee", "#d62d20", "#2f5d8a", "#e8a29b", "#e6eef6"
EV = {e["id"]: e["value"] for e in json.load(open(os.path.join(OUT, "data.json"), encoding="utf-8"))["evidence"]}
S = {n: {D.datetime.strptime(t, "%Y-%m-%d %H:%M"): v for t, v in s.items()} for n, s in json.load(open(os.path.join(HERE, "data", "series.json"))).items()}
def day(d): return T("{d} Nov", d=d)
def save(n, parts):
    if MISSING: sys.exit(f"{n}: missing {LANG} strings: {sorted(set(MISSING))}")
    open(os.path.join(OUT, n + SUFFIX + ".svg"), "w", encoding="utf-8").write("\n".join(parts))
def head(W, H, label, title, sub, **k):  # k: numbers for {placeholders} in the label and title
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" aria-label="{T(label, **k).strip(chr(0x2067) + chr(0x2069))}">',
            '<rect width="100%" height="100%" fill="#fff"/>',
            f'<text x="16" y="20" font-size="14" font-weight="700" fill="{INK}">{T(title, **k)}</text>',
            f'<text x="16" y="36" font-size="10.5" fill="{INK3}">{T(sub)}</text>']
H = lambda *a: D.datetime(2026, 11, *a)

# 1. Lahore, hour by hour, 8 pm on 12 Nov to 11 pm on 15 Nov.
L = S["lahore"]; t0, t1 = H(12, 20), H(15, 23); n = int((t1 - t0).total_seconds() // 3600) + 1
W, Hh, l, r, top, h = 720, 342, 46, 16, 60, 215
LN = EV["lahore_night"]; CL = EV["cities"]["lahore"]
assert CL["low_time"] == "2026-11-13 05:00" and CL["evening_12_nov_high_hour"] == 20 and CL["back_at_200"] == "2026-11-13 20:00"  # "nine hours", "the same evening"
o = head(W, Hh, "Lahore’s hourly IQAir city figure from 8 pm on 12 November to 11 pm on 15 November 2026: it falls from {a} to {b} by 5 am on 13 November, stays below 200 until the evening, and is between {lo} and {hi} on 14 and 15 November",
         "Lahore: from {a} to {b} in nine hours, back above 200 the same evening",
         "IQAir city figure (median of stations), US AQI+, each hour from 8 pm on 12 Nov to 11 pm on 15 Nov 2026, Pakistan time",
         a=LN["at_2000"], b=LN["at_0500"], lo=min(LN["afternoon_low_14"], LN["afternoon_low_15"]), hi=max(LN["morning_high_14"], LN["morning_high_15"]))
ymax = 420; y = lambda v: top + h - v / ymax * h; bw = (W - l - r) / n
for g in (100, 200, 300, 400):
    o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{INK3 if g == 200 else HAIR}"{" stroke-dasharray=\"3 3\"" if g == 200 else ""}/><text x="{l-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{g}</text>')
for i in range(n):
    t = t0 + D.timedelta(hours=i); v = L.get(t); x = l + i * bw
    if v is not None:
        low = t == H(13, 5)
        o.append(f'<rect x="{x+0.7:.1f}" y="{y(v):.1f}" width="{bw-1.4:.1f}" height="{top+h-y(v):.1f}" fill="{PKC if v < 200 else INC}" rx="1"/>')
        if t in (H(12, 20), H(13, 5)): o.append(f'<text x="{x+bw/2:.1f}" y="{y(v)-5:.1f}" font-size="11" font-weight="700" text-anchor="{"start" if t == H(12, 20) else "middle"}" fill="{INK}">{v}</text>')
    if t.hour in (0, 12):
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top+h}" y2="{top+h+3}" stroke="{INK3}"/><text x="{x:.1f}" y="{top+h+13}" font-size="9.5" text-anchor="middle" fill="{INK3}">{T("midnight") if t.hour == 0 else T("noon")}</text>')
    if t.hour == 12: o.append(f'<text x="{x:.1f}" y="{top+h+26}" font-size="10" font-weight="700" text-anchor="middle" fill="{INK}">{day(t.day)}</text>')
xr = l + 7 * bw + bw / 2; xw = l + 9.5 * bw
o.append(f'<line x1="{xr:.1f}" x2="{xr:.1f}" y1="{top+6}" y2="{y(L[H(13, 3)])-3:.1f}" stroke="{INK}" stroke-width="1"/><text x="{xr+4:.1f}" y="{top+12}" font-size="10" fill="{INK}">{T("3 am: the airport’s only report of rain")}</text>')
o.append(f'<line x1="{xw:.1f}" x2="{xw:.1f}" y1="{top+24}" y2="{y(L[H(13, 5)])-20:.1f}" stroke="{INK}" stroke-width="1"/><text x="{xw+4:.1f}" y="{top+30}" font-size="10" fill="{INK}">{T("5:30 am: wind at the airport reaches {v} km/h", v=EV["lahore_airport"]["wind_peak_kmh"])}</text>')
o.append(f'<rect x="{W-r-232}" y="44" width="10" height="10" fill="{PKC}"/><text x="{W-r-218}" y="53" font-size="10" fill="{INK}">{T("below 200")}</text>')
o.append(f'<rect x="{W-r-120}" y="44" width="10" height="10" fill="{INC}"/><text x="{W-r-106}" y="53" font-size="10" fill="{INK}">{T("200 or above")}</text>')
o.append(f'<text x="16" y="{Hh-20}" font-size="9" fill="{INK3}">{T("IQAir hourly city figure, captured 14 and 16 Nov; IQAir revises some hours after first showing them.")}</text>')
o.append(f'<text x="16" y="{Hh-8}" font-size="9" fill="{INK3}">{T("Airport reports: Lahore airport weather reports (METAR) via Iowa Environmental Mesonet. HamariHawa")}</text>')
o.append("</svg>"); save("lahore", o)

# 2. Twelve places, 9 to 15 Nov, with the hours that were not captured left blank.
ROWS = [("Pakistani Punjab", ["lahore", "gujranwala", "sialkot", "faisalabad", "multan", "rawalpindi"], FIRE),
        ("Indian Punjab and Chandigarh (one government feed per city; Chandigarh three and a private sensor)", ["amritsar", "jalandhar", "ludhiana", "patiala", "bathinda", "chandigarh"], "#6b6b70")]
a0, a1 = H(9, 0), H(16, 0); span = (a1 - a0).total_seconds()
W, cw, ch, gap = 720, 104, 100, 12; PITCH = ch + 84; Hh = 62 + 2 * PITCH + 22; ym = 600
o = head(W, Hh, "Hourly IQAir city figures for six cities in Pakistani Punjab and six places on the Indian side, 9 to 15 November 2026, with a gap from 11 to 12 November that was not captured. The Pakistani cities fall sharply on the night of 12 to 13 November",
         "Twelve places, 9 to 15 November",
         "IQAir hourly city figures, US AQI+, Pakistan time. Shaded: 1 am on 11 Nov to 7 pm on 12 Nov, not captured. Dashed line: 200")
o.append(f'<clipPath id="c"><rect x="0" y="0" width="{W}" height="{Hh}"/></clipPath>')
for ri, (title, names, col) in enumerate(ROWS):
    gy = 62 + ri * PITCH + 32
    o.append(f'<text x="16" y="{gy-22}" font-size="11" font-weight="700" fill="{INK}">{T(title)}</text>')
    for k, nme in enumerate(names):
        gx = 16 + k * (cw + gap); X = lambda t: gx + (t - a0).total_seconds() / span * cw; yy = lambda v: gy + ch - min(v, ym) / ym * ch
        o.append(f'<text x="{gx}" y="{gy-5}" font-size="11" font-weight="700" fill="{INK}">{T(nme.title())}</text>')
        o.append(f'<rect x="{X(H(11, 1)):.1f}" y="{gy}" width="{X(H(12, 20))-X(H(11, 1)):.1f}" height="{ch}" fill="{BAND}"/>')
        for g in (200, 400, 600):
            o.append(f'<line x1="{gx}" x2="{gx+cw}" y1="{yy(g):.1f}" y2="{yy(g):.1f}" stroke="{INK3 if g == 200 else HAIR}"{" stroke-dasharray=\"2 2\"" if g == 200 else ""}/>')
            if k == 0: o.append(f'<text x="{gx+cw}" y="{yy(g)-2:.1f}" font-size="8" text-anchor="end" fill="{INK3}">{g}</text>')
        o.append(f'<line x1="{gx}" x2="{gx+cw}" y1="{gy+ch}" y2="{gy+ch}" stroke="{INK3}"/>')
        segs, cur, prev = [], [], None
        for t in sorted(S[nme]):
            if t < a0 or t >= a1: continue
            if prev is not None and (t - prev) > D.timedelta(hours=1) and cur: segs.append(cur); cur = []
            cur.append(f"{X(t):.1f},{yy(S[nme][t]):.1f}"); prev = t
        if cur: segs.append(cur)
        for sg in segs: o.append(f'<polyline points="{" ".join(sg)}" fill="none" stroke="{col}" stroke-width="1.4"/>')
        c = EV["cities"][nme]
        o.append(f'<text x="{gx}" y="{gy+ch+24}" font-size="9" fill="{INK3}">{T("10 Nov average {a}", a=c["day"]["10"]["mean"])}</text>')
        o.append(f'<text x="{gx}" y="{gy+ch+35}" font-size="9" fill="{INK}">{T("13 Nov average {a}", a=c["day"]["13"]["mean"])}</text>')
        for d in (10, 13, 15):
            o.append(f'<line x1="{X(H(d, 0)):.1f}" x2="{X(H(d, 0)):.1f}" y1="{gy+ch}" y2="{gy+ch+3}" stroke="{INK3}"/><text x="{X(H(d, 12)):.1f}" y="{gy+ch+12}" font-size="8.5" text-anchor="middle" fill="{INK3}">{d}</text>')
o.append(f'<text x="16" y="{Hh-20}" font-size="9" fill="{INK3}">{T("Scale stops at 600: on 9 and 10 Nov Multan (highest {m}) and Lahore (highest {l}) went above it. Day numbers are November dates; ticks mark midnight.", m=f"{EV['cities']['multan']['highest_9_10_nov']:,}", l=EV["cities"]["lahore"]["highest_9_10_nov"])}</text>')
o.append(f'<text x="16" y="{Hh-8}" font-size="9" fill="{INK3}">{T("IQAir city pages captured 11, 14 and 16 Nov. The Indian feeds are attributed by IQAir to the Central Pollution Control Board and are shown for reference. HamariHawa")}</text>')
o.append("</svg>"); save("cities", o)

# 3. Fires, 1 to 15 Nov, NOAA-20.
F = EV["fires"]["days"]; days = sorted(F)
W, Hh, l, r, top, h = 720, 290, 46, 16, 64, 170
o = head(W, Hh, "Daily NOAA-20 satellite fire spots in Pakistani and Indian Punjab, 1 to 15 November 2026: lowest on 12 and 13 November, when Lahore was cloudy, and higher again on 15 November",
         "The month’s fewest fire spots on 12 and 13 November; more again by the 15th",
         "Satellite fire spots per Pakistan-time day, Pakistani and Indian Punjab, NOAA-20 satellite, 1 to 15 Nov 2026")
ymax = 1000; y = lambda v: top + h - v / ymax * h; bw = (W - l - r) / len(days)
i0 = days.index("2026-11-12")
o.append(f'<rect x="{l+i0*bw:.1f}" y="{top}" width="{2*bw:.1f}" height="{h}" fill="{BAND}"/><text x="{l+i0*bw+bw:.1f}" y="{top+12}" font-size="10" text-anchor="middle" fill="{PKC}">{T("cloud over Lahore")}</text>')
for g in (250, 500, 750, 1000):
    o.append(f'<line x1="{l}" x2="{W-r}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{HAIR}"/><text x="{l-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{g:,}</text>')
for i, k in enumerate(days):
    p, q = F[k]["pk_punjab_noaa20"], F[k]["in_punjab_noaa20"]; x = l + i * bw + 3
    o.append(f'<rect x="{x:.1f}" y="{y(p):.1f}" width="{bw-6:.1f}" height="{top+h-y(p):.1f}" fill="{PKC}"/>')
    o.append(f'<rect x="{x:.1f}" y="{y(p+q):.1f}" width="{bw-6:.1f}" height="{y(p)-y(p+q):.1f}" fill="{INC}"/>')
    o.append(f'<text x="{x+bw/2-3:.1f}" y="{y(p+q)-4:.1f}" font-size="9.5" text-anchor="middle" fill="{INK}">{p+q}</text>')
    o.append(f'<text x="{x+bw/2-3:.1f}" y="{top+h+13}" font-size="9.5" text-anchor="middle" fill="{INK3}">{int(k[8:])}</text>')
o.append(f'<text x="{W/2:.0f}" y="{top+h+27}" font-size="9.5" text-anchor="middle" fill="{INK3}">{T("November 2026")}</text>')
o.append(f'<rect x="{W-r-232}" y="44" width="10" height="10" fill="{PKC}"/><text x="{W-r-218}" y="53" font-size="10" fill="{INK}">{T("Pakistani Punjab")}</text>')
o.append(f'<rect x="{W-r-112}" y="44" width="10" height="10" fill="{INC}"/><text x="{W-r-98}" y="53" font-size="10" fill="{INK}">{T("Indian Punjab")}</text>')
o.append(f'<text x="16" y="{Hh-20}" font-size="9" fill="{INK3}">{T("Cloud hides fires from satellites, so the low counts of 12 and 13 Nov do not show that burning stopped.")}</text>')
o.append(f'<text x="16" y="{Hh-8}" font-size="9" fill="{INK3}">{T("NASA FIRMS VIIRS (NOAA-20), near real time, via HamariHawa’s daily archive, retrieved 16 Nov. HamariHawa")}</text>')
o.append("</svg>"); save("fires", o)
print("ok", LANG)
