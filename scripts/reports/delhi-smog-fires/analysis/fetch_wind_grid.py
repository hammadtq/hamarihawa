# ERA5 100 m wind (speed km/h, direction) on a 0.5 degree grid, 27.5-33.0N, 72.5-78.5E, hourly UTC, 12 Oct-30 Nov of each study year
# (2026: to 5 Nov), from the Open-Meteo archive. One file per year and grid row.
import json, os, sys, time, urllib.request
H = sys.argv[1]; out = os.path.join(H, 'raw', 'windgrid'); os.makedirs(out, exist_ok=True)
LATS = [27.5 + 0.5 * i for i in range(12)]; LONS = [72.5 + 0.5 * j for j in range(13)]
for y in (2016, 2017, 2018, 2019, 2020, 2021, 2025, 2026):
    end = '2026-11-05' if y == 2026 else f'{y}-11-30'
    for la in LATS:
        fn = os.path.join(out, f'{y}_{la}.json')
        if os.path.exists(fn): continue
        url = ('https://archive-api.open-meteo.com/v1/archive?latitude=' + ','.join(str(la) for _ in LONS) + '&longitude=' + ','.join(str(lo) for lo in LONS)
               + f'&start_date={y}-10-12&end_date={end}&hourly=wind_speed_100m,wind_direction_100m&models=era5&timezone=GMT')
        for a in range(8):
            try:
                with urllib.request.urlopen(url, timeout=300) as r: d = json.load(r)
                assert len(d) == len(LONS)
                json.dump(dict(lat=la, lons=LONS, time=d[0]['hourly']['time'], ws=[x['hourly']['wind_speed_100m'] for x in d], wd=[x['hourly']['wind_direction_100m'] for x in d]), open(fn, 'w'))
                print('ok', y, la, flush=True); break
            except Exception as e:
                print('retry', y, la, str(e)[:120], flush=True); time.sleep(20 * (a + 1))
        time.sleep(3)
