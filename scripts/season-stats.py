#!/usr/bin/env python3
"""Season statistics for the "Two Punjabs" report, from the FIRMS downloads backfill-days.py cached.

Counts only Suomi NPP (the one VIIRS satellite flying in every season since 2012), counted like the
daily archive: distinct fire spots per Pakistan-time day, summed over 1 October-30 November.
For Pakistani Punjab, Indian Punjab and Haryana it records the season total, night-pass spots, fire
power, the daily series and the count per district. India's official season totals are stored next to
ours so the report can check one against the other.

Usage: python3 -I scripts/season-stats.py <backfill out dir>
Writes site/public/report/two-punjabs/seasons.json.
"""
import importlib.util, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("build_feed", os.path.join(HERE, "build-feed.py"))
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)

OUT = os.path.join(HERE, "..", "site", "public", "report", "two-punjabs", "seasons.json")
STATES = [("PK", "Punjab"), ("IN", "Punjab"), ("IN", "Haryana")]
YEARS = range(2019, 2026)
# India's official paddy-season fire counts for Indian Punjab (15 Sep-30 Nov, CAQM / Punjab Remote
# Sensing Centre, as reported in the press). 2020 is also reported as 83,002 by the environment ministry.
OFFICIAL_IN_PUNJAB = {2019: 52991, 2020: 76590, 2021: 71304, 2022: 49922, 2023: 36663, 2024: 10909, 2025: 5114}


def season_csv(raw, year):
    """The cached Suomi NPP CSVs for one season, glued into one (header once)."""
    parts = sorted(f for f in os.listdir(raw) if f.startswith("VIIRS_SNPP_") and f.split("_")[-2][:4] == str(year))
    if not parts:
        sys.exit(f"no cached Suomi NPP files for {year}; run backfill-days.py first")
    lines = []
    for f in parts:
        text = open(os.path.join(raw, f), encoding="utf-8").read().splitlines()
        lines += text if not lines else text[1:]
    return "\n".join(lines)


def main():
    raw = os.path.join(sys.argv[1], "raw")
    seasons = {}
    for y in YEARS:
        feed = bf.build(24, [season_csv(raw, y), None, None, None])
        by_day = defaultdict(list)
        for p in feed["_all"]:
            d = bf.local_date(p["t"])
            if f"{y}-10-01" <= d <= f"{y}-11-30":
                by_day[d].append(p)
        stats = {f"{cc}|{st}": {"total": 0, "night": 0, "frp": 0.0, "daily": {}, "districts": defaultdict(int)} for cc, st in STATES}
        for d, pts in sorted(by_day.items()):
            for p in bf.distinct(pts).values():
                s = stats.get(f"{p['cc']}|{p['state']}")
                if not s:
                    continue
                s["total"] += 1
                s["night"] += 1 if p["night"] else 0
                s["frp"] += p["frp"]
                s["daily"][d] = s["daily"].get(d, 0) + 1
                s["districts"][p["district"] or p["state"]] += 1
        for s in stats.values():
            s["frp"] = round(s["frp"])
            s["districts"] = dict(sorted(s["districts"].items(), key=lambda kv: -kv[1]))
        seasons[str(y)] = stats
        print(y, {k: (v["total"], v["night"]) for k, v in stats.items()})
    out = {
        "title": "Two Punjabs: crop-fire seasons 2019-2025",
        "source": "NASA FIRMS, VIIRS Suomi NPP 375 m, final processing (SP). Distinct fire spots per Pakistan-time day, 1 Oct-30 Nov.",
        "licence": "CC BY 4.0, HamariHawa (hamarihawa.org)",
        "official_in_punjab": {"window": "15 Sep-30 Nov", "source": "CAQM / Punjab Remote Sensing Centre via press reports",
                               "counts": {str(k): v for k, v in OFFICIAL_IN_PUNJAB.items()}},
        "seasons": seasons,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("wrote", os.path.relpath(OUT), os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
