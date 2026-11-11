# Build one HTML page per day (satellite photo + that day's MODIS fire detections + city labels + Delhi PM2.5) for the smoke animation.
# The number printed on each frame is every MODIS detection in the study box (73.0-79.5E, 27.0-32.6N, both countries) dated that day in India time,
# day and night passes together; it is NOT the Punjab + Haryana count (data.json entry november_2025_frames gives both).
# Chrome headless then screenshots each page and ffmpeg joins them (see make_animation.sh). python3 make_frames.py H
import csv, json, os, sys, datetime as dt, collections
H = sys.argv[1]; SAT = os.path.join(H, 'raw', 'sat', 'truecolor'); OUT = os.path.join(H, 'frames'); os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
W, Hh = 1200, 1040; X0, X1, Y0, Y1 = 72.0, 79.5, 26.5, 33.0
px = lambda lon, lat: ((lon - X0) / (X1 - X0) * W, (Y1 - lat) / (Y1 - Y0) * Hh)
pm = {r['date']: float(r['median']) for r in csv.DictReader(open(os.path.join(H, 'out', 'pm25_daily.csv')))}
fires = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(H, 'out', 'firms_detections_classified.csv'))):
    if r['date'][5:7] == '11': fires[r['date']].append((float(r['lon']), float(r['lat'])))
B = json.load(open(os.path.join(HERE, 'inputs', 'borders.json')))
def border_paths():
    out = []
    for poly in B['PK']:
        ring = poly[0] if isinstance(poly[0][0], list) else poly
        seg = []
        for lon, lat in ring:
            if X0 - 0.5 <= lon <= X1 + 0.5 and Y0 - 0.5 <= lat <= Y1 + 0.5: seg.append(px(lon, lat))
            elif seg: out.append(seg); seg = []
        if seg: out.append(seg)
    return ''.join('<polyline points="' + ' '.join(f'{x:.0f},{y:.0f}' for x, y in s) + '" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="1.6" stroke-dasharray="7 5"/>' for s in out if len(s) > 1)
BORDER = border_paths()
CITIES = [('Delhi', 77.21, 28.61, 1), ('Lahore', 74.34, 31.55, 0), ('Amritsar', 74.87, 31.63, 0), ('Ludhiana', 75.86, 30.90, 0), ('Bathinda', 74.95, 30.21, 0), ('Chandigarh', 76.78, 30.73, 0), ('Hisar', 75.72, 29.15, 0), ('Jaipur', 75.79, 26.91, 0), ('Lucknow', 80.95, 26.85, 0), ('Multan', 71.47, 30.20, 0), ('Faisalabad', 73.08, 31.42, 0)]
def colour(v): return '#2e9e4f' if v <= 60 else '#e0a100' if v <= 120 else '#e8590c' if v <= 250 else '#b0121b'
for fn in sorted(os.listdir(SAT)):
    d = fn[:10]; D = dt.date.fromisoformat(d); v = pm.get(d); f = fires.get(d, [])
    dots = ''.join(f'<circle cx="{px(lo, la)[0]:.1f}" cy="{px(lo, la)[1]:.1f}" r="2.6" fill="#ff2a1a" stroke="#fff" stroke-width=".5"/>' for lo, la in f if X0 <= lo <= X1 and Y0 <= la <= Y1)
    labs = ''
    for n, lo, la, big in CITIES:
        if not (X0 < lo < X1): continue
        x, y = px(lo, la)
        labs += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{6 if big else 3.5}" fill="none" stroke="#fff" stroke-width="{2.5 if big else 1.5}"/><text x="{x + 10:.0f}" y="{y + 5:.0f}" font-size="{22 if big else 16}" font-weight="{700 if big else 500}" fill="#fff" stroke="#000" stroke-opacity=".55" stroke-width="3" paint-order="stroke">{n}</text>'
    pmbox = (f'<rect x="{W - 330}" y="20" width="310" height="92" rx="10" fill="#000" fill-opacity=".62"/><text x="{W - 314}" y="50" font-size="17" fill="#ddd">Delhi PM2.5 that day (µg/m³)</text>'
             + (f'<text x="{W - 314}" y="98" font-size="46" font-weight="700" fill="{colour(v)}" stroke="#fff" stroke-width=".6">{v:.0f}</text>' if v is not None else f'<text x="{W - 314}" y="92" font-size="26" fill="#bbb">no data</text>'))
    html = f'''<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#000}}svg{{position:absolute;left:0;top:0;font-family:Helvetica,Arial,sans-serif}}</style>
<img src="file://{os.path.join(SAT, fn)}" width="{W}" height="{Hh}"><svg width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}">{BORDER}{dots}{labs}
<rect x="20" y="20" width="330" height="92" rx="10" fill="#000" fill-opacity=".62"/><text x="36" y="62" font-size="36" font-weight="700" fill="#fff">{D.day} {D:%B %Y}</text>
<text x="36" y="96" font-size="17" fill="#ddd"><tspan fill="#ff5a4d">●</tspan> {len(f):,} MODIS fire detections, whole map area</text>{pmbox}
<text x="20" y="{Hh - 16}" font-size="14" fill="#fff" stroke="#000" stroke-opacity=".5" stroke-width="3" paint-order="stroke">NASA Worldview / GIBS: VIIRS (NOAA-20) true colour, early afternoon. Fires: NASA FIRMS MODIS. PM2.5: government monitors via OpenAQ. HamariHawa.</text></svg>'''
    open(os.path.join(OUT, d + '.html'), 'w').write(html)
print('pages', len(os.listdir(OUT)))
