# Every number in the rain-spell report, computed from the files in data/. python3 build_evidence.py
# Writes site/public/report/punjab-rain-nov-2026/data.json (the evidence list) and data/series.json (hourly city
# series for the charts). Parses on Python 3.9.
import csv, glob, json, os, re, statistics, datetime as D

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "punjab-rain-nov-2026")
os.makedirs(OUT, exist_ok=True)
PKT = D.timedelta(hours=5)
E = []
def rnd(x): return int(x + 0.5)  # halves round up
def add(id, claim, value, source, method): E.append({"id": id, "claim": claim, "value": value, "source": source, "method": method})

# ---------------------------------------------------------------- 1. Rain gauges, Pakistan (SYNOP via OGIMET)
ST = {"41640": "Lahore City", "41571": "Chaklala (Rawalpindi)", "41573": "Murree", "41598": "Jhelum", "41600": "Sialkot City",
      "41630": "Faisalabad", "41675": "Multan", "41678": "Bahawalnagar", "41700": "Bahawalpur", "41594": "Sargodha",
      "41535": "Kakul (Abbottabad)", "41536": "Balakot"}
def rrr(g):  # 6RRRt group -> (mm or "trace", period code)
    v = int(g[1:4]); return ("trace" if v == 990 else round((v - 990) / 10, 1) if v > 990 else float(v)), g[4]
synop = {}  # station -> {utc datetime: {"s1": (amount, t) or None, "r24": mm or None, "s3_3h": amount or None, "nil": bool, "raw": str}}
for f in sorted(glob.glob(os.path.join(DATA, "rainfall", "ogimet", "synop-block-*.txt"))):
    for line in open(f, encoding="utf-8"):
        p = line.strip().split(",", 6)
        if len(p) < 7 or p[0] not in ST: continue
        t = D.datetime(int(p[1]), int(p[2]), int(p[3]), int(p[4]), int(p[5])); body = p[6].rstrip("=").split()
        rec = {"s1": None, "r24": None, "s3_3h": None, "nil": "NIL" in body, "raw": p[6]}
        if not rec["nil"] and len(body) > 5:
            s3 = body.index("333") if "333" in body else len(body)
            for g in body[5:s3]:
                if re.fullmatch(r"6\d{4}", g): rec["s1"] = rrr(g); break
            for g in body[s3 + 1:]:
                if re.fullmatch(r"7\d{4}", g) and t.hour == 3: rec["r24"] = "trace" if g[1:] == "9999" else int(g[1:]) / 10
                if re.fullmatch(r"6\d{3}7", g): rec["s3_3h"] = rrr(g)[0]  # tR 7 = past 3 hours
        synop.setdefault(p[0], {})[t] = rec
DAYS = ["2026-11-%02d" % d for d in range(11, 16)]
rain = {}
for sid, name in ST.items():
    row = {}
    for d in DAYS:
        rec = synop.get(sid, {}).get(D.datetime.fromisoformat(d + "T03:00"))
        row[d] = None if rec is None or rec["nil"] or rec["r24"] is None else rec["r24"]
    rain[name] = row
