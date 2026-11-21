# Charts for the landfill report. python3 charts.py [en|ur|hi]   (run build_evidence.py first)
# Writes plumes-lahore.svg and timeline.svg into site/public/report/landfill-methane/ (name.ur.svg / name.hi.svg for the other
# languages). Labels go through T(); translations are in strings.<lang>.json, keyed by the English text.
import base64, csv, json, os, sys, datetime as D
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "landfill-methane")
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
INK, INK3, HAIR, FIRE, GREY, FILL = "#1d1d1b", "#7c7c80", "#eeeeee", "#d62d20", "#2f5d8a", "#f1ece2"
EV = {e["id"]: e["value"] for e in json.load(open(os.path.join(OUT, "data.json"), encoding="utf-8"))["evidence"]}
ROWS = list(csv.DictReader(open(os.path.join(HERE, "inputs", "site_detections.csv"))))
OSM = {e["id"]: [(p["lon"], p["lat"]) for p in e["geometry"]] for e in json.load(open(os.path.join(HERE, "inputs", "osm_landfills.json")))["elements"]}
def save(n, parts):
    if MISSING: sys.exit(f"{n}: missing {LANG} strings: {sorted(set(MISSING))}")
    open(os.path.join(OUT, n + SUFFIX + ".svg"), "w", encoding="utf-8").write("\n".join(parts + ["</svg>"]))
def head(W, H, label, title, sub, **k):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" aria-label="{T(label, **k).strip(chr(0x2067) + chr(0x2069))}">',
            '<rect width="100%" height="100%" fill="#fff"/>',
            f'<text x="16" y="20" font-size="14" font-weight="700" fill="{INK}">{T(title, **k)}</text>',
            f'<text x="16" y="36" font-size="10.5" fill="{INK3}">{T(sub)}</text>']


CACHE = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else "~/.cache/hamarihawa/landfill-report")
MD = os.path.join(HERE, "inputs", "methane")
PLUME, MUTED = "#7b2d8e", "#b9b9bd"
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
def dstr(s): return T("{d} {m} {y}", d=int(s[8:10]), m=T(MON[int(s[5:7]) - 1]), y=s[:4])
def img(pid, x, y, w, h):
    b = base64.b64encode(open(os.path.join(CACHE, "raw", "methane", pid + "_plume.png"), "rb").read()).decode()
    return f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" preserveAspectRatio="none" href="data:image/png;base64,{b}"/>'
def plumes(city):
    P = json.load(open(os.path.join(MD, city + "_plumes.json")))["items"]
    for p in P: p["scene"] = p["plume_id"].split("-")[0]; p["lon"], p["lat"] = p["geometry_json"]["coordinates"]
    return P

