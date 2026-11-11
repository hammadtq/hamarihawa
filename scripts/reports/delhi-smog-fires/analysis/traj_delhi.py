# 48-hour back-paths from central Delhi on ERA5 100 m winds, four arrivals a day (03, 09, 15, 21 IST), every day 15 Oct-30 Nov of the study
# years, and an "upstream fire-detection index" for each day (draft 3). Horizontal only: no vertical motion, no mixing, no dispersion.
# Winds: the inner 0.5 degree grid (raw/windgrid, 27.5-33N 72.5-78.5E) where it exists, the outer 1 degree grid (raw/windouter, 24-35N 69-83E)
# elsewhere. Every path records how many hours it was followed and why it stopped:
#   complete        followed for the full 48 hours
#   left_domain     left the outer wind domain (at least 2.4 degrees beyond the fire box on every side); there is no fire data out there
#   no_wind_data    ERA5 had no wind for that hour (the end of the 2026 record)
# A day's index is VALID only if none of its four paths stopped for no_wind_data. Otherwise the index is missing (blank), never zero.
# Index: distinct MODIS detections (any state, India or Pakistan, inside the fire box 73.0-79.5E 27.0-32.6N) within 25 km of an hourly path
# point, acquired between 24 hours before and 3 hours after the air passed that point. Detection time is the satellite overpass, not
# ignition: the index says the air passed near a place where a fire was detected around that time, not that it crossed a burning field.
# Two alternatives are written for sensitivity checks: strict (24 hours before to 0 hours after) and calendar (draft 2's rule: detected on the
# local date the air passed or the day before, whatever the hour).
# Output: out/traj_paths.csv (one row per path), out/traj_daily.csv (one row per day). python3 traj_delhi.py H
import csv, json, glob, os, sys, math, datetime as dt, collections
H = sys.argv[1]; IST = dt.timedelta(hours=5, minutes=30); FBOX = (73.0, 27.0, 79.5, 32.6)
def load(folder, lats, lons):
    G = {}
    for fn in glob.glob(os.path.join(H, 'raw', folder, '*.json')):
        d = json.load(open(fn)); y = int(os.path.basename(fn)[:4]); i = lats.index(d['lat'])
        g = G.setdefault(y, dict(t0=dt.datetime.fromisoformat(d['time'][0]), n=len(d['time']), u={}, v={}, lats=lats, lons=lons))
        g['n'] = min(g['n'], len(d['time']))
        for j in range(len(lons)):
            U = []; V = []
            for s, a in zip(d['ws'][j], d['wd'][j]):
                if s is None or a is None: U.append(None); V.append(None)
                else: U.append(-s * math.sin(math.radians(a))); V.append(-s * math.cos(math.radians(a)))
            g['u'][(i, j)] = U; g['v'][(i, j)] = V
    return G
IN = load('windgrid', [27.5 + 0.5 * i for i in range(12)], [72.5 + 0.5 * j for j in range(13)])
OUT = load('windouter', [24.0 + i for i in range(12)], [69.0 + j for j in range(15)])
if not IN or not OUT: sys.exit('missing raw/windgrid or raw/windouter')
for y, g in OUT.items():
    if len(g['u']) != 12 * 15: sys.exit(f'outer wind grid incomplete for {y}')
def interp(g, lat, lon, t):
    lats, lons = g['lats'], g['lons']; st_ = lats[1] - lats[0]; i = (lat - lats[0]) / st_; j = (lon - lons[0]) / st_
    if not (0 <= i < len(lats) - 1 and 0 <= j < len(lons) - 1): return 'outside'
    h0 = int(math.floor(t)); f = t - h0
    if not (0 <= h0 < g['n'] - 1): return 'nodata'
    i0, j0 = int(i), int(j); di, dj = i - i0, j - j0; U = V = 0
    for hh, wt in ((h0, 1 - f), (h0 + 1, f)):
        for a, b, w in ((i0, j0, (1 - di) * (1 - dj)), (i0 + 1, j0, di * (1 - dj)), (i0, j0 + 1, (1 - di) * dj), (i0 + 1, j0 + 1, di * dj)):
            u = g['u'][(a, b)][hh]
            if u is None: return 'nodata'
            U += wt * w * u; V += wt * w * g['v'][(a, b)][hh]
    return U, V  # km/h
def uv(y, lat, lon, t_in, t_out):
    w = interp(IN[y], lat, lon, t_in)
    if w == 'outside': w = interp(OUT[y], lat, lon, t_out)
    return w
