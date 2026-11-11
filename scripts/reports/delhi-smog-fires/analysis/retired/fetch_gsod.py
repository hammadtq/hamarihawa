# Fetch NOAA GSOD daily files (visibility) for Delhi and nearby stations, 1973-2026.
import os, sys, time, urllib.request, urllib.error
H = sys.argv[1]
STATIONS = {'42182099999': 'New Delhi Safdarjung', '42181099999': 'New Delhi Palam (IGI)',
            '42131099999': 'Hisar', '42101099999': 'Patiala', '42099099999': 'Ludhiana', '42071099999': 'Amritsar'}
out = os.path.join(H, 'raw', 'gsod')
for sid in STATIONS:
    for y in range(1973, 2027):
        fn = os.path.join(out, f'{sid}_{y}.csv')
        if os.path.exists(fn): continue
        url = f'https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{y}/{sid}.csv'
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=60) as r: body = r.read()
                open(fn, 'wb').write(body); print('ok', sid, y, body.count(b'\n') - 1, flush=True); break
            except urllib.error.HTTPError as e:
                if e.code == 404: open(fn, 'wb').write(b''); print('none', sid, y, flush=True); break
                time.sleep(5 * (attempt + 1))
            except Exception as e:
                print('retry', sid, y, str(e)[:100], flush=True); time.sleep(5 * (attempt + 1))
        time.sleep(0.3)
