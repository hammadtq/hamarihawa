# Every number in the Ravi drains report, computed from the files in inputs/. python3 build_evidence.py
# Writes site/public/report/ravi-drains/data.json (the evidence list). Parses on Python 3.9.
import csv, datetime, glob, json, math, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__)); INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "ravi-drains")
os.makedirs(OUT, exist_ok=True)
E = []
def rnd(x): return int(x + 0.5)  # halves round up
def r2(x): return rnd(x * 100) / 100
def add(id, claim, value, source, method, status): E.append({"id": id, "claim": claim, "value": value, "source": source, "method": method, "status": status})

S2 = "Copernicus Sentinel-2 Level-2A surface reflectance, tiles 43RDQ and 43SDR, read from Microsoft Planetary Computer on 23 Nov 2026 by measure_ravi.py; one file per date in inputs/profiles/, with the scene ids used beside it"
SIPHON = 55.8                      # river kilometre of the Ravi Siphon on the centre line; distances in the report count from here
UP, DOWN = (56.0, 77.0), (86.0, 105.0)   # the two stretches compared, in line kilometres
MIN_WIDE = 30                      # a 500 m bin is used only if it has at least this many 10 m pixels of water at least 40 m wide

# ---------------------------------------------------------------- the centre line and the landmarks
LINE = json.load(open(os.path.join(INP, "ravi_line.json")))["points"]
def to_xy(lon, lat):  # local metres, good to a few metres over this area
    return (lon - 74.3) * 111320.0 * math.cos(math.radians(31.55)), (lat - 31.55) * 110946.0
LXY = [to_xy(p["lon"], p["lat"]) for p in LINE]
def river_km(lon, lat):
    x, y = to_xy(lon, lat); d, i = min((math.hypot(a - x, b - y), i) for i, (a, b) in enumerate(LXY))
    return LINE[i]["km"], d
LAND = [("Old Ravi Bridge", 74.3015, 31.6116, "bridge, OpenStreetMap"), ("Saggian bypass bridge", 74.2692, 31.5783, "bridge, OpenStreetMap"),
        ("M-2 motorway bridge", 74.2462, 31.5537, "bridge, OpenStreetMap"),
        ("Dark side channel", 74.314, 31.6245, "a dark channel joining from the city side, read off the true-colour image of 18 Oct 2026; position to about 200 m")]
landmarks = {}
for name, lon, lat, kind in LAND:
    k, d = river_km(lon, lat)
    landmarks[name] = {"lon": lon, "lat": lat, "km_below_siphon": rnd(k - SIPHON), "line_km": round(k, 1), "metres_from_centre_line": rnd(d), "kind": kind}

# ---------------------------------------------------------------- the profiles
def load(path):
    p = {}
    for r in csv.DictReader(open(path)):
        if r["red_wide"] in ("", "nan") or int(r["wide_px"]) < MIN_WIDE: continue
        p[float(r["km"])] = {"red": float(r["red_wide"]), "width": float(r["median_width_m"]) if r["median_width_m"] else None}
    return p
PROF = {os.path.basename(f)[:10]: load(f) for f in sorted(glob.glob(os.path.join(INP, "profiles", "*.csv")))}
def season(d): return "october" if d[5:7] == "10" else "spring"
def med(p, a, b, key="red", need=10):
    v = [x[key] for k, x in p.items() if a <= k < b and x[key] is not None]
    return st.median(v) if len(v) >= need else None
rows = []
for d, p in PROF.items():
    u, dn = med(p, *UP), med(p, *DOWN)
    rows.append({"date": d, "season": season(d), "upstream": u, "downstream": dn, "ratio": dn / u if u and dn else None, "width_downstream_m": med(p, *DOWN, key="width", need=5)})
