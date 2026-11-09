# Builds the report's data.json and the claim ledger (ledger.md) from the retained inputs, so every number in the
# article is recomputed here rather than typed in. Run after fetch_summaries.py, traj.py, traj_sensitivity.py,
# stations_lahore.py and stations_delhi.py:  python3 build_evidence.py
import json, os, glob, statistics as st, datetime as D
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "lahore-morning-after-diwali", "data.json")
J = lambda f: json.load(open(os.path.join(DATA, f)))
ev = []
def add(id, claim, value, source, where, when, units, method, status, files):
    ev.append({"id": id, "claim": claim, "value": value, "source": source, "geography": where, "interval_tz": when,
               "units": units, "method": method, "status": status, "files": files})

# ---------- fires ----------
S = {os.path.basename(f)[:10]: json.load(open(f))["summary"] for f in glob.glob(os.path.join(DATA, "day-summaries", "20*.json"))}
st_ = lambda d, k, i=0: S[d]["states"].get(k, [0] * 4)[i]
two = lambda d, i=0: st_(d, "PK|Punjab", i) + st_(d, "IN|Punjab", i)
days26 = sorted(d for d in S if "2026-10-01" <= d <= "2026-11-08")
tbl = {d: {"PK_Punjab": st_(d, "PK|Punjab"), "IN_Punjab": st_(d, "IN|Punjab"), "two_Punjabs": two(d), "two_Punjabs_NOAA20": two(d, 2),
           "PK_Punjab_NOAA20": st_(d, "PK|Punjab", 2), "IN_Punjab_NOAA20": st_(d, "IN|Punjab", 2), "all_Pakistan": S[d]["pk"], "all_India": S[d]["in"]}
       for d in ("2026-11-06", "2026-11-07", "2026-11-08")}
FIRMS = "NASA FIRMS VIIRS (NOAA-20, NOAA-21; Suomi NPP until 2 Nov 2026) and MODIS: 2019-2025 from standard/final processing (SP), 2026 from near real time (NRT); merged into spots by HamariHawa's daily archive (scripts/build-feed.py distinct(): VIIRS detections falling in the same ~0.004 deg (~400 m) grid cell on the same PKT day count once; MODIS near a VIIRS spot dropped); /api/day?d=, fetched 9 Nov 2026"
add("fires_table", "Fire spots per PKT day, Pakistani and Indian Punjab, all satellites and NOAA-20 only", tbl, FIRMS,
    "Punjab (Pakistan), Punjab (India) as assigned by geo.py district/state lookup", "Pakistan-time calendar days 6-8 Nov 2026", "spots",
    "summary.states[country|state] = [spots, night, NOAA-20 spots, NOAA-20 night]", "reproduced from HamariHawa archive (consistent with own archive; not independently checked against NASA raw rows)",
    "analysis/data/day-summaries/2026-11-0{6,7,8}.json")
season = {}
for b, i in (("all_satellites", 0), ("NOAA20", 2)):
    rk = sorted(days26, key=lambda d: -two(d, i))
    season[b] = {"max_day": rk[0], "max": two(rk[0], i), "second_day": rk[1], "second": two(rk[1], i)}
m = max(days26, key=lambda d: S[d]["spots"]); season["whole_countries_all_satellites"] = {"max_day": m, "max": S[m]["spots"]}
m = max(days26, key=lambda d: S[d]["sn"][0]); season["whole_countries_NOAA20"] = {"max_day": m, "max": S[m]["sn"][0]}
m = max(days26, key=lambda d: S[d]["snc"][0]); season["northern_plains_box_NOAA20"] = {"max_day": m, "max": S[m]["snc"][0], "box": "geo.COMPARE_BOX 25-35.5N 66-88.5E"}
add("season_max_2026", "8 Nov 2026 was the busiest recorded day of 1 Oct-8 Nov 2026 in the two Punjabs (all satellites 2,859; NOAA-20 931), and also for the whole countries (all satellites 5,419; NOAA-20 1,974) and the northern-plains box (NOAA-20 1,276)", season, FIRMS,
    "Pakistani + Indian Punjab; whole countries (all Pakistan and India in the archive); northern-plains box", "1 Oct-8 Nov 2026, PKT days", "spots", "max over days", "reproduced from archive; season incomplete", "analysis/data/day-summaries/")
