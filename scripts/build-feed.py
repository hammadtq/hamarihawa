#!/usr/bin/env python3
"""Build the fire feed JSON the site serves, and optionally upload it to Cloudflare KV.

Runs every 15 minutes from .github/workflows/feed.yml. Satellites only pass a few
times a day, so the slow part (naming every fire after its village) happens here
instead of inside a web request.

Usage:
  python3 -I scripts/build-feed.py --out <dir>             # write fires-24.json etc. locally
  python3 -I scripts/build-feed.py --out <dir> --upload    # also PUT them to KV

Upload needs CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID and KV_NAMESPACE_ID in the environment.
Uploads are skipped when NASA's files haven't changed since the last run (KV key "meta").
"""
import argparse, csv, io, json, math, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PLACES = os.path.join(ROOT, "site", "public", "places")
TOWNS = json.load(open(os.path.join(ROOT, "site", "src", "towns.json"), encoding="utf-8"))

# FIRMS_BASE lets CI go through the site's proxy (/api/firms), because GitHub's runners can't reach NASA directly.
FIRMS = os.environ.get("FIRMS_BASE", "https://firms.modaps.eosdis.nasa.gov/data/active_fire").rstrip("/")
SOURCES = [  # (satellite index used by the page, label, path prefix)
    (0, "Suomi NPP", "suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_South_Asia"),
    (1, "NOAA-20", "noaa-20-viirs-c2/csv/J1_VIIRS_C2_South_Asia"),
    (2, "NOAA-21", "noaa-21-viirs-c2/csv/J2_VIIRS_C2_South_Asia"),
    (3, "MODIS", "modis-c6.1/csv/MODIS_C6_1_South_Asia"),
]
WINDOWS = {24: "24h", 48: "48h", 168: "7d"}
BBOX = (25.0, 35.5, 66.0, 88.5)
UA = {"User-Agent": "hamarihawa.org feed builder (+https://hamarihawa.org/about/)"}


