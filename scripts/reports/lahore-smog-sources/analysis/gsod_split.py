# Split low-visibility days into Oct-Nov (crop-smoke season) and Dec-Jan (fog season); decade summaries as % of valid days.
import csv, glob, os, sys, datetime as dt, collections
H = sys.argv[1]
ST = {'41641099999': 'Lahore airport', '41640099999': 'Lahore City', '42071099999': 'Amritsar', '41630099999': 'Faisalabad', '41600099999': 'Sialkot City', '41571099999': 'Islamabad'}
MI1, MI2 = 1/1.609344, 2/1.609344
res = {}
for sid in ST:
    days = {}
    for fn in glob.glob(os.path.join(H, 'raw', 'gsod', f'{sid}_*.csv')):
        for r in csv.DictReader(open(fn)):
            v = float(r['VISIB'])
            if v < 999: days[dt.date.fromisoformat(r['DATE'])] = v
    for y in range(1973, 2025):
        on = [days[d] for d in (dt.date(y, 10, 1) + dt.timedelta(i) for i in range(61)) if d in days]
        dj = [days[d] for d in (dt.date(y, 12, 1) + dt.timedelta(i) for i in range(62)) if d in days]
        res[(sid, y)] = dict(on_n=len(on), on2=sum(v < MI2 for v in on), on1=sum(v < MI1 for v in on),
                             dj_n=len(dj), dj2=sum(v < MI2 for v in dj), dj1=sum(v < MI1 for v in dj))
with open(os.path.join(H, 'out', 'gsod_split_octnov_decjan.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['station', 'season_start_year', 'octnov_valid', 'octnov_lt2km', 'octnov_lt1km', 'decjan_valid', 'decjan_lt2km', 'decjan_lt1km'])
    for (sid, y), r in sorted(res.items()): w.writerow([sid, y] + list(r.values()))
print('Per season: Oct-Nov valid/<2km/<1km  ||  Dec-Jan valid/<2km/<1km')
for sid in ('41641099999', '41640099999', '42071099999'):
    print('\n' + ST[sid])
    for y in range(1973, 2025):
        r = res[(sid, y)]
        if r['on_n'] + r['dj_n'] == 0: continue
        print(f"{y}-{(y+1)%100:02d}: {r['on_n']}/{r['on2']}/{r['on1']} || {r['dj_n']}/{r['dj2']}/{r['dj1']}")
print('\nDecade summary: % of valid days with daily-mean visibility <2 km and <1 km; only seasons with >=70% coverage in that half')
for sid, nm in ST.items():
    print('\n' + nm)
    for d0 in (1973, 1980, 1990, 2000, 2010, 2020):
        d1 = 1979 if d0 == 1973 else d0 + 9
        for half, n, a, b, full in (('Oct-Nov', 'on_n', 'on2', 'on1', 61), ('Dec-Jan', 'dj_n', 'dj2', 'dj1', 62)):
            sel = [res[(sid, y)] for y in range(d0, min(d1, 2024) + 1) if res[(sid, y)][n] >= 0.7 * full]
            if not sel: continue
            N = sum(s[n] for s in sel)
            print(f"  {d0}-{min(d1, 2024)} {half}: seasons {len(sel)}, <2km {100*sum(s[a] for s in sel)/N:.1f}%, <1km {100*sum(s[b] for s in sel)/N:.1f}%")
