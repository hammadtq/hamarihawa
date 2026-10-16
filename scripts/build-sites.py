#!/usr/bin/env python3
"""Build the "Pollution sites" directory (site/public/sources/sites.json) from the source layers.

Categories (each item: name, lat, lon, district, state, cc, evidence fields):
  landfills   landfills with methane plumes seen by Carbon Mapper, plus named OSM landfills that
              burn often (always-hot spots on them)
  plants      power and industrial plants with CO2 plumes (Carbon Mapper) or year-round heat (FIRMS)
  hot         always-hot industrial sites not covered above (flares, furnaces, cement, steel)
  kilnbelts   districts with the most brick kilns, with research PM2.5 estimates where available
City traffic hotspots come live from /api/no2.json on the page itself, so they stay current.

Usage: python3 -I scripts/build-sites.py
"""
import json, math, os, time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "site", "public", "sources")
PLACES = os.path.join(ROOT, "site", "public", "places")


def load(name):
    p = os.path.join(SRC, name)
    return json.load(open(p, encoding="utf-8"))["items"] if os.path.exists(p) else []


def km(a1, o1, a2, o2):
    return math.hypot(a1 - a2, (o1 - o2) * math.cos(math.radians(a1))) * 111.2


_cells = {}


def where(lat, lon):
    """Nearest GeoNames place -> (place, district, state, cc), using the site's quarter-degree cells."""
    best, bd, reg = None, 1e9, None
    a, b = math.floor(lat * 4), math.floor(lon * 4)
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            k = f"{a + i}_{b + j}"
            if k not in _cells:
                p = os.path.join(PLACES, f"{k}.json")
                _cells[k] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
            c = _cells[k]
            if not c:
                continue
            for q in c["p"]:
                d = km(lat, lon, q[0], q[1])
                if d < bd:
                    best, bd, reg = q, d, c["r"]
    if not best:
        return "", "", "", ""
    district, state, cc = reg[best[3]].split("|")
    return best[2], district, state, cc


def nearest(items, lat, lon, max_km, name_at=2):
    best, bd = None, max_km
    for it in items:
        if abs(it[0] - lat) > max_km / 100 or abs(it[1] - lon) > max_km / 90:
            continue
        d = km(lat, lon, it[0], it[1])
        nm = it[name_at] if len(it) > name_at else ""
        if d < bd and isinstance(nm, str) and nm:
            best, bd = it, d
    return best


def main():
    cm = load("carbonmapper.json")
    landfills = load("osm-landfill.json")
    plants = load("plants.json")
    industrial = load("osm-industrial.json")
    hot = load("hotspots.json")
    kilns = load("kilns.json")
    out = {"landfills": [], "plants": [], "hot": [], "kilnbelts": []}
    used_hot = set()

    def base(lat, lon, name):
        place, district, state, cc = where(lat, lon)
        return {"name": name or place, "lat": round(lat, 4), "lon": round(lon, 4), "near": place,
                "district": district, "state": state, "cc": cc}

    def hot_near(lat, lon, r_km):
        hits = [(i, h) for i, h in enumerate(hot) if km(lat, lon, h[0], h[1]) < r_km]
        for i, _ in hits:
            used_hot.add(i)
        return max((h[2] for _, h in hits), default=0)

    # Landfills: Carbon Mapper methane sources in the waste sector, named from OSM.
    for it in cm:
        lat, lon, gas, sector, rate, plumes, pers, first, last = it
        if sector != "landfill":
            continue
        lf = nearest(landfills, lat, lon, 3)
        e = base(lat, lon, lf[2] if lf else "")
        e.update(gas=gas, rate=rate, plumes=plumes, persistence=pers, first=first, last=last,
                 heatDays=hot_near(lat, lon, 2), unnamed=not lf)
        out["landfills"].append(e)
    # Named OSM landfills that satellites see burning repeatedly, if not already listed.
    for lf in landfills:
        if not lf[2] or any(km(lf[0], lf[1], x["lat"], x["lon"]) < 3 for x in out["landfills"]):
            continue
        d = hot_near(lf[0], lf[1], 1 + lf[3] / 1000)
        if d >= 5:
            e = base(lf[0], lf[1], lf[2])
            e.update(heatDays=d)
            out["landfills"].append(e)
    out["landfills"].sort(key=lambda x: (-(x.get("rate") or 0), -x.get("heatDays", 0)))

    # Plants: CO2 plumes from power/industry, named from OSM power plants or industrial estates.
    for it in cm:
        lat, lon, gas, sector, rate, plumes, pers, first, last = it
        if sector not in ("power", "industry") or gas != "CO2":
            continue
        pl = nearest(plants, lat, lon, 6, name_at=3)
        name = pl[3] if pl else ""
        if not name:
            est = nearest(industrial, lat, lon, 4)
            name = est[2] if est else ""
        e = base(lat, lon, name)
        e.update(kind=(pl[2] if pl else sector), co2_t_h=round(rate / 1000), plumes=plumes, persistence=pers,
                 first=first, last=last, heatDays=hot_near(lat, lon, 4), unnamed=not name)
        out["plants"].append(e)
    out["plants"].sort(key=lambda x: -x["co2_t_h"])

    # Always-hot sites not already counted (cement, steel, refineries, flares, furnaces).
    for i, h in enumerate(hot):
        if i in used_hot or h[2] < 20 or h[4] == "Brick kiln":
            continue
        e = base(h[0], h[1], h[4] if h[4] and h[4] not in ("Industrial area", "Landfill") else "")
        e.update(days=h[2], months=h[3], label=h[4] or "", unnamed=not (h[4] and h[4] not in ("Industrial area", "Landfill")))
        out["hot"].append(e)
    out["hot"].sort(key=lambda x: -x["days"])

    # Kiln belts: districts with the most kilns.
    belts = {}
    for k in kilns:
        _, district, state, cc = where(k[0], k[1])
        key = (district or state, state, cc)
        b = belts.setdefault(key, {"n": 0, "pm": 0.0, "pmn": 0, "lat": 0.0, "lon": 0.0, "zig": 0})
        b["n"] += 1; b["lat"] += k[0]; b["lon"] += k[1]
        if k[2] == 2:
            b["zig"] += 1
        if k[3] is not None:
            b["pm"] += k[3]; b["pmn"] += 1
    for (district, state, cc), b in sorted(belts.items(), key=lambda kv: -kv[1]["n"])[:30]:
        out["kilnbelts"].append({"name": district, "district": district, "state": state, "cc": cc,
                                 "lat": round(b["lat"] / b["n"], 4), "lon": round(b["lon"] / b["n"], 4),
                                 "kilns": b["n"], "zigzagPct": round(100 * b["zig"] / b["n"]),
                                 "pm25_t_day": round(b["pm"] / 1000, 1) if b["pmn"] >= 0.5 * b["n"] else None})

    for k in ("landfills", "plants", "hot", "kilnbelts"):
        out[k] = [x for x in out[k] if x["cc"] in ("PK", "IN")]  # India and Pakistan only
    out["built"] = time.strftime("%Y-%m-%d")
    path = os.path.join(SRC, "sites.json")
    json.dump(out, open(path, "w"), separators=(",", ":"), ensure_ascii=False)
    print({k: len(v) for k, v in out.items() if isinstance(v, list)}, "->", path)
    for k in ("landfills", "plants", "hot", "kilnbelts"):
        for x in out[k][:4]:
            print(" ", k, {kk: x[kk] for kk in x if kk in ("name", "district", "state", "cc", "rate", "co2_t_h", "days", "kilns", "heatDays")})


if __name__ == "__main__":
    main()
