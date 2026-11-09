# Sensitivity of the Lahore back-paths: arrival times spanning the overnight rise (00, 03, 06, 09 PKT Monday 9 Nov,
# plus 09 PKT Sunday for comparison), both levels, corridor widths 10/20/40 km. Reuses traj.py's functions.
# Border test: the map's country polygons; times are 15-minute model samples, not measured travel times.
# Writes data/traj-sensitivity.json. Fire times are those kept by HamariHawa's daily archive (newest observation of
# each merged ~400 m spot), so an earlier observation of the same spot may be missing from the 24 h window.
import json, datetime as D, collections, io, contextlib, runpy
with contextlib.redirect_stdout(io.StringIO()):
    T = runpy.run_path("traj.py")
back, along, PKT, C, T0 = T["back"], T["along"], T["PKT"], T["C"], T["T0"]
import os
BORD = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "data", "places", "borders.json")))
def _inring(lat, lon, ring):
    ins = False; n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]; x2, y2 = ring[i - 1]
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1: ins = not ins
    return ins
def in_india(lat, lon):
    return any(_inring(lat, lon, poly[0]) and not any(_inring(lat, lon, h) for h in poly[1:]) for poly in BORD["IN"])
out = {}
arrivals = [D.datetime(2026, 11, 9, h) for h in (0, 3, 6, 9)] + [D.datetime(2026, 11, 8, 9)]
for arr in arrivals:
    for lev in ("10m", "925hPa"):
        p = back(*C["Lahore"], arr - PKT, 24, lev)
        row = {"arrival_PKT": arr.strftime("%Y-%m-%d %H:%M"), "level": lev}
        # where the path was at 18:00 and 00:00 PKT Sunday night, and when it crossed 74.57 E (the border near Lahore is ~74.55-74.6 E)
        for lab, tt in (("at_18_PKT_Sun", D.datetime(2026, 11, 8, 18)), ("at_00_PKT_Mon", D.datetime(2026, 11, 9, 0))):
            th = ((tt - PKT) - T0).total_seconds() / 3600
            q = min(p, key=lambda x: abs(x[2] - th))
            row[lab] = [round(q[0], 3), round(q[1], 3)] if abs(q[2] - th) < 0.2 else None
        # first backward 15-minute sample inside India, using the same country polygons as the map (data/places/borders.json)
        hit = next((x for x in p if in_india(x[0], x[1])), None)
        cross = (T0 + D.timedelta(hours=hit[2]) + PKT).strftime("%a %H:%M") if hit else None
        row["first_backward_sample_in_India_PKT"] = cross
        row["hours_before_arrival"] = round((arr - PKT - T0).total_seconds() / 3600 - hit[2], 2) if hit else None
        for R in (10, 20, 40):
            h = along(p, R); cc = [v[0] for v in h.values()]
            row[f"fires_{R}km"] = {"PK": cc.count("PK"), "IN": cc.count("IN")}
        row["top_districts_20km"] = collections.Counter(v[1] + "(" + v[0] + ")" for v in along(p, 20).values()).most_common(5)
        out[f"{row['arrival_PKT']}|{lev}"] = row
        print(row["arrival_PKT"], lev, row["at_18_PKT_Sun"], row["at_00_PKT_Mon"], "first in India:", cross, row["hours_before_arrival"], {R: row[f"fires_{R}km"] for R in (10, 20, 40)})
json.dump({"method": "see traj.py; GFS via Open-Meteo gfs_seamless, requested on a 0.5 degree grid, timezone GMT, fetched 9 Nov 2026", "rows": out}, open("data/traj-sensitivity.json", "w"), indent=1)
