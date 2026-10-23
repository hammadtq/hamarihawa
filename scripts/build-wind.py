#!/usr/bin/env python3
"""Wind right now on a regular 2-degree grid over the whole region, for the map's wind streaks (/api/wind).

Runs hourly from .github/workflows/wind.yml and stores the grid in the KV key "wind": one write an hour, so
the Worker never calls Open-Meteo itself. A 2-degree grid is 360 points; Open-Meteo's free tier counts each
point as a call and allows 10,000 a day, so hourly is about 8,600.

Usage:
  python3 -I scripts/build-wind.py --out <file>             # write the grid locally
  python3 -I scripts/build-wind.py --out <file> --upload    # also PUT it to KV (same environment as build-feed.py)
"""
import argparse, json, os, time, urllib.request

import importlib.util as _ilu
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = _ilu.spec_from_file_location("geo", os.path.join(HERE, "geo.py"))
geo = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(geo)

STEP = 2.0
R = geo.REGION
NX = int((R["e"] - R["w"]) // STEP) + 2  # one column past the east edge, so the whole region interpolates
NY = int((R["n"] - R["s"]) // STEP) + 2
LAT0, LON0 = R["s"], R["w"]


def fetch(lats, lons):
    url = ("https://api.open-meteo.com/v1/forecast?latitude=" + ",".join(f"{x:g}" for x in lats) +
           "&longitude=" + ",".join(f"{x:g}" for x in lons) +
           "&current=wind_speed_10m,wind_direction_10m&wind_speed_unit=kmh&timezone=GMT")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "hamarihawa.org wind"}), timeout=60) as r:
                rows = json.load(r)
                return rows if isinstance(rows, list) else [rows]
        except Exception as e:  # noqa: BLE001 - retry anything, then give up
            print("open-meteo:", e)
            time.sleep(10 * (attempt + 1))
    raise SystemExit("Open-Meteo unavailable")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--upload", action="store_true")
    a = ap.parse_args()
    # Row-major from the south-west corner, as wind.js reads it.
    lats = [LAT0 + j * STEP for j in range(NY) for i in range(NX)]
    lons = [LON0 + i * STEP for j in range(NY) for i in range(NX)]
    rows = fetch(lats, lons)
    if len(rows) != len(lats):
        raise SystemExit(f"expected {len(lats)} points, got {len(rows)}")
    body = {"time": rows[0]["current"]["time"], "lat0": LAT0, "lon0": LON0, "step": STEP, "nx": NX, "ny": NY,
            "speed": [x["current"]["wind_speed_10m"] for x in rows], "dir": [x["current"]["wind_direction_10m"] for x in rows],
            "source": "Open-Meteo forecast (best-match weather models), 10 m wind, km/h; dir is where the wind comes from"}
    data = json.dumps(body, separators=(",", ":")).encode()
    open(a.out, "wb").write(data)
    print(f"{NX}x{NY} grid at {body['time']}, {len(data) // 1024} KB")
    if a.upload:
        acct, ns, tok = os.environ["CLOUDFLARE_ACCOUNT_ID"], os.environ["KV_NAMESPACE_ID"], os.environ["CLOUDFLARE_API_TOKEN"]
        req = urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{acct}/storage/kv/namespaces/{ns}/values/wind",
                                     data=data, method="PUT", headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=60).read()
        print("uploaded wind")


if __name__ == "__main__":
    main()
