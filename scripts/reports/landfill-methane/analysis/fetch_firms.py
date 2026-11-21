#!/usr/bin/env python3
"""Download every VIIRS active-fire detection over Lahore, all year round, from NASA FIRMS's area API.

Usage: python3 fetch_firms.py <H> [delhi]     (H = ~/.cache/hamarihawa/landfill-report)
Writes <H>/raw/firms/<PRODUCT>_<start>_<days>.csv (Lahore) or <H>/raw/firms-delhi/... (with "delhi"), one file per 5-day request; a rerun skips files it has.
The MAP_KEY is read from ~/.config/hamarihawa/firms_key (or FIRMS_MAP_KEY) and is never printed.
"""
import json, os, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

API = "https://firms.modaps.eosdis.nasa.gov"
DELHI = len(sys.argv) > 2 and sys.argv[2] == "delhi"
# Lahore district and its edges, or Delhi with the landfills on its edges (Bandhwari, Ghaziabad)
W, S, E, N = (76.95, 28.35, 77.65, 28.85) if DELHI else (74.15, 31.30, 74.55, 31.75)
SATS = [("VIIRS_SNPP", "2012-01-20"), ("VIIRS_NOAA20", "2018-04-01"), ("VIIRS_NOAA21", "2023-03-01")]
END = date(2026, 11, 17)
UA = {"User-Agent": "research-script/1.0"}


def key():
    k = os.environ.get("FIRMS_MAP_KEY")
    if not k:
        p = os.path.expanduser("~/.config/hamarihawa/firms_key")
        k = open(p).read().strip() if os.path.exists(p) else ""
    if not k:
        sys.exit("No FIRMS MAP_KEY")
    return k


def fetch(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429:
                raise SystemExit(f"FIRMS refused a request (HTTP {e.code}): {e.read().decode('utf-8', 'replace')[:160]}")
            time.sleep(20 * (attempt + 1))
        except Exception:  # noqa: BLE001
            time.sleep(20 * (attempt + 1))
    raise SystemExit("FIRMS kept failing")


def main():
    out = os.path.join(os.path.expanduser(sys.argv[1]), "raw", "firms-delhi" if DELHI else "firms")
    os.makedirs(out, exist_ok=True)
    k = key()
    sp_end = {}
    for line in fetch(f"{API}/api/data_availability/csv/{k}/all").splitlines()[1:]:
        name, _, end = line.split(",")
        if name.endswith("_SP"):
            sp_end[name[:-3]] = date.fromisoformat(end)
    jobs = []
    for sat, first in SATS:
        d = date.fromisoformat(first)
        while d <= END:
            days = min(5, (END - d).days + 1)
            last = d + timedelta(days=days - 1)
            if d <= sp_end[sat] < last:  # don't straddle the SP/NRT boundary
                days = (sp_end[sat] - d).days + 1
                last = sp_end[sat]
            prod = f"{sat}_SP" if last <= sp_end[sat] else f"{sat}_NRT"
            path = os.path.join(out, f"{prod}_{d}_{days}.csv")
            if not os.path.exists(path):
                jobs.append((prod, d, days, path))
            d = last + timedelta(days=1)
    print(len(jobs), "requests to make", flush=True)

    def run(j):
        prod, d, days, path = j
        text = fetch(f"{API}/api/area/csv/{k}/{prod}/{W},{S},{E},{N}/{days}/{d}")
        if not text.startswith("latitude"):
            raise SystemExit(f"Unexpected reply for {prod} {d}: {text[:120]}")
        with open(path + ".tmp", "w") as f:
            f.write(text)
        os.rename(path + ".tmp", path)
        time.sleep(1)

    done = 0
    for i in range(0, len(jobs), 100):
        # the limit is 5,000 transactions in a rolling 10 minutes; wait until there is room for the next 100 requests
        while json.loads(fetch(f"{API}/mapserver/mapkey_status/?MAP_KEY={k}")).get("current_transactions", 0) > 3800:
            time.sleep(30)
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(run, jobs[i:i + 100]))
        done += len(jobs[i:i + 100])
        print(done, "done", flush=True)

if __name__ == "__main__":
    main()
