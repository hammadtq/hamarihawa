# MODIS fire detections (FIRMS) in the study box, classified by country and state and summarised by day and year (draft 3).
# Inputs: raw/firms/*.csv (FIRMS area API), inputs/borders.json (country outlines), inputs/in_states_box.json (geoBoundaries state polygons).
# Changes from draft 2: the acquisition time is kept (FIRMS acq_date/acq_time are UTC) and every date used downstream is the local date in
# Indian Standard Time (UTC+5:30); states come from boundary polygons, not from the nearest mapped settlement; no path outside this folder.
# A detection whose local date falls outside 1 Oct-30 Nov is dropped. Night passes late on 30 September (UTC) that fall on 1 October local
# time are not in the downloads, so 1 October is very slightly undercounted.
# Output: out/firms_detections_classified.csv, firms_season_counts.csv, firms_daily.csv. python3 firms_analysis.py H
import csv, glob, json, math, os, sys, statistics as st, datetime as dt, collections
from firms_season import in_season, partial_label
H = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__)); IST = dt.timedelta(hours=5, minutes=30)
for need in ('inputs/borders.json', 'inputs/in_states_box.json'):
    if not os.path.exists(os.path.join(HERE, need)): sys.exit('missing ' + need + ' (run make_inputs.py)')
B = json.load(open(os.path.join(HERE, 'inputs', 'borders.json'))); S = json.load(open(os.path.join(HERE, 'inputs', 'in_states_box.json')))['states']
NAME = {'IN-PB': 'Punjab', 'IN-HR': 'Haryana', 'IN-UP': 'Uttar Pradesh', 'IN-DL': 'Delhi', 'IN-RJ': 'Rajasthan', 'IN-UT': 'Uttarakhand', 'IN-CH': 'Chandigarh', 'IN-HP': 'Himachal Pradesh',
        'IN-JK': 'Jammu and Kashmir', 'IN-LA': 'Ladakh'}
BAND = 0.02   # degrees of latitude: each ring's edges are bucketed by band so a point is tested only against edges that can cross its latitude
def bands(ring):
    idx = collections.defaultdict(list); n = len(ring); j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
        if yi != yj:
            for b in range(int(math.floor(min(yi, yj) / BAND)), int(math.floor(max(yi, yj) / BAND)) + 1): idx[b].append((xi, yi, xj, yj))
        j = i
    return idx
def prep(polys):
    out = []
    for poly in polys:
        rings = poly if isinstance(poly[0][0], list) else [poly]
        xs = [p[0] for p in rings[0]]; ys = [p[1] for p in rings[0]]
        out.append((min(xs), min(ys), max(xs), max(ys), [bands(r) for r in rings]))
    return out
CPOLY = {k: prep(v) for k, v in B.items()}; SPOLY = {k: prep(v['polygons']) for k, v in S.items()}
def inring(x, y, idx):
    c = False
    for xi, yi, xj, yj in idx.get(int(math.floor(y / BAND)), ()):
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: c = not c
    return c
def which(P, lon, lat):
    for k, polys in P.items():
        for x0, y0, x1, y1, rings in polys:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and inring(lon, lat, rings[0]) and not any(inring(lon, lat, r) for r in rings[1:]): return k
    return None
def km(lat1, lon1, lat2, lon2):
    r = math.radians; a = math.sin(r(lat2 - lat1) / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))
files = sorted(glob.glob(os.path.join(H, 'raw', 'firms', '*.csv')))
if not files: sys.exit('no FIRMS files in ' + os.path.join(H, 'raw', 'firms'))
seen = set(); fires = []; dropped = collections.Counter(); cache = {}
for fn in files:
    for r in csv.DictReader(open(fn, newline='')):
        key = (r['latitude'], r['longitude'], r['acq_date'], r['acq_time'], r['satellite'])
        if key in seen: continue
        seen.add(key)
        if int(r['confidence']) < 30: dropped['conf<30'] += 1; continue
        if r.get('type') not in (None, '', '0'): dropped['type ' + r['type']] += 1; continue
        t = r['acq_time'].zfill(4); utc = dt.datetime.fromisoformat(r['acq_date']) + dt.timedelta(hours=int(t[:2]), minutes=int(t[2:])); loc = utc + IST
        if not in_season(loc.date()): dropped['local date outside season window'] += 1; continue
        lat, lon = float(r['latitude']), float(r['longitude']); ck = (r['latitude'], r['longitude'])
        if ck not in cache:
            cc = which(CPOLY, lon, lat); sc = which(SPOLY, lon, lat) if cc == 'IN' else None
            cache[ck] = (cc, NAME.get(sc, 'unassigned') if cc == 'IN' else '')
        cc, state = cache[ck]
        if cc is None: dropped['no country'] += 1; continue
        fires.append(dict(id=f"{r['satellite'][0]}{utc:%Y%m%d%H%M}_{r['latitude']}_{r['longitude']}", utc=utc, loc=loc, date=loc.date(), lat=lat, lon=lon, cc=cc, st=state,
                          d=km(28.61, 77.21, lat, lon), sat=r['satellite'], conf=r['confidence'], dn=r.get('daynight', '')))