DIW = {2019: "2019-10-27", 2020: "2020-11-14", 2021: "2021-11-04", 2022: "2022-10-24", 2023: "2023-11-12", 2024: "2024-10-31", 2025: "2025-10-20", 2026: "2026-11-08"}
past = {}
for y in range(2019, 2027):
    ds = [d for d in S if d.startswith(str(y)) and d[5:7] in ("10", "11") and d <= "2026-11-08"]
    row = {"diwali": DIW[y]}
    for b, i in (("all_satellites", 0), ("NOAA20", 2)):
        m = max(ds, key=lambda d: two(d, i)); row[b] = {"max_day": m, "max": two(m, i), "diwali_count": two(DIW[y], i),
            "diwali_minus_max_days": (D.date.fromisoformat(DIW[y]) - D.date.fromisoformat(m)).days, "ties": sum(two(d, i) == two(m, i) for d in ds) - 1}
    past[y] = row
add("diwali_vs_peak", "Busiest recorded Oct-Nov day in the two Punjabs vs Diwali, 2019-2026 (2026 to 8 Nov). Diwali was the busiest day only in 2026, on both series; four historical peak dates differ between the series. Known NOAA-20 data gaps (e.g. 1 Oct 2023: 0 NOAA-20 spots vs 640 all-satellite) are missing data, not zero fires; they do not change these maxima", past, FIRMS,
    "Pakistani + Indian Punjab", "1 Oct-30 Nov each year (2026: to 8 Nov), PKT days", "spots", "max over days; Diwali = main Lakshmi Puja day", "reproduced from archive", "analysis/data/day-summaries/")
add("noaa20_season_peaks", "NOAA-20 busiest recorded day, two Punjabs: 2019-2022 range 4,268-6,483; 2025 911 (SP); 2026 to 8 Nov 931 (NRT). 931 vs 911 differs by 20 spots (2.2%) across different processing stages: provisional",
    {y: past[y]["NOAA20"]["max"] for y in past}, FIRMS, "Pakistani + Indian Punjab", "Oct-Nov", "NOAA-20 spots", "max over days", "reproduced from archive", "analysis/data/day-summaries/")
d8 = json.load(open(os.path.join(DATA, "day-2026-11-08.json")))
import collections
c = collections.Counter()
for p in d8["spots"]:
    n, s_, cc = d8["dict"]["district"][p[5]]; c[f"{n} ({cc})"] += 1
add("districts_8nov", "Busiest districts on 8 Nov: Jhang (PK) 287, Sangrur 245, Bathinda 213, Firozpur 207, Hafizabad (PK) 193", dict(c.most_common(8)), FIRMS,
    "districts", "8 Nov 2026 PKT", "spots", "count of day-file spots by district", "reproduced from archive", "analysis/data/day-2026-11-08.json")
add("pk_punjab_max", "Pakistani Punjab's busiest day of 2026 so far: 1 Nov, 1,719 spots (all of Pakistan that day: 1,849)",
    {"PK_Punjab": st_("2026-11-01", "PK|Punjab"), "all_Pakistan": S["2026-11-01"]["pk"], "max_day": max(days26, key=lambda d: st_(d, "PK|Punjab"))}, FIRMS,
    "Pakistani Punjab", "1 Oct-8 Nov 2026", "spots", "max over days", "reproduced from archive", "analysis/data/day-summaries/")
add("snpp", "Suomi NPP data delivery ceased 2 Nov 2026 15:40 UTC; HamariHawa's reference satellite is NOAA-20 (legacy keys snpp/sn/snc now hold NOAA-20 counts)", None,
    "NOAA NESDIS notice 2 Nov 2026; scripts/build-feed.py comments at REF_SI", "", "", "", "", "documented", "scripts/build-feed.py")