lh = synop["41640"]
l00, l03 = lh[D.datetime(2026, 11, 13, 0)], lh[D.datetime(2026, 11, 13, 3)]
assert lh[D.datetime(2026, 11, 12, 12)]["s1"] == (0.0, "2") and l03["s3_3h"] == 0.0  # 12 h to 5 pm on 12 Nov and 3 h to 8 am on 13 Nov were dry, so the 24 h is a trace
assert l00["s1"] == ("trace", "2") and l00["s3_3h"] == "trace" and l03["r24"] is None
nonzero3h = [t for t, r in lh.items() if r["s3_3h"] not in (None, 0.0)]
assert nonzero3h == [D.datetime(2026, 11, 13, 0)]
assert [t for t, r in lh.items() if r["s1"] and r["s1"][0] != 0.0] == [D.datetime(2026, 11, 13, 0)]
rain["Lahore City"]["2026-11-13"] = "trace"
plains = ["Lahore City", "Faisalabad", "Multan", "Bahawalpur"]
cloud = {(t + PKT).strftime("%d %H:%M"): (None if r["raw"].split()[4][0] == "/" else int(r["raw"].split()[4][0])) for t, r in sorted(lh.items()) if not r["nil"]}
cl = lambda a, b: [v for k, v in cloud.items() if a <= k <= b and v is not None]
add("rain_pk", "24-hour rainfall (mm) ending 08:00 PKT on each date at Pakistan Meteorological Department observatories; null = no 24-hour figure in the report; Lahore City on 13 Nov is the 12-hour figure",
    {"stations": rain,
     "murree_total_11_15": round(sum(v for v in rain["Murree"].values() if isinstance(v, float)), 1),
     "plains_stations": plains,
     "plains_measurable_days": sum(1 for s in plains for v in rain[s].values() if isinstance(v, float) and v > 0),
     "lahore": {"12h_to_05_pkt_13_nov": "trace", "3h_to_05_pkt_13_nov": "trace", "24h_group_13_nov": "not in the report",
                "report_00utc_13_nov": l00["raw"], "report_03utc_13_nov": l03["raw"],
                "other_3h_periods_with_rain_10_15_nov": 0,
                "cloud_eighths_by_report_pkt": cloud,
                "cloud_min_12nov1400_to_13nov1400": min(cl("12 14:00", "13 14:00")), "cloud_max_12nov1400_to_13nov1400": max(cl("12 14:00", "13 14:00")),
                "cloud_max_10nov_to_12nov0800": max(cl("10 05:00", "12 08:00")), "cloud_max_13nov2000_to_14nov1400": max(cl("13 20:00", "14 14:00"))}},
    "PMD observatory SYNOP reports as exchanged on the WMO network, relayed by OGIMET (ogimet.com/cgi-bin/getsynop), fetched 15 Nov 2026; data/rainfall/ogimet/",
    "Section 3 group 7RRRR of the 03 UTC report = 24 h total in tenths of mm ending 08:00 PKT. Lahore City's 03 UTC report on 13 Nov has no 7RRRR group; its 00 UTC report gives section 1 group 69902 (trace in 12 h) and section 3 group 69907 (trace in the past 3 h). One gauge per place. Sargodha sent NIL reports. Cloud cover is the N digit of the Nddff group (eighths of the sky). Decoded by this script; rules in data/rainfall/ogimet/README.txt.")

# ---------------------------------------------------------------- 2. Rain, Indian side (IMD PDFs, 15 Nov issue)
def imd_table(fn, first, last):
    t = open(os.path.join(DATA, "rainfall", "pdf-imd-text", fn), encoding="utf-8").read().replace("\n", " ")
    t = t[t.rindex("DISTRICT TODAY"):]
    rows = re.findall(r"([A-Z][A-Z ()]+?)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)", t)
    out = {}
    for r in rows:
        n = r[0].strip()
        if "DEPARTURE" in n: n = n.rsplit("DEPARTURE", 1)[1].strip()
        if n.startswith("SUBDIVISION") or n == "RAINFALL": continue
        out[n] = {"today_mm": float(r[1]), "month_mm": float(r[2])}
    assert first in out and last in out, (fn, list(out))
    return out
