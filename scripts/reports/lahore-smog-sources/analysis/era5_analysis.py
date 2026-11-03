# ERA5 (Open-Meteo archive, models=era5) boundary-layer height and 10 m wind at 31.55N 74.34E, local time.
import json, glob, os, sys, math, statistics as st, collections, csv
H = sys.argv[1]
data = collections.defaultdict(list)  # (year, month) -> list of (date, hour, blh, ws)
nulls = 0
for fn in sorted(glob.glob(os.path.join(H, 'raw', 'era5', '*.json'))):
    d = json.load(open(fn))['hourly']
    for t, b, w in zip(d['time'], d['boundary_layer_height'], d['wind_speed_10m']):
        if b is None or w is None: nulls += 1; continue
        data[(int(t[:4]), int(t[5:7]))].append((t[:10], int(t[11:13]), b, w))
def stats(rec):
    blh = st.mean(r[2] for r in rec); ws = st.mean(r[3] for r in rec)
    days = collections.defaultdict(list)
    for r in rec: days[r[0]].append(r)
    dmax = st.mean(max(x[2] for x in v) for v in days.values())
    night = st.mean(r[2] for r in rec if r[1] >= 20 or r[1] <= 6)
    calm = 100 * sum(1 for r in rec if r[3] < 1.0) / len(rec)
    return dict(blh=blh, blh_dmax=dmax, blh_night=night, ws=ws, calm=calm, n=len(rec))
def theilsen(xs, ys):
    sl = sorted((ys[j] - ys[i]) / (xs[j] - xs[i]) for i in range(len(xs)) for j in range(i + 1, len(xs)))
    n = len(sl); return sl[n // 2] if n % 2 else (sl[n // 2 - 1] + sl[n // 2]) / 2
def mk_p(ys):
    n = len(ys); s = sum((ys[j] > ys[i]) - (ys[j] < ys[i]) for i in range(n) for j in range(i + 1, n))
    var = n * (n - 1) * (2 * n + 5) / 18; z = (s - (1 if s > 0 else -1 if s < 0 else 0)) / math.sqrt(var)
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
rows = []
for y in range(1980, 2026):
    r = dict(year=y)
    for m, lab in ((10, 'oct'), (11, 'nov')):
        s = stats(data[(y, m)])
        for k, v in s.items(): r[f'{lab}_{k}'] = round(v, 2) if k != 'n' else v
    rows.append(r)
with open(os.path.join(H, 'out', 'era5_oct_nov.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('nulls', nulls)
print('year | Oct BLH mean | Oct BLH daily max | Oct wind | Nov BLH mean | Nov BLH daily max | Nov BLH night | Nov wind | Nov % hours wind<1 m/s')
for r in rows:
    print(f"{r['year']} | {r['oct_blh']:.0f} | {r['oct_blh_dmax']:.0f} | {r['oct_ws']:.2f} | {r['nov_blh']:.0f} | {r['nov_blh_dmax']:.0f} | {r['nov_blh_night']:.0f} | {r['nov_ws']:.2f} | {r['nov_calm']:.0f} | hrs {r['nov_n']}")
print('\ndecade | Oct BLH | Oct dmax | Oct wind | Nov BLH | Nov dmax | Nov night | Nov wind | Nov calm%')
for d0 in (1980, 1990, 2000, 2010, 2020):
    sel = [r for r in rows if d0 <= r['year'] < d0 + 10]
    f = lambda k: st.mean(r[k] for r in sel)
    print(f"{d0}s ({sel[0]['year']}-{sel[-1]['year']}) | {f('oct_blh'):.0f} | {f('oct_blh_dmax'):.0f} | {f('oct_ws'):.2f} | {f('nov_blh'):.0f} | {f('nov_blh_dmax'):.0f} | {f('nov_blh_night'):.0f} | {f('nov_ws'):.2f} | {f('nov_calm'):.1f}")
print('\nTheil-Sen slope per decade, 1980-2025 (Mann-Kendall two-sided p, no autocorrelation correction)')
xs = [r['year'] for r in rows]
for k in ('oct_blh', 'oct_blh_dmax', 'oct_ws', 'nov_blh', 'nov_blh_dmax', 'nov_blh_night', 'nov_ws', 'nov_calm'):
    ys = [r[k] for r in rows]
    print(f"{k}: {10 * theilsen(xs, ys):+.2f} per decade (mean {st.mean(ys):.2f}), p={mk_p(ys):.3f}")