# ---------- Lahore ----------
L = J("iqair-lahore-hourly.json")["rows"]; Lm = {r["pkt"]: r for r in L}
add("lahore_city_hourly", "IQAir Lahore city figure (median of station hourly concentrations): Sun 00-09 200-223; Sun 14:00 137; Sun 21:00 212; Mon 00:00 233, 04:00 313, 09:00 398.5 (AQI 646), 11:00 280, 12:00 185.5, 15:00 97.4; Sun 09:00 219 (AQI 294)",
    {k: [v["pm25"], v["us_aqi"]] for k, v in Lm.items()}, "IQAir Lahore city page, History > Hourly (https://www.iqair.com/air-quality/pakistan/punjab/lahore)",
    "Lahore city", "hours labelled by start, PKT (UTC+5), Sat 7 Nov 18:00-Mon 9 Nov 16:00; captured ~17:00 PKT 9 Nov", "PM2.5 µg/m³ and US AQI+",
    "displayed values; city = median per IQAir docs", "as displayed; IQAir later revised some hours (9 am shown as AQI 648 at 21:30 PKT)", "analysis/data/iqair-lahore-hourly.json")
aqi = lambda c: round(301 + (c - 225.5) * 199 / 99.9) if c > 225.4 else round(201 + (c - 125.5) * 99 / 99.9)
add("aqi_check", "US AQI from PM2.5 with EPA 2024 breakpoints: 398.5 -> 646; 219 -> 294; AQI 500 = 325.4 µg/m³", {"398.5": aqi(398.5), "219": aqi(219)},
    "US EPA Technical Assistance Document (2024 PM2.5 breakpoints)", "", "", "", "linear interpolation within breakpoints", "computed", "")
LS = J("lahore-stations-stats.json")
add("lahore_stations", "52 Lahore station feeds read; 49 with 9 am values both days; 48 higher Mon; 26 with AQI+ at least twice as high (index ratio, not a concentration ratio); median AQI+ 294 -> 645; 39 above 500; Ravi Road 265 -> 257 (peak 457 in the hour starting 04:00, preceded by 436); above 1,000: Allama Iqbal Town 1,063 (10:00), QIE Indus Plus 1,012 (09:00); hourly station median Sun 19:00-23:00 = 267-292",
    {k: v for k, v in LS.items()}, "IQAir station pages linked from the Lahore city page, History > Hourly US AQI+", "Lahore", "hours by start, PKT; captured 16:40-16:42 UTC 9 Nov",
    "US AQI+", "per-station comparison of the 09:00 hour Sun vs Mon; medians over stations with data", "reproduced from retained re-capture; differs slightly from the first capture (48/48 rose, 29 doubled, median 651, 41 > 500), which was summarised in-browser and not retained",
    "analysis/data/iqair-lahore-stations-recapture.json, analysis/stations_lahore.py")
O = J("iqair-others-hourly.json")["cities"]
add("pk_cities", "Multan >600 from 00:00 to 10:00 Mon, peak 700 at 02:00; Faisalabad >500 08:00-13:00, peak 612 at 11:00; Gujranwala peak 298 (Sat night 288); Islamabad max 181",
    {c: [[list(r.values())[0], r["us_aqi"]] for r in O[c]["rows"]] for c in ("multan", "faisalabad", "gujranwala", "islamabad")},
    "IQAir city pages, History > Hourly", "city figures", "hours by start, PKT; captured ~17:00 PKT 9 Nov", "US AQI+", "displayed values", "as displayed; not read station by station", "analysis/data/iqair-others-hourly.json")