print('kept', len(fires), 'dropped', dict(dropped), file=sys.stderr)
with open(os.path.join(H, 'out', 'firms_detections_classified.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['id', 'acq_utc', 'local_ist', 'date', 'lat', 'lon', 'country', 'state', 'km_from_delhi', 'satellite', 'confidence', 'daynight'])
    for x in fires: w.writerow([x['id'], x['utc'].strftime('%Y-%m-%dT%H:%MZ'), x['loc'].strftime('%Y-%m-%dT%H:%M+05:30'), x['date'], x['lat'], x['lon'], x['cc'], x['st'], round(x['d'], 1), x['sat'], x['conf'], x['dn']])
BANDS = [(0, 100), (100, 200), (200, 300), (300, 400), (400, 9999)]
def band(d):
    for a, b in BANDS:
        if a <= d < b: return f'{a}-{b}' if b < 9999 else f'{a}+'
def grp(x):
    if x['cc'] == 'PK': return 'PK'
    return x['st'] if x['st'] in ('Punjab', 'Haryana', 'Uttar Pradesh', 'Delhi', 'Rajasthan') else 'IN other'
GR = ['Punjab', 'Haryana', 'Uttar Pradesh', 'Delhi', 'Rajasthan', 'IN other', 'PK']; BL = ['0-100', '100-200', '200-300', '300-400', '400+']
rows = []
for y in range(2001, 2027):
    fy = [x for x in fires if x['date'].year == y]; row = dict(year=y, partial=partial_label(y), total=len(fy)); c = collections.Counter(grp(x) for x in fy)
    for g in GR: row[g] = c.get(g, 0)
    for s_ in ('Terra', 'Aqua'): row['PbHr_' + s_] = sum(1 for x in fy if x['sat'] == s_ and x['st'] in ('Punjab', 'Haryana'))
    row['PbHr_day'] = sum(1 for x in fy if x['dn'] == 'D' and x['st'] in ('Punjab', 'Haryana'))
    cb = collections.Counter(band(x['d']) for x in fy if x['cc'] == 'IN')
    for b in BL: row['IN_' + b + 'km'] = cb.get(b, 0)
    for g in ('Punjab', 'Haryana'):
        s = [x for x in fy if x['st'] == g]
        row[g + '_median_date'] = (dt.date(y, 10, 1) + dt.timedelta(st.median((x['date'] - dt.date(y, 10, 1)).days for x in s))).strftime('%d %b') if s else ''
        row[g + '_median_km'] = round(st.median(x['d'] for x in s)) if s else None
    rows.append(row)
with open(os.path.join(H, 'out', 'firms_season_counts.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
daily = collections.defaultdict(collections.Counter)
for x in fires:
    daily[x['date']][grp(x)] += 1
    if x['cc'] == 'IN': daily[x['date']]['IN_' + band(x['d'])] += 1
with open(os.path.join(H, 'out', 'firms_daily.csv'), 'w', newline='') as f:
    w = csv.writer(f); cols = GR + ['IN_' + b for b in BL]; w.writerow(['date'] + cols)
    for d in sorted(daily): w.writerow([d] + [daily[d].get(c, 0) for c in cols])
for r in rows[15:]: print(r['year'], r['partial'], r['total'], [r[g] for g in GR], 'Terra/Aqua', r['PbHr_Terra'], r['PbHr_Aqua'], 'day', r['PbHr_day'])
