# Season stats from NOAA GSOD daily files. Season Y = 1 Oct..31 Dec of Y plus 1..31 Jan of Y+1 (123 days).
import csv, glob, os, sys, datetime as dt, statistics as st
H = sys.argv[1]
STATIONS = {'42182099999': 'New Delhi Safdarjung', '42181099999': 'New Delhi Palam (IGI)', '42131099999': 'Hisar', '42101099999': 'Patiala', '42099099999': 'Ludhiana', '42071099999': 'Amritsar'}
MI1, MI2 = 1/1.609344, 2/1.609344
rows_out = []
for sid, name in STATIONS.items():
    days = {}
    for fn in sorted(glob.glob(os.path.join(H, 'raw', 'gsod', f'{sid}_*.csv'))):
        for r in csv.DictReader(open(fn, newline='')):
            if not r.get('VISIB'): continue
            d = dt.date.fromisoformat(r['DATE'])
            v = float(r['VISIB']); n = int(r['VISIB_ATTRIBUTES'] or 0)
            days[d] = (None if v >= 999 else v, n, r['FRSHTT'].strip())
    years = sorted({d.year for d in days})
    for y in range(min(years), max(years) + 1):
        season = [dt.date(y, 10, 1) + dt.timedelta(i) for i in range(123)]
        vals = [days[d] for d in season if d in days and days[d][0] is not None]
        nvalid = len(vals)
        fog_all = sum(1 for d in season if d in days and days[d][2][:1] == '1')
        def mon(m, yy):
            v = [days[d][0] for d in days if d.year == yy and d.month == m and days[d][0] is not None]
            return (round(st.mean(v) * 1.609344, 2) if len(v) >= 15 else None, len(v))
        nov, dec = mon(11, y), mon(12, y)
        obs = [x[1] for x in vals]
        rows_out.append(dict(station=sid, name=name, season=f'{y}-{(y+1)%100:02d}', valid_days=nvalid,
            coverage_pct=round(100 * nvalid / 123), poor=('POOR' if nvalid < 0.7 * 123 else ''),
            lt1km=sum(1 for x in vals if x[0] < MI1), lt2km=sum(1 for x in vals if x[0] < MI2),
            lt1km_pct=round(100 * sum(1 for x in vals if x[0] < MI1) / nvalid, 1) if nvalid else None,
            lt2km_pct=round(100 * sum(1 for x in vals if x[0] < MI2) / nvalid, 1) if nvalid else None,
            nov_mean_km=nov[0], nov_n=nov[1], dec_mean_km=dec[0], dec_n=dec[1], fog_flag_days=fog_all,
            median_obs_per_day=(st.median(obs) if obs else None)))
with open(os.path.join(H, 'out', 'gsod_season_visibility.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0])); w.writeheader(); w.writerows(rows_out)
for sid, name in STATIONS.items():
    print(f'\n## {name} ({sid})')
    print('season | valid | cov% | <1km | <2km | <1km% | <2km% | Nov km | Dec km | fog | obs/day')
    for r in rows_out:
        if r['station'] == sid and r['valid_days'] > 0:
            print(f"{r['season']} | {r['valid_days']} | {r['coverage_pct']}{'*' if r['poor'] else ''} | {r['lt1km']} | {r['lt2km']} | {r['lt1km_pct']} | {r['lt2km_pct']} | {r['nov_mean_km']} | {r['dec_mean_km']} | {r['fog_flag_days']} | {r['median_obs_per_day']}")
