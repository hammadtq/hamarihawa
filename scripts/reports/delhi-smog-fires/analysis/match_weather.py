# Compare each day of the peak fire weeks (25 Oct-20 Nov) with days of the SAME season, after the main rice-burning weeks, that had a similar
# value of ONE ventilation measure (draft 3). Ventilation = mean over the same local calendar day (00-23 IST, the day the PM2.5 value covers)
# of ERA5 mixing height x 100 m wind speed at the grid point nearest central Delhi. Controls: (a) December-January, (b) 1-14 October; the up
# to 5 nearest days by ln(ventilation), within a factor of 1.25, at least 3. Difference = target day minus the mean of its control days.
# This matches on one scalar. It does not hold temperature, humidity, rain, wind direction, chemistry or the mix of sources constant, and
# different wind speeds and mixing heights can give the same product. Neither control set is a no-fire counterfactual or a bound.
# Output: out/match_weather.csv (one row per target day), out/match_controls.csv (one row per target-control pair). python3 match_weather.py H
import csv, json, glob, os, sys, math, statistics as st, datetime as dt, collections
H = sys.argv[1]; SUF = sys.argv[2] if len(sys.argv) > 2 else ''   # SUF '_alt30' = hourly-grid sensitivity
pm = {dt.date.fromisoformat(r['date']): float(r['median']) for r in csv.DictReader(open(os.path.join(H, 'out', f'pm25_daily{SUF}.csv')))}
hrs = collections.defaultdict(list)
for fn in glob.glob(os.path.join(H, 'raw', 'era5', '*.json')):
    d = json.load(open(fn))['hourly']
    for t, b, w in zip(d['time'], d['boundary_layer_height'], d['wind_speed_100m']):
        if b is not None and w is not None: hrs[t[:10]].append(b * w)
V = {d: st.mean(hrs[d.isoformat()]) for d in pm if len(hrs.get(d.isoformat(), ())) >= 20}
rows = []; pairs = []
for y in range(2016, 2027):
    fire = sorted(d for d in V if dt.date(y, 10, 25) <= d <= dt.date(y, 11, 20))
    ctrl = {'dec_jan': [d for d in V if dt.date(y, 12, 1) <= d <= dt.date(y + 1, 1, 31)], 'early_oct': [d for d in V if dt.date(y, 10, 1) <= d <= dt.date(y, 10, 14)]}
    for name, cs in ctrl.items():
        if len(fire) < 10 or len(cs) < (20 if name == 'dec_jan' else 8): continue
        for d in fire:
            near = sorted(cs, key=lambda c: (abs(math.log(V[c] / V[d])), c))[:5]
            near = [c for c in near if abs(math.log(V[c] / V[d])) <= math.log(1.25)]
            if len(near) < 3: continue
            cp = st.mean(pm[c] for c in near)
            rows.append(dict(season=y, control=name, date=d, pm=pm[d], vent=round(V[d]), controls=len(near), control_pm=round(cp, 2), diff=round(pm[d] - cp, 2)))
            for c in near: pairs.append(dict(season=y, control=name, date=d, control_date=c, control_pm=pm[c], vent=round(V[d]), control_vent=round(V[c]), ln_ratio=round(math.log(V[c] / V[d]), 4)))
for name, rr in ((f'match_weather{SUF}.csv', rows), (f'match_controls{SUF}.csv', pairs)):
    with open(os.path.join(H, 'out', name), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rr[0])); w.writeheader(); w.writerows(rr)
for name in ('dec_jan', 'early_oct'):
    s = [r for r in rows if r['control'] == name]; print(name, 'targets', len(s), 'by season', dict(collections.Counter(r['season'] for r in s)))
    if s: print('  mean pm', round(st.mean(r['pm'] for r in s), 1), 'controls', round(st.mean(r['control_pm'] for r in s), 1), 'diff', round(st.mean(r['diff'] for r in s), 1))
