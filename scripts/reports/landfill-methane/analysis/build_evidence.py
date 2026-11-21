# Every number in the landfill report, computed from the files in inputs/. python3 build_evidence.py
# Writes site/public/report/landfill-methane/data.json (the evidence list). Parses on Python 3.9.
import csv, json, math, os, statistics, datetime as D
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "landfill-methane")
os.makedirs(OUT, exist_ok=True)
E = []
def rnd(x): return int(x + 0.5)  # halves round up
def r1(x): return rnd(x * 10) / 10
def add(id, claim, value, source, method, status): E.append({"id": id, "claim": claim, "value": value, "source": source, "method": method, "status": status})
FIRMS = "NASA FIRMS area API, VIIRS 375 m active fire product (S-NPP, NOAA-20, NOAA-21), standard processing where available and near real time after it; downloaded 18 Nov 2026 by fetch_firms.py; extract in inputs/site_detections.csv"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

box = json.load(open(os.path.join(INP, "box_summary.json")))
rows = list(csv.DictReader(open(os.path.join(INP, "site_detections.csv"))))
for r in rows:
    r["dist_m"] = int(r["dist_m"]); r["frp"] = float(r["frp"]); r["t"] = D.datetime.strptime(r["pkt"], "%Y-%m-%d %H:%M")

# ---------------------------------------------------------------- 1. The download
add("download", "VIIRS detections over Lahore, 20 January 2012 to 17 November 2026",
    {"total": box["total"], "first": box["first"], "last": box["last"], "bbox_w_s_e_n": box["bbox_w_s_e_n"], "by_satellite": box["by_satellite"],
     "static_source": box["by_type"]["2"], "classified": box["total"] - box["by_type"]["not classified (near real time)"],
     "static_pct_of_classified": rnd(100 * box["by_type"]["2"] / (box["total"] - box["by_type"]["not classified (near real time)"])),
     "within_1km_of_a_landfill": len(rows), "years": 15},
    FIRMS, "Every detection in the box, duplicates (same satellite, time and position) removed. S-NPP from 2012, NOAA-20 from 2018, NOAA-21 from 2023, so later years have more passes. 'Static source' is FIRMS type 2 ('other static land source'); near-real-time rows are not classified.",
    "computed from the download")

# ---------------------------------------------------------------- 2. The outlines
def area_km2(pts):
    a = sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1] for i in range(len(pts) - 1))
    return abs(a) / 2 * 111.32 * 110.54 * math.cos(math.radians(31.62))
osm = {e["id"]: [(p["lon"], p["lat"]) for p in e["geometry"]] for e in json.load(open(os.path.join(INP, "osm_landfills.json")))["elements"]}
ar = {"lakhodair": area_km2(osm[961551528]), "mehmood_booti": area_km2(osm[1370790548])}
add("outlines", "Area of each site's OpenStreetMap outline",
    {k: {"km2": rnd(v * 100) / 100, "hectares": rnd(v * 100), "acres": rnd(v * 247.105)} for k, v in ar.items()},
    "OpenStreetMap ways 961551528 (Lakho Der Landfill) and 1370790548 (Mehmood Booti Landfill), read 18 Nov 2026; inputs/osm_landfills.json",
    "Planar area of the outline. The outlines are volunteers' tracings of satellite imagery, not surveyed boundaries; Lakhodair's includes ground beside the waste mound.",
    "computed; outline not independently surveyed")

# ---------------------------------------------------------------- 3. Lakhodair
def episodes(rr):  # detections on Pakistan-time dates no more than a day apart are one episode
    out = []
    for r in sorted(rr, key=lambda r: r["t"]):
        if out and (r["t"].date() - out[-1][-1]["t"].date()).days <= 1: out[-1].append(r)
        else: out.append([r])
    return out
def ep_row(ep):
    passes = sorted({(r["sat"], r["pkt"]) for r in ep})
    return {"from": ep[0]["pkt"], "to": ep[-1]["pkt"], "detections": len(ep), "satellite_passes": len(passes),
            "day_detections": sum(r["daynight"] == "D" for r in ep), "night_detections": sum(r["daynight"] == "N" for r in ep),
            "strongest_mw": r1(max(r["frp"] for r in ep)), "month": MONTHS[ep[0]["t"].month - 1], "year": ep[0]["t"].year}