def back(y, arr_utc, hours=48, step=0.25):
    lat, lon = 28.61, 77.21; ti = (arr_utc - IN[y]['t0']).total_seconds() / 3600; to = (arr_utc - OUT[y]['t0']).total_seconds() / 3600
    path = [(lat, lon, arr_utc)]; reason = 'complete'
    for k in range(int(hours / step)):
        w = uv(y, lat, lon, ti - k * step, to - k * step)
        if w == 'outside': reason = 'left_domain'; break
        if w == 'nodata': reason = 'no_wind_data'; break
        lat -= w[1] * step / 111.0; lon -= w[0] * step / (111.0 * math.cos(math.radians(lat)))
        path.append((lat, lon, arr_utc - dt.timedelta(hours=(k + 1) * step)))
    return path, reason
fires = collections.defaultdict(lambda: collections.defaultdict(list))  # year -> 0.25 deg cell -> [(lat, lon, utc, id, country|state)]
fn = os.path.join(H, 'out', 'firms_detections_classified.csv')
if not os.path.exists(fn): sys.exit('missing out/firms_detections_classified.csv (run firms_analysis.py)')
for r in csv.DictReader(open(fn)):
    la, lo = float(r['lat']), float(r['lon']); u = dt.datetime.strptime(r['acq_utc'], '%Y-%m-%dT%H:%MZ')
    fires[u.year][(int(la * 4), int(lo * 4))].append((la, lo, u, r['id'], r['country'] + '|' + r['state']))
def km(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2; return 12742 * math.asin(math.sqrt(x))
prow = []; drow = []
for y in sorted(IN):
    if y not in OUT: sys.exit(f'no outer wind grid for {y}')
    d = dt.date(y, 10, 15)
    while d <= dt.date(y, 11, 30):
        main = {}; strict = set(); cal = set(); reasons = []; hrs = 0.0; inbox = 0.0
        for hh in (3, 9, 15, 21):
            arr = dt.datetime.combine(d, dt.time(hh)) - IST; p, why = back(y, arr); reasons.append(why); h = (len(p) - 1) / 4; hrs += h
            hb = sum(1 for la, lo, t in p[1:] if FBOX[0] <= lo <= FBOX[2] and FBOX[1] <= la <= FBOX[3]) / 4; inbox += hb
            prow.append(dict(date=d.isoformat(), arrival_ist=f'{hh:02d}:00', hours_followed=h, stop=why, hours_in_fire_box=hb, end_lat=round(p[-1][0], 2), end_lon=round(p[-1][1], 2)))
            for la, lo, t in p[::4]:
                locd = (t + IST).date()
                for ci in (int(la * 4) - 1, int(la * 4), int(la * 4) + 1):
                    for cj in range(int(lo * 4) - 2, int(lo * 4) + 3):
                        for fl, fo, fu, fid, st_ in fires[y].get((ci, cj), ()):
                            lag = (t - fu).total_seconds() / 3600  # hours from detection to the air's passage; negative = detected after
                            if not (-27 <= lag <= 51) or km(fl, fo, la, lo) > 25: continue
                            if -3 <= lag <= 24: main[fid] = st_
                            if 0 <= lag <= 24: strict.add(fid)
                            if (fu + IST).date() in (locd, locd - dt.timedelta(1)): cal.add(fid)
        valid = 'no_wind_data' not in reasons; c = collections.Counter(main.values())
        drow.append(dict(date=d.isoformat(), valid=int(valid), paths_complete=reasons.count('complete'), paths_left_domain=reasons.count('left_domain'), paths_no_wind=reasons.count('no_wind_data'),
                         path_hours=hrs, hours_in_fire_box=inbox, upwind=len(main) if valid else '', upwind_strict=len(strict) if valid else '', upwind_calendar=len(cal) if valid else '',
                         upwind_punjab=c.get('IN|Punjab', 0) if valid else '', upwind_haryana=c.get('IN|Haryana', 0) if valid else '', upwind_pk=sum(v for k, v in c.items() if k.startswith('PK')) if valid else ''))
        d += dt.timedelta(1)
last = max(r['date'] for r in drow if r['paths_no_wind'] < 4)   # days after the wind record ends are not written at all
drow = [r for r in drow if r['date'] <= last]; prow = [r for r in prow if r['date'] <= last]
for name, rows in (('traj_paths.csv', prow), ('traj_daily.csv', drow)):
    with open(os.path.join(H, 'out', name), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('days', len(drow), 'valid', sum(r['valid'] for r in drow), 'paths', collections.Counter(r['stop'] for r in prow))
print('valid days with 4 complete paths', sum(1 for r in drow if r['valid'] and r['paths_complete'] == 4), '; with a path that left the domain', sum(1 for r in drow if r['valid'] and r['paths_left_domain']))
