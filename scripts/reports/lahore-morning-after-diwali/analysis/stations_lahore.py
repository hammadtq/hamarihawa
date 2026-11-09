# Lahore station statistics from the IQAir re-capture (data/iqair-lahore-stations-recapture.json).
# Value i is the hour starting 2026-11-07 22:00 PKT + i h. Writes data/lahore-stations-stats.json.
import json, statistics as st, datetime as D
R = json.load(open("data/iqair-lahore-stations-recapture.json"))
t0 = D.datetime(2026, 11, 7, 22)
def idx(s): return int((D.datetime.fromisoformat(s) - t0).total_seconds() // 3600)
rows = {r[0]: [int(x) if x else None for x in r[5].split(",")] for r in R["rows"]}
assert all(len(v) == 47 for v in rows.values())
S9, M9 = idx("2026-11-08 09:00"), idx("2026-11-09 09:00")
ev = range(idx("2026-11-08 19:00"), idx("2026-11-08 23:00") + 1)     # hours starting 19:00..23:00 Sun
night = range(idx("2026-11-09 00:00"), idx("2026-11-09 10:00") + 1)  # hours starting 00:00..10:00 Mon
pairs = {k: (v[S9], v[M9]) for k, v in rows.items() if v[S9] and v[M9]}
out = {
 "stations_captured": len(rows),
 "with_both_9am": len(pairs),
 "rose": sum(b > a for a, b in pairs.values()),
 "at_least_doubled": sum(b >= 2 * a for a, b in pairs.values()),
 "median_sun_9am": st.median(a for a, b in pairs.values()),
 "median_mon_9am": st.median(b for a, b in pairs.values()),
 "mon_9am_above_500": sum(b > 500 for a, b in pairs.values()),
 "mon_9am_values_n": sum(1 for v in rows.values() if v[M9]),
 "mon_9am_above_500_all": sum(1 for v in rows.values() if v[M9] and v[M9] > 500),
 "median_of_station_max_sun_19_23": st.median(max(x for x in (v[i] for i in ev) if x) for v in rows.values() if any(v[i] for i in ev)),
 "median_sun_9am_all": st.median(v[S9] for v in rows.values() if v[S9]),
 "median_hour_by_hour": {(t0 + D.timedelta(hours=i)).strftime("%a %H:%M"): st.median(x for x in (v[i] for v in rows.values()) if x) for i in range(47)},
 "night_max_above_1000": {k: max(x for x in (v[i] for i in night) if x) for k, v in rows.items() if max([x for x in (v[i] for i in night) if x] or [0]) > 1000},
 "night_max_top": sorted(((k, max(x for x in (v[i] for i in night) if x), (t0 + D.timedelta(hours=max((i for i in night if v[i]), key=lambda i: v[i]))).strftime("%H:%M")) for k, v in rows.items() if any(v[i] for i in night)), key=lambda x: -x[1])[:6],
}
json.dump(out, open("data/lahore-stations-stats.json", "w"), indent=1)
for k, v in out.items():
    if k != "median_hour_by_hour": print(k, v)
print({k: v for k, v in out["median_hour_by_hour"].items() if k.startswith(("Sun 0", "Sun 19", "Sun 2", "Mon"))})