L = [r for r in rows if r["site"] == "lakhodair"]; Lin = [r for r in L if r["dist_m"] == 0]; Lout = [r for r in L if r["dist_m"] > 0]
Lep = [ep_row(e) for e in episodes(Lin)]
bym = Counter(r["t"].month for r in Lin)
assert not [r for r in Lin if r["t"] < D.datetime(2016, 4, 1)]  # nothing inside the outline before the site opened
assert all(r["type"] in ("0", "") for r in Lin)  # none classed as a static source
big = max(Lep, key=lambda e: e["detections"])
assert big["from"].startswith("2019-06-04") and big["to"].startswith("2019-06-05")
assert max(Lep, key=lambda e: e["strongest_mw"])["from"].startswith("2016-06-04") and [e["from"][:7] for e in Lep if e["month"] not in ("Apr", "May", "Jun", "Jul")] == ["2026-02"]  # dates named in the text
assert math.hypot((74.4178 - 74.3847) * 94.8, (31.6282 - 31.6104) * 110.54) > 3.5  # "about four kilometres"
add("lakhodair", "VIIRS detections whose centre falls inside Lakhodair's outline, 2012 to 17 November 2026",
    {"detections": len(Lin), "episodes": len(Lep), "pkt_dates": len({r["t"].date() for r in Lin}),
     "by_month": {MONTHS[m - 1]: bym.get(m, 0) for m in range(1, 13)},
     "april_to_july": sum(bym[m] for m in (4, 5, 6, 7)), "october_november": bym[10] + bym[11],
     "episodes_april_to_july": sum(e["month"] in ("Apr", "May", "Jun", "Jul") for e in Lep),
     "day": sum(r["daynight"] == "D" for r in Lin), "night": sum(r["daynight"] == "N" for r in Lin),
     "median_mw": r1(statistics.median(r["frp"] for r in Lin)), "strongest_mw": r1(max(r["frp"] for r in Lin)),
     "before_april_2016": 0, "episode_list": Lep, "largest": big,
     "episodes_single_detection": sum(e["detections"] == 1 for e in Lep),
     "years_with_an_episode": sorted({e["year"] for e in Lep}), "years_without": [y for y in range(2016, 2027) if y not in {e["year"] for e in Lep}]},
    FIRMS, "A detection counts when the centre of its 375 m pixel is inside the OpenStreetMap outline; the fire can be anywhere in the pixel. Dates and times are Pakistan time (UTC+5). Detections on dates no more than a day apart are one episode. Power is fire radiative power in megawatts. No news report of any of these episodes was found.",
    "computed from the download; not confirmed by any report on the ground")
# ---------------------------------------------------------------- 4. Mehmood Booti
M = [r for r in rows if r["site"] == "mehmood_booti"]; Min = [r for r in M if r["dist_m"] == 0]; Mout = [r for r in M if r["dist_m"] > 0]
near = [r for r in M if r["dist_m"] <= 200]
tyM = [r for r in Mout if r["type"]]
add("mehmood_booti", "VIIRS detections inside and around Mehmood Booti's outline, 2012 to 17 November 2026",
    {"inside": len(Min), "inside_night": sum(r["daynight"] == "N" for r in Min), "inside_strongest_mw": r1(max(r["frp"] for r in Min)),
     "inside_by_year": dict(sorted(Counter(r["t"].year for r in Min).items())),
     "inside_nov_dec_2021": sum(D.datetime(2021, 11, 1) <= r["t"] < D.datetime(2022, 1, 1) for r in Min),
     "inside_while_in_use_2012_to_march_2016": sum(r["t"] < D.datetime(2016, 4, 1) for r in Min),
     "inside_since_sept_2024": sum(r["t"] >= D.datetime(2024, 9, 1) for r in Min),
     "inside_or_within_200m": len(near), "inside_or_within_200m_2012_to_march_2016": sum(r["t"] < D.datetime(2016, 4, 1) for r in near),
     "outside_within_1km": len(Mout), "outside_night_pct": rnd(100 * sum(r["daynight"] == "N" for r in Mout) / len(Mout)),
     "outside_static_pct_of_classified": rnd(100 * sum(r["type"] == "2" for r in tyM) / len(tyM)),
     "inside_list": [{"pkt": r["pkt"], "satellite": r["sat"], "mw": r["frp"]} for r in sorted(Min, key=lambda r: r["t"])]},
    FIRMS + ". Works named from Google Maps labels read on 18 Nov 2026 (Ravi Steel Mill, Fatima Steel, New Malik Foundries).",
    "As for Lakhodair. S-NPP was the only one of the three satellites flying before 2018, so the years the dump was in use had fewer passes.",
    "computed; what produced the heat inside the outline is not known")