pun = imd_table("imd-chandigarh-rainfall_pun-fetched-2026-11-15.txt", "AMRITSAR", "TARN TARAN")
har = imd_table("imd-chandigarh-rainfall_har-fetched-2026-11-15.txt", "AMBALA", "YAMUNA NAGAR")
add("rain_in", "Month-to-date rainfall (mm), 1 to 15 November 2026 (to 08:30 IST 15 Nov), by district, India Meteorological Department",
    {"punjab_districts_listed": len(pun), "punjab_zero": sum(1 for v in pun.values() if v["month_mm"] == 0),
     "punjab_nonzero": {k: v["month_mm"] for k, v in pun.items() if v["month_mm"] > 0},
     "haryana_rows_listed": len(har), "haryana_zero": sum(1 for v in har.values() if v["month_mm"] == 0),
     "delhi_month_to_date": {"Safdarjung": 0.0, "Ridge": 0.0, "Palam": "trace", "Lodhi Road": "trace", "Ayanagar": 1.4},
     "punjab": pun, "haryana": har},
    "IMD Meteorological Centre Chandigarh, 'Rainfall Status Punjab' and 'Rainfall Status Haryana', and IMD New Delhi 'Observational data of Delhi', issues of 15 Nov 2026; data/rainfall/pdf-imd/ (PDFs, SHA256SUMS.txt) and pdf-imd-text/",
    "Monthly 'ACTUAL' column of the district table, read from the PDF text. Figures are rounded to 0.1 mm; the same bulletin says very light rain occurred at isolated places in Punjab in the 24 h to 08:30 IST 15 Nov. The Haryana table includes a row for Chandigarh. Delhi figures were read from the Observational table by hand (Ayanagar's 1.4 mm fell in the 24 h to 08:30 IST 15 Nov). The issues of 12-14 Nov were overwritten before we fetched them.")

# ---------------------------------------------------------------- 3. Airport reports (METAR via Iowa Environmental Mesonet)
AP = {"OPLA": "Lahore", "OPFA": "Faisalabad", "OPMT": "Multan", "OPST": "Sialkot", "OPIS": "Islamabad", "VIAR": "Amritsar"}
def metar(st):
    out = []
    for r in csv.DictReader(open(os.path.join(DATA, "rainfall", "iem-metar", st + ".csv"), encoding="utf-8")):
        t = D.datetime.strptime(r["valid"], "%Y-%m-%d %H:%M") + PKT
        f = lambda k: None if r[k] in ("M", "") else float(r[k])
        vis = re.search(r"KT (\d{4}) ", r["metar"])
        out.append({"t": t, "kt": f("sknt"), "dir": f("drct"), "wx": "" if r["wxcodes"] == "M" else r["wxcodes"], "vis_m": int(vis.group(1)) if vis else None, "raw": r["metar"]})
    return out
M = {st: metar(st) for st in AP}
nights = {}
for st, name in AP.items():
    row = {}
    for d in range(9, 15):
        t0 = D.datetime(2026, 11, d, 20); t1 = t0 + D.timedelta(hours=12)
        w = [x["kt"] for x in M[st] if t0 <= x["t"] < t1 and x["kt"] is not None]
        rainy = sorted({x["t"].strftime("%d %b %H:%M") for x in M[st] if t0 <= x["t"] < t1 and ("RA" in x["wx"] or "DZ" in x["wx"])})
        row["%d-%d" % (d, d + 1)] = {"mean_kt": round(sum(w) / len(w), 1), "mean_kmh": rnd(sum(w) / len(w) * 1.852), "max_kt": int(max(w)), "max_kmh": rnd(max(w) * 1.852), "reports": len(w), "rain_reports": len(rainy)}
    nights[name] = row
for name in ("Lahore", "Faisalabad", "Multan", "Sialkot", "Amritsar"):
    assert max(nights[name], key=lambda k: nights[name][k]["mean_kt"]) == "12-13", name
wet = lambda st: [x for x in M[st] if "RA" in x["wx"] or "DZ" in x["wx"]]
ts = [x["t"] for x in M["OPST"] if "TS" in x["wx"] and D.datetime(2026, 11, 12, 20) <= x["t"] < D.datetime(2026, 11, 13, 8)]
add("airport_rain", "Airport reports with rain or drizzle, 9 Nov to midday 15 Nov 2026 (Pakistan time), and Sialkot's thunderstorm reports on the night of 12-13 Nov",
    {"reports_with_rain": {AP[st]: len(wet(st)) for st in AP}, "period": [min(x["t"] for x in M["OPLA"]).strftime("%Y-%m-%d %H:%M"), max(x["t"] for x in M["OPLA"]).strftime("%Y-%m-%d %H:%M")],
     "sialkot_thunderstorm_first": min(ts).strftime("%H:%M"), "sialkot_thunderstorm_last": max(ts).strftime("%H:%M"), "sialkot_thunderstorm_reports": len(ts)},
    "Airport METAR reports via Iowa Environmental Mesonet; data/rainfall/iem-metar/", "Reports whose weather group includes RA (rain) or DZ (drizzle); TS = thunderstorm. A METAR says what the weather was at the time of the report; it gives no rainfall amount.")
