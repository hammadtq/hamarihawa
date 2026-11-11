# Put the pieces together: for each fire-season day, the fires its air passed over (traj_daily.csv), satellite aerosol (aod_daily.csv),
# relative CO at Delhi monitors, and the excess over weather-matched December-January days (match_weather.csv).
# Output out/answer_daily.csv and printed tables. python3 answer.py H
import csv, json, glob, os, sys, statistics as st, datetime as dt, collections
H = sys.argv[1]; O = lambda n: os.path.join(H, 'out', n)
pm = {r['date']: float(r['median']) for r in csv.DictReader(open(O('pm25_daily.csv')))}
tr = {r['date']: r for r in csv.DictReader(open(O('traj_daily.csv')))}
aod = {r['date']: r for r in csv.DictReader(open(O('aod_daily.csv')))}
mw = {r['date']: float(r['diff']) for r in csv.DictReader(open(O('match_weather.csv'))) if r['control'] == 'dec_jan'}
# relative CO: each sensor's daily value divided by that sensor's own median (units differ between sensors); city value = median across sensors (>=5)
co_day = collections.defaultdict(list)
for fn in glob.glob(os.path.join(H, 'raw', 'openaq', 'co_*.json')):
    s = json.load(open(fn)); v = [(d, x) for d, x, n in s['rows'] if x is not None and x > 0 and n >= 18]
    if len(v) < 100: continue
    m = st.median(x for d, x in v)
    for d, x in v: co_day[d].append(x / m)
co = {d: st.median(v) for d, v in co_day.items() if len(v) >= 5}
rows = []
for d, t in sorted(tr.items()):
    if d not in pm: continue
    D = dt.date.fromisoformat(d); a = aod.get(d, {})
    rows.append(dict(date=d, year=D.year, part=('15-31 Oct' if D.month == 10 else '1-15 Nov' if D.day <= 15 else '16-30 Nov'), pm=pm[d], upwind=int(t['upwind']), upwind_punjab=int(t['upwind_punjab']),
                     upwind_haryana=int(t['upwind_haryana']), co_rel=round(co[d], 2) if d in co else '', aod_delhi=a.get('delhi', '') if a and float(a.get('delhi_cover') or 0) >= 0.3 else '',
                     aod_punjab=a.get('punjab', '') if a and float(a.get('punjab_cover') or 0) >= 0.3 else '', excess_vs_dec_jan=mw.get(d, '')))
with open(O('answer_daily.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
us = sorted(r['upwind'] for r in rows); q1, q2 = us[len(us) // 3], us[2 * len(us) // 3]
T = lambda r: 'few' if r['upwind'] <= q1 else 'many' if r['upwind'] > q2 else 'some'
def m(x, f=st.median): x = [float(v) for v in x if v != '']; return (f'{f(x):.0f}' if f(x) > 20 else f'{f(x):.2f}') + f' ({len(x)})' if x else '-'
print(f'days {len(rows)}; fires on the air\'s path, terciles: few <= {q1}, many > {q2}')
print('\nA. median Delhi PM2.5 by fires on the path, within each part of the season')
for p in ('15-31 Oct', '1-15 Nov', '16-30 Nov'):
    print(f'  {p}: ' + ' | '.join(f"{k} {m([r['pm'] for r in rows if r['part'] == p and T(r) == k])}" for k in ('few', 'some', 'many')))
print('\nB. peak fire weeks (25 Oct-20 Nov): mean excess over weather-matched December-January days, by fires on the path')
B = [r for r in rows if r['excess_vs_dec_jan'] != '']
for k in ('few', 'some', 'many'):
    s = [r for r in B if T(r) == k]
    if s: print(f"  {k}: excess {st.mean(r['excess_vs_dec_jan'] for r in s):+.0f} µg/m³, mean PM2.5 {st.mean(r['pm'] for r in s):.0f}, days {len(s)}")
print('  by year, few+some vs many:')
for y in sorted({r['year'] for r in B}):
    a = [r['excess_vs_dec_jan'] for r in B if r['year'] == y and T(r) != 'many']; b = [r['excess_vs_dec_jan'] for r in B if r['year'] == y and T(r) == 'many']
    print(f"   {y}: not-many {st.mean(a):+.0f} ({len(a)})" if a else f'   {y}: not-many -', f"| many {st.mean(b):+.0f} ({len(b)})" if b else '| many -')
print('\nC. tracers by fires on the path (all window days): median relative CO; median AOD over Delhi; median AOD over Punjab fire belt')
for k in ('few', 'some', 'many'):
    s = [r for r in rows if T(r) == k]
    print(f"  {k}: CO {m([r['co_rel'] for r in s])} | AOD Delhi {m([r['aod_delhi'] for r in s])} | AOD Punjab {m([r['aod_punjab'] for r in s])}")
print('\nD. same, 1-15 Nov only: PM2.5 | relative CO | AOD Delhi')
for k in ('few', 'some', 'many'):
    s = [r for r in rows if T(r) == k and r['part'] == '1-15 Nov']
    print(f"  {k}: PM {m([r['pm'] for r in s])} | CO {m([r['co_rel'] for r in s])} | AOD Delhi {m([r['aod_delhi'] for r in s])}")
print('\nE. upwind fires by year (mean per day, 25 Oct-20 Nov) and share of days in the "many" tercile')
for y in sorted({r['year'] for r in rows}):
    s = [r for r in rows if r['year'] == y and r['excess_vs_dec_jan'] != ''] or [r for r in rows if r['year'] == y and r['part'] != '16-30 Nov']
    print(f"   {y}: mean upwind {st.mean(r['upwind'] for r in s):.0f}, many-days {100 * sum(T(r) == 'many' for r in s) / len(s):.0f}%, n {len(s)}")