# ---------------------------------------------------------------- 5. Methane: Carbon Mapper's plume catalogue
MD = os.path.join(INP, "methane")
CM = "Carbon Mapper public data portal (data.carbonmapper.org), plume catalogue, source list and scene footprints, retrieved 19 Nov 2026 and again, unchanged, on 21 Nov 2026 by fetch_methane.py and fetch_scenes.py; inputs/methane/. Plumes are from NASA's EMIT instrument on the International Space Station and from Planet's Tanager-1 satellite."
def t_h(kg): return rnd(kg / 100) / 10  # kg per hour -> tonnes per hour, one decimal
def t_h2(kg): return rnd(kg / 10) / 100
def in_ring(lon, lat, ring):
    c = False
    for i in range(len(ring) - 1):
        (x1, y1), (x2, y2) = ring[i], ring[i + 1]
        if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c
def covers(s, lon, lat):
    g = s["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    return any(in_ring(lon, lat, p[0]) for p in polys)
def km(lon1, lat1, lon2, lat2): return math.hypot((lon1 - lon2) * 111.32 * math.cos(math.radians(lat1)), (lat1 - lat2) * 110.54)
INST = {"iss": "EMIT (space station)", "tan": "Tanager-1"}
def load(city):
    P = json.load(open(os.path.join(MD, city + "_plumes.json")))["items"]
    S = json.load(open(os.path.join(MD, city + "_scenes.json")))["scenes"]
    F = json.load(open(os.path.join(MD, city + "_sources.json")))["features"]
    for p in P: p["lon"], p["lat"] = p["geometry_json"]["coordinates"]; p["scene"] = p["plume_id"].split("-")[0]
    return P, S, F
def passes(P, S, lon, lat, tz_h, radius_km=1.0):
    """Every scene whose footprint covers the point, with the plumes Carbon Mapper lists within radius_km of it."""
    out = []
    for s in S:
        if not covers(s, lon, lat): continue
        ps = [p for p in P if p["scene"] == s["id"] and km(p["lon"], p["lat"], lon, lat) <= radius_km]
        q = [p for p in ps if p["emission_auto"] is not None]
        t = D.datetime.strptime(s["datetime"][:16], "%Y-%m-%dT%H:%M") + D.timedelta(hours=tz_h)
        out.append({"local_time": t.strftime("%Y-%m-%d %H:%M"), "instrument": INST[s["platform"]], "scene": s["id"], "plumes": len(ps), "plumes_with_a_rate": len(q),
                    "tonnes_per_hour": t_h2(sum(p["emission_auto"] for p in q)) if q else None,
                    "uncertainty_tonnes_per_hour": t_h2(math.sqrt(sum(p["emission_uncertainty_auto"] ** 2 for p in q))) if q else None,
                    "uncertainty_if_errors_fully_shared": t_h2(sum(p["emission_uncertainty_auto"] for p in q)) if q else None,
                    "wind_m_per_s": r1(ps[0]["wind_speed_avg_auto"]) if ps else None,
                    "scene_cloud_pct": s.get("cloud_cover_pct"), "scene_cloud_pct_assessed": s.get("cloud_cover_pct_assessed"),
                    "scene_light_haze_pct": r1(s["light_haze_pct"]) if s.get("light_haze_pct") is not None else None, "sensitivity_mode": s.get("sensitivity_mode")})
    return out
LP, LS, LF = load("lahore")
LK = (74.4188, 31.6264); MB = (74.3854, 31.6102)  # centre of Carbon Mapper's Lakhodair source; centre of Mehmood Booti's outline
assert len(LF) == 1 and all(km(p["lon"], p["lat"], *LK) < 1 for p in LP)  # every plume in the Lahore box is at Lakhodair
lk = passes(LP, LS, *LK, 5); lkp = [x for x in lk if x["plumes"]]; lkq = [x for x in lk if x["tonnes_per_hour"]]
src = LF[0]["properties"]
multi = [x for x in lk if x["plumes_with_a_rate"] > 1]; ex = lk[3]
assert (lk[3]["plumes"], lk[3]["plumes_with_a_rate"]) == (3, 2) and all(x["plumes"] == x["plumes_with_a_rate"] for x in lkq if x is not lk[3])  # "two of three plumes" in the table
assert all(x["plumes"] for x in lk if x["instrument"] == "Tanager-1")  # "a plume on every Tanager-1 pass"
assert src["observation_date_count"] == len(lk) and src["detection_date_count"] == len(lkp)
big1 = max((p for p in LP if p["emission_auto"]), key=lambda p: p["emission_auto"])
def m_to_ring(lon, lat, ring):  # metres from a point to the nearest edge of an outline
    kx, ky = 111320 * math.cos(math.radians(lat)), 110540; best = 1e9
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        ax, ay, bx, by = (x1 - lon) * kx, (y1 - lat) * ky, (x2 - lon) * kx, (y2 - lat) * ky
        dx, dy = bx - ax, by - ay; t = max(0, min(1, -(ax * dx + ay * dy) / ((dx * dx + dy * dy) or 1)))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best
LKO = osm[961551528]; outside = [p for p in LP if not in_ring(p["lon"], p["lat"], LKO)]
far = max(outside, key=lambda p: m_to_ring(p["lon"], p["lat"], LKO))
smog = [x for x in lkp if x["local_time"][5:7] in ("11", "12")]
landgem_2023 = 76558  # tonnes of methane in 2023, LandGEM model figure reported by Dawn, 14 Oct 2024
add("ch4_lakhodair", "Methane plumes imaged over Lakhodair landfill, June 2023 to March 2026",
    {"passes": len(lk), "passes_with_a_plume": len(lkp), "passes_without": len(lk) - len(lkp), "plumes": len(LP), "plumes_with_a_rate": sum(p["emission_auto"] is not None for p in LP),
     "first": lkp[0]["local_time"], "last": lkp[-1]["local_time"], "pass_list": lk,
     "pass_without_plume": [x for x in lk if not x["plumes"]][0],
     "passes_with_more_than_one_rated_plume": len(multi),
     "example_multi_plume_pass": {"local_time": ex["local_time"], "plumes": ex["plumes"], "plumes_with_a_rate": ex["plumes_with_a_rate"], "tonnes_per_hour": ex["tonnes_per_hour"],
                                  "uncertainty_in_quadrature": ex["uncertainty_tonnes_per_hour"], "uncertainty_if_errors_fully_shared": ex["uncertainty_if_errors_fully_shared"]},
     "passes_with_a_rate": len(lkq), "lowest_pass_tonnes_per_hour": min(x["tonnes_per_hour"] for x in lkq), "highest_pass_tonnes_per_hour": max(x["tonnes_per_hour"] for x in lkq),
     "highest_pass": max(lkq, key=lambda x: x["tonnes_per_hour"]), "largest_single_plume_tonnes_per_hour": t_h(big1["emission_auto"]),
     "carbon_mapper_average_tonnes_per_hour": t_h(src["emission_auto"]), "carbon_mapper_average_uncertainty": t_h(src["emission_uncertainty_auto"]),
     "carbon_mapper_persistence_pct": rnd(100 * src["persistence"]),
     "plume_origins_inside_openstreetmap_outline": len(LP) - len(outside), "plume_origins_outside_outline": len(outside),
     "farthest_origin_outside_outline": {"plume": far["plume_id"], "metres_outside": rnd(m_to_ring(far["lon"], far["lat"], LKO) / 10) * 10},
     "carbon_mapper_average_on_passes_with_a_rate_tonnes_per_hour": t_h(src["avg_emission_auto"]),
     "carbon_mapper_detection_passes": src["detection_date_count"], "carbon_mapper_observation_passes": src["observation_date_count"],
     "average_as_tonnes_per_day": rnd(src["emission_auto"] * 24 / 1000), "average_as_tonnes_per_year": rnd(src["emission_auto"] * 8760 / 1e6) * 1000,
     "average_as_tonnes_co2e_per_year_over_100_years": rnd(src["emission_auto"] * 8.76 * 27 / 1e4) * 10000,
     "average_as_typical_us_passenger_cars": rnd(src["emission_auto"] * 8.76 * 27 / 4.6 / 1e4) * 10000, "tonnes_co2_per_typical_us_car_per_year": 4.6,
     "smog_season_passes_with_plume": len(smog), "smog_season_dates": [x["local_time"] for x in smog],
     "tanager_passes": sum(x["instrument"] == "Tanager-1" for x in lk), "emit_passes": sum(x["instrument"] != "Tanager-1" for x in lk),
     "ghgsat_2020_21_tonnes_per_hour": 6.4, "ghgsat_range": [2.3, 16.0], "landgem_2023_tonnes": landgem_2023, "landgem_2023_tonnes_per_hour": r1(landgem_2023 / 8760),
     "project_methane_million_m3_per_year": 18.8, "project_methane_tonnes_per_hour": r1(18.8e6 * 0.668 / 1000 / 8760), "project_methane_tonnes_per_year": rnd(18.8e6 * 0.668 / 1e5) * 100,
     "satellite_minus_project_tonnes_per_hour": r1(t_h(src["emission_auto"]) - r1(18.8e6 * 0.668 / 1000 / 8760)), "ghgsat_ratio_to_carbon_mapper": r1(6.4 / (src["emission_auto"] / 1000)), "lahore_city_tropomi_tonnes_per_hour": 50, "lahore_city_inventory_tonnes_per_hour": 25, "landfill_share_of_city_pct": 13},
    [CM, "Maasakkers et al., Science Advances 8, eabn9683 (2022), Table 1: GHGSat 2020-21 and TROPOMI 2020 figures", "https://www.dawn.com/news/1865081 (Dawn, 14 Oct 2024): LandGEM model figures", "https://www.dawn.com/news/2016325 (Dawn, 18 July 2026): the gas project expects about 18.8 million cubic metres of methane a year, converted here at 0.668 kg per cubic metre (methane at 20 C and sea-level pressure)"],
    "A pass is a scene whose footprint covers the centre of the landfill. A pass's rate is the sum of the plumes Carbon Mapper gave a rate for; plumes without a published rate are counted as plumes but add nothing to the sum, so those sums are lower bounds. The pass uncertainty is ours, not Carbon Mapper's: the plumes' published uncertainties added in quadrature, which assumes their errors are independent. Plumes in one scene share the same wind estimate, so the errors are probably partly shared; 'uncertainty_if_errors_fully_shared' is the plain sum, the other extreme. The project figure of 18.8 million cubic metres is Dawn's report of the methane the planned project is 'expected to generate' each year for upgrading to biomethane; it is a forecast for a project not yet built, not a measurement of what escapes to the air, so it and the satellite rate are different quantities. Carbon Mapper's average is its own figure for the source, weighted by persistence (passes with a plume over unobscured passes). Times are Pakistan time. Each rate is a snapshot at one moment of one morning or afternoon; a daily or yearly figure assumes the rate holds around the clock. The GHGSat, TROPOMI and LandGEM figures are quoted, not recomputed; the three methods differ and are not a trend.",
    "computed from Carbon Mapper's catalogue; published figures quoted")
mb = passes(LP, LS, *MB, 5)
assert [x["scene"] for x in mb] == [x["scene"] for x in lk]
tan_mb = [x for x in mb if x["instrument"] == "Tanager-1"]; emit_mb = [x for x in mb if x["instrument"] != "Tanager-1"]
assert all(x["scene_cloud_pct"] is not None for x in tan_mb) and all(x["scene_cloud_pct"] is None for x in emit_mb)
CLEAR = 10  # per cent of the scene; our own threshold for calling a Tanager-1 scene mostly cloud-free
cloudy = [x for x in tan_mb if x["scene_cloud_pct"] > CLEAR]
other_lahore = [s for s in LS if not covers(s, *LK)]
add("ch4_mehmood_booti", "Methane passes over Mehmood Booti and the rest of Lahore",
    {"passes": len(mb), "plumes": sum(x["plumes"] for x in mb), "passes_before_sept_2024": sum(x["local_time"] < "2024-09" for x in mb), "passes_since_sept_2024": sum(x["local_time"] >= "2024-09" for x in mb),
     "tanager_passes_since_sept_2024": sum(x["local_time"] >= "2024-09" and x["instrument"] == "Tanager-1" for x in mb),
     "scenes_over_lahore_box": len(LS), "scenes_not_covering_lakhodair": len(other_lahore), "plumes_elsewhere_in_lahore_box": 0, "sources_in_lahore_box": len(LF),
     "passes_before_sept_2024_with_a_plume": sum(x["plumes"] for x in mb if x["local_time"] < "2024-09"),
     "tanager_passes": len(tan_mb), "emit_passes": len(emit_mb), "clear_threshold_pct": CLEAR,
     "tanager_passes_scene_cloud_at_most_threshold": len(tan_mb) - len(cloudy), "tanager_highest_cloud_among_those_pct": max(x["scene_cloud_pct"] for x in tan_mb if x["scene_cloud_pct"] <= CLEAR),
     "tanager_passes_cloudier": len(cloudy), "cloudiest_tanager_pass": {"local_time": cloudy[0]["local_time"], "scene_cloud_pct": cloudy[0]["scene_cloud_pct"]},
     "emit_passes_with_a_published_cloud_figure": 0,
     "tanager_passes_second_cloud_field_50_or_more": sum(x["scene_cloud_pct_assessed"] >= 50 for x in tan_mb),
     "tanager_low_cloud_passes_with_second_cloud_field_50_or_more": sum(x["scene_cloud_pct_assessed"] >= 50 for x in tan_mb if x["scene_cloud_pct"] <= CLEAR),
     "haziest_tanager_pass": (lambda h: {"local_time": h["local_time"], "scene_light_haze_pct": rnd(h["scene_light_haze_pct"])})(max((x for x in tan_mb if x["scene_light_haze_pct"] is not None), key=lambda x: x["scene_light_haze_pct"])),
     "tanager_passes_haze_above_5_pct": sum((x["scene_light_haze_pct"] or 0) > 5 for x in tan_mb), "pass_quality": [{k: x[k] for k in ("local_time", "instrument", "scene", "scene_cloud_pct", "scene_cloud_pct_assessed", "scene_light_haze_pct", "sensitivity_mode")} for x in mb],
     "emit_passes_since_sept_2024": sum(x["local_time"] >= "2024-09" and x["instrument"] != "Tanager-1" for x in mb),
     "first_pass": mb[0]["local_time"], "last_pass": mb[-1]["local_time"], "passes_since_flaring_began_june_2026": sum(x["local_time"] >= "2026-06" for x in mb),
     "same_passes_with_a_plume_at_lakhodair": len(lkp), "first_tanager_pass": [x for x in mb if x["instrument"] == "Tanager-1"][0]["local_time"],
     "lakhodair_average_as_multiple_of_tanager_limit": [rnd(src["emission_auto"] / 180), rnd(src["emission_auto"] / 90)],
     "tanager_detection_limit_kg_per_hour": [90, 180], "emit_detection_limit_kg_per_hour": 700, "km_from_lakhodair": r1(km(*MB, *LK))},
    [CM, "https://carbonmapper.org/articles/product-guide (Tanager-1: 90% probability of detection at 90-180 kg/h)", "https://cpaess.ucar.edu/abstract-iwggms-20/detection-limits-and-multi-sensor-persistence-framework-airborne-and-satellite (EMIT: 90% at 700 kg/h under favourable conditions)"],
    "The same scenes that cover Lakhodair cover the centre of Mehmood Booti's outline. Coverage is by footprint only: we did not check whether the pixels over the site were cloud-free or usable, because the scene rasters need a Carbon Mapper account. The cloud, haze and sensitivity-mode fields are Carbon Mapper's scene-wide figures from its public STAC records (fields cm:scene:cloud_cover_pct, cm:scene:cloud_cover_pct_assessed, cm:light_haze_pct, cm:sensitivity_mode), retrieved 21 Nov 2026; EMIT scenes carry no automated cloud figure, and the 'assessed' field's definition was not found. The 10 per cent threshold for a mostly cloud-free scene is ours. The detection limits are for favourable conditions and are not a threshold that applies to every pass. No plume in the catalogue lies within 1 km of it, or anywhere in the Lahore box (W 73.9, S 31.2, E 74.7, N 31.8) other than Lakhodair. Whether cloud or haze obscured Mehmood Booti on any pass is not published for a site with no source, so 'no plume' means none above the instruments' limits was reported, not that none existed. Locations of Lahore's other dumps (Saggian, Sundar, Tibba) were not established, so which scenes covered them is not checked.",
    "computed; absence of a plume is not a measurement of zero")

# ---------------------------------------------------------------- 6. Heat and methane at Lakhodair
HOT = (3, 4, 5, 6)  # March to June: the hot, dry months before the monsoon
def dts(s): return D.datetime.strptime(s[:10], "%Y-%m-%d").date()
heat_days = sorted({r["t"].date() for r in Lin})
gaps = [min(abs((dts(x["local_time"]) - h).days) for h in heat_days) for x in lkp]
lk_hot = Counter(r["t"].month for r in Lin)
add("fires", "Heat detections and methane at Lakhodair",
    {"heat_detections": len(Lin), "heat_days": len(heat_days), "march_to_june": sum(lk_hot[m] for m in HOT), "october_november": lk_hot[10] + lk_hot[11],
     "plume_passes": len(lkp), "plume_passes_within_7_days_of_heat": sum(g <= 7 for g in gaps), "closest_gap_days": min(gaps),
     "plume_passes_by_month": {MONTHS[m - 1]: sum(int(x["local_time"][5:7]) == m for x in lkp) for m in range(1, 13)},
     "mehmood_booti_heat_inside_outline": len(Min), "mehmood_booti_heat_since_sept_2024": sum(r["t"] >= D.datetime(2024, 9, 1) for r in Min),
     "mehmood_booti_strongest_mw": r1(max(r["frp"] for r in Min)), "mehmood_booti_all_at_night": all(r["daynight"] == "N" for r in Min)},
    [FIRMS, CM],
    "Heat detections are those whose 375 m pixel centre is inside the site's OpenStreetMap outline (entries 'lakhodair' and 'mehmood_booti'). Dates are Pakistan time. A plume pass 'within 7 days of heat' has a heat detection on the site within 7 days before or after. Steel furnaces stand beside both sites and produce heat detections of their own; what produced the few faint night-time detections inside Mehmood Booti's outline is not known.",
    "computed; the two records are compared by date and season only and show no cause")
assert all(r["daynight"] == "N" for r in Min) and sum(g <= 7 for g in gaps) == 0

# ---------------------------------------------------------------- 8. Quoted facts (not computed)
add("press_lahore", "What is reported about the two Lahore sites and the work on them",
    {"mehmood_booti": {"acres": 42, "waste_million_tonnes": 13, "dumping_since": 1997, "stopped_taking_most_waste": 2016, "project_cost_rs_billion": 3.37, "work_began": "September 2024",
                       "phase_1_due": "end of July 2025", "phase_2_due": "31 December 2025", "solar_mw": 5, "forest_acres": 11, "gas_wells_reported_by_dawn_march_2025": 52, "gas_wells_in_bidding_documents": 72, "acres_in_bidding_documents": 42, "acres_of_openstreetmap_outline": rnd(ar["mehmood_booti"] * 247.105),
                       "flaring_inaugurated": "June 2026", "carbon_credits_2026_2040": 900000, "v20_book_november_2026": {"rehabilitation_tonnes_co2e_per_year": 100000, "rehabilitation_page": 51, "methane_capture_tonnes_co2e_per_year": 13827, "methane_capture_page": 55, "wastewater_plant_tonnes_co2e_per_year": 491000, "wastewater_plant_page": 50, "entries_at_the_site": 3, "readiness_of_all": "feasibility"}, "validators_visit": "November 2026",
                       "epa_committee_notified": "5 March 2025", "epa_committee_report_due": "27 March 2025", "landgem_peak_year": 2017},
     "lakhodair": {"opened": 2016, "tonnes_per_day_low": 5000, "tonnes_per_day_high": 5500, "waste_million_tonnes_march_2026": 18, "acres": 200,
                   "feasibility_due": "August 2026", "pilot_bio_cng_reported": "March 2026", "pilot_bio_cng_kg_per_day": 85, "project_carbon_credits_per_year": 275000, "v20_book_november_2026": {"readiness": "feasibility", "tonnes_co2e_per_year": 190000, "page": 53}, "consultation": "February 2026", "partnership_years": 20, "un_assistance_announced": "February 2025"},
     "clouds_2021": {"month": "August 2021", "operator_confirmed": "October 2021"}, "other_dumps_named": ["Sundar", "Tibba", "Saggian"]},
    ["https://www.dawn.com/news/1901264 (Dawn, 30 March 2025: Mehmood Booti's size, tonnage, cost, wells, phases)",
     "https://epd.punjab.gov.pk/system/files/Mehmood%20Booti%20Committee%20Solid%20Waste%20Mar25-1.pdf (EPA Punjab notification 223/PSO/DG/EPA/2025, 5 March 2025)",
     "https://www.arabnews.pk/node/2594935 (Arab News, 26 March 2025: most waste went to the site until 2016)",
     "https://www.dawn.com/news/1911938 (Dawn, 19 May 2025: flaring and carbon credits proposal)",
     "https://www.nation.com.pk/14-Jun-2026/pakistan-s-first-carbon-credit-market-project-nears-completion (The Nation, 14 June 2026: flaring system inaugurated, phase two launched)",
     "https://www.azernews.az/region/259733.html (14 June 2026, citing RUDA: first phase completed, gas being captured)",
     "https://dailytimes.com.pk/1577786/ruda-pioneers-methane-capture-validation-at-mehmood-booti/ (Daily Times, 7 Nov 2026: validators' visit)",
     "https://cvfv20.org/wp-content/uploads/2026/11/Carbon-Markets-Investment-Book-First-Version.pdf (Climate Vulnerable Forum and V20, Carbon Markets Investment Book, first version, November 2026, read 21 Nov 2026: projects No. 31, 32, 34 and 36, pages 44 to 55; proponent estimates before deductions; the three Mehmood Booti entries may overlap)",
     "https://unepccc.org/landfill-moves-forward-with-article-6-stakeholder-consultation/ (UNEP Copenhagen Climate Centre, 9 March 2026: Lakhodair consultation, tonnage)",
     "https://www.dawn.com/news/2016325 (Dawn, 18 July 2026: Lakhodair feasibility study)",
     "https://www.brecorder.com/news/amp/40410896 and https://www.thenews.pk/print/1403669-waste-to-value-project (Business Recorder and The News, 10 March 2026: the provincial local government minister said a pilot bio-CNG plant at Lakhodair had started production, about 85 kg of CNG a day from waste; neither report says whether it uses gas drawn from the landfill)",
     "https://ruda.gov.pk/system/files/Rehabilitation of Mehmood Booti Dumpsite Bidding Documents.pdf (Ravi Urban Development Authority, bidding documents, Volume III, Special Provisions: '72 gas collection wells will be installed in the dumpsite'; area 42 acres; undated in the text we read)",
     "https://www.bnnbloomberg.ca/pakistan-landfill-confirms-methane-leaks-blames-higher-dumping-1.1661863 (Bloomberg, 5 Oct 2021)",
     "https://www.thenews.pk/tns/detail/1415845-a-rs-230-million-eid-ul-azha-operation (The News on Sunday, 17 May 2026: other dump sites)"],
    "Press reports of officials' statements and one official notification; not independently checked. No source gives a measured quantity of gas captured or flared at Mehmood Booti, and the EPA committee's report was not found. The 2017 peak is from a LandGEM model study, not a measurement.",
    "as reported; not independently checked")
add("science", "What methane and landfill gas do",
    {"landfill_gas_methane_pct": [45, 60], "landfill_gas_co2_pct": [40, 60], "flammable_range_pct": [5, 15],
     "gwp_20_years": 80, "gwp_100_years": 27, "atmospheric_life_years": 12, "capture_pct": [60, 90], "burning_landfill_gas_emits_some_nox": True,
     "ozone_deaths_avoided_by_45pct_cut": 260000},
    ["https://www.atsdr.cdc.gov/HAC/landfill/html/ch2.html and ch3.html (US ATSDR, Landfill Gas Primer: composition, flammable range)",
     "IPCC AR6 Working Group I, Table 7.15: non-fossil methane, 79.7 times CO2 over 20 years and 27.0 over 100, rounded here",
     "https://wmo.int/media/news/global-methane-assessment-released (UNEP/CCAC Global Methane Assessment, 2021: ozone, lifetime)",
     "https://www.epa.gov/lmop/benefits-landfill-gas-energy-projects (US EPA: capture of roughly 60 to 90 percent)",
     "https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle (US EPA: a typical passenger vehicle emits about 4.6 tonnes of CO2 a year, at 22.2 miles a gallon and 11,500 miles a year; used in ch4_lakhodair for the car comparison: yearly methane x 27 / 4.6, rounded to the nearest 10,000)",
     "https://www.fireengineering.com/fire-safety/landfill-fires-their-magnitude-characteristics-and-mitigation/ (summary of US FEMA report FA-225, 2002: methane and landfill fires)",
     "https://www.who.int/news-room/fact-sheets/detail/dioxins-and-their-effects-on-human-health (WHO: uncontrolled waste burning and dioxins)"],
    "Quoted from the sources; general figures, not measurements at these sites.", "quoted from published sources")

json.dump({"report": "Satellites repeatedly detect methane over Lahore's Lakhodair landfill, but none reported at nearby Mehmood Booti", "published": "2026-11-21", "version": "1.1",
           "inputs": {"note": "Inputs and scripts in the repository under scripts/reports/landfill-methane/analysis/"},
           "evidence": E}, open(os.path.join(OUT, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("evidence entries", len(E))
for e in E[4:]: print(json.dumps({k: v for k, v in e["value"].items() if k not in ("inside_list", "pass_list")}, indent=None)[:1800], "\n")