calm = [nights[n][k]["mean_kmh"] for n in ("Lahore", "Faisalabad", "Multan") for k in ("9-10", "10-11", "11-12")]
add("calm_nights", "Lowest and highest night-average wind (km/h) at Lahore, Faisalabad and Multan airports on the three nights of 9-10, 10-11 and 11-12 November",
    {"min_kmh": min(calm), "max_kmh": max(calm)}, "As wind_nights", "As wind_nights")
add("wind_nights", "Mean and highest reported wind (knots) at airports, 8 pm to 8 am Pakistan time, nights of 9-10 to 14-15 November 2026, and the number of reports with rain or drizzle",
    nights, "Airport METAR reports via Iowa Environmental Mesonet (mesonet.agron.iastate.edu), fetched 15 Nov 2026; data/rainfall/iem-metar/",
    "All reports (usually half-hourly) with a wind speed, from 20:00 to 07:59 PKT (the 08:00 report is not included). Calm is counted as 0. A METAR gives the wind at the airport at the time of the report, not a night-long record. km/h = knots x 1.852, rounded.")
la = M["OPLA"]; W = lambda a, b: [x for x in la if a <= x["t"] < b]
rainrep = [x for x in la if "RA" in x["wx"] or "DZ" in x["wx"]]
assert len(rainrep) == 1
at = lambda *a: next(x for x in la if x["t"] == D.datetime(*a))
peak = max(W(D.datetime(2026, 11, 13, 0), D.datetime(2026, 11, 13, 8)), key=lambda x: x["kt"])
add("lahore_airport", "Lahore airport reports on the night of 12-13 November 2026 (Pakistan time)",
    {"rain_reports_9_nov_to_midday_15_nov": len(rainrep), "rain_report_time": rainrep[0]["t"].strftime("%Y-%m-%d %H:%M"), "rain_report": rainrep[0]["raw"],
     "wind_kt_20_to_02": sorted({int(x["kt"]) for x in W(D.datetime(2026, 11, 12, 20), D.datetime(2026, 11, 13, 2, 1))}),
     "wind_kt_0500": int(at(2026, 11, 13, 5)["kt"]), "wind_dir_0500": int(at(2026, 11, 13, 5)["dir"]),
     "wind_peak_kt": int(peak["kt"]), "wind_peak_kmh": rnd(peak["kt"] * 1.852), "wind_kmh_0500": rnd(at(2026, 11, 13, 5)["kt"] * 1.852),
     "wind_kmh_20_to_0230_max": rnd(max(x["kt"] for x in W(D.datetime(2026, 11, 12, 20), D.datetime(2026, 11, 13, 2, 31))) * 1.852), "wind_kmh_20_to_0230_min": rnd(min(x["kt"] for x in W(D.datetime(2026, 11, 12, 20), D.datetime(2026, 11, 13, 2, 31))) * 1.852),
     "rain_weather_20_to_0230": sorted({x["wx"] for x in W(D.datetime(2026, 11, 12, 20), D.datetime(2026, 11, 13, 2, 31))}),
     "vis_m_0430": at(2026, 11, 13, 4, 30)["vis_m"], "vis_m_0400": at(2026, 11, 13, 4)["vis_m"], "wind_peak_time": peak["t"].strftime("%H:%M"), "wind_peak_dir": int(peak["dir"]),
     "vis_m_2000": at(2026, 11, 12, 20)["vis_m"], "vis_m_0300": at(2026, 11, 13, 3)["vis_m"], "vis_m_0500": at(2026, 11, 13, 5)["vis_m"], "vis_m_0700": at(2026, 11, 13, 7)["vis_m"],
     "weather_2000": at(2026, 11, 12, 20)["wx"], "weather_0700": at(2026, 11, 13, 7)["wx"]},
    "OPLA METAR via Iowa Environmental Mesonet; data/rainfall/iem-metar/OPLA.csv",
    "Times converted from UTC to PKT (UTC+5). FU = smoke, BR = mist, -RA = light rain. Visibility is the prevailing visibility group of the report.")

