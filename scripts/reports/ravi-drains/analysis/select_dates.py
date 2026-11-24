# Which Sentinel-2 dates the report uses, and why the others were left out. python3 select_dates.py
# Writes inputs/scenes.json: every date with a Sentinel-2 pass over the river in the two seasons, 2018 to 2026, with
# the scenes found, the decision and the reason. Standard library only; parses on Python 3.9.
#
# The rule (the same one that picked the dates measured on 21 Nov 2026):
#   seasons   1 March to 20 April and 1 to 25 October of each year
#   catalogue Element 84 Earth Search, collection sentinel-2-l2a, box 74.20-74.45 E, 31.45-31.70 N
#   accept    both tiles (43RDQ and 43SDR) have a scene that day with scene cloud cover below 3 percent
#             and less than 5 percent of the tile without data
# The pixels themselves are read from Microsoft Planetary Computer's copy of the same scenes (measure_ravi.py), so the
# manifest also lists the Planetary Computer scene for each tile and its processing baseline.
import collections, datetime, json, os, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); INP = os.path.join(HERE, "inputs")
BBOX = [74.20, 31.45, 74.45, 31.70]; TILES = ("43RDQ", "43SDR"); CLOUD_LT, NODATA_LT = 3.0, 5.0
SEASONS = (("spring", "03-01", "04-20"), ("october", "10-01", "10-25")); YEARS = range(2018, 2027)
def post(url, body):
    for a in range(6):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=90))
        except Exception: time.sleep(6)
    sys.exit("failed " + url)
def pick(items):
    """One scene per tile, the same way every time: the one with the least missing data (a second pass the same day
    can clip the tile), then the newest processing baseline, then the highest scene id."""
    return sorted(items, key=lambda f: (-float(f["properties"].get("s2:nodata_pixel_percentage", 0)), float(f["properties"].get("s2:processing_baseline", "0")), f["id"]))[-1]
def planetary(date):
    F = post("https://planetarycomputer.microsoft.com/api/stac/v1/search", {"collections": ["sentinel-2-l2a"], "bbox": BBOX, "datetime": date + "T00:00:00Z/" + date + "T23:59:59Z", "limit": 50})["features"]
    out = {}
    for t in TILES:
        its = [f for f in F if f["properties"].get("s2:mgrs_tile") == t]
        if its:
            p = pick(its)
            out[t] = {"id": p["id"], "processing_baseline": p["properties"].get("s2:processing_baseline"), "no_data_pct": round(float(p["properties"].get("s2:nodata_pixel_percentage", 0)), 2), "scenes_in_catalogue": len(its), "other_ids": sorted(f["id"] for f in its if f["id"] != p["id"])}
    return out
if __name__ == "__main__":
    dates = []
    for y in YEARS:
        for season, a, b in SEASONS:
            F = post("https://earth-search.aws.element84.com/v1/search", {"collections": ["sentinel-2-l2a"], "bbox": BBOX, "datetime": "%d-%sT00:00:00Z/%d-%sT23:59:59Z" % (y, a, y, b), "limit": 300,
                     "fields": {"include": ["id", "properties.datetime", "properties.eo:cloud_cover", "properties.grid:code", "properties.s2:nodata_pixel_percentage", "properties.s2:processing_baseline"], "exclude": ["links", "geometry", "assets"]}})["features"]
            if len(F) >= 300: sys.exit("more scenes than one page; raise the limit")
            by = collections.defaultdict(lambda: collections.defaultdict(list))
            for f in F:
                p = f["properties"]; t = p["grid:code"][-5:]
                if t in TILES: by[p["datetime"][:10]][t].append({"id": f["id"], "cloud_pct": round(p["eo:cloud_cover"], 2), "no_data_pct": round(p.get("s2:nodata_pixel_percentage", 0), 2), "processing_baseline": p.get("s2:processing_baseline")})
            for d in sorted(by):
                why = []
                for t in TILES:
                    sc = by[d].get(t, [])
                    if not sc: why.append("no scene for tile " + t)
                    elif not [s for s in sc if s["cloud_pct"] < CLOUD_LT]: why.append("tile %s cloud cover %s%%" % (t, min(s["cloud_pct"] for s in sc)))
                    elif not [s for s in sc if s["cloud_pct"] < CLOUD_LT and s["no_data_pct"] < NODATA_LT]: why.append("tile %s has %s%% without data" % (t, min(s["no_data_pct"] for s in sc if s["cloud_pct"] < CLOUD_LT)))
                dates.append({"date": d, "season": season, "selected": not why, "reason": "; ".join(why) if why else "both tiles clear and complete", "earth_search": {t: by[d].get(t, []) for t in TILES}})
            print(y, season, len(by), "dates with a pass,", sum(1 for x in dates if x["selected"] and x["date"][:4] == str(y) and x["season"] == season), "selected", flush=True)
    for x in dates:
        if x["selected"]:
            x["planetary_computer"] = planetary(x["date"])
            prof = os.path.join(INP, "profiles", x["date"] + ".csv")
            x["measured"] = os.path.exists(prof)
            if not x["measured"]: x["not_measured_reason"] = "Planetary Computer has %d of the 2 tiles for this date" % len(x["planetary_computer"])
    sel = [x for x in dates if x["selected"]]
    json.dump({"made": datetime.date.today().isoformat(), "rule": {"seasons": "1 March to 20 April; 1 to 25 October", "years": [YEARS[0], YEARS[-1]], "catalogue": "Element 84 Earth Search, sentinel-2-l2a", "bbox_w_s_e_n": BBOX, "tiles": list(TILES),
               "cloud_cover_below_pct": CLOUD_LT, "no_data_below_pct": NODATA_LT, "scene_choice": "where the catalogue lists more than one scene for a tile and date: the one with the least missing data, then the newest processing baseline, then the highest scene id"},
               "counts": {"dates_with_a_pass": len(dates), "selected": len(sel), "rejected": len(dates) - len(sel), "selected_and_measured": sum(1 for x in sel if x["measured"]), "selected_not_measured": sum(1 for x in sel if not x["measured"])},
               "dates": dates}, open(os.path.join(INP, "scenes.json"), "w"), indent=1)
    print(json.dumps({"dates_with_a_pass": len(dates), "selected": len(sel), "measured": sum(1 for x in sel if x["measured"])}))
    print("selected but not measured:", [(x["date"], x.get("not_measured_reason")) for x in sel if not x["measured"]])
    print("more than one scene for a tile:", [(x["date"], t, v["scenes_in_catalogue"]) for x in sel for t, v in x["planetary_computer"].items() if v["scenes_in_catalogue"] > 1])
