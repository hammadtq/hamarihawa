#!/usr/bin/env python3
"""Seed the fires-around-each-city store ("city-days") and its summary ("city-fires") from NASA FIRMS.

Counts, for every city with a city page and every Pakistan-time day, the distinct fire spots within 50 and
250 km and Suomi NPP's own spots within 250 km (build-feed.py city_day_counts), over the stubble seasons
(1 Oct-30 Nov 2019-2025) and from 1 October 2026 to yesterday. Downloads go through backfill-days.py's cache,
so seasons already fetched for the daily archive cost no API calls. After this, build-feed.py adds each new
day itself.

Usage: python3 -I scripts/backfill-city-fires.py --out DIR --raw ~/.cache/hamarihawa/raw [--upload]
Writes two KV keys with --upload.
"""
import argparse, importlib.util, json, os, time
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


bf = load("build_feed", "build-feed.py")
bd = load("backfill_days", "backfill-days.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--raw", required=True, help="backfill-days.py's download cache")
    ap.add_argument("--upload", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    firms = bd.Firms(a.raw)
    today = bf.local_date(int(time.time() * 1000))
    periods = [(date(y, 10, 1), date(y, 11, 30)) for y in range(2019, 2026)]
    periods.append((date(2026, 10, 1), date.fromisoformat(today) - timedelta(days=1)))
    store = {}
    for d0, d1 in periods:
        # Pakistan-time days start at 19:00 UTC the day before, so fetch one extra UTC day in front, as backfill-days does.
        feed = bf.build(168, firms.csvs(d0 - timedelta(days=1), d1))  # 168: build() cuts shorter windows to their last hours
        lo, hi = d0.isoformat(), d1.isoformat()
        bf.add_city_days(store, feed["_all"], keep=lambda d: lo <= d <= hi)
        print(f"{lo}..{hi}: {sum(1 for d in store['days'] if lo <= d <= hi)} days, {firms.calls} API calls so far", flush=True)
    index = json.loads(bf.kv("GET", "days") or b"{}") if a.upload else {}
    summary = bf.city_fires(store, index, today, int(time.time() * 1000))
    sbody = json.dumps(store, separators=(",", ":"), sort_keys=True).encode()
    fbody = json.dumps(summary, separators=(",", ":"), ensure_ascii=False).encode()
    open(os.path.join(a.out, "city-days.json"), "wb").write(sbody)
    open(os.path.join(a.out, "city-fires.json"), "wb").write(fbody)
    print(f"city-days {len(sbody) // 1024} KB, city-fires {len(fbody) // 1024} KB, {len(store['days'])} days")
    if a.upload:
        bf.kv("PUT", "city-days", sbody)
        bf.kv("PUT", "city-fires", fbody)
        print("uploaded city-days and city-fires")


if __name__ == "__main__":
    main()