cams = dict(zip(J("dw-lahore.json")["a"]["time"], J("dw-lahore.json")["a"]["pm2_5"]))
ratios = [round(Lm[t]["pm25"] / cams[t.replace(" ", "T")], 2) for t in Lm if "2026-11-07 18:00" <= t <= "2026-11-08 08:00"]
add("cams", "CAMS series retrieved 9 Nov: Lahore 148.1 at 21:00 Sun, 84.8 at 09:00 Mon; city figure / model 1.5-2.0 Sat 18:00-Sun 08:00; 4.7 at 09:00 Mon",
    {"cams_sun_21": cams["2026-11-08T21:00"], "cams_mon_09": cams["2026-11-09T09:00"], "ratio_range_sat_night": [min(ratios), max(ratios)], "ratio_mon_09": round(398.5 / cams["2026-11-09T09:00"], 2)},
    "CAMS global via Open-Meteo air-quality API (hourly=pm2_5,us_aqi&past_days=5&timezone=Asia/Karachi), retrieved 9 Nov 2026", "grid point nearest 31.55N 74.34E (~0.4 deg grid)",
    "PKT; series as served on 9 Nov (rolling, not the run available 8 Nov)", "PM2.5 µg/m³", "model value vs IQAir city median: different spatial samples", "computed; forecast vintage NOT recovered", "analysis/data/dw-lahore.json")
add("epd_warning", "Punjab EPD special report (via Dunya News, 8 Nov 16:50 PKT): pollution could reach dangerous levels Sun night-Mon morning, worst until ~10 am Mon; cites Diwali fireworks, winds from Indian Punjab, crop burning, still night air; comparison report promised 10 Nov", None,
    "https://urdu.dunyanews.tv/index.php/ur/SpecialReport/981841 (read 9 Nov 2026)", "Lahore, Kasur, border areas", "8 Nov 2026", "", "news report", "attributed to news report; original EPD bulletin not found", "")

# ---------- weather / paths ----------
W = J("wx-cities.json")["Lahore"]["hourly"]; t = W["time"]
def night(a, b):
    ii = [i for i, x in enumerate(t) if a <= x <= b]
    return {"wind_kmh": round(st.mean(W["wind_speed_10m"][i] for i in ii), 1), "mixing_m": round(st.mean(W["boundary_layer_height"][i] for i in ii)),
            "rh_max": max(W["relative_humidity_2m"][i] for i in ii), "inversion_hours": sum(W["temperature_925hPa"][i] > W["temperature_2m"][i] for i in ii), "hours": len(ii)}
add("weather", "GFS at Lahore: Sat night mean wind 4.6 km/h, mixing 28 m; Sun night 7.3 km/h, 51 m; RH max 37-38%; inversion most hours both nights; wind turned from NW to E at 18:00 PKT Sat",
    {"sat_night": night("2026-11-07T18:00", "2026-11-08T08:00"), "sun_night": night("2026-11-08T18:00", "2026-11-09T08:00")},
    "GFS via Open-Meteo forecast API (gfs_seamless), retrieved 9 Nov", "Lahore grid point", "PKT, 18:00-08:00", "km/h, m, %", "means of hourly model values", "computed from model output (not measurement)", "analysis/data/wx-cities.json")
TS = J("traj-sensitivity.json")["rows"]
add("paths", "Modelled back-paths to Lahore (arrivals 00/03/06/09 PKT Mon, 10 m and 925 hPa) all approach from the east; with the map's country polygons, the first backward 15-min sample inside India is 3-4.75 h before arrival (9 am 925 hPa: 04:45); midnight-arrival air near Amritsar at 18:00 Sun; 9 am-arrival air 93-115 km E at 18:00, near Tarn Taran at 00:00; spots within 10/20/40 km of the 9 am paths: 22/47/146 (10 m) and 19/42/146 (925 hPa); each 40 km total = 126 IN + 20 PK. Proximity screen on retained detection times, not a count of contributing fires",
    TS, "traj.py, traj_sensitivity.py on GFS winds (data/wind-grid.json: Open-Meteo gfs_seamless, 0.5 deg request grid 28-34N 69-78E, timezone GMT, retrieved 9 Nov)",
    "Punjab", "24 h back from each arrival", "km; spots", "u/v bilinear in space, linear in time, 15-min steps, horizontal only; fire screen samples every second step (30 min), bounding box derived from R then haversine test (draft 7 had a fixed 0.25/0.3 deg box that truncated the 40 km search); archive keeps one time per merged spot",
    "computed; approximate; 925 hPa is several hundred m above ground and may be decoupled from surface at night", "analysis/data/traj-sensitivity.json, analysis/data/traj.json")
