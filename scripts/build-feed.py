#!/usr/bin/env python3
"""Build the fire feed JSON the site serves, and optionally upload it to Cloudflare KV.

Runs every 15 minutes from .github/workflows/feed.yml. Satellites only pass a few
times a day, so the slow part (naming every fire after its village) happens here
instead of inside a web request.

Usage:
  python3 -I scripts/build-feed.py --out <dir>             # write fires-24.json etc. locally
  python3 -I scripts/build-feed.py --out <dir> --upload    # also PUT them to KV

Upload needs CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID and KV_NAMESPACE_ID in the environment.
Cloudflare's free plan allows 1,000 KV writes a day, so every write goes through Publisher: values that
haven't changed are skipped, the 24 h feed is written at most every 20 minutes and everything else at most
hourly, and the day's total stops at Publisher.LIMIT. The run's bookkeeping lives in the KV key "state".
"""
import argparse, csv, hashlib, io, json, math, os, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

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
         # Industrial radii come from bounding boxes, which overstate long thin estates, so stay well inside.
         "industrial": lambda it: it[3] * 0.6 + 150}


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
            # The active_fire CSVs say "A"/"T"; the area API (backfill-days.py) spells the names out.
            label = "Aqua" if r.get("satellite") in ("A", "Aqua") else "Terra"
        else:
            if conf in ("low", "l"): continue
            conf = "high" if conf in ("high", "h") else "nominal"
            label = sat
        hhmm = r["acq_time"].zfill(4)
        t = datetime.strptime(f"{r['acq_date']} {hhmm}", "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
        out.append({"lat": lat, "lon": lon, "sat": label, "si": sat_i, "t": int(t.timestamp() * 1000),
                    "frp": float(r.get("frp") or 0), "conf": conf, "night": r.get("daynight") == "N"})
    return out


def distinct(points):
    """Distinct fire spots: merge the same ~400 m spot seen by several VIIRS satellites,
    and drop MODIS (1 km) detections that a VIIRS satellite already caught nearby.
    Keyed dict of the first (newest) point at each spot."""
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
    return spots


def drop_bursts(points):
    """Drop daytime bursts that one VIIRS satellite reports and the others don't confirm.
    Over the Thar desert (Bikaner, Jaisalmer, Barmer) a single afternoon pass sometimes flags hundreds of
    "fires" across hot, bright sand, while the other VIIRS satellites, crossing within the hour, see next to
    nothing there. A pass is a burst when it has 50+ daytime detections in one 1-degree cell and every other
    VIIRS satellite that flew over that longitude in daylight within 2.5 hours saw under a tenth as many in
    the cell. A satellite that hadn't flown there yet (or whose data isn't out) isn't counted, so with no
    witness nothing is dropped. Only the desert (25-29N, 70-74E) is checked: on farmland a satellite can
    miss a real pass behind cloud or at the edge of its swath, and in 2019-2025 the test wrongly caught a
    few Punjab and Haryana passes that way, while every desert burst it caught was in this box."""
    win, cell = 150 * 60 * 1000, lambda p: (int(p["lat"] // 1), int(p["lon"] // 1))
    in_thar = lambda c: 25 <= c[0] <= 28 and 70 <= c[1] <= 73
    day = [p for p in points if p["si"] < 3 and not p["night"]]
    passes = {}
    for p in day:
        passes.setdefault((p["si"], p["t"] // 1800000, cell(p)), []).append(p["t"])
    def unconfirmed(si, b, c):
        ts = passes[(si, b, c)]
        t0 = sorted(ts)[len(ts) // 2]
        others = []
        for o in (0, 1, 2):
            if o == si or not any(q["si"] == o and abs(q["t"] - t0) <= win and abs(q["lon"] - c[1] - 0.5) <= 3 for q in day):
                continue
            others.append(sum(1 for q in day if q["si"] == o and abs(q["t"] - t0) <= win and cell(q) == c))
        return bool(others) and max(others) < 0.1 * len(ts)

    bad = {k for k, ts in passes.items() if len(ts) >= 50 and in_thar(k[2]) and unconfirmed(*k)}
    # A burst spills into the next cells; drop the same pass there too when those cells are just as unconfirmed.
    for si, b, c in list(bad):
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                k = (si, b, (c[0] + i, c[1] + j))
                if k not in bad and in_thar(k[2]) and len(passes.get(k, ())) >= 10 and unconfirmed(*k):
                    bad.add(k)
    if not bad:
        return points
    keep = [p for p in points if p["si"] >= 3 or p["night"] or (p["si"], p["t"] // 1800000, cell(p)) not in bad]
    print(f"  dropped {len(points) - len(keep)} detections in {len(bad)} unconfirmed daytime bursts: "
          + ", ".join(f"{SOURCES[si][1]} {c[0]}N {c[1]}E" for si, _, c in sorted(bad)), file=sys.stderr)
    return keep


def build(hours, csvs):
    points = []
    for (si, sat, _), text in zip(SOURCES, csvs):
        if text:
            points += parse(si, sat, text)
    points = drop_bursts(points)

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

    spots = distinct(points)
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

    spot_ids = {id(p) for p in spots.values()}
    spot_idx = [i for i, p in enumerate(points) if id(p) in spot_ids]
    row = lambda p: [p["lat"], p["lon"], p["t"], round(p["frp"], 1),
                     {"Suomi NPP": 0, "NOAA-20": 1, "NOAA-21": 2, "Aqua": 3, "Terra": 4}[p["sat"]],
                     p["place"], p["district"], p["cc"], p["kind"]]
    return {
        "generated": int(time.time() * 1000),
        "hours": hours,
        "latest": points[0]["t"] if points else None,
        "source": "NASA FIRMS: VIIRS 375 m (Suomi NPP, NOAA-20, NOAA-21) and MODIS 1 km (Aqua, Terra), near real time",
        "stats": stats,
        "events": events,
        "points": [row(p) for p in points],
        # One placemark per distinct spot for the KML; removed before the JSON is written.
        "_spots": [row(p) for p in points if id(p) in spot_ids],
        # Every point, for the daily archive and the trend; also removed before writing.
        "_all": points,
        # Positions in "points" of the distinct spots, for the v2 feed's map list.
        "_spot_idx": spot_idx,
    }


SAT_INDEX = {"Suomi NPP": 0, "NOAA-20": 1, "NOAA-21": 2, "Aqua": 3, "Terra": 4}
V2_FIELDS = ["lat", "lon", "t", "frp", "sat", "place", "district", "kind"]
V2_EVENT = ["t", "sat", "district", "night", "n", "high", "frpMax", "frpSum", "lat", "lon", "kinds", "places", "sites",
            "place", "placeKm", "town", "townKm", "flat", "flon", "kind"]


class Dict:
    """Values to small integers, in first-seen order: the v2 formats store each name once."""
    def __init__(self):
        self.items, self.ix = [], {}

    def __call__(self, v):
        if v not in self.ix:
            self.ix[v] = len(self.items)
            self.items.append(v)
        return self.ix[v]


def feed_v2(feed):
    """The v2 fire feed (/api/fires?v=2): names stored once in "dict" and points as rows of numbers.
    A point is [lat, lon, t, frp, sat, place, district, kind]: t in minutes after "t0" (ms), sat as in v1,
    and place, district and kind are positions in dict.place, dict.district ([name, state, cc]) and
    dict.kind. The 7-day feed also lists, in "spots", the points that are distinct fire spots. Events are rows
    too, in the order of "event_fields": t and sat as for points, district/place/town/kind as positions in
    the dictionaries (town -1 when none), kinds as a flat [kind, count, ...] list and places as positions."""
    places, districts, kinds = Dict(), Dict(), Dict()
    pts = feed["_all"]
    t0 = min((p["t"] for p in pts), default=0)
    rows = [[round(p["lat"], 4), round(p["lon"], 4), (p["t"] - t0) // 60000, round(p["frp"], 1), SAT_INDEX[p["sat"]],
             places(p.get("place") or ""), districts((p.get("district") or "", p.get("state") or "", p.get("cc") or "")),
             kinds(p["kind"])] for p in pts]
    ev = [[(e["t"] - t0) // 60000, SAT_INDEX[e["sat"]], districts((e["district"] or "", e["state"] or "", e["cc"] or "")),
           1 if e["night"] else 0, e["n"], e["high"], e["frpMax"], e["frpSum"], e["lat"], e["lon"],
           [x for k, c in e["kinds"].items() for x in (kinds(k), c)], [places(x) for x in e["places"]], e["sites"],
           places(e.get("place") or ""), e.get("placeKm"), places(e["town"]) if e.get("town") else -1, e.get("townKm"),
           round(e["flat"], 4), round(e["flon"], 4), kinds(e["kind"])] for e in feed["events"]]
    out = {k: v for k, v in feed.items() if not k.startswith("_") and k not in ("points", "events")}
    out.update(v=2, t0=t0, fields=V2_FIELDS, event_fields=V2_EVENT, events=ev,
               dict={"place": places.items, "district": [list(d) for d in districts.items], "kind": kinds.items},
               points=rows)
    if feed["hours"] == 168:
        out["spots"] = feed["_spot_idx"]
    return out


KML_MAX = 25_000  # placemarks; about 600 bytes each, which keeps a KML well under KV's 25 MiB


KIND_TEXT = {"crop": "likely crop burning", "urban": "near a town: waste or industry?", "open": "open land",
             "kiln": "at a brick kiln", "landfill": "at a landfill", "industrial": "in an industrial area",
             "hotspot": "at an always-hot spot"}


def kml(feed):
    """The same fires as KML for Google Earth / Google My Maps. Colour by age at build time
    (KML is aabbggrr): red under 3 h, orange under 12 h, brown older; icon size by fire power."""
    from xml.sax.saxutils import escape as x
    now = feed["generated"]
    styles = {"a": "ff202dd6", "b": "ff1a8cf0", "c": "ff2a4a7a"}
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
           f"<name>HamariHawa fires, last {feed['hours']} h</name>",
           "<description>Fires seen by NASA satellites (VIIRS, MODIS) over Pakistan and North India. "
           "Live map: https://hamarihawa.org. Data: NASA FIRMS; place names: GeoNames.</description>"]
    for k, c in styles.items():
        for sz, sc in (("s", 0.5), ("m", 0.75), ("l", 1.0)):
            out.append(f'<Style id="{k}{sz}"><IconStyle><color>{c}</color><scale>{sc}</scale><Icon>'
                       "<href>https://maps.google.com/mapfiles/kml/shapes/shaded_dot.png</href></Icon></IconStyle>"
                       "<LabelStyle><scale>0</scale></LabelStyle></Style>")
    sats = ["Suomi NPP", "NOAA-20", "NOAA-21", "Aqua", "Terra"]
    spots = feed["_spots"]
    if len(spots) > KML_MAX:
        # Too many for one file: keep the strongest fires and say so.
        out.append(f"<Snippet>The {KML_MAX:,} strongest of {len(spots):,} fire spots; the full list is in the JSON feed.</Snippet>")
        spots = sorted(spots, key=lambda r: -r[3])[:KML_MAX]
    for lat, lon, t, frp, si, place, district, cc, kind in spots:
        age = (now - t) / 3.6e6
        st = ("a" if age < 3 else "b" if age < 12 else "c") + ("l" if frp >= 50 else "m" if frp >= 10 else "s")
        when = datetime.fromtimestamp(t / 1000, timezone.utc)
        where = ", ".join(v for v in (place, district, {"PK": "Pakistan", "IN": "India"}.get(cc, cc)) if v)
        desc = (f"Seen {when:%d %b %Y %H:%M} UTC by {sats[si]}<br>Fire power {frp:g} MW<br>{KIND_TEXT.get(kind, kind)}"
                f'<br><a href="https://hamarihawa.org/#at={lat},{lon},12">Open on HamariHawa</a>')
        out.append(f"<Placemark><name>{x('Fire near ' + where)}</name><styleUrl>#{st}</styleUrl>"
                   f"<TimeStamp><when>{when:%Y-%m-%dT%H:%M:%SZ}</when></TimeStamp>"
                   f"<description><![CDATA[{desc}]]></description>"
                   f"<Point><coordinates>{lon},{lat}</coordinates></Point></Placemark>")
    out.append("</Document></kml>")
    return "\n".join(out).encode()


# Days run on Pakistan time (UTC+5) so the ~1:30 am pass belongs to the date it happened on.
LOCAL = timedelta(hours=5)
TREND_DAYS = 14


def local_date(t):
    return (datetime.fromtimestamp(t / 1000, timezone.utc) + LOCAL).strftime("%Y-%m-%d")


def summarise(spots):
    s = {"spots": len(spots), "pk": 0, "in": 0, "night": 0, "crop": 0, "frp": 0}
    for p in spots:
        if p["cc"] == "PK": s["pk"] += 1
        elif p["cc"] == "IN": s["in"] += 1
        if p["night"]: s["night"] += 1
        if p["kind"] == "crop": s["crop"] += 1
        s["frp"] += p["frp"]
    s["frp"] = round(s["frp"])
    return s


def day_files(points, keep=lambda date: True, source="NASA FIRMS near real time"):
    """Split points into Pakistan-time days: {date: day file} for the dates `keep` accepts.
    summary.snpp counts spots Suomi NPP saw on its own, the one satellite flying every year since
    2012, so past seasons compare fairly with today's four-satellite counts; summary.sn splits it as
    [all, PK, IN, night all, night PK, night IN]. The day file's "districts" lists the busiest
    districts as [district, state, cc, spots, lat, lon, Suomi NPP spots] (centre of that day's fires),
    for the trends map and the district pages; "places" lists the villages with the most spots as
    [place, district, cc, spots], for the daily fire pages."""
    by_day = {}
    for p in points:
        by_day.setdefault(local_date(p["t"]), []).append(p)
    out = {}
    for date, pts in sorted(by_day.items()):
        if not keep(date):
            continue
        spots = sorted(distinct(pts).values(), key=lambda p: p["t"])
        sn_spots = distinct([p for p in pts if p["si"] == 0]).values()
        sn, sn_d = [0] * 6, {}
        for p in sn_spots:
            col = 1 if p["cc"] == "PK" else 2 if p["cc"] == "IN" else None
            k = (p["district"] or p["state"] or "?", p["state"] or "", p["cc"] or "")
            sn_d[k] = sn_d.get(k, 0) + 1
            sn[0] += 1
            if col: sn[col] += 1
            if p["night"]:
                sn[3] += 1
                if col: sn[3 + col] += 1
        summary = {**summarise(spots), "snpp": sn[0], "sn": sn}
        by_d, by_p = {}, {}
        for p in spots:
            k = (p["district"] or p["state"] or "?", p["state"] or "", p["cc"] or "")
            a = by_d.setdefault(k, [0, 0.0, 0.0])
            a[0] += 1; a[1] += p["lat"]; a[2] += p["lon"]
            if p.get("place"):
                pk = (p["place"], p["district"] or "", p["cc"] or "")
                by_p[pk] = by_p.get(pk, 0) + 1
        # Per state (country|state): [spots, night spots, Suomi NPP spots, Suomi NPP night spots], every state,
        # so regional series (the two Punjabs, Haryana) never depend on the capped district list.
        states = {}
        for p in spots:
            a = states.setdefault(f"{p['cc'] or ''}|{p['state'] or ''}", [0, 0, 0, 0])
            a[0] += 1; a[1] += 1 if p["night"] else 0
        for p in sn_spots:
            a = states.setdefault(f"{p['cc'] or ''}|{p['state'] or ''}", [0, 0, 0, 0])
            a[2] += 1; a[3] += 1 if p["night"] else 0
        summary["states"] = dict(sorted(states.items()))
        districts = [[d, st, cc, n, round(la / n, 2), round(lo / n, 2), sn_d.get((d, st, cc), 0)]
                     for (d, st, cc), (n, la, lo) in sorted(by_d.items(), key=lambda kv: -kv[1][0]) if n >= 2][:80]
        places = [[pl, d, cc, n] for (pl, d, cc), n in sorted(by_p.items(), key=lambda kv: -kv[1]) if n >= 2][:12]
        dd = Dict()
        rows = [[round(p["lat"], 4), round(p["lon"], 4), p["t"], round(p["frp"], 1), SAT_INDEX[p["sat"]],
                 dd((p["district"] or "", p["state"] or "", p["cc"] or "")), p["kind"], 1 if p["night"] else 0] for p in spots]
        # "dict" must come before "fields": the Worker parses only the part of the file before "fields".
        out[date] = {"date": date, "v": 2, "source": source, "summary": summary, "districts": districts, "places": places,
                     "dict": {"district": [list(d) for d in dd.items]},
                     "fields": ["lat", "lon", "t", "frp", "sat", "district", "kind", "night"], "spots": rows}
    return out


def index_entry(summary, partial):
    """A day's entry in the "days" index: the day summary without the per-state breakdown, which only the
    day file carries (the index is parsed on every page render, so it stays small)."""
    return {**{k: v for k, v in summary.items() if k != "states"}, "partial": partial}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


SEASON = ("10-01", "11-30")  # the October-November rice-stubble season
PAGE_MIN = (500, 20)  # a district gets a page once the archive holds 500+ spots on 20+ days


def district_index(index, dist):
    """Compact per-district numbers for the district pages (/district/<slug>/), which the Worker renders.
    Only complete days count. Each season is [Suomi NPP spots, Suomi NPP to this season's date,
    all-satellite spots, all-satellite to date]; the Suomi NPP figures are None when some day lacks them.
    Totals are a floor: the dist index keeps each day's 80 busiest districts with 2+ spots."""
    done = sorted(d for d in index if not index[d].get("partial") and d in dist)
    if not done:
        return {}
    last = done[-1]
    cur = int(last[:4]) if last[5:] >= SEASON[0] else int(last[:4]) - 1
    to = min(last[5:], SEASON[1]) if cur == int(last[:4]) else SEASON[1]
    recent = done[-30:]
    by = {}
    for date in done:
        y, md = int(date[:4]), date[5:]
        season = y if SEASON[0] <= md <= SEASON[1] else None
        for r in dist[date]:
            name, state, cc, n = r[0], r[1], r[2], r[3]
            if not name or name == "?" or name == state:
                continue
            e = by.setdefault((name, state, cc), {"n": 0, "days": 0, "la": 0.0, "lo": 0.0, "s": {}, "daily": {}, "peak": None})
            e["n"] += n; e["days"] += 1; e["la"] += r[4] * n; e["lo"] += r[5] * n
            e["daily"][date] = n
            if season is not None:
                t = e["s"].setdefault(season, [0, 0, 0, 0])
                sn = r[6] if len(r) > 6 else None
                t[2] += n
                if md <= to: t[3] += n
                if sn is None or t[0] is None:
                    t[0] = t[1] = None
                else:
                    t[0] += sn
                    if md <= to: t[1] += sn
                if season == cur and (e["peak"] is None or n > e["peak"][1]):
                    e["peak"] = [date, n]
    keep = {k: e for k, e in by.items() if e["n"] >= PAGE_MIN[0] and e["days"] >= PAGE_MIN[1]}
    # Short slugs ("okara"), falling back to name + state, then + country, when two districts share one.
    slugs, out = {}, {}
    for k in keep:
        slugs.setdefault(slug(k[0]), []).append(k)
    named = {}
    for s0, ks in slugs.items():
        for k in ks:
            named[k] = s0 if len(ks) == 1 else slug(f"{k[0]} {k[1]}") if len({x[1] for x in ks}) == len(ks) else slug(f"{k[0]} {k[1]} {k[2]}")
    for cc in ("PK", "IN"):
        ranked = sorted((k for k in keep if k[2] == cc), key=lambda k: -(keep[k]["s"].get(cur, [0, 0, 0, 0])[3]))
        for i, k in enumerate(ranked):
            e = keep[k]
            out[named[k]] = {"name": k[0], "state": k[1], "cc": cc,
                             "lat": round(e["la"] / e["n"], 2), "lon": round(e["lo"] / e["n"], 2),
                             "s": {str(y): v for y, v in sorted(e["s"].items())},
                             "r": [e["daily"].get(d, 0) for d in recent], "peak": e["peak"],
                             "rank": i + 1, "of": len(ranked)}
    return {"last": last, "season": cur, "to": to, "recent": recent, "d": out}


def split_dpages(dp):
    """The district pages' data as a small index (every district's name, place, rank and the two seasons
    the listings show) plus one shard per country and state with the full history, so a page render parses
    a few KB instead of every district. Returns (index, {shard key: {slug: detail}})."""
    if not dp.get("d"):
        return dp, {}
    cur = dp["season"]
    idx, shards = {k: v for k, v in dp.items() if k != "d"}, {}
    idx["d"] = {}
    for sl, e in dp["d"].items():
        key = f"dpages-{e['cc']}-{slug(e['state']) or 'other'}"
        idx["d"][sl] = {"name": e["name"], "state": e["state"], "cc": e["cc"], "lat": e["lat"], "lon": e["lon"],
                        "rank": e["rank"], "of": e["of"], "shard": key,
                        "s": {y: v for y, v in e["s"].items() if y in (str(cur), str(cur - 1))}}
        shards.setdefault(key, {})[sl] = {"s": e["s"], "r": e["r"], "peak": e["peak"]}
    return idx, shards


def dist_years(dist):
    """The per-day district lists split by year (KV keys dist-YYYY), so no single value grows past KV's limit."""
    out = {}
    for d, rows in dist.items():
        out.setdefault(d[:4], {})[d] = rows
    return out


FIRST_YEAR = 2019


def load_dist(now_year):
    """Every dist-YYYY key merged; falls back to the old single "dist" key the first time."""
    dist, found = {}, False
    for y in range(FIRST_YEAR, now_year + 1):
        body = kv("GET", f"dist-{y}")
        if body:
            dist.update(json.loads(body)); found = True
    if not found:
        dist = json.loads(kv("GET", "dist") or b"{}")
    return dist


MAX_VALUE = 24 * 2**20  # KV refuses values over 25 MiB


class Publisher:
    """Every KV write goes through here. The free plan allows 1,000 writes a day (reset 00:00 UTC); this job
    stops at LIMIT, leaving the rest for the NO2 job, wind and hand-run fixes. Values whose content hasn't
    changed since they were last written (hash kept in the state key) are skipped."""
    LIMIT = 850

    def __init__(self, upload, state, out):
        self.upload, self.state, self.out = upload, state, out
        utc_day = time.strftime("%Y-%m-%d", time.gmtime())
        if state.get("wday") != utc_day:
            state["wday"], state["writes"] = utc_day, 0
        self.hashes = state.setdefault("hash", {})
        self.written, self.skipped = [], []

    def put(self, key, body, same=None):
        """Write body to KV key; `same` is the part that must change for a write to count (default: body)."""
        h = hashlib.sha1(same if same is not None else body).hexdigest()[:16]
        if self.hashes.get(key) == h:
            return False
        if len(body) > MAX_VALUE:
            print(f"  {key} is {len(body) / 2**20:.1f} MiB, over KV's limit; not written", file=sys.stderr)
            self.skipped.append(key)
            return False
        if self.state["writes"] + 2 > self.LIMIT:  # one is kept for the state key itself
            self.skipped.append(key)
            return False
        if self.upload:
            kv("PUT", key, body)
        self.state["writes"] += 1
        self.hashes[key] = h
        self.written.append(key)
        return True

    def finish(self):
        if self.skipped:
            print(f"  write budget reached ({self.state['writes']} today); left for later: {', '.join(self.skipped)}", file=sys.stderr)
        if self.upload and self.written:
            self.state["writes"] += 1
            kv("PUT", "state", json.dumps(self.state, separators=(",", ":"), sort_keys=True).encode())
        print(f"wrote {len(self.written)} KV keys ({self.state['writes']} today): {', '.join(self.written) or 'none'}")


def feed_body(feed):
    """The feed as uploaded, and the part that decides whether it changed (everything but `generated`)."""
    body = json.dumps(feed, separators=(",", ":"), ensure_ascii=False).encode()
    same = json.dumps({k: v for k, v in feed.items() if k != "generated"}, separators=(",", ":"), ensure_ascii=False).encode()
    return body, same


def archive(points, now):
    """The 7-day points as day files. The oldest date in the window is cut off part way, so it is left out."""
    first = local_date(now - 168 * 3600 * 1000)
    return day_files(points, keep=lambda date: date > first)


def compare(points, hours):
    """Spots in the last `hours` and in the `hours` before that, for the "up on yesterday" tag.
    Both windows are cut from the same 7-day points and end at the newest detection, so they line up
    exactly (NASA's own 24 h file ends whenever NASA last processed, and the pass that straddles its
    start would otherwise be counted in both windows or neither) and the lag before new passes are
    published doesn't shorten the current window alone."""
    if not points:
        return None, None
    hi = max(p["t"] for p in points)
    mid, lo = hi - hours * 3600 * 1000, hi - 2 * hours * 3600 * 1000
    cur = summarise(list(distinct([p for p in points if mid < p["t"] <= hi]).values()))
    prev = summarise(list(distinct([p for p in points if lo < p["t"] <= mid]).values()))
    pick = lambda s: {k: s[k] for k in ("spots", "pk", "in")}
    return pick(cur), pick(prev)


def kv(method, key, body=None):
    acct, ns, tok = os.environ["CLOUDFLARE_ACCOUNT_ID"], os.environ["KV_NAMESPACE_ID"], os.environ["CLOUDFLARE_API_TOKEN"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/storage/kv/namespaces/{ns}/values/{key}"
    data, _ = get(url, method=method, data=body, headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    return data


# Write tiers: the 24 h feed is what most visitors see, so it goes out at most every FAST seconds; the rest
# (48 h and 7 d feeds and KML, the archive and its indexes) at most every SLOW seconds. A minute of slack
# because scheduled runs drift.
FAST, SLOW = 20 * 60 - 60, 60 * 60 - 60


def tiers_due(state, rev, now_s, pk_today, force=False):
    """(fast, slow): whether each tier should publish now. A tier publishes when NASA's files changed since
    it last did and its interval has passed; the hourly tier also runs once after Pakistan midnight with no
    new data, to close yesterday's day file."""
    tiers = state.get("tiers", {})
    def due(name, every, extra=False):
        t = tiers.get(name, {})
        return force or ((t.get("src") != rev or extra) and now_s - t.get("at", 0) >= every)
    return due("fast", FAST), due("slow", SLOW, extra=tiers.get("slow", {}).get("pkday") != pk_today)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--force", action="store_true", help="publish every tier now, even if nothing is due")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    now_s = int(time.time())
    now = now_s * 1000

    # NASA's files change a few times a day; a tier only publishes when they have changed since it last did.
    stamps = {}
    for _, sat, path in SOURCES:
        _, h = get(f"{FIRMS}/{path}_24h.csv", method="HEAD")
        stamps[sat] = h.get("Last-Modified", "")
    rev = hashlib.sha1(json.dumps(stamps, sort_keys=True).encode()).hexdigest()[:16]
    state_path = os.path.join(a.out, "state.json")
    state = json.loads(kv("GET", "state") or b"{}") if a.upload else (
        json.load(open(state_path)) if os.path.exists(state_path) else {})
    tiers = state.setdefault("tiers", {})
    pk_today = local_date(now)

    fast, slow = tiers_due(state, rev, now_s, pk_today, a.force)
    if not (fast or slow):
        print("nothing due: NASA files unchanged, or published less than", FAST // 60, "min ago")
        return
    pub = Publisher(a.upload, state, a.out)

    # The 7-day file goes first: it feeds the daily archive and the trend shown on the shorter windows.
    days_path = os.path.join(a.out, "days.json")
    dist_path = os.path.join(a.out, "dist.json")
    index = json.loads(kv("GET", "days") or b"{}") if a.upload else (
        json.load(open(days_path)) if os.path.exists(days_path) else {})
    dist = load_dist(int(pk_today[:4])) if a.upload else (
        json.load(open(dist_path)) if os.path.exists(dist_path) else {})
    history = None
    for hours in sorted(WINDOWS, reverse=True):
        tier_ok = fast if hours == 24 else slow
        if hours != 168 and not tier_ok:
            continue
        win = WINDOWS[hours]
        csvs = []
        for _, sat, path in SOURCES:
            body, _ = get(f"{FIRMS}/{path}_{win}.csv")
            csvs.append(body.decode("utf-8", "replace") if body else None)
        if not any(csvs):
            sys.exit(f"no FIRMS data for {win}")
        feed = build(hours, csvs)
        if hours == 168:
            history = feed["_all"]
            days = archive(history, now)
            yesterday = local_date(now - 86400 * 1000)
            os.makedirs(os.path.join(a.out, "days"), exist_ok=True)
            for date, day in days.items():
                # Today and yesterday are still filling in; older days are only written once.
                if date not in index or date in (pk_today, yesterday):
                    dbody = json.dumps(day, separators=(",", ":"), ensure_ascii=False).encode()
                    open(os.path.join(a.out, "days", f"{date}.json"), "wb").write(dbody)
                    if slow:
                        pub.put(f"day-{date}", dbody)
                index[date] = index_entry(day["summary"], date == pk_today)
                dist[date] = day["districts"]
            ibody = json.dumps(index, separators=(",", ":"), sort_keys=True).encode()
            open(days_path, "wb").write(ibody)
            open(dist_path, "wb").write(json.dumps(dist, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode())
            dp_index, shards = split_dpages(district_index(index, dist))
            open(os.path.join(a.out, "dpages-index.json"), "wb").write(
                json.dumps(dp_index, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode())
            if slow:
                pub.put("days", ibody)
                touched = {d[:4] for d in days}
                for y, part in dist_years(dist).items():
                    # Years this run changed, plus any year never written as its own key (the split from "dist").
                    if y in touched or a.force or f"dist-{y}" not in pub.hashes:
                        pub.put(f"dist-{y}", json.dumps(part, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode())
                # The district pages change about once a day; only changed shards are written.
                for key, part in sorted(shards.items()):
                    pub.put(key, json.dumps(part, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode())
                pub.put("dpages-index", json.dumps(dp_index, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode())
            print(f"archive: {len(days)} days, {len(index)} in index, {len(shards)} district shards")
        recent = sorted(index)[-TREND_DAYS:]
        cur, prev = compare(history, hours) if hours < 168 else (None, None)
        feed["trend"] = {
            # cur and prev are the same window length cut from the same points; the page compares those two.
            "cur": cur, "prev": prev,
            "fields": ["date", "spots", "pk", "in", "night", "partial"],
            "days": [[d, index[d]["spots"], index[d]["pk"], index[d]["in"], index[d]["night"],
                      1 if index[d].get("partial") else 0] for d in recent],
        }
        kbody = kml(feed)
        v2body, v2same = feed_body(feed_v2(feed))
        del feed["_spots"], feed["_all"], feed["_spot_idx"]
        body, same = feed_body(feed)
        open(os.path.join(a.out, f"fires-{hours}-v2.json"), "wb").write(v2body)
        open(os.path.join(a.out, f"fires-{hours}.json"), "wb").write(body)
        print(f"{win}: {feed['stats']['spots']} spots, {len(feed['events'])} events, {len(body) // 1024} KB (v2 {len(v2body) // 1024} KB)")
        open(os.path.join(a.out, f"fires-{hours}.kml"), "wb").write(kbody)
        # The KML colours fires by age at build time, so it goes out with its feed, never on its own.
        if tier_ok:
            pub.put(f"fires-{hours}-v2", v2body, v2same)
            if pub.put(f"fires-{hours}", body, same):
                pub.put(f"kml-{hours}", kbody)
    for name, ran in (("fast", fast), ("slow", slow)):
        if ran:
            tiers[name] = {"src": rev, "at": now_s, "pkday": pk_today}
    state["stamps"] = stamps
    if not a.upload:
        open(state_path, "w").write(json.dumps(state, separators=(",", ":"), sort_keys=True))
    pub.finish()


if __name__ == "__main__":
    main()