# 1. Lakhodair and Mehmood Booti: one small map per satellite pass, with the plume images Carbon Mapper published.
LK = EV["ch4_lakhodair"]; LP = plumes("lahore")
COLS, PW, PH, GAP, TOP = 4, 164, 150, 12, 62
rows_n = -(-len(LK["pass_list"]) // COLS)
W, H = 16 * 2 + COLS * PW + (COLS - 1) * GAP, TOP + rows_n * (PH + 30) + 40
LON0, LAT0, SPAN = 74.370, 31.662, 7.8  # top-left corner and width in km
KX, KY = 94.8, 110.54; sc = PW / SPAN
o = head(W, H, "Twelve small maps of the Mehmood Booti dump and Lakhodair landfill, one for each satellite pass between June 2023 and March 2026. A plume streams from Lakhodair on {a} of the {b} passes. No methane plume is reported over Mehmood Booti in any of them.",
         "A methane plume reported at Lakhodair in {a} of {b} satellite scenes; none at Mehmood Booti",
         "Each map is one pass. Purple-to-yellow shapes are the methane plumes as imaged; outlines are the two sites", a=LK["passes_with_a_plume"], b=LK["passes"])
for i, ps in enumerate(LK["pass_list"]):
    x0, y0 = 16 + (i % COLS) * (PW + GAP), TOP + (i // COLS) * (PH + 30) + 16
    px = lambda lon, lat: (x0 + (lon - LON0) * KX * sc, y0 + (LAT0 - lat) * KY * sc)
    rate = T("{r} t/h", r=ps["tonnes_per_hour"]) if ps["tonnes_per_hour"] else (T("plume, no rate") if ps["plumes"] else T("no plume"))
    o.append(f'<text x="{x0}" y="{y0-5}" font-size="10.5" fill="{INK}"><tspan font-weight="700">{dstr(ps["local_time"])}</tspan>  <tspan fill="{INK3}">{rate}</tspan></text>')
    o.append(f'<clipPath id="p{i}"><rect x="{x0}" y="{y0}" width="{PW}" height="{PH}"/></clipPath><rect x="{x0}" y="{y0}" width="{PW}" height="{PH}" fill="#f6f6f4" stroke="{HAIR}"/><g clip-path="url(#p{i})">')
    for wid in (961551528, 1370790548):
        o.append(f'<polygon points="{" ".join("%.1f,%.1f" % px(*p) for p in OSM[wid])}" fill="#e4dfd3" stroke="{INK}" stroke-width="0.8"/>')
    for p in LP:
        if p["scene"] == ps["scene"]:
            w_, s_, e_, n_ = p["plume_bounds"]; (xa, ya), (xb, yb) = px(w_, n_), px(e_, s_)
            o.append(img(p["plume_id"], xa, ya, xb - xa, yb - ya))
    for wid in (961551528, 1370790548):
        o.append(f'<polygon points="{" ".join("%.1f,%.1f" % px(*p) for p in OSM[wid])}" fill="none" stroke="{INK}" stroke-width="0.8"/>')
    if i == 0:
        (xa, ya), (xb, yb) = px(74.4188, 31.6385), px(74.3854, 31.6030)
        o.append(f'<text x="{xa:.1f}" y="{ya:.1f}" font-size="9" text-anchor="middle" fill="{INK}">{T("Lakhodair")}</text><text x="{xb:.1f}" y="{yb:.1f}" font-size="9" text-anchor="middle" fill="{INK}">{T("Mehmood Booti")}</text>')
        o.append(f'<line x1="{x0+8}" x2="{x0+8+2*sc:.1f}" y1="{y0+14}" y2="{y0+14}" stroke="{INK}" stroke-width="1.3"/><text x="{x0+8}" y="{y0+10}" font-size="9" fill="{INK}">{T("2 km")}</text>')
    o.append("</g>")
o.append(f'<text x="16" y="{H-22}" font-size="9" fill="{INK3}">{T("Plume images and rates: Carbon Mapper (data.carbonmapper.org), from NASA EMIT and Planet Tanager-1. Outlines: OpenStreetMap contributors.")}</text>')
o.append(f'<text x="16" y="{H-9}" font-size="9" fill="{INK3}">{T("t/h = tonnes of methane an hour at the moment of the pass. Dates are Pakistan time. North is up.")}</text>')
save("plumes-lahore", o)

# 2. Every pass over the two sites on one time line, with the milestones of the work.
MBv = EV["ch4_mehmood_booti"]; PR = EV["press_lahore"]["mehmood_booti"]
W, H, X0, X1 = 720, 392, 150, 700; YM, Y0, Y1 = 96, 150, 300; TMAX = 4.5
T0, T1 = D.date(2023, 1, 1), D.date(2027, 1, 1)
def tx(s): d = D.date(int(s[:4]), int(s[5:7]), int(s[8:10])); return X0 + (X1 - X0) * (d - T0).days / (T1 - T0).days
def ty(v): return Y1 - (Y1 - Y0) * v / TMAX
o = head(W, H, "Chart of every satellite pass over the two sites from 2023 to 2026. Mehmood Booti: no plume on any of {b} passes. Lakhodair: a plume on {a}, with rates from about 0.6 to 3.6 tonnes an hour.",
         "Every satellite pass: a plume at Lakhodair on all but one, none reported at Mehmood Booti", "Each mark is one pass. Lakhodair's rates are in tonnes of methane an hour; bars are uncertainty, combined by us for multi-plume passes", a=LK["passes_with_a_plume"], b=LK["passes"])
for y in range(2023, 2027):
    x = tx(f"{y}-01-01"); o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{YM-22}" y2="{Y1}" stroke="{HAIR}"/><text x="{x+4:.1f}" y="{Y1+14}" font-size="10" fill="{INK3}">{y}</text>')
for v in (0, 1, 2, 3, 4):
    o.append(f'<line x1="{X0}" x2="{X1}" y1="{ty(v):.1f}" y2="{ty(v):.1f}" stroke="{HAIR}"/><text x="{X0-6}" y="{ty(v)+3.5:.1f}" font-size="9.5" text-anchor="end" fill="{INK3}">{v}</text>')
for date, lab, dy in (("2024-09-01", "capping begins at Mehmood Booti", 0), ("2026-06-01", "gas flare inaugurated", 0)):
    x = tx(date); o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{YM-22}" y2="{Y1}" stroke="{INK}" stroke-dasharray="3 3" stroke-width="0.9"/><text x="{x-4:.1f}" y="{YM-26+dy}" font-size="9.5" text-anchor="end" fill="{INK}">{T(lab)}</text>')
o.append(f'<text x="16" y="{YM+4}" font-size="11" font-weight="700" fill="{INK}">{T("Mehmood Booti")}</text><text x="16" y="{YM+17}" font-size="9.5" fill="{INK3}">{T("no plume reported, {b} passes", b=MBv["passes"])}</text>')
o.append(f'<text x="16" y="{Y0+24}" font-size="11" font-weight="700" fill="{INK}">{T("Lakhodair")}</text><text x="16" y="{Y0+37}" font-size="9.5" fill="{INK3}">{T("plume on {a} of {b} passes", a=LK["passes_with_a_plume"], b=LK["passes"])}</text>')
av, au, pj = LK["carbon_mapper_average_tonnes_per_hour"], LK["carbon_mapper_average_uncertainty"], LK["project_methane_tonnes_per_hour"]
o.append(f'<rect x="{X0}" y="{ty(av+au):.1f}" width="{X1-X0}" height="{ty(av-au)-ty(av+au):.1f}" fill="{PLUME}" opacity="0.10"/>')
o.append(f'<line x1="{X0}" x2="{X1}" y1="{ty(pj):.1f}" y2="{ty(pj):.1f}" stroke="{INK}" stroke-width="1.2"/>')
def mark(x, y, tan, fill):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{fill}" stroke="{PLUME if fill != "#fff" else INK3}" stroke-width="1.4"/>' if tan else f'<rect x="{x-4:.1f}" y="{y-4:.1f}" width="8" height="8" fill="{fill}" stroke="{PLUME if fill != "#fff" else INK3}" stroke-width="1.4"/>'
for ps in LK["pass_list"]:
    x = tx(ps["local_time"]); tan = ps["instrument"] == "Tanager-1"
    o.append(mark(x, YM, tan, "#fff"))
    if ps["tonnes_per_hour"]:
        v, u = ps["tonnes_per_hour"], ps["uncertainty_tonnes_per_hour"]
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{ty(v+u):.1f}" y2="{ty(max(v-u, 0)):.1f}" stroke="{PLUME}" stroke-width="1.2"/>' + mark(x, ty(v), tan, PLUME))
    elif ps["plumes"]:
        o.append(mark(x, Y1 + 36, tan, PLUME))
    else:
        o.append(mark(x, ty(0), tan, "#fff"))
o.append(f'<text x="16" y="{Y1+39}" font-size="9.5" fill="{INK3}">{T("plume, no rate published")}</text>')
o.append(f'<text x="{X0+6}" y="{ty(pj)+12:.1f}" font-size="9.5" fill="{INK}">{T("planned project’s forecast gas output, {v} (not a measurement)", v=pj)}</text>')
o.append(f'<text x="{X0+6}" y="{ty(av+au)-4:.1f}" font-size="9.5" fill="{PLUME}">{T("Carbon Mapper’s source estimate, {v} ± {u}", v=av, u=au)}</text>')
ly = H - 26
o.append(mark(20, ly - 3, True, PLUME) + f'<text x="29" y="{ly}" font-size="9.5" fill="{INK}">{T("Tanager-1, plume")}</text>' + mark(124, ly - 3, False, PLUME) + f'<text x="133" y="{ly}" font-size="9.5" fill="{INK}">{T("EMIT, plume")}</text>'
         + mark(204, ly - 3, True, "#fff") + mark(216, ly - 3, False, "#fff") + f'<text x="225" y="{ly}" font-size="9.5" fill="{INK}">{T("no plume reported")}</text>')
o.append(f'<text x="16" y="{H-8}" font-size="9" fill="{INK3}">{T("Source: Carbon Mapper (data.carbonmapper.org), retrieved 19 and 21 Nov 2026. Milestones and the forecast as reported in the press.")}</text>')
save("timeline", o)
print("charts written", LANG)
