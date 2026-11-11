# Join Delhi daily PM2.5 (out/pm25_daily.csv) to daily fire detections in Indian Punjab + Haryana (out/firms_daily.csv)
# and ERA5 daily weather at Delhi. Fire season window: 15 Oct - 30 Nov.
# fires2 = Punjab+Haryana detections on the day and the day before. nw = share of the 24 hours to noon with 100 m wind from 270-360 deg.
import csv, json, glob, os, sys, collections, statistics as st, datetime as dt, math
H = sys.argv[1]
pm = {r['date']: float(r['median']) for r in csv.DictReader(open(os.path.join(H, 'out', 'pm25_daily.csv')))}
fire = {r['date']: int(r['Punjab']) + int(r['Haryana']) for r in csv.DictReader(open(os.path.join(H, 'out', 'firms_daily.csv')))}
hrs = {}
for fn in glob.glob(os.path.join(H, 'raw', 'era5', '*.json')):
    d = json.load(open(fn))['hourly']
    for t, b, w100, d100 in zip(d['time'], d['boundary_layer_height'], d['wind_speed_100m'], d['wind_direction_100m']):
        if None not in (b, w100, d100): hrs[t] = (b, w100, d100)
def wx(day):
    t0 = dt.datetime.combine(day, dt.time(12)) - dt.timedelta(hours=24)
    rec = [hrs.get((t0 + dt.timedelta(hours=i)).strftime('%Y-%m-%dT%H:00')) for i in range(24)]
    rec = [r for r in rec if r]
    if len(rec) < 20: return None
    return dict(blh=st.mean(r[0] for r in rec), ws=st.mean(r[1] for r in rec), nw=sum(270 <= r[2] <= 360 for r in rec) / len(rec))
rows = []
for ds, v in sorted(pm.items()):
    d = dt.date.fromisoformat(ds)
    if not (dt.date(d.year, 10, 15) <= d <= dt.date(d.year, 11, 30)): continue
    w = wx(d)
    if not w: continue
    f2 = fire.get(ds, 0) + fire.get((d - dt.timedelta(1)).isoformat(), 0)
    rows.append(dict(date=ds, year=d.year, pm=v, fires2=f2, **{k: round(x, 2) for k, x in w.items()}))
with open(os.path.join(H, 'out', 'join_daily.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('days', len(rows), collections.Counter(r['year'] for r in rows))
def med(x): return round(st.median(x)) if x else None
fs = sorted(r['fires2'] for r in rows); q1, q2 = fs[len(fs) // 3], fs[2 * len(fs) // 3]
vs = sorted(r['blh'] * r['ws'] for r in rows); v1, v2 = vs[len(vs) // 3], vs[2 * len(vs) // 3]
print(f'fire terciles (2-day Punjab+Haryana detections): low <= {q1}, high > {q2}; ventilation terciles (BLH x 100 m wind): {v1:.0f}, {v2:.0f}')
def ft(r): return 'low' if r['fires2'] <= q1 else 'high' if r['fires2'] > q2 else 'mid'
def vt(r): x = r['blh'] * r['ws']; return 'poor' if x <= v1 else 'good' if x > v2 else 'mid'
print('\nmedian Delhi PM2.5 by fire tercile:'); 
for k in ('low', 'mid', 'high'):
    s = [r['pm'] for r in rows if ft(r) == k]; print(f'  {k}: {med(s)} (n={len(s)})')
print('\nby ventilation tercile x fire tercile: median PM2.5 (n)')
for v in ('poor', 'mid', 'good'):
    print(' ', v, ' | '.join(f"{k} {med([r['pm'] for r in rows if vt(r) == v and ft(r) == k])} ({sum(1 for r in rows if vt(r) == v and ft(r) == k)})" for k in ('low', 'mid', 'high')))
print('\nhigh-fire days split by wind: NW share >= 0.5 vs < 0.5')
for lab, c in (('from NW', lambda r: r['nw'] >= 0.5), ('not NW', lambda r: r['nw'] < 0.5)):
    for k in ('low', 'high'):
        s = [r['pm'] for r in rows if ft(r) == k and c(r)]; print(f'  {lab}, {k} fires: {med(s)} (n={len(s)})')
# least squares: ln(pm) ~ a + b*ln(1+fires2) + c*ln(vent) + d*nw + year dummies
def ols(X, y):
    n = len(X[0]); A = [[sum(x[i] * x[j] for x in X) for j in range(n)] for i in range(n)]; b = [sum(x[i] * yy for x, yy in zip(X, y)) for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(A[k][i])); A[i], A[p] = A[p], A[i]; b[i], b[p] = b[p], b[i]
        for k in range(i + 1, n):
            f = A[k][i] / A[i][i]; b[k] -= f * b[i]
            for j in range(i, n): A[k][j] -= f * A[i][j]
    x = [0] * n
    for i in reversed(range(n)): x[i] = (b[i] - sum(A[i][j] * x[j] for j in range(i + 1, n))) / A[i][i]
    return x
years = sorted({r['year'] for r in rows})
X = [[1, math.log(1 + r['fires2']), math.log(r['blh'] * r['ws']), r['nw']] + [1.0 if r['year'] == y else 0.0 for y in years[1:]] for r in rows]
y = [math.log(r['pm']) for r in rows]
co = ols(X, y); pred = [sum(a * b for a, b in zip(co, x)) for x in X]
ss = sum((a - b) ** 2 for a, b in zip(y, pred)); tot = sum((a - st.mean(y)) ** 2 for a in y)
print(f'\nregression ln(PM2.5): ln(1+fires2) {co[1]:+.3f}, ln(ventilation) {co[2]:+.3f}, NW share {co[3]:+.3f}; R2 {1 - ss / tot:.2f}, n {len(rows)}')
# counterfactual: set fires to zero, same weather
cf = [math.exp(p - co[1] * x[1]) for p, x in zip(pred, X)]; act = [math.exp(p) for p in pred]
print(f'model mean PM2.5 15 Oct-30 Nov: with fires {st.mean(act):.0f}, fires set to zero {st.mean(cf):.0f}, difference {100 * (1 - st.mean(cf) / st.mean(act)):.0f}%')
top = sorted(rows, key=lambda r: -r['fires2'])[:len(rows) // 10]; idx = {id(r): i for i, r in enumerate(rows)}
print(f'on the top 10% fire days: with {st.mean(act[idx[id(r)]] for r in top):.0f}, without {st.mean(cf[idx[id(r)]] for r in top):.0f}')
# Dec-Jan (no crop fires) vs fire window, per season
print('\nseason | 15 Oct-30 Nov mean (days) | Dec-Jan mean (days)')
for yv in range(2016, 2026):
    a = [v for ds, v in pm.items() if dt.date(yv, 10, 15) <= dt.date.fromisoformat(ds) <= dt.date(yv, 11, 30)]
    b = [v for ds, v in pm.items() if dt.date(yv, 12, 1) <= dt.date.fromisoformat(ds) <= dt.date(yv + 1, 1, 31)]
    if len(a) >= 25 and len(b) >= 30: print(f'  {yv}-{(yv + 1) % 100:02d} | {st.mean(a):.0f} ({len(a)}) | {st.mean(b):.0f} ({len(b)})')