def get(url, method="GET", data=None, headers=None):
    req = urllib.request.Request(url, data=data, method=method, headers={**UA, **(headers or {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, {}
            if attempt == 2:
                raise
        except urllib.error.URLError:
            if attempt == 2:
                raise
        time.sleep(3 * (attempt + 1))


def dist2(lat1, lon1, lat2, lon2):
    dx = (lon2 - lon1) * math.cos(math.radians(lat1))
    dy = lat2 - lat1
    return dx * dx + dy * dy


def km(d2):
    return math.sqrt(d2) * 111.2


_cells = {}


def cell(key):
    if key not in _cells:
        path = os.path.join(PLACES, f"{key}.json")
        _cells[key] = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None
    return _cells[key]


def cell_keys(lat, lon):
    la, lo = lat * 4, lon * 4
    a, b = math.floor(la), math.floor(lon * 4)
    m = 0.12  # ~3 km in quarter-degree units
    da = -1 if la - a < m else 1 if la - a > 1 - m else 0
    db = -1 if lo - b < m else 1 if lo - b > 1 - m else 0
    keys = [f"{a}_{b}"]
    if da: keys.append(f"{a + da}_{b}")
    if db: keys.append(f"{a}_{b + db}")
    if da and db: keys.append(f"{a + da}_{b + db}")
    return keys


# Known pollution sources from scripts/build-sources.py. A fire close enough to one is labelled
# by it ("at a brick kiln", "at Ghazipur Landfill") instead of the season/location guess.
SOURCES_DIR = os.path.join(ROOT, "site", "public", "sources")


def _load_sources():
    out = {}
    for kind, fname in [("landfill", "osm-landfill.json"), ("kiln", "kilns.json"),
                        ("hotspot", "hotspots.json"), ("industrial", "osm-industrial.json")]:
        path = os.path.join(SOURCES_DIR, fname)
        if not os.path.exists(path):
            continue
        idx = {}
        for it in json.load(open(path, encoding="utf-8"))["items"]:
            idx.setdefault((round(it[0] * 20), round(it[1] * 20)), []).append(it)
        out[kind] = idx
    return out


KNOWN = _load_sources()
# How far (metres) from a source a VIIRS 375 m pixel centre can be and still be "at" it.
REACH = {"landfill": lambda it: it[3] + 500, "kiln": lambda it: 400, "hotspot": lambda it: 500,
         "industrial": lambda it: it[3] + 300}


def match_source(lat, lon):
    """Return (kind, name) of the source this fire sits on, or (None, None). Priority follows the dict order."""
    for kind, idx in KNOWN.items():
        best, best_d = None, float("inf")
        k = (round(lat * 20), round(lon * 20))
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for it in idx.get((k[0] + i, k[1] + j), ()):
                    d = math.sqrt(dist2(lat, lon, it[0], it[1])) * 111_200
                    if d < REACH[kind](it) and d < best_d:
                        best, best_d = it, d
        if best is not None:
            name = best[2] if kind in ("landfill", "industrial") else best[4] if kind == "hotspot" and len(best) > 4 else ""
            return kind, name if isinstance(name, str) else ""
    return None, None


def classify(p, town, town_d2):
    # Heuristic only: fires close to big towns are often industrial or waste burning;
    # fires in open country during harvest months are most likely crop-residue burning.
    if town and km(town_d2) < 4 + min(8, town[6] / 1e6):
        return "urban"
    m = datetime.fromtimestamp(p["t"] / 1000, timezone.utc).month
    return "crop" if m in (10, 11, 4, 5) else "open"


def parse(sat_i, sat, text):
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        try:
            lat, lon = float(r["latitude"]), float(r["longitude"])
        except (KeyError, ValueError):
            continue
        if not (BBOX[0] <= lat <= BBOX[1] and BBOX[2] <= lon <= BBOX[3]):
            continue
        conf = r.get("confidence", "")
        if sat_i == 3:  # MODIS confidence is 0-100
            try: c = int(conf)
            except ValueError: continue
            if c < 30: continue
            conf = "high" if c >= 80 else "nominal"
            label = "Aqua" if r.get("satellite") == "A" else "Terra"
        else:
            if conf in ("low", "l"): continue
            conf = "high" if conf in ("high", "h") else "nominal"
            label = sat
        hhmm = r["acq_time"].zfill(4)
        t = datetime.strptime(f"{r['acq_date']} {hhmm}", "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
        out.append({"lat": lat, "lon": lon, "sat": label, "si": sat_i, "t": int(t.timestamp() * 1000),
                    "frp": float(r.get("frp") or 0), "conf": conf, "night": r.get("daynight") == "N"})
    return out


def build(hours, csvs):
    points = []
    for (si, sat, _), text in zip(SOURCES, csvs):
        if text:
            points += parse(si, sat, text)

    for p in points:
        best, best_d, best_r = None, float("inf"), None
        for k in cell_keys(p["lat"], p["lon"]):
            c = cell(k)
            if not c: continue
            for q in c["p"]:
                d = dist2(p["lat"], p["lon"], q[0], q[1])
                if d < best_d:
                    best, best_d, best_r = q, d, c["r"]
        town, town_d = None, float("inf")
        for tw in TOWNS:
            d = dist2(p["lat"], p["lon"], tw[0], tw[1])
            if d < town_d:
                town, town_d = tw, d
        if best:
            district, state, cc = best_r[best[3]].split("|")
            p.update(place=best[2], district=district, state=state, cc=cc, placeKm=round(km(best_d), 1))
        else:
            p.update(place="", district=town[3] if town else "", state=town[4] if town else "", cc=town[5] if town else "")
        if town:
            p["town"], p["townKm"] = town[2], round(km(town_d))
        src, site = match_source(p["lat"], p["lon"])
        p["kind"] = src or classify(p, town, town_d)
        p["site"] = site or ""

    points.sort(key=lambda p: -p["t"])

    # One feed event per satellite pass and district, named after its strongest fire.
    events, by_key = [], {}
    for p in points:
        key = (p["sat"], p["t"] // (20 * 60 * 1000), p["district"] or p.get("town"), p["state"])
        e = by_key.get(key)
        if not e:
            e = {"t": p["t"], "sat": p["sat"], "district": p["district"], "state": p["state"], "cc": p["cc"],
                 "night": p["night"], "n": 0, "high": 0, "frpMax": -1, "frpSum": 0, "lat": 0, "lon": 0,
                 "kinds": {}, "places": [], "sites": []}
            by_key[key] = e
            events.append(e)
        e["n"] += 1
        e["frpSum"] += p["frp"]
        e["lat"] += p["lat"]
        e["lon"] += p["lon"]
        e["kinds"][p["kind"]] = e["kinds"].get(p["kind"], 0) + 1
        if p["site"] and p["site"] not in e["sites"] and len(e["sites"]) < 3:
            e["sites"].append(p["site"])
        if p["conf"] == "high": e["high"] += 1
        if p["place"] and p["place"] not in e["places"] and len(e["places"]) < 4:
            e["places"].append(p["place"])
        if p["frp"] > e["frpMax"]:
            e.update(frpMax=p["frp"], place=p["place"] or p.get("town", ""), placeKm=p.get("placeKm"),
                     town=p.get("town"), townKm=p.get("townKm"), flat=p["lat"], flon=p["lon"])
    for e in events:
        e["lat"], e["lon"] = round(e["lat"] / e["n"], 4), round(e["lon"] / e["n"], 4)
        e["frpMax"], e["frpSum"] = round(e["frpMax"], 1), round(e["frpSum"])
        e["kind"] = max(e["kinds"].items(), key=lambda kv: kv[1])[0]
    events.sort(key=lambda e: (-e["t"], -e["n"]))

    # Distinct fire spots: merge the same ~400 m spot seen by several VIIRS satellites,
    # and drop MODIS (1 km) detections that a VIIRS satellite already caught nearby.
    spots, viirs_grid = {}, set()
    for p in points:
        if p["si"] < 3:
            spots.setdefault((round(p["lat"] / 0.004), round(p["lon"] / 0.004)), p)
            viirs_grid.add((round(p["lat"] / 0.01), round(p["lon"] / 0.01)))
    for p in points:
        if p["si"] == 3:
            g = (round(p["lat"] / 0.01), round(p["lon"] / 0.01))
            if not any((g[0] + i, g[1] + j) in viirs_grid for i in (-1, 0, 1) for j in (-1, 0, 1)):
                spots.setdefault(("m",) + g, p)
    stats = {"detections": len(points), "spots": len(spots), "pk": 0, "in": 0, "crop": 0, "kinds": {}}
    by_d = {}
    for p in spots.values():
        if p["cc"] == "PK": stats["pk"] += 1
        elif p["cc"] == "IN": stats["in"] += 1
        if p["kind"] == "crop": stats["crop"] += 1
        stats["kinds"][p["kind"]] = stats["kinds"].get(p["kind"], 0) + 1
        k = (p["district"] or p["state"] or "?", p["state"] or "", p["cc"] or "")
        by_d[k] = by_d.get(k, 0) + 1
    stats["topDistricts"] = [{"district": d, "state": s, "cc": c, "n": n}
                             for (d, s, c), n in sorted(by_d.items(), key=lambda kv: -kv[1])[:10]]

    return {
        "generated": int(time.time() * 1000),
        "hours": hours,
        "latest": points[0]["t"] if points else None,
        "source": "NASA FIRMS: VIIRS 375 m (Suomi NPP, NOAA-20, NOAA-21) and MODIS 1 km (Aqua, Terra), near real time",
        "stats": stats,
        "events": events,
        "points": [[p["lat"], p["lon"], p["t"], round(p["frp"], 1),
                    {"Suomi NPP": 0, "NOAA-20": 1, "NOAA-21": 2, "Aqua": 3, "Terra": 4}[p["sat"]],
                    p["place"], p["district"], p["cc"], p["kind"]] for p in points],
    }


def kv(method, key, body=None):
    acct, ns, tok = os.environ["CLOUDFLARE_ACCOUNT_ID"], os.environ["KV_NAMESPACE_ID"], os.environ["CLOUDFLARE_API_TOKEN"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/storage/kv/namespaces/{ns}/values/{key}"
    data, _ = get(url, method=method, data=body, headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--force", action="store_true", help="upload even if NASA's files are unchanged")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    # NASA's files change a few times a day; skip the run when nothing is new.
    stamps = {}
    for _, sat, path in SOURCES:
        _, h = get(f"{FIRMS}/{path}_24h.csv", method="HEAD")
        stamps[sat] = h.get("Last-Modified", "")
    if a.upload and not a.force:
        prev = kv("GET", "meta")
        if prev and json.loads(prev).get("stamps") == stamps:
            print("NASA files unchanged since last upload; nothing to do")
            return

    for hours, win in WINDOWS.items():
        csvs = []
        for _, sat, path in SOURCES:
            body, _ = get(f"{FIRMS}/{path}_{win}.csv")
            csvs.append(body.decode("utf-8", "replace") if body else None)
        if not any(csvs):
            sys.exit(f"no FIRMS data for {win}")
        feed = build(hours, csvs)
        body = json.dumps(feed, separators=(",", ":"), ensure_ascii=False).encode()
        open(os.path.join(a.out, f"fires-{hours}.json"), "wb").write(body)
        print(f"{win}: {feed['stats']['spots']} spots, {len(feed['events'])} events, {len(body) // 1024} KB")
        if a.upload:
            kv("PUT", f"fires-{hours}", body)
    if a.upload:
        kv("PUT", "meta", json.dumps({"stamps": stamps, "at": int(time.time())}).encode())
        print("uploaded to KV")


if __name__ == "__main__":
    main()