# ---------------------------------------------------------------- 4. IQAir hourly city figures (three captures)
CAPS = [("before", "iqair-before-2026-11-11T0130PKT.json"), ("after", "iqair-after-2026-11-14T2000PKT.json"), ("rebound", "iqair-rebound-2026-11-16T0030PKT.json")]
def series(ys, last_cat, cap_utc, india):
    """hour-start (PKT) -> value. The last category is the latest hour start at or before the capture time."""
    off = D.timedelta(hours=5, minutes=30) if india else PKT
    cap = D.datetime.strptime(cap_utc[:19], "%Y-%m-%dT%H:%M:%S") + off
    hh, mm = map(int, last_cat.split(":")); last = cap.replace(hour=hh, minute=mm, second=0)
    if last > cap: last -= D.timedelta(days=1)
    vals = ys.split(","); out = {}
    for i, v in enumerate(vals):
        t = last - D.timedelta(hours=len(vals) - 1 - i)
        if india: t -= D.timedelta(minutes=30)  # an IST hour starting hh:30 is the PKT hour starting hh:00
        if v != "": out[t] = int(v)
    return out
CITY = {}; LAHORE_ST = {}; NST = {}
for tag, fn in CAPS:
    for path, c in json.load(open(os.path.join(DATA, fn), encoding="utf-8"))["cities"].items():
        name = path.split("/")[-1]; india = "/india/" in path
        CITY.setdefault(name, {}).update(series(c["city"]["ys"], c["city"]["last"], c["captured_utc_end"], india))  # later captures overwrite
        NST.setdefault(name, {})[tag] = {"stations": len(c["rows"]), "from": sorted({r[1] for r in c["rows"]})}
        if name == "lahore" and tag == "after":
            for r in c["rows"]:
                if not r[6]: LAHORE_ST[r[0]] = series(r[5], r[4], c["captured_utc_end"], india)
H = lambda *a: D.datetime(2026, 11, *a)
def daymean(name, d):
    v = [CITY[name].get(H(d, h)) for h in range(24)]; v = [x for x in v if x is not None]
    return {"mean": rnd(sum(v) / len(v)), "hours": len(v), "max": max(v), "min": min(v)}
