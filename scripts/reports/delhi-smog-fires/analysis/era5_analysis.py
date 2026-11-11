# ERA5 (Open-Meteo archive, models=era5) at 28.61N 77.21E, local time (IST): monthly boundary-layer height and wind,
# and how often the 100 m wind blows from the north-west quarter (from Punjab/Haryana) in the fire season.
import json, glob, os, sys, statistics as st, collections, csv
H = sys.argv[1]
mon = collections.defaultdict(list); nulls = 0
for fn in sorted(glob.glob(os.path.join(H, 'raw', 'era5', '*.json'))):
    d = json.load(open(fn))['hourly']
    for t, b, w, wd, w100, d100 in zip(d['time'], d['boundary_layer_height'], d['wind_speed_10m'], d['wind_direction_10m'], d['wind_speed_100m'], d['wind_direction_100m']):
        if None in (b, w, d100, w100): nulls += 1; continue
        mon[(int(t[:4]), int(t[5:7]))].append((t[:10], int(t[11:13]), b, w, w100, d100))
def nw(deg): return 270 <= deg <= 360   # blowing FROM west through north
rows = []
for (y, m), rec in sorted(mon.items()):
    days = collections.defaultdict(list)
    for r in rec: days[r[0]].append(r)
    aft = [r for r in rec if 12 <= r[1] <= 16]
    if len(rec) < 600 or not aft: continue
    rows.append(dict(year=y, month=m, n=len(rec), blh=round(st.mean(r[2] for r in rec)), blh_dmax=round(st.mean(max(x[2] for x in v) for v in days.values())),
        blh_night=round(st.mean(r[2] for r in rec if r[1] >= 20 or r[1] <= 6)), ws10=round(st.mean(r[3] for r in rec), 2),
        calm_pct=round(100 * sum(r[3] < 1 for r in rec) / len(rec), 1), ws100=round(st.mean(r[4] for r in rec), 2),
        nw_pct=round(100 * sum(nw(r[5]) for r in rec) / len(rec), 1), nw_aft_pct=round(100 * sum(nw(r[5]) for r in aft) / len(aft), 1),
        vent_aft=round(st.mean(r[2] * r[4] for r in aft))))
with open(os.path.join(H, 'out', 'era5_monthly.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('nulls', nulls)
print('\nmonthly climatology 2016-2025: month | BLH mean | BLH daily max | BLH night | wind 10 m | calm % | wind 100 m | from-NW % (all hours) | from-NW % (12-16h) | afternoon ventilation m2/s')
for m in range(1, 13):
    sel = [r for r in rows if r['month'] == m and 2016 <= r['year'] <= 2025]
    f = lambda k: st.mean(r[k] for r in sel)
    print(f"{m:2d} | {f('blh'):.0f} | {f('blh_dmax'):.0f} | {f('blh_night'):.0f} | {f('ws10'):.2f} | {f('calm_pct'):.1f} | {f('ws100'):.2f} | {f('nw_pct'):.0f} | {f('nw_aft_pct'):.0f} | {f('vent_aft'):.0f}")
print('\nby year, Oct and Nov: BLH mean, from-NW % all hours')
for y in range(1980, 2026):
    o = [r for r in rows if r['year'] == y and r['month'] in (10, 11)]
    if len(o) == 2: print(y, '|', o[0]['blh'], o[0]['nw_pct'], '|', o[1]['blh'], o[1]['nw_pct'])
