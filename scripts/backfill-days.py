#!/usr/bin/env python3
"""Fill the daily fire archive for past dates from NASA FIRMS's area API.

The live feed (build-feed.py) only sees the last 7 days. This one-off script fetches older
days with a FIRMS MAP_KEY, names and classifies the fires the same way, and writes the same
day files (KV "day-YYYY-MM-DD") and index entries (KV "days"). Dates already in the index are
left alone, so it never overwrites what the live feed archived.

Usage:
  python3 -I scripts/backfill-days.py --out <dir> --season 2019-2025          # 1 Oct-30 Nov each year
  python3 -I scripts/backfill-days.py --out <dir> --range 2026-10-01 2026-10-13
  ... --upload   # also write to KV (needs CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, KV_NAMESPACE_ID)

The MAP_KEY is read from ~/.config/hamarihawa/firms_key (or FIRMS_MAP_KEY) and is never printed.
FIRMS allows 5,000 transactions per 10 minutes; this paces itself and stops well before that.
Raw CSVs are cached in <out>/raw so a rerun doesn't fetch again.
"""
import argparse, importlib.util, json, os, sys, time, urllib.error, urllib.request
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("build_feed", os.path.join(HERE, "build-feed.py"))
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)

API = "https://firms.modaps.eosdis.nasa.gov"
# Same order as build-feed's SOURCES: (FIRMS name stem, first date it exists).
SATS = [("VIIRS_SNPP", "2012-01-20"), ("VIIRS_NOAA20", "2018-04-01"), ("VIIRS_NOAA21", "2023-03-01"), ("MODIS", "2000-11-01")]
S, N, W, E = bf.BBOX
STOP_AT = 4000  # transactions in the current 10-minute window
CHUNK = 5  # most days the area API returns per request


def key():
    k = os.environ.get("FIRMS_MAP_KEY")
    if not k:
        path = os.path.expanduser("~/.config/hamarihawa/firms_key")
        k = open(path).read().strip() if os.path.exists(path) else ""
    if not k:
        sys.exit("No FIRMS MAP_KEY: put it in ~/.config/hamarihawa/firms_key")
    return k


def fetch(url):
    req = urllib.request.Request(url, headers=bf.UA)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code < 500:  # a rejected request won't succeed on retry; FIRMS says why in the body
                sys.exit(f"FIRMS refused a request (HTTP {e.code}): {e.read().decode('utf-8', 'replace')[:160]}")
            if attempt == 3:
                sys.exit(f"FIRMS kept failing (HTTP {e.code})")
            time.sleep(10 * (attempt + 1))
        except Exception as e:  # noqa: BLE001 - retry anything, then give up with a clean message
            if attempt == 3:
                # The URL holds the key, so only the error type is shown.
                sys.exit(f"FIRMS request failed after retries ({type(e).__name__})")
            time.sleep(10 * (attempt + 1))


class Firms:
    def __init__(self, raw_dir):
        self.k, self.raw, self.calls = key(), raw_dir, 0
        os.makedirs(raw_dir, exist_ok=True)
        # Final ("SP") processing ends a few months back; newer dates come from near real time ("NRT").
        self.sp_end = {}
        for line in fetch(f"{API}/api/data_availability/csv/{self.k}/all").splitlines()[1:]:
            name, _, end = line.split(",")
            if name.endswith("_SP"):
                self.sp_end[name[:-3]] = end

    def budget(self):
        st = json.loads(fetch(f"{API}/mapserver/mapkey_status/?MAP_KEY={self.k}"))
        used = int(st.get("current_transactions") or 0)
        if used > STOP_AT:
            print(f"  {used} transactions used in this window; waiting 10 minutes")
            time.sleep(600)

    def chunk(self, stem, start, days):
        """CSV text for one satellite, `days` (1-5) days from `start`, or None if it wasn't flying."""
        first = dict(SATS)[stem]
        end = start + timedelta(days=days - 1)
        if end.isoformat() < first:
            return None
        product = f"{stem}_SP" if end.isoformat() <= self.sp_end.get(stem, "") else f"{stem}_NRT"
        cache = os.path.join(self.raw, f"{product}_{start}_{days}.csv")
        if os.path.exists(cache):
            return open(cache, encoding="utf-8").read()
        if self.calls and self.calls % 50 == 0:
            self.budget()
        text = fetch(f"{API}/api/area/csv/{self.k}/{product}/{W},{S},{E},{N}/{days}/{start}")
        self.calls += 1
        time.sleep(1)
        if not text.startswith("latitude"):
            sys.exit(f"FIRMS answered {product} {start} with: {text[:120]!r}")
        open(cache, "w", encoding="utf-8").write(text)
        return text

    def csvs(self, d0, d1):
        """One CSV per satellite (build-feed's order) covering UTC dates d0..d1, in the 5-day chunks the API allows."""
        out = []
        for stem, _ in SATS:
            parts, d = [], d0
            while d <= d1:
                n = min(CHUNK, (d1 - d).days + 1)
                text = self.chunk(stem, d, n)
                if text:
                    lines = text.splitlines()
                    parts.append("\n".join(lines if not parts else lines[1:]))
                d += timedelta(days=n)
            out.append("\n".join(parts) if parts else None)
        return out


