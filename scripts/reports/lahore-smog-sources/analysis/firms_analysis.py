# MODIS fire counts (FIRMS) by side, state and fortnight. Inputs: raw/firms/*.csv, borders.json, places tiles.
import csv, glob, json, math, os, sys, statistics as st, datetime as dt, collections
H = sys.argv[1]
REPO = '/Users/hammadtariq/go/src/github.com/hammadtq/hamarihawa/data'
B = json.load(open(f'{REPO}/places/borders.json'))
def rings_bbox(polys):
    out = []
    for poly in polys:
        ring = poly[0] if isinstance(poly[0][0], list) else poly
        xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
        out.append((min(xs), min(ys), max(xs), max(ys), poly))
    return out
POLY = {k: rings_bbox(v) for k, v in B.items()}
def inring(x, y, ring):
    c = False; n = len(ring); j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: c = not c
        j = i
    return c
def country(lon, lat):
    for k, polys in POLY.items():
        for x0, y0, x1, y1, poly in polys:
            if x0 <= lon <= x1 and y0 <= lat <= y1:
                rings = poly if isinstance(poly[0][0], list) else [poly]
                if inring(lon, lat, rings[0]) and not any(inring(lon, lat, r) for r in rings[1:]):
                    return k
    return None
_tiles = {}
def tile(i, j):
    if (i, j) not in _tiles:
        fn = f'{REPO}/places/{i}_{j}.json'
        _tiles[(i, j)] = json.load(open(fn)) if os.path.exists(fn) else None
    return _tiles[(i, j)]
def state(lon, lat, cc):
    i, j = int(math.floor(lat / 0.25)), int(math.floor(lon / 0.25)); best = (9e9, None)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            t = tile(i + di, j + dj)
            if not t: continue
            for p in t['p']:
                reg = t['r'][p[3]].split('|')
                if reg[2] != cc: continue
                d = (p[0] - lat) ** 2 + ((p[1] - lon) * math.cos(math.radians(lat))) ** 2
                if d < best[0]: best = (d, reg[1])
    return best[1] or '?'
def km(lat1, lon1, lat2, lon2):
    r = math.radians; a = math.sin(r(lat2 - lat1) / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))
seen = set(); fires = []; dropped = collections.Counter()
for fn in sorted(glob.glob(os.path.join(H, 'raw', 'firms', '*.csv'))):
    for r in csv.DictReader(open(fn, newline='')):
        key = (r['latitude'], r['longitude'], r['acq_date'], r['acq_time'], r['satellite'])
        if key in seen: continue
        seen.add(key)
        if int(r['confidence']) < 30: dropped['conf<30'] += 1; continue
        if r.get('type') not in (None, '', '0'): dropped['type ' + r['type']] += 1; continue
        lat, lon = float(r['latitude']), float(r['longitude'])
        cc = country(lon, lat)
        if cc is None: dropped['no country'] += 1; continue
        fires.append(dict(date=dt.date.fromisoformat(r['acq_date']), lat=lat, lon=lon, cc=cc,
                          st=state(lon, lat, cc), d=km(31.55, 74.34, lat, lon), sat=r['satellite']))
print('kept', len(fires), 'dropped', dict(dropped), file=sys.stderr)
with open(os.path.join(H, 'out', 'firms_detections_classified.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['date', 'lat', 'lon', 'country', 'state', 'km_from_lahore', 'satellite'])
    for x in fires: w.writerow([x['date'], x['lat'], x['lon'], x['cc'], x['st'], round(x['d'], 1), x['sat']])
def fortnight(d):
    return ('Oct1-15' if d.day <= 15 else 'Oct16-31') if d.month == 10 else ('Nov1-15' if d.day <= 15 else 'Nov16-30')
FN = ['Oct1-15', 'Oct16-31', 'Nov1-15', 'Nov16-30']
rows = []
for y in range(2001, 2027):
    fy = [x for x in fires if x['date'].year == y]
    win = [x for x in fy if dt.date(y, 10, 15) <= x['date'] <= dt.date(y, 11, 30)]
    todate = [x for x in fy if dt.date(y, 10, 15) <= x['date'] <= dt.date(y, 11, 1)]
    row = dict(year=y, partial=('to 1 Nov (NRT)' if y == 2026 else ''))
    row['r100_PK'] = sum(1 for x in win if x['d'] <= 100 and x['cc'] == 'PK')
    row['r100_IN'] = sum(1 for x in win if x['d'] <= 100 and x['cc'] == 'IN')
    row['box_PK_all'] = sum(1 for x in win if x['cc'] == 'PK')
    row['box_PK_Punjab'] = sum(1 for x in win if x['cc'] == 'PK' and x['st'] == 'Punjab')
    row['box_IN_all'] = sum(1 for x in win if x['cc'] == 'IN')
    row['box_IN_Punjab'] = sum(1 for x in win if x['cc'] == 'IN' and x['st'] == 'Punjab')
    row['box_IN_Haryana'] = sum(1 for x in win if x['cc'] == 'IN' and x['st'] == 'Haryana')
    row['todate_PKPunjab_15Oct_1Nov'] = sum(1 for x in todate if x['cc'] == 'PK' and x['st'] == 'Punjab')
    row['todate_INPunjab_15Oct_1Nov'] = sum(1 for x in todate if x['cc'] == 'IN' and x['st'] == 'Punjab')
    for side, cond in (('PK', lambda x: x['cc'] == 'PK' and x['st'] == 'Punjab'), ('IN', lambda x: x['cc'] == 'IN' and x['st'] == 'Punjab')):
        s = [x for x in fy if cond(x)]  # 1 Oct - 30 Nov
        c = collections.Counter(fortnight(x['date']) for x in s)
        for k in FN: row[f'{side}_{k}'] = c.get(k, 0)
        row[f'{side}_peak_fortnight'] = max(FN, key=lambda k: c.get(k, 0)) if s else ''
        row[f'{side}_median_date'] = (dt.date(y, 10, 1) + dt.timedelta(st.median((x['date'] - dt.date(y, 10, 1)).days for x in s))).strftime('%d %b') if s else ''
        row[f'{side}_share_Nov_pct'] = round(100 * sum(1 for x in s if x['date'].month == 11) / len(s)) if s else None
    rows.append(row)
with open(os.path.join(H, 'out', 'firms_season_counts.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('year | 100km PK | 100km IN | box PK (PB) | box IN (PB/HR/all) | PK med date, peak, %Nov | IN med date, peak, %Nov')
for r in rows:
    print(f"{r['year']}{'*' if r['partial'] else ''} | {r['r100_PK']} | {r['r100_IN']} | {r['box_PK_all']} ({r['box_PK_Punjab']}) | {r['box_IN_Punjab']}/{r['box_IN_Haryana']}/{r['box_IN_all']} | {r['PK_median_date']}, {r['PK_peak_fortnight']}, {r['PK_share_Nov_pct']} | {r['IN_median_date']}, {r['IN_peak_fortnight']}, {r['IN_share_Nov_pct']}")
print('\nfortnight counts, 1 Oct-30 Nov, Punjab only:  PK: Oct1-15/Oct16-31/Nov1-15/Nov16-30 | IN: same')
for r in rows:
    print(r['year'], '|', '/'.join(str(r[f'PK_{k}']) for k in FN), '|', '/'.join(str(r[f'IN_{k}']) for k in FN), '| to-date 15Oct-1Nov PK', r['todate_PKPunjab_15Oct_1Nov'], 'IN', r['todate_INPunjab_15Oct_1Nov'])