both = [r for r in rows if r["ratio"] is not None]
SC = json.load(open(os.path.join(INP, "scenes.json")))   # written by select_dates.py: every pass, the decision and the reason
assert sorted(x["date"] for x in SC["dates"] if x.get("measured")) == sorted(PROF), "scenes.json and inputs/profiles/ disagree"
def pct_darker(r): return rnd(100 * (1 - r))
by = {s: [r for r in both if r["season"] == s] for s in ("october", "spring")}
_d = sorted(x["date"] for x in SC["dates"]); _g = [(datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days for a, b in zip(_d, _d[1:])]
GAPS = sorted(sorted(set(_g), key=lambda v: -_g.count(v))[:2])
add("dates", "Selected low-cloud Sentinel-2 dates measured along the Ravi, 2018 to 2026",
    {"measured": len(rows), "october": sum(r["season"] == "october" for r in rows), "spring": sum(r["season"] == "spring" for r in rows),
     "first_year": int(min(PROF)[:4]), "last_year": int(max(PROF)[:4]), "years": int(max(PROF)[:4]) - int(min(PROF)[:4]) + 1, "first_date": min(PROF), "last_date": max(PROF),
     "passes_in_the_two_seasons": SC["counts"]["dates_with_a_pass"], "passes_rejected": SC["counts"]["rejected"], "cloud_cover_below_pct": rnd(SC["rule"]["cloud_cover_below_pct"]), "no_data_below_pct": rnd(SC["rule"]["no_data_below_pct"]), "usual_days_between_acquisitions": GAPS,
     "chosen": SC["counts"]["selected"], "not_measured": SC["counts"]["selected"] - len(rows), "with_both_stretches": len(both), "measured_but_not_compared": len(rows) - len(both), "october_with_both": len(by["october"]), "spring_with_both": len(by["spring"]),
     "date_list": sorted(PROF)},
    S2 + "; the list of every pass, the scenes, the decision and the reason is in inputs/scenes.json (select_dates.py)",
    "The catalogue lists an image of this stretch on 279 dates in the two seasons of the nine years (two orbits of the Sentinel-2 satellites cover it); 'usual_days_between_acquisitions' gives the two commonest gaps between one such date and the next. These are candidate dates, most of them cloudy. A date was chosen if, in the Earth Search scene catalogue, both tiles had a scene with cloud cover below 3 percent and less than 5 percent of the tile without data, between 1 March and 20 April or 1 and 25 October (November to February is too hazy; the monsoon too cloudy). Every date that met the rule was chosen; none was picked or dropped by eye. Two chosen dates could not be measured because Planetary Computer did not hold both tiles. A date counts in the comparison only if both stretches have at least 10 usable 500 m bins.",
    "computed from the measurements")
add("method", "How the water was measured",
    {"pixel_m": 10, "bin_m": 500, "min_width_m": 40, "within_m_of_centre_line": 700, "min_pixels_per_bin": MIN_WIDE, "siphon_line_km": SIPHON,
     "upstream_km_below_siphon": [rnd(UP[0] - SIPHON), rnd(UP[1] - SIPHON)], "downstream_km_below_siphon": [rnd(DOWN[0] - SIPHON), rnd(DOWN[1] - SIPHON)],
     "centre_line_km": round(LINE[-1]["km"], 1), "band": "red, 665 nm (band 4)"},
    S2 + "; centre line in inputs/ravi_line.json (OpenStreetMap contributors)",
    "Water pixels: (green - shortwave infrared)/(green + shortwave infrared) above 0, near infrared below 0.15, not flagged as cloud, cloud shadow or cirrus in the scene classification, within 700 m of the centre line. Each water pixel gets the river kilometre of the nearest point on the centre line. Width is the shorter of the east-west and north-south runs of water through the pixel; only pixels where the water is at least 40 m wide are used, to keep bank pixels out. The figure for each 500 m of river is the median red reflectance of those pixels. Distances are along OpenStreetMap's mapped centre line, which is longer than the present channel in places, so they are approximate river distances.",
    "method")

lo, hi = min(both, key=lambda r: r["ratio"]), max(both, key=lambda r: r["ratio"])
add("comparison", "The river below Lahore compared with the river above it, date by date",
    {"dates": len(both), "darker_below": sum(r["ratio"] < 1 for r in both), "not_darker": sum(r["ratio"] >= 1 for r in both),
     "least_pct_darker": pct_darker(hi["ratio"]), "least_date": hi["date"], "most_pct_darker": pct_darker(lo["ratio"]), "most_date": lo["date"],
     "october_median_pct_darker": pct_darker(st.median(r["ratio"] for r in by["october"])), "spring_median_pct_darker": pct_darker(st.median(r["ratio"] for r in by["spring"])),
     "october_range_pct": [pct_darker(max(r["ratio"] for r in by["october"])), pct_darker(min(r["ratio"] for r in by["october"]))],
     "spring_range_pct": [pct_darker(max(r["ratio"] for r in by["spring"])), pct_darker(min(r["ratio"] for r in by["spring"]))],
     "exceptions": [{"date": r["date"], "pct_darker": round(100 * (1 - r["ratio"]), 1)} for r in sorted(both, key=lambda r: r["date"]) if r["ratio"] >= 1 or pct_darker(r["ratio"]) == 0], "exceptions_within_pct": 1,
     "at_least_10_pct_darker": sum(r["ratio"] <= 0.90 for r in both), "at_least_20_pct_darker": sum(r["ratio"] <= 0.80 for r in both),
     "by_date": [{"date": r["date"], "pct_darker": pct_darker(r["ratio"]), "upstream_reflectance": round(r["upstream"], 3), "downstream_reflectance": round(r["downstream"], 3),
                  "downstream_width_m": rnd(r["width_downstream_m"]) if r["width_downstream_m"] else None} for r in both]},
    S2, "For each date, the median red reflectance of the 500 m bins in the downstream stretch divided by the same for the upstream stretch (stretches in 'method'). 'Percent darker' is 100 x (1 - that ratio), rounded.",
    "computed from the measurements")

# flow: wider water below the city goes with a smaller difference
def third(rs, top):
    s = sorted([r for r in rs if r["width_downstream_m"]], key=lambda r: r["width_downstream_m"]); n = len(s) // 3
    return s[-n:] if top else s[:n]
wide, narrow = third(by["october"], True), third(by["october"], False)
add("flow", "Water width below the city, and how the difference changes with it",
    {"october_median_width_m": rnd(st.median(r["width_downstream_m"] for r in by["october"])), "spring_median_width_m": rnd(st.median(r["width_downstream_m"] for r in by["spring"] if r["width_downstream_m"])),
     "october_dates_in_each_third": len(wide), "widest_third_min_width_m": rnd(min(r["width_downstream_m"] for r in wide)), "widest_third_median_pct_darker": pct_darker(st.median(r["ratio"] for r in wide)),
     "narrowest_third_max_width_m": rnd(max(r["width_downstream_m"] for r in narrow)), "narrowest_third_median_pct_darker": pct_darker(st.median(r["ratio"] for r in narrow))},
    S2, "Width is the median water width of the bins in the downstream stretch on that date, a rough stand-in for flow. October dates are ranked by it and the widest and narrowest thirds compared.",
    "computed from the measurements")

# the shape along the river: each date divided by its own upstream median, then the median across dates for each kilometre
def norm(p):
    u = med(p, *UP)
    return {k: x["red"] / u for k, x in p.items()} if u else None
def per_date(ps, kms):   # one value per date: the mean of that date's usable 500 m bins among kms, so every date weighs the same
    out = []
    for p in ps:
        v = [p[kk] for kk in kms if kk in p]
        if v: out.append(st.mean(v))
    return sorted(out)
def shape(dates, prof=None):
    ps = [n for n in (norm((prof or PROF)[d]) for d in dates) if n]; out = {}
    for k in range(46, 135):
        v = per_date(ps, (float(k), k + 0.5))
        if len(v) >= 4: out[k] = {"median": r2(st.median(v)), "q1": r2(v[len(v) // 4]), "q3": r2(v[3 * len(v) // 4]), "dates": len(v)}
    return out, len(ps)
def onset_of(sh): return min(k for k in sh if k > 60 and all(j in sh and sh[j]["median"] < 0.95 for j in range(k, k + 5)))
OCT = [d for d in PROF if season(d) == "october"]; SPR = [d for d in PROF if season(d) == "spring"]
sh_o, n_o = shape(OCT); sh_s, n_s = shape(SPR)
def at(sh, below): return sh[rnd(SIPHON + below)]["median"]
onset = onset_of(sh_o)
flat = [sh_o[k]["median"] for k in range(46, 77) if k in sh_o]
add("shape", "Brightness of the water along the river, relative to the stretch above the city",
    {"october_dates": n_o, "spring_dates": n_s, "upstream_flat_min": min(flat), "upstream_flat_max": max(flat), "upstream_flat_km": 76 - 46 + 1,
     "onset_km_below_siphon": rnd(onset - SIPHON), "onset_km_above_old_ravi_bridge": rnd(landmarks["Old Ravi Bridge"]["line_km"] - onset), "onset_threshold_pct": 5, "onset_run_km": 5, "dates_in_the_profile": n_o + n_s,
     "october_pct_darker_at_km_below_siphon": {str(b): rnd(100 * (1 - at(sh_o, b))) for b in (20, 24, 26, 30, 34, 44, 54)},
     "spring_pct_darker_at_km_below_siphon": {str(b): rnd(100 * (1 - at(sh_s, b))) for b in (20, 24, 26, 30, 34, 44, 54)},
     "checkpoints": [{"km_below_siphon": b, "october_pct_darker": rnd(100 * (1 - at(sh_o, b)))} for b in (24, 30, 44, 54)], "uneven_beyond_km": 60,
     "october_by_km_below_siphon": {str(k - 56): v for k, v in sh_o.items()}, "spring_by_km_below_siphon": {str(k - 56): v for k, v in sh_s.items()}},
    S2, "Each date's profile is divided by that date's upstream median, so 1.00 means 'as bright as above the city'. For each kilometre every date gives one value (the mean of its two 500 m bins, or the one that could be measured), and the median and quartiles are taken across dates, so each date counts once; a kilometre is shown if at least four dates have a value. The onset is the first kilometre from which the October median stays below 0.95 for five kilometres. Kilometres below the siphon are line kilometres minus 56, rounded.",
    "computed from the measurements")

# year by year (October), for the strip chart and to look for a trend
years = {}
for y in range(2018, 2027):
    ds = [d for d in OCT if d[:4] == str(y)]; rs = [r for r in by["october"] if r["date"][:4] == str(y)]
    ps = [n for n in (norm(PROF[d]) for d in ds) if n]; cells = {}
    for k in range(46, 134, 2):
        v = per_date(ps, (float(k), k + 0.5, k + 1.0, k + 1.5))
        if v: cells[str(k - 56)] = r2(st.median(v))
    years[str(y)] = {"dates": len(ps), "measured": len(ds), "compared": len(rs), "pct_darker": pct_darker(st.median(r["ratio"] for r in rs)) if rs else None,
                     "pct_darker_exact": round(100 * (1 - st.median(r["ratio"] for r in rs)), 2) if rs else None, "by_km_below_siphon": cells}
ys = [years[str(y)]["pct_darker"] for y in range(2018, 2027)]
springs = {}
for y in range(2018, 2027):
    ds = [d for d in SPR if d[:4] == str(y)]; rs = [r for r in by["spring"] if r["date"][:4] == str(y)]
    ps = [n for n in (norm(PROF[d]) for d in ds) if n]; cells = {}
    for k in range(46, 134, 2):
        v = per_date(ps, (float(k), k + 0.5, k + 1.0, k + 1.5))
        if v: cells[str(k - 56)] = r2(st.median(v))
    springs[str(y)] = {"dates": len(ps), "measured": len(ds), "compared": len(rs), "pct_darker": pct_darker(st.median(r["ratio"] for r in rs)) if rs else None, "by_km_below_siphon": cells}
# is there a direction to it? a straight line through the yearly October figures, with its 95 percent interval
T975 = {5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 20: 2.086, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 30: 2.042}   # Student's t, 97.5th percentile
def line(xs, vs):
    n = len(xs); mx, my = st.mean(xs), st.mean(vs); sxx = sum((x - mx) ** 2 for x in xs); b = sum((x - mx) * (v - my) for x, v in zip(xs, vs)) / sxx
    se = math.sqrt(sum((v - my - b * (x - mx)) ** 2 for x, v in zip(xs, vs)) / (n - 2) / sxx); t = T975[n - 2]
    return {"points": n, "slope_points_a_year": round(b, 2), "low": round(b - t * se, 2), "high": round(b + t * se, 2), "fall_at_most": rnd(abs(min(b - t * se, 0)) * 10) / 10, "rise_at_most": rnd(max(b + t * se, 0) * 10) / 10,
            "includes_zero": b - t * se <= 0 <= b + t * se}
yx = [y for y in range(2018, 2027) if years[str(y)]["pct_darker_exact"] is not None]
trend_years = line(yx, [years[str(y)]["pct_darker_exact"] for y in yx])
trend_dates = line([int(r["date"][:4]) + (int(r["date"][8:10]) - 1) / 365.0 for r in by["october"]], [100 * (1 - r["ratio"]) for r in by["october"]])
sp_ys = [springs[str(y)]["pct_darker"] for y in range(2018, 2027) if springs[str(y)]["pct_darker"] is not None]
add("years", "Year by year: how much darker the river was below the city",
    {"october": years, "spring": springs, "october_least_pct": min(ys), "october_least_year": 2018 + ys.index(min(ys)), "october_most_pct": max(ys), "october_most_year": 2018 + ys.index(max(ys)),
     "first_three_years_mean_pct": rnd(st.mean(ys[:3])), "last_three_years_mean_pct": rnd(st.mean(ys[-3:])),
     "october_trend": trend_years, "october_trend_date_by_date": trend_dates,
     "spring_least_pct": min(sp_ys), "spring_most_pct": max(sp_ys), "spring_years_with_a_figure": len(sp_ys), "spring_years_with_one_date_or_none": sum(1 for y in range(2018, 2027) if springs[str(y)]["compared"] <= 1)},
    S2, "For each year, the median across that year's October dates of the date-by-date figure in 'comparison'. 'dates' is the number of dates that contribute to the strip chart (the stretch above the city could be measured), 'compared' the number with both stretches, 'measured' all dates measured that year. Each cell is the median across dates of that date's mean over 2 km of river, relative to its upstream median. The trend is an ordinary least-squares line through the nine yearly October figures (unrounded), with a 95 percent interval from Student's t; 'date by date' is the same line through the individual October dates. An interval that includes zero means no trend can be told apart from none; it does not show that nothing changed.",
    "computed from the measurements")

add("watch", "The measure to follow as the measures take effect, and the trigger for reporting a change",
    {"baseline_pct": pct_darker(st.median(r["ratio"] for r in by["october"])), "low_pct": min(ys), "high_pct": max(ys), "years_running": 2, "years_in_baseline": len(ys)},
    S2, "The baseline is the October median in 'comparison'; low and high are the smallest and largest yearly October figures in 'years'. The rule (a yearly October figure outside that range for two years running) is ours, set before any new data; it is a plain threshold, not a statistical test, and with yearly figures built from two to four dates it can be met by chance.",
    "rule set by HamariHawa")
# repeated local dark spots
def dips(km):
    n = t = 0
    for p in PROF.values():
        if km not in p: continue
        nb = [p[km + o]["red"] for o in (-2, -1.5, -1, 1, 1.5, 2) if km + o in p]
        if len(nb) < 4: continue
        t += 1; n += p[km]["red"] / st.median(nb) < 0.88
    return n, t
d80, d88 = dips(80.0), dips(88.0)
add("spots", "Two places where the water is repeatedly darker than the water just above and below",
    {"first_km_below_siphon": rnd(80.0 - SIPHON), "first_dates": d80[0], "first_of": d80[1], "second_km_below_siphon": rnd(88.0 - SIPHON), "second_dates": d88[0], "second_of": d88[1], "threshold_pct": 12},
    S2, "A 500 m bin counts as a dark spot on a date if its red reflectance is at least 12 percent below the median of the six bins from 1 to 2 km either side. These two bins are the only ones between the siphon and the motorway bridge that do so on at least 40 percent of dates.",
    "computed from the measurements; what causes them is not identified")

# the control across the tile join
ctl = []
for f in sorted(glob.glob(os.path.join(INP, "profiles_northern_tile", "*.csv"))):
    d = os.path.basename(f)[:10]; a, b = PROF[d], load(f)
    fa, fb = med(a, 84, 92, need=5) / med(a, 74, 78, need=5), med(b, 84, 92, need=5) / med(b, 74, 78, need=5)
    ctl.append({"date": d, "fall_pct_southern_tile": rnd(100 * (1 - fa)), "fall_pct_northern_tile": rnd(100 * (1 - fb))})
join_km = next(LINE[i]["km"] for i in range(1, len(LINE)) if (LINE[i - 1]["lat"] - 31.62) * (LINE[i]["lat"] - 31.62) < 0 and LINE[i]["km"] > 60)
add("control", "Check that the fall is not made by the join between two image tiles",
    {"join_km_below_siphon": rnd(join_km - SIPHON), "dates_checked": len(ctl), "dates": ctl, "tile_overlap_km": 10},
    S2 + "; the re-measured profiles are in inputs/profiles_northern_tile/",
    "The river crosses from tile 43SDR into tile 43RDQ close to where the fall begins. The two tiles overlap by about 10 km, so four dates were measured again taking the northern tile wherever it has data, which moves the join about 10 km downstream. The fall is the drop in median red reflectance from the 4 km above the join to the 8 km starting 4 km below it, measured both ways.",
    "computed from the measurements")
# the same measurement made three more ways from one fresh read of every image (measure_ravi.py --checks)
def summary(prof):
    c = [(d, med(p, *DOWN) / med(p, *UP)) for d, p in prof.items() if med(p, *UP) and med(p, *DOWN)]
    oc = [r for d, r in c if season(d) == "october"]; sp = [r for d, r in c if season(d) == "spring"]
    sh, _ = shape([d for d in prof if season(d) == "october"], prof)
    return {"dates_measured": len(prof), "dates_compared": len(c), "darker_below": sum(r < 1 for _, r in c), "october_dates": len(oc), "spring_dates": len(sp),
            "october_median_pct_darker": pct_darker(st.median(oc)), "spring_median_pct_darker": pct_darker(st.median(sp)), "onset_km_below_siphon": rnd(onset_of(sh) - SIPHON)}, dict(c)
CHK = {}
for v in ("near300", "core"):
    prof = {os.path.basename(f)[:10]: load(f) for f in sorted(glob.glob(os.path.join(INP, "profiles_checks", v, "*.csv")))}
    assert sorted(prof) == sorted(PROF), "profiles_checks/%s is incomplete: %d of %d dates" % (v, len(prof), len(PROF))
    CHK[v], _ = summary(prof)
# the scenes: the profiles must come from the scenes listed in scenes.json; and what the fixed rule changed
used = {os.path.basename(f)[:10]: json.load(open(f)) for f in glob.glob(os.path.join(INP, "profiles", "*.scenes.json"))}
for x in SC["dates"]:
    if x.get("measured"): assert sorted(t["id"] for t in used[x["date"]]) == sorted(t["id"] for t in x["planetary_computer"].values()), "scene ids differ for " + x["date"]
first = {os.path.basename(f)[:10]: load(f) for f in sorted(glob.glob(os.path.join(INP, "profiles_first_run", "*.csv")))}
f_sum, f_c = summary(first); mine = {r["date"]: r["ratio"] for r in both}; same = sorted(set(mine) & set(f_c)); gained = sorted(set(mine) - set(f_c))
RULE = {"dates_with_two_versions_of_a_scene": sum(1 for x in SC["dates"] if x.get("measured") and any(t["scenes_in_catalogue"] > 1 for t in x["planetary_computer"].values())),
        "first_run_dates_compared": f_sum["dates_compared"], "first_run_darker_below": f_sum["darker_below"], "dates_gained": gained, "dates_gained_count": len(gained), "dates_lost": sorted(set(f_c) - set(mine)),
        "gained_date": gained[0] if gained else None, "gained_date_pct_darker": round(100 * (1 - mine[gained[0]]), 1) if gained else None,
        "largest_change_on_other_dates_points": round(max(abs(100 * (mine[d] - f_c[d])) for d in same), 1), "largest_change_on_other_dates_points_exact": round(max(abs(100 * (mine[d] - f_c[d])) for d in same), 2)}
add("mask_checks", "The same comparison with the water picked out in stricter ways",
    {"standard": {"within_m_of_centre_line": 700, "dates_compared": len(both), "darker_below": sum(r["ratio"] < 1 for r in both), "october_median_pct_darker": pct_darker(st.median(r["ratio"] for r in by["october"])),
                  "spring_median_pct_darker": pct_darker(st.median(r["ratio"] for r in by["spring"])), "onset_km_below_siphon": rnd(onset - SIPHON)},
     "scene_rule": RULE, "within_300_m": CHK["near300"], "core_water_only": CHK["core"], "narrow_buffer_m": 300, "core_m_from_any_edge": 20,
     "side_channel_m_from_centre_line": landmarks["Dark side channel"]["metres_from_centre_line"]},
    S2 + "; profiles in inputs/profiles_checks/ (measure_ravi.py --checks, run 23 Nov 2026); the first run of 21 Nov 2026 is kept in inputs/profiles_first_run/",
    "Every measured date was read again on 23 Nov 2026 and measured three ways from the same read. The standard method, with the scene for each tile chosen by the fixed rule in scenes.json: these replaced the first run's profiles and are what the report uses. The first run (21 Nov 2026) took whichever scene the catalogue returned first, which matters only on dates with two versions of a scene; 'scene_rule' records what changed. 'within_300_m': water pixels within 300 m of the centre line instead of 700 m, which leaves out side channels, ponds and outer braids, including the dark side channel at the northern edge. 'core_water_only': instead of the 40 m width test along rows and columns, a pixel is used only if every pixel within 20 m of it in any direction is water, which keeps bank pixels out whichever way the river runs. The same stretches and thresholds are used in all of them.",
    "computed from the measurements")
add("landmarks", "Fixed points along the river", {"ravi_siphon_line_km": SIPHON, "points": landmarks},
    "OpenStreetMap contributors (bridges, the river's centre line), downloaded 21 Nov 2026",
    "The nearest point of the centre line to each bridge. The Ravi Siphon, where the Bambawali-Ravi-Bedian canal passes under the river, is the usual starting point for distances in published studies of this reach.",
    "computed from the map")

# the two close-ups: the same image, cut at two places
CU_DATE, CU = "2026-10-18", {}
for name, km in (("above", 64.0), ("below", 104.0)):
    pt = min(LINE, key=lambda q: abs(q["km"] - km))
    CU[name] = {"km_below_siphon": rnd(km - SIPHON), "line_km": km, "lon": pt["lon"], "lat": pt["lat"], "red_reflectance": round(med(PROF[CU_DATE], km - 2, km + 2, need=4), 3)}
add("closeups", "Two close-ups of the river from the same satellite image, above and below the city",
    {"date": CU_DATE, "width_km": 4, "above": CU["above"], "below": CU["below"], "pct_darker_below": rnd(100 * (1 - CU["below"]["red_reflectance"] / CU["above"]["red_reflectance"])),
     "below_km_past_m2_bridge": CU["below"]["km_below_siphon"] - landmarks["M-2 motorway bridge"]["km_below_siphon"]},
    S2 + "; image ravi-above-below.jpg, true colour (bands 4, 3, 2)",
    "Both squares are cut from the image of 18 October 2026, 4 km across, centred on the river's centre line, with one colour scaling for the whole image, so the two can be compared. The reflectance is the median of the measured 500 m bins inside each square on that date.",
    "computed from the measurements")

# where a mapped open drain reaches the river's centre line
USED = set(json.load(open(os.path.join(INP, "population_near_drains.json"), encoding="utf-8"))["osm_way_ids_used"]); mouths = []
for e in json.load(open(os.path.join(INP, "osm_waterways.json"), encoding="utf-8"))["elements"]:
    if e["id"] not in USED: continue
    for end in (e["geometry"][0], e["geometry"][-1]):
        k, d = river_km(end["lon"], end["lat"])
        if d < 50: mouths.append({"km_below_siphon": rnd(k - SIPHON), "line_km": round(k, 1), "lon": end["lon"], "lat": end["lat"], "osm_way": e["id"]})
mouths.sort(key=lambda m: m["line_km"])
add("mouths", "Where a mapped open drain reaches the river",
    {"count": len(mouths), "km_below_siphon": [m["km_below_siphon"] for m in mouths], "points": mouths, "first": mouths[0]["km_below_siphon"], "second": mouths[1]["km_below_siphon"], "third": mouths[2]["km_below_siphon"],
     "fourth": mouths[3]["km_below_siphon"], "last": mouths[-1]["km_below_siphon"],
     "first_km_below_the_onset": mouths[0]["km_below_siphon"] - rnd(onset - SIPHON), "side_channel_km_below_the_onset": landmarks["Dark side channel"]["km_below_siphon"] - rnd(onset - SIPHON)},
    "OpenStreetMap contributors (inputs/osm_waterways.json), downloaded 21 Nov 2026",
    "Ends of the mapped waterways tagged as drains or nalas (the set in 'drain_map') that lie within 50 m of the river's centre line. Whether each carries sewage is not established from the map. OpenStreetMap does not name these channels, and outfalls that reach the river through pumping stations and short channels are not all mapped, so this is not a list of the eight published outfalls.",
    "computed from the map; names not established")

# where the drain from the Mehmood Booti side reaches the river: read from the 10 m images, not from the map
JN, SITE2, MAPEND_WAY = (74.3347, 31.6264), (74.3344, 31.6194), 316890931
def metres(p, q): return math.hypot((p[0] - q[0]) * 111320 * math.cos(math.radians(31.62)), (p[1] - q[1]) * 110900)
jk, jd = river_km(*JN)
mapend = [e for e in json.load(open(os.path.join(INP, "osm_waterways.json"), encoding="utf-8"))["elements"] if e["id"] == MAPEND_WAY][0]["geometry"][-1]
add("junction", "Where the Mehmood Booti drain reaches the river, and what a published study measured in it",
    {"lon": JN[0], "lat": JN[1], "km_below_siphon": round(jk - SIPHON, 1), "km_below_siphon_rounded": rnd(jk - SIPHON), "metres_from_centre_line": rnd(jd / 10) * 10,
     "onset_km_below_siphon": rnd(onset - SIPHON), "image_dates": ["2022-03-13", "2026-10-18"], "image": "ravi-onset-2022-03-13.jpg", "image_date": "2022-03-13",
     "mapped_drain_ends_km_from_junction": round(metres((mapend["lon"], mapend["lat"]), JN) / 1000, 1), "mapped_drain_osm_way": MAPEND_WAY,
     "study": {"sampled_from": "2020-06-01", "sampled_to": "2020-06-05", "samples": 20, "sites": 2, "site_2_lon": SITE2[0], "site_2_lat": SITE2[1], "site_2_km_from_junction": round(metres(SITE2, JN) / 1000, 1),
               "dissolved_oxygen_mg_l": 0.29, "bod_mg_l": [146, 432], "cod_mg_l": [210, 705], "suspended_solids_mg_l": [473, 2675], "published": 2025},
     "published_flow_cusecs": 20.87, "osm_chimney_nodes_beside_the_drain": [5556685222, 5556620025], "osm_steel_works_way": 761672815, "osm_steel_works_km_from_junction": round(metres((74.332, 31.6074), JN) / 1000, 1)},
    ["Copernicus Sentinel-2 Level-2A, tile 43SDR, 10 m true colour, 13 March 2022 and 18 October 2026 (make_onset_image.py)",
     "OpenStreetMap contributors (inputs/osm_waterways.json, downloaded 21 Nov 2026; inputs/osm_onset_features.json, industrial sites, chimneys and place names around the junction, queried from the Overpass API on 23 Nov 2026)",
     "https://journal.pecongress.org.pk/wp-content/uploads/2025/12/03-Habib-ur-Rehman.pdf (Habib Ur Rehman, Faakhar Raza and Shazia Ghaffar, 'Physico-chemical and microbiological water quality assessment of Mehmood Booti drain in Lahore city', Pakistan Engineering Congress Journal, January to June 2025)"],
    "The junction is where a thin black channel coming from the east meets the river in the two images. The match between it and the start of the fall is a match in place and does not establish that the channel causes the fall; its position was read by eye from the images and is good to about 100 m. It is given as a distance below the siphon by taking the nearest point of the centre line. OpenStreetMap draws a drain from the Mehmood Booti side (the way given) that stops short of the river; the distance is from its mapped end to the junction. The study sampled the Mehmood Booti drain at two sites twice a day for five days; its second site, 'near the Rani Chowk of Village Bhamma', is given at 31 deg 37 min 10 s north, 74 deg 20 min 04 s east, which falls on the black channel in the images. That the channel in the images is the drain the study sampled rests on that position. The ranges are the study's, for both sites together; it calls the area 'densely industrialized' and reports levels 'far above the acceptable standards'. It measured no metals. OpenStreetMap (queried 23 Nov 2026) marks two chimneys at 74.3609 E, 31.6097 N, beside the mapped drain, and an industrial site named as a steel works at 74.332 E, 31.6074 N; what either discharges is not established.",
    "position read from the images; study as published")
add("industry_sources", "Industrial discharge to the Ravi at Lahore, as published",
    {"factories_identified_2012": 217, "factories_identified_year": 2012, "clusters_large": 2, "clusters_small": 11, "units_in_clusters": 1213, "clusters_year": 2021,
     "sediment_pct_higher_below_city": {"cadmium": 917, "chromium": 461, "nickel": 853, "lead": 179, "mercury": 1699}, "sediment_year": 2013, "sediment_sites": 4,
     "pollution_index_pct_highly_contaminated": {"river_ravi": 56, "drains": 100, "canals": 72}, "pollution_index_year": 2024},
    ["https://nation.com.pk/19-May-2012/217-factories-polluting-ravi-lhc-told (The Nation, 19 May 2012: the provincial environment department told the Lahore High Court it had identified 217 industrial units discharging waste into the Ravi 'during last week' and had issued them notices; survey teams were still identifying more)",
     "https://tribune.com.pk/story/381042/river-pollution-lahore-high-court-asks-for-detail-of-industries-polluting-the-ravi (The Express Tribune, 18 May 2012: 'Finding differences in reports submitted' by the environment department and the water agency about industries dumping pollutants in the Ravi, the court's green bench ordered them to submit revised lists)",
     "https://pecongress.org.pk/wp-content/uploads/2025/04/Paper-No.-174.pdf (Ahmad, Mal, Shabbir and Mumtaz, International Waterlogging and Salinity Research Institute, 'Impact assessment of domestic and industrial effluent on ground water quality surrounding Lahore', Pakistan Engineering Congress, World Water Day 2021, paper 174: 'two large and 11 small industries clusters having 1213 units')",
     "https://link.springer.com/article/10.1007/s10661-013-3284-2 (Shakir, Qazi and Chaudhry, 'Monitoring the impact of urban effluents on mineral contents of water and sediments of four sites of the river Ravi, Lahore', Environmental Monitoring and Assessment 185, 2013; abstract)",
     "https://link.springer.com/article/10.1186/s12302-023-00824-2 (Iqbal, Siddique, Qadir, Ahmad, Liess and Shahid, 'Human health and ecology at risk: a case study of metal pollution in Lahore, Pakistan', Environmental Sciences Europe 36, 2024; abstract)"],
    "Quoted from the sources; none of it is ours. The 217 is one report from one week of May 2012 while the survey was still going on, and the court found that the department's list and the water agency's differed; it is not a settled count. The 2013 study sampled water and riverbed sediment at the Ravi Siphon, above the city, and at Shahdara, Sundar and Balloki below it; the percentages are how much higher the mean concentration in sediment was at Sundar than at the siphon in the low-flow season, from the abstract. The 2024 study's figures are the shares of its samples from each kind of water body that its pollution index classed as highly contaminated with metals, from the abstract. The same 2021 paper gives a daily volume of industrial waste that is larger than the published totals for all of the city's wastewater, so we do not use it.",
    "as published; not independently checked")
add("official_monitoring", "What the provincial government reports it is doing to measure and control discharge to the river",
    {"stations": 15, "parameters": 14, "entry_points_in_lahore": 10, "stations_named_on_the_ravi_at_lahore": 2, "hudiara_sampling_points": 56, "treatment_plants_at_least": 8, "reported": "2026-10-24", "data_not_public_reported": "2026-10-11",
     "mahmood_booti_plant_assessment": "September 2021", "mahmood_booti_plant_acres": 280},
    ["https://tribune.com.pk/story/2636585/punjab-envisages-water-quality-index (The Express Tribune, 24 Oct 2026, 'Punjab envisages Water Quality Index': 15 automated stations across the province's canals, rivers and other water bodies, analysing 14 parameters every hour, including stations 'near the Ravi Siphon and the river's confluence with Hudiara drain'; a water quality index in preparation; samples from 56 locations along the Hudiara drain to apportion its pollution between local industry, urban discharge and water entering from across the border; 'specialised water squads' to monitor industrial discharges; untreated sewage and contaminated water entering the river at 'around 10 locations' in Lahore; 'at least eight' treatment plants)",
     "https://tribune.com.pk/story/2634269/water-pollution-monitoring-lacks-public-transparency (The Express Tribune, 11 Oct 2026, 'Water pollution monitoring lacks public transparency': the 15 stations send data to a central control room every hour, 'the data remains out of public reach')",
     "https://epd.punjab.gov.pk/system/files/WWTP-Mehmood-Booti-Final.pdf (Ravi Urban Development Authority, 'Wastewater treatment plant at Mahmood Booti/Shadbagh, Lahore: environmental impact assessment study', September 2021: a plant on 280 acres at Shadbagh, the site surrounded by the settlements of Jhuggian Jodha, Bhamma and Khokhar Pind)"],
    "Quoted from the sources. The 15 stations are spread over the province; the article names two places on the Ravi at Lahore, near the Ravi Siphon and at the confluence with the Hudiara drain. We have not seen data from the stations; the 11 Oct 2026 report says it was not public. We did not establish the present status of the Mahmood Booti/Shadbagh plant.",
    "as reported; not independently checked")

# ---------------------------------------------------------------- people near mapped drains
P = json.load(open(os.path.join(INP, "population_near_drains.json"), encoding="utf-8"))
FRAME = {"west": 74.10, "south": 31.375, "east": 74.50, "north": 31.70}   # the map in the report
segs, raw_m, named_m = {}, 0.0, 0.0
for e in json.load(open(os.path.join(INP, "osm_waterways.json"), encoding="utf-8"))["elements"]:
    if e["id"] not in USED: continue
    for a, b in zip(e["geometry"], e["geometry"][1:]):
        (ax, ay), (bx, by_) = to_xy(a["lon"], a["lat"]), to_xy(b["lon"], b["lat"]); L = math.hypot(bx - ax, by_ - ay); raw_m += L
        key = tuple(sorted([(a["lon"], a["lat"]), (b["lon"], b["lat"])]))
        if key not in segs: segs[key] = (L, (a["lon"] + b["lon"]) / 2, (a["lat"] + b["lat"]) / 2, bool(e.get("tags", {}).get("name")))
tot_m = sum(v[0] for v in segs.values())
frame_m = sum(v[0] for v in segs.values() if FRAME["west"] <= v[1] <= FRAME["east"] and FRAME["south"] <= v[2] <= FRAME["north"])
add("drain_map", "Waterways tagged as drains or nalas in OpenStreetMap around Lahore, as drawn on the map",
    {"drain_km": rnd(tot_m / 1000), "km_inside_the_map_frame": rnd(frame_m / 1000), "duplicate_km_removed": round((raw_m - tot_m) / 1000, 1), "named_km": rnd(sum(v[0] for v in segs.values() if v[3]) / 1000),
     "unnamed_km": rnd(sum(v[0] for v in segs.values() if not v[3]) / 1000), "ways": len(USED), "window_w_s_e_n": P["window_w_s_e_n"], "map_frame": FRAME},
    "OpenStreetMap contributors: every waterway in the window tagged as a drain, plus named nalas, not in a culvert or covered; waterways tagged as irrigation canals left out (inputs/osm_waterways.json; the list of ways used is in inputs/population_near_drains.json)",
    "Lengths summed along the mapped lines after removing segments that appear twice. This is everything so tagged inside the window, not only channels that reach the Ravi, and the tag does not say what a channel carries: some on the outskirts may carry farm or storm water. The map is incomplete, mainly in the north of the city.",
    "computed from the map")

# ---------------------------------------------------------------- published figures (each one opened and read)
CUSEC = 0.0283168
flows = [("Mehmood Booti", 20.87), ("Shad Bagh", 139), ("Farrukhabad", 219), ("Budha Ravi", 41.99), ("Main Outfall", 193), ("Gulshan-e-Ravi", 246.5), ("Babu Sabu", 270.7), ("Hudiara", 535.7)]
tot = sum(v for _, v in flows)
add("drain_flows", "Discharge of the eight drains entering the Ravi at Lahore, as published",
    {"drains": [{"name": n, "cusecs": rnd(v), "cubic_metres_per_second": round(v * CUSEC, 1), "pct_of_the_eight": rnd(100 * v / tot)} for n, v in flows],
     "sum_cusecs": rnd(tot), "sum_of_the_rounded_rows_cusecs": sum(rnd(v) for n, v in flows), "sum_cubic_metres_per_second": rnd(tot * CUSEC), "count": len(flows), "paper_total_2006_cusecs": 990, "paper_total_now_cusecs": 3304,
     "largest": "Hudiara", "largest_pct": rnd(100 * 535.7 / tot)},
    "https://pecongress.org.pk/document/environment-threats-to-groundwater-2/ (Hassan, Hassan and Akhtar, Irrigation Research Institute, Government of the Punjab, 'Environment Threats to Groundwater in Lahore Area', Pakistan Engineering Congress; Table 2)",
    "Copied from the paper's Table 2 and rounded; listed in the order the drains meet the river, upstream first. The paper gives no date for the discharge column (its water-quality columns are May 2011 and March 2012). The same paper says the city's discharge to the river was about 990 cusecs in 2006 and 'now has crossed to 3,304 cusecs'; its own table sums to about half of that, and it does not explain the difference.",
    "as published; not independently checked")
add("treatment", "Sewage treatment in Lahore, as reported",
    {"untreated_mgd": 640, "untreated_million_litres_a_day": rnd(640 * 4.546 / 10) * 10, "untreated_mgd_low": 540, "untreated_million_litres_a_day_low": rnd(540 * 4.546 / 10) * 10,
     "plants_planned": 6, "phase_one_pct_of_untreated": rnd(100.0 * 88 / 640), "phase_one_pct_of_untreated_low_total": rnd(100.0 * 88 / 540), "babu_sabu_phase_one_mgd": 88, "babu_sabu_ultimate_mgd": 198,
     "babu_sabu_cost_billion_rupees": 56, "babu_sabu_cost_billion_rupees_2025": 50.2, "provincial_approval": "2025-08-13", "federal_approval": "2026-08-21", "launch_within_months_of_approval": 6, "french_agency_share_pct": 74,
     "babu_sabu_land_acquired": "1992-93", "babu_sabu_preconstruction_months": 12, "babu_sabu_construction_months": 42, "aiib_million_usd": 160, "aiib_approved": "2025-10-09", "trunk_sewer_km": 32.3, "drains_freed_km": 9,
     "hudiara_societies_with_primary_treatment": 32, "hudiara_societies_registered": 49, "hudiara_industries_with_plants": 18, "disposal_stations_central_zone": 6, "disposal_capacity_cusecs": 1270, "esia_pages": [23, 24, 58]},
    ["https://www.dawn.com/news/1948317 (Dawn, 12 Oct 2025: 'Lahore currently lacks a treatment facility'; the river receives 'approximately 640 million gallons per day (MGD) of untreated wastewater'; six treatment plants planned)",
     "https://www.dawn.com/news/1931168 (Dawn, 16 Aug 2025: Babu Sabu plant approved by the provincial development working party on 13 Aug 2025, to give the city 'its first large-scale wastewater treatment facility'; 88 MGD in phase one, 198 MGD ultimately, Rs50.2bn)",
     "https://www.dawn.com/news/2024473 (Dawn, 22 Aug 2026, 'Largest wastewater treatment plant gets Centre's nod': the Executive Committee of the National Economic Council approved Rs56bn for the Babu Sabu plant on 21 Aug 2026, 'paving the way for its launch within the next six months after completion of the bidding process'; 74 percent of the funds from the French development agency; 12 months of pre-construction and 42 of construction)",
     "https://nation.com.pk/23-Aug-2026/ecnec-approves-rs-56b-babu-sabu-wastewater-treatment-plant-project (The Nation, 23 Aug 2026: the same approval; 88 MGD; six plants needed in all)",
     "https://www.dawn.com/news/1975517 (Dawn, 25 Feb 2026, 'Govt mulls sewage treatment plants on Hudiara Drain': 'out of 49 housing societies registered with the LDA, primary treatment plants are operational in 32 societies'; 'treatment plants in 18 industries of the Packages Cluster are now operational'; plants are planned at points along the drain)",
     "https://www.aiib.org/en/projects/details/2025/approved/Pakistan-Lahore-Water-and-Wastewater-Management-Project.html (AIIB project page: USD 160 million approved 9 Oct 2025; three trunk sewers of about 32.3 km; 'nearly 9 km of local surface drains' to be freed from wastewater; the Babu Sabu plant is to be built by the water agency with French development agency funding)",
     "https://www.aiib.org/en/projects/details/2025/_download/Pakistan/Environmental-and-Social-Impact-Assessment-ESIA.pdf (updated environmental and social impact assessment for the sewer from Larech Colony to Gulshan-e-Ravi: Table 3-2, six outfall disposal stations in the central zone with 1,270 cusecs of pumps, PDF page 58; five disposal stations pump sewage into the river and others into storm water drains that end in the river, PDF page 23; 'An estimated 540 MGD (1000 Cusec) of untreated domestic sewage is being disposed of into River Ravi', PDF page 24)"],
    "Quoted from the sources. Two totals are published for the untreated wastewater reaching the river: 640 MGD (Dawn, Oct 2025) and 540 MGD, of domestic sewage (the water agency's assessment for the bank); neither is ours and we give both. Gallons are imperial as used in Pakistan (4.546 litres); litres are rounded to the nearest 10 million. The first phase's share is 88 MGD over each total. The plant's cost was Rs50.2bn at provincial approval in Aug 2025 and Rs56bn at federal approval in Aug 2026. Dawn gives the bank's financing as $235 million; the bank's own page says USD 160 million, which is used here. As of the Aug 2026 reports the plant was still to be tendered; we found no later report that construction has begun, and did not confirm it either way.",
    "as reported; not independently checked")
add("ground", "What samplers on the river bank recorded",
    {"samples": 12, "sites": 4, "from": "November 2009", "to": "March 2010", "year": 2011},
    "https://pecongress.org.pk/document/paper-no-704-water-quality-assessment-of-river-ravi-around-lahore-city-2/ (Afaf Ayesha, Irrigation and Power Department, Lahore, 'Water quality assessment of river Ravi around Lahore city', Pakistan Engineering Congress, 71st annual session, paper 704, 2011; Table 2)",
    "Quoted from the paper's Table 2: colour 'yellowish' and odour 'odorless' at the Ravi Siphon; colour 'blackish' and odour objectionable at Shahdara Bridge, Mohlanwal village and the confluence of the Hudiara and Sattu Katla drains. Colour and odour were judged by eye and nose. Twelve samples, November 2009 to March 2010.",
    "as published; not independently checked")
add("industry", "One industrial estate's route to the Ravi, as published",
    {"industries": 475, "wastewater_cubic_metres_a_day": 134541, "bod_mg_l": 400, "sampled_industries_bod_range_mg_l": [118, 2337], "year": 2016},
    "https://www.paspk.org/wp-content/uploads/2016/06/Wastewater-Characterization.pdf (Haydar, Hussain, Haider and Attiq-ur-Rehman, 'Wastewater characterization of selected industries in Quaid-e-Azam Industrial Estate: treatment options and impact on groundwater quality', Proceedings of the Pakistan Academy of Sciences B 53(2), 2016)",
    "Quoted from the paper, which reports these as approximate figures for the estate and did not itself count or meter every industry: about 475 industries discharging 134,541 cubic metres of wastewater a day, reaching the Ravi through the Sattu Katla and Hudiara drains, with no treatment facility at the estate at the time. The paper's own measurements are of a sample of industries and of the combined drain.",
    "as published; not independently checked")
json.dump({"report": "The Ravi darkens below Lahore: a nine-year satellite baseline of river colour for checking measures on sewage and industrial discharge", "published": "2026-11-24", "version": "1.0",
           "inputs": {"note": "Inputs and scripts in the repository under scripts/reports/ravi-drains/analysis/"},
           "evidence": E}, open(os.path.join(OUT, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("evidence entries", len(E))
for e in E:
    v = {k: x for k, x in e["value"].items() if k not in ("date_list", "by_date", "october_by_km_below_siphon", "spring_by_km_below_siphon", "october", "spring", "km_by_name", "points")}
    print(e["id"], json.dumps(v, ensure_ascii=False)[:1500], "\n")