T = J("traj.json")
add("paths_other_cities", "Faisalabad 9 am-arrival air over Lahore 12:00-18:00 Sun; Multan near-ground air near Pakpattan Sun evening, across Vehari overnight; Multan 925 hPa path from Ganganagar",
    {k: {"pk": v["pk"], "in": v["in"], "top": v["top"]} for k, v in T.items() if k.split("|")[0] in ("Faisalabad", "Multan")}, "traj.py", "", "", "", "as above", "computed; approximate", "analysis/data/traj.json")

# ---------- Delhi ----------
DS = J("delhi-stations-stats.json")
add("delhi_feeds", "IQAir Delhi: 30 feeds = 17 attributed to CPCB, 10 to DPCC, 3 private. Private (Luca VV Block C 2,089 at 04:30; TL Safdarjung 1,565; Daniel I Poorvi Marg 1,410) all > 1,000 Sun night, midday 209-222; DPCC > 1,000 Sun night: Vivek Vihar 1,591, Anand Vihar 1,380, Sonia Vihar 1,085; DPCC > 1,000 Sat night: 4 feeds; CPCB night max 192-198; 16 of the 17 CPCB-attributed feeds form two groups: 11 feeds showed the same value in 12 of 13 overnight readings (18:30 Sun-06:30 Mon IST) and 5 feeds in 13 of 13 (whole capture: 37/46 and 41/47); the 17th feed has a different series; Anand Vihar DPCC 1,380 vs CPCB-attributed 178 at 23:30 IST Sun",
    DS, "IQAir station pages (https://www.iqair.com/air-quality/india/delhi/delhi/<slug>), 'Station from' attribution and History > Hourly US AQI+", "Delhi",
    "hours by start, IST (UTC+5:30); Sun night = 18:30 Sun-06:30 Mon; captured 16:43-16:44 UTC 9 Nov", "US AQI+", "max/median per feed; groups from a >=90% pairwise-agreement graph, then direct simultaneous agreement within each group over the stated window",
    "reproduced from retained re-capture; NOT checked against CPCB/DPCC records; cause of CPCB-feed similarity unresolved", "analysis/data/iqair-delhi-stations-recapture.json, analysis/data/iqair-delhi-inventory.json, analysis/stations_delhi.py")
add("diwali_date", "Diwali 8 Nov 2026", None, "India Post holiday list (indiapost.gov.in/holidays-list): 'Diwali (Deepavali) 08-November-2026 Sunday'", "", "", "", "", "verified", "")
add("diwali_past", "Past Diwali (Lakshmi Puja) dates 2019-2025", DIW, "Standard Hindu calendar dates; not checked against official notices for each year", "", "", "", "", "not independently re-verified (2024 and 2025 observed by some on 1 Nov / 21 Oct)", "")

data = {"report": json.load(open(os.path.join(HERE, "..", "meta.json")))["title"], "published": "2026-11-09", "version": "2026-11-09f",
        "centre": {"lat": 31.5497, "lon": 74.3436, "name": "central Lahore"},
        "inputs": {"note": "Raw captures and scripts in the repository under scripts/reports/lahore-morning-after-diwali/analysis/; draft 6 frozen in analysis/frozen-draft6/"},
        "evidence": ev}
json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
with open(os.path.join(HERE, "ledger.md"), "w") as f:
    f.write("# Claim ledger\n\nGenerated by build_evidence.py. Values are in data.json under the same id.\n\n| id | claim | source | geography | interval / timezone | units | method | status |\n|---|---|---|---|---|---|---|---|\n")
    for e in ev:
        f.write("| " + " | ".join(str(e[k]).replace("|", "/").replace("\n", " ") for k in ("id", "claim", "source", "geography", "interval_tz", "units", "method", "status")) + " |\n")
print(len(ev), "evidence items"); print(json.dumps(season)); print({y: (past[y]["all_satellites"]["diwali_minus_max_days"], past[y]["NOAA20"]["diwali_minus_max_days"]) for y in past})