PK = ["lahore", "gujranwala", "faisalabad", "multan", "sialkot", "rawalpindi", "islamabad"]
INC = ["amritsar", "jalandhar", "ludhiana", "patiala", "bathinda", "chandigarh"]
cities = {}
for n in PK + INC:
    s = CITY[n]; start = s.get(H(12, 20))
    lows = {t: v for t, v in s.items() if H(12, 20) <= t <= H(13, 23)}; tl = min(lows, key=lambda t: (lows[t], t))
    reb = {t: v for t, v in s.items() if tl < t <= H(15, 23)}; tr = max(reb, key=lambda t: (reb[t], -t.timestamp()))
    pre = {t: v for t, v in s.items() if t <= H(11, 0)}; tp = max(pre, key=lambda t: pre[t])
    ev = {t: v for t, v in s.items() if H(12, 20) <= t <= H(12, 23)}; te = max(ev, key=lambda t: ev[t])
    run = []
    for t in sorted(x for x in s if x >= tl):
        if s[t] >= 200: break
        run.append(t)
    b = tl
    while b - D.timedelta(hours=1) in s and s[b - D.timedelta(hours=1)] < 200: b -= D.timedelta(hours=1)
    nt = {t: v for t, v in s.items() if H(12, 20) <= t <= H(13, 8)}; tn = min(nt, key=lambda t: (nt[t], t))
    cities[n] = {"night_low": nt[tn], "night_low_hour": tn.hour, "evening_12_nov_high": ev[te], "evening_12_nov_high_hour": te.hour, "fall_from_evening": ev[te] - lows[tl],
                 "below_200_from": b.strftime("%Y-%m-%d %H:%M"), "below_200_hours": int((run[-1] - b).total_seconds() // 3600) + 1 if run else 0,
                 "below_200_to_end_of_capture": bool(run) and run[-1] == max(s),
                 "at_20_12_nov": start, "low": lows[tl], "low_time": tl.strftime("%Y-%m-%d %H:%M"), "low_hour": tl.hour, "low_day": tl.day,
                 "fall": None if start is None else start - lows[tl],
                 "back_at_200": next((t.strftime("%Y-%m-%d %H:%M") for t in sorted(s) if t > tl and s[t] >= 200), None),
                 "highest_after_low": reb[tr], "highest_after_low_time": tr.strftime("%Y-%m-%d %H:%M"),
                 "highest_9_10_nov": pre[tp], "highest_9_10_nov_time": tp.strftime("%Y-%m-%d %H:%M"),
                 "day": {str(d): daymean(n, d) for d in (10, 13, 14, 15)},
                 "stations": NST[n]}
add("cities", "IQAir hourly city figure (US AQI+, median of stations) for 13 places: value in the hour from 8 pm on 12 Nov, the lowest hour up to the end of 13 Nov, the highest hour after that to the end of 15 Nov, the highest hour captured on 9-10 Nov, and 24-hour means for 10, 13, 14 and 15 Nov (Pakistan time)",
    cities, "IQAir city pages, History > Hourly, captured 11 Nov 01:30, 14 Nov 20:00 and 16 Nov 00:30 PKT; data/iqair-*.json",
    "Hours are hour starts in Pakistan time; Indian pages show hours starting at half past in India time, which are the same hours. Where two captures overlap (14 Nov 01:00-18:00) the later one is used, because IQAir revises hours. No capture covers 11 Nov 01:00 to 12 Nov 19:00. Day means are the mean of the hourly city figures of that calendar day (hours counted in 'hours'; Faisalabad has 23 on 10 Nov), halves rounded up. night_low is the lowest hour from 20:00 on 12 Nov to 08:00 on 13 Nov. Indian cities other than Chandigarh have one feed each, attributed to the Central Pollution Control Board; Chandigarh has three such feeds and one private sensor. These relayed feeds were unreliable on Diwali night (see the Diwali report) and are shown for reference only.")
assert all(cities[n]["day"]["15"]["mean"] < cities[n]["day"]["10"]["mean"] for n in PK)
assert cities["sialkot"]["night_low_hour"] == 2 and cities["jalandhar"]["low_hour"] == 14 and cities["ludhiana"]["low_hour"] == 14
L = CITY["lahore"]
lh_hours = {t.strftime("%d %H:%M"): L[t] for t in sorted(L) if H(12, 20) <= t <= H(13, 12)}
both = {k: (v[H(12, 20)], v[H(13, 5)]) for k, v in LAHORE_ST.items() if H(12, 20) in v and H(13, 5) in v}
add("lahore_night", "Lahore's IQAir city figure hour by hour on the night of 12-13 November, and its stations one by one",
    {"hourly": lh_hours, "at_2000": L[H(12, 20)], "at_0200": L[H(13, 2)], "at_0300": L[H(13, 3)], "at_0400": L[H(13, 4)], "at_0500": L[H(13, 5)],
     "fall_2000_to_0100": L[H(12, 20)] - L[H(13, 1)], "fall_0100_to_0500": L[H(13, 1)] - L[H(13, 5)],
     "afternoon_low_13": min(L[H(13, h)] for h in range(12, 18)), "afternoon_low_14": min(L[H(14, h)] for h in range(12, 18)), "afternoon_low_15": min(L[H(15, h)] for h in range(12, 18)),
     "morning_high_14": max(L[H(14, h)] for h in range(0, 12)), "morning_high_15": max(L[H(15, h)] for h in range(0, 12)),
     "at_2300_15": L[H(15, 23)], "at_2000_10": L[H(10, 20)], "at_0100_13": L[H(13, 1)],
     "lowest_hour_10": min(L[H(10, h)] for h in range(24)), "hours_13_below_lowest_of_10": sum(1 for h in range(24) if L[H(13, h)] < min(L[H(10, x)] for x in range(24))),
     "afternoon_low_10": min(L[H(10, h)] for h in range(12, 18)), "morning_high_10": max(L[H(10, h)] for h in range(0, 12)),
     "stations_in_capture": len(LAHORE_ST), "stations_with_both_hours": len(both), "stations_lower_at_0500": sum(1 for a, b in both.values() if b < a),
     "stations_at_least_halved": sum(1 for a, b in both.values() if b <= a / 2),
     "station_median_2000": statistics.median(a for a, b in both.values()), "station_median_0500": statistics.median(b for a, b in both.values())},
    "IQAir Lahore city page and the station pages linked from it, captured 14 Nov 2026 19:57-20:02 PKT; data/iqair-after-2026-11-14T2000PKT.json",
    "Station comparison: stations with a reading in both the hour from 20:00 on 12 Nov and the hour from 05:00 on 13 Nov. Readings are what IQAir displayed; instruments were not checked.")

# ---------------------------------------------------------------- 5. Fires
fires = {}
for f in sorted(glob.glob(os.path.join(DATA, "day-summaries", "2026-11-*.json"))):
    s = json.load(open(f))["summary"]["states"]; g = lambda k, i: s.get(k, [0, 0, 0, 0])[i]
    fires[os.path.basename(f)[:10]] = {"pk_punjab": g("PK|Punjab", 0), "in_punjab": g("IN|Punjab", 0), "two_punjabs": g("PK|Punjab", 0) + g("IN|Punjab", 0),
                                         "pk_punjab_noaa20": g("PK|Punjab", 2), "in_punjab_noaa20": g("IN|Punjab", 2), "two_punjabs_noaa20": g("PK|Punjab", 2) + g("IN|Punjab", 2)}
assert sorted(fires, key=lambda k: fires[k]["two_punjabs_noaa20"])[:2] == ["2026-11-13", "2026-11-12"]
rng = lambda a, b, k: sum(fires["2026-11-%02d" % d][k] for d in range(a, b + 1))
add("fires", "Satellite fire spots per Pakistan-time day in Pakistani and Indian Punjab, 1-15 November 2026, all satellites and NOAA-20 alone",
    {"days": fires,
     "noaa20_mean_7_10": rnd(rng(7, 10, "two_punjabs_noaa20") / 4), "noaa20_mean_12_13": rnd(rng(12, 13, "two_punjabs_noaa20") / 2),
     "all_mean_7_10": rnd(rng(7, 10, "two_punjabs") / 4), "all_mean_12_13": rnd(rng(12, 13, "two_punjabs") / 2)},
    "NASA FIRMS VIIRS and MODIS via HamariHawa's daily archive (hamarihawa.org/api/day?d=YYYY-MM-DD), retrieved " + open(os.path.join(DATA, "day-summaries", "RETRIEVED.txt")).read().strip()[:16] + " UTC; data/day-summaries/",
    "Near-real-time data; states[key][0] = spots on all satellites, [2] = NOAA-20. Cloud hides fires from the satellites, so low counts on cloudy days are not evidence that burning stopped. The latest days can still change as late data arrive.")

json.dump({"report": "Lahore got a trace of rain, Faisalabad and Multan none. Their air improved anyway", "published": "2026-11-16", "version": "2026-11-16a",
           "inputs": {"note": "Raw captures, downloads and scripts in the repository under scripts/reports/punjab-rain-nov-2026/analysis/"},
           "evidence": E}, open(os.path.join(OUT, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({n: {t.strftime("%Y-%m-%d %H:%M"): v for t, v in sorted(CITY[n].items())} for n in PK + INC}, open(os.path.join(DATA, "series.json"), "w"))
print("evidence entries", len(E))