def periods(a):
    if a.season:
        y0, y1 = (int(x) for x in a.season.split("-"))
        for y in range(y0, y1 + 1):
            yield date(y, 10, 1), date(y, 11, 30)
    if a.range:
        yield date.fromisoformat(a.range[0]), date.fromisoformat(a.range[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--season", help="years, e.g. 2019-2025 (1 Oct-30 Nov each)")
    ap.add_argument("--range", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--summaries", action="store_true", help="only recompute the days and dist indexes")
    a = ap.parse_args()
    if not (a.season or a.range):
        ap.error("give --season and/or --range")
    os.makedirs(os.path.join(a.out, "days"), exist_ok=True)

    index_path = os.path.join(a.out, "days.json")
    index = json.loads(bf.kv("GET", "days") or b"{}") if a.upload else (
        json.load(open(index_path)) if os.path.exists(index_path) else {})
    dist_path = os.path.join(a.out, "dist.json")
    dist = bf.load_dist(date.today().year) if a.upload else (
        json.load(open(dist_path)) if os.path.exists(dist_path) else {})
    firms, added = Firms(os.path.join(a.out, "raw")), []
    for d0, d1 in periods(a):
        # Pakistan-time days start at 19:00 UTC the day before, so fetch one extra UTC day in front.
        csvs = firms.csvs(d0 - timedelta(days=1), d1)
        feed = bf.build(24, csvs)
        source = "NASA FIRMS " + ("final processing (SP)" if d1.isoformat() <= firms.sp_end.get("VIIRS_SNPP", "")
                                  else "near real time (NRT)")
        # --summaries recomputes the index and district entries from cached downloads without rewriting day files.
        days = bf.day_files(feed["_all"], keep=lambda s: d0.isoformat() <= s <= d1.isoformat() and (a.summaries or s not in index),
                            source=source)
        for d, day in days.items():
            index[d] = {**day["summary"], "partial": False}
            dist[d] = day.pop("districts")
            if a.summaries:
                continue
            body = json.dumps(day, separators=(",", ":"), ensure_ascii=False).encode()
            open(os.path.join(a.out, "days", f"{d}.json"), "wb").write(body)
            added.append((d, body))
        tot = sum(day["summary"]["spots"] for day in days.values())
        print(f"{d0}..{d1}: {len(days)} new days, {tot} spots, {firms.calls} API calls so far")

    open(index_path, "w").write(json.dumps(index, separators=(",", ":"), sort_keys=True))
    open(dist_path, "w").write(json.dumps(dist, separators=(",", ":"), sort_keys=True, ensure_ascii=False))
    def put_dist():
        # Only the years this run touched; each year is its own key (see build-feed.py dist_years).
        touched = {d[:4] for d, _ in added} | {str(p0.year) for p0, _ in periods(a)}
        for y, part in bf.dist_years(dist).items():
            if y in touched:
                bf.kv("PUT", f"dist-{y}", json.dumps(part, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode())
    if a.upload and a.summaries:
        bf.kv("PUT", "days", json.dumps(index, separators=(",", ":"), sort_keys=True).encode())
        put_dist()
        print("uploaded the days and dist indexes")
    if a.upload and added:
        acct, ns, tok = os.environ["CLOUDFLARE_ACCOUNT_ID"], os.environ["KV_NAMESPACE_ID"], os.environ["CLOUDFLARE_API_TOKEN"]
        url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/storage/kv/namespaces/{ns}/bulk"
        for i in range(0, len(added), 100):
            batch = [{"key": f"day-{d}", "value": body.decode()} for d, body in added[i:i + 100]]
            bf.get(url, method="PUT", data=json.dumps(batch).encode(),
                   headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        bf.kv("PUT", "days", json.dumps(index, separators=(",", ":"), sort_keys=True).encode())
        put_dist()
        print(f"uploaded {len(added)} days and the indexes to KV")


if __name__ == "__main__":
    main()
