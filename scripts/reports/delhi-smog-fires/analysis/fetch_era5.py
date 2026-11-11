# Fetch ERA5 hourly boundary-layer height and 10 m / 100 m wind for central Delhi (28.61N 77.21E) from the Open-Meteo archive.
import os, sys, time, urllib.request
H = sys.argv[1]
out = os.path.join(H, 'raw', 'era5')
END = {2026: '2026-11-05'}  # ERA5 on Open-Meteo lags about five days
for y in range(1980, 2027):
    fn = os.path.join(out, f'era5_delhi_{y}.json')
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        continue
    url = ('https://archive-api.open-meteo.com/v1/archive?latitude=28.61&longitude=77.21'
           f'&start_date={y}-01-01&end_date={END.get(y, f"{y}-12-31")}'
           '&hourly=boundary_layer_height,wind_speed_10m,wind_direction_10m,wind_speed_100m,wind_direction_100m'
           '&wind_speed_unit=ms&models=era5&timezone=Asia%2FKolkata')
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
            print('retry', y, str(e)[:200], flush=True)
            time.sleep(30 * (attempt + 1))
    time.sleep(10)
