# Fetch ERA5 hourly boundary-layer height and 10 m wind for central Lahore from Open-Meteo archive.
import os, sys, time, urllib.request
H = sys.argv[1]
out = os.path.join(H, 'raw', 'era5')
for y0 in range(1980, 2026):
    y1 = y0
    fn = os.path.join(out, f'era5_lahore_{y0}_{y1}.json')
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        continue
    url = ('https://archive-api.open-meteo.com/v1/archive?latitude=31.55&longitude=74.34'
           f'&start_date={y0}-01-01&end_date={y1}-12-31&hourly=boundary_layer_height,wind_speed_10m'
           '&wind_speed_unit=ms&models=era5&timezone=Asia%2FKarachi')
    for attempt in range(10):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                body = r.read()
            if b'"hourly"' not in body:
                raise RuntimeError(body[:200])
            open(fn, 'wb').write(body)
            print('ok', fn, len(body), flush=True)
            break
        except Exception as e:
            print('retry', y0, str(e)[:200], flush=True)
            time.sleep(30 * (attempt + 1))
    time.sleep(10)
