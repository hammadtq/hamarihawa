# Outer wind domain for the back-paths (draft 3): ERA5 100 m wind on a 1 degree grid, 24-35N, 69-83E, hourly UTC, 12 Oct-30 Nov of each study
# year (2026: to 9 Nov; hours ERA5 has not published yet come back empty), from the Open-Meteo archive. The inner 0.5 degree grid
# (fetch_wind_grid.py) is used where it exists and this grid everywhere else, so that a path leaving the inner grid can still be followed.
# One file per year and grid row in raw/windouter/. Paced to stay under Open-Meteo's free hourly limit. python3 fetch_wind_outer.py H
import json, os, sys, time, urllib.request
H = sys.argv[1]; out = os.path.join(H, 'raw', 'windouter'); os.makedirs(out, exist_ok=True)
LATS = [24.0 + i for i in range(12)]; LONS = [69.0 + j for j in range(15)]
for y in (2016, 2017, 2018, 2019, 2020, 2021, 2025, 2026):
    end = '2026-11-09' if y == 2026 else f'{y}-11-30'
    for la in LATS:
        fn = os.path.join(out, f'{y}_{la}.json')
        if os.path.exists(fn): continue
        url = ('https://archive-api.open-meteo.com/v1/archive?latitude=' + ','.join(str(la) for _ in LONS) + '&longitude=' + ','.join(str(lo) for lo in LONS)
               + f'&start_date={y}-10-12&end_date={end}&hourly=wind_speed_100m,wind_direction_100m&models=era5&timezone=GMT')
        for a in range(8):
            try:
                with urllib.request.urlopen(url, timeout=300) as r: d = json.load(r)
                assert len(d) == len(LONS)
                json.dump(dict(lat=la, lons=LONS, grid_lat=[x['latitude'] for x in d], grid_lon=[x['longitude'] for x in d], url=url, fetched=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                               time=d[0]['hourly']['time'], ws=[x['hourly']['wind_speed_100m'] for x in d], wd=[x['hourly']['wind_direction_100m'] for x in d]), open(fn, 'w'))
                print('ok', y, la, flush=True); break
            except Exception as e:
                print('retry', y, la, str(e)[:160], flush=True); time.sleep(60 * (a + 1))
        time.sleep(40)
print('DONE', flush=True)
