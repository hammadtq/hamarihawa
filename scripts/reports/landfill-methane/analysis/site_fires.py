#!/usr/bin/env python3
"""Extract the VIIRS detections on and within 1 km of Lahore's two landfills from the year-round download.

Usage: python3 site_fires.py <H>   (H = the folder fetch_firms.py wrote to)
Writes inputs/site_detections.csv (one row per detection, with Pakistan time and the distance to the outline; 0 = inside)
and inputs/box_summary.json (totals for the whole Lahore box), and prints a summary. Parses on Python 3.9.
"""
import csv, datetime, glob, json, math, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1])
SITES = {961551528: "lakhodair", 1370790548: "mehmood_booti"}
polys = {}
for e in json.load(open(os.path.join(HERE, "inputs", "osm_landfills.json")))["elements"]:
    if e["id"] in SITES:
        polys[SITES[e["id"]]] = [(p["lon"], p["lat"]) for p in e["geometry"]]


def dist_m(lon, lat, pts):
    kx, ky = 111320 * math.cos(math.radians(lat)), 110540
    inside, best = False, 1e18
    for i in range(len(pts) - 1):
        x1, y1 = (pts[i][0] - lon) * kx, (pts[i][1] - lat) * ky
        x2, y2 = (pts[i + 1][0] - lon) * kx, (pts[i + 1][1] - lat) * ky
        if (y1 > 0) != (y2 > 0) and 0 < x1 + (0 - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, -(x1 * dx + y1 * dy) / (dx * dx + dy * dy))) if dx or dy else 0
        best = min(best, math.hypot(x1 + t * dx, y1 + t * dy))
    return 0.0 if inside else best


rows, seen, allrows = [], set(), 0
box = {"by_satellite": Counter(), "by_type": Counter(), "by_daynight": Counter(), "first": "9999", "last": "0000", "files": 0}
for f in sorted(glob.glob(os.path.join(H, "raw", "firms", "*.csv"))):
    sat = os.path.basename(f).split("_")[1]
    box["files"] += 1
    with open(f) as fh:
        for r in csv.DictReader(fh):
            k = (sat, r["acq_date"], r["acq_time"], r["latitude"], r["longitude"])
            if k in seen:
                continue
            seen.add(k)
            allrows += 1
            box["by_satellite"][sat] += 1; box["by_type"][r.get("type", "") or "not classified (near real time)"] += 1; box["by_daynight"][r["daynight"]] += 1
            box["first"] = min(box["first"], r["acq_date"]); box["last"] = max(box["last"], r["acq_date"])
            la, lo = float(r["latitude"]), float(r["longitude"])
            for name, pts in polys.items():
                d = dist_m(lo, la, pts)
                if d <= 1000:
                    pk = datetime.datetime.strptime(r["acq_date"] + r["acq_time"].zfill(4), "%Y-%m-%d%H%M") + datetime.timedelta(hours=5)
                    rows.append(dict(site=name, dist_m=round(d), sat=sat, date=r["acq_date"], time=r["acq_time"].zfill(4), pkt=pk.strftime("%Y-%m-%d %H:%M"), lat=la, lon=lo,
                                     frp=r["frp"], daynight=r["daynight"], type=r.get("type", ""), conf=r["confidence"],
                                     scan=r["scan"], track=r["track"]))
box.update(total=allrows, bbox_w_s_e_n=[74.15, 31.30, 74.55, 31.75], by_satellite=dict(box["by_satellite"]), by_type=dict(box["by_type"]), by_daynight=dict(box["by_daynight"]))
json.dump(box, open(os.path.join(HERE, "inputs", "box_summary.json"), "w"), indent=1)
with open(os.path.join(HERE, "inputs", "site_detections.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(sorted(rows, key=lambda r: (r["site"], r["date"], r["time"])))
print(allrows, "detections in the Lahore box;", len(rows), "within 1 km of a landfill")
for name in polys:
    rr = [r for r in rows if r["site"] == name]
    ins = [r for r in rr if r["dist_m"] == 0]
    print("\n==", name, "| inside:", len(ins), "| <=200 m:", sum(r["dist_m"] <= 200 for r in rr), "| <=1 km:", len(rr))
    print(" inside by year :", dict(sorted(Counter(r["date"][:4] for r in ins).items())))
    print(" inside days/yr :", dict(sorted(Counter(y for y, _ in {(r["date"][:4], r["date"]) for r in ins}).items())))
    print(" inside by month:", dict(sorted(Counter(r["date"][5:7] for r in ins).items())))
    print(" inside day/night:", dict(Counter(r["daynight"] for r in ins)), "type:", dict(Counter(r["type"] for r in ins)), "sat:", dict(Counter(r["sat"] for r in ins)))
    fr = sorted(float(r["frp"]) for r in ins)
    if fr:
        print(" inside FRP median %.1f max %.1f" % (fr[len(fr) // 2], fr[-1]))
    ring = [r for r in rr if 0 < r["dist_m"] <= 200]
    print(" 1-200 m by year:", dict(sorted(Counter(r["date"][:4] for r in ring).items())))
    byday = defaultdict(list)
    for r in ins:
        byday[r["date"]].append(float(r["frp"]))
    top = sorted(byday.items(), key=lambda kv: -len(kv[1]))[:12]
    print(" busiest days inside:", [(d, len(v), round(sum(v), 1)) for d, v in top])
