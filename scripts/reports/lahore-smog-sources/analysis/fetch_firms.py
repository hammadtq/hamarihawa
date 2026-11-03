# Fetch NASA FIRMS MODIS detections (area API) for the Punjab box, 1 Oct - 30 Nov each year.
import os, sys, time, datetime as dt, urllib.request
H = sys.argv[1]
KEY = open(os.path.expanduser('~/.config/hamarihawa/firms_key')).read().strip()
BOX = '72.0,29.5,76.9,32.6'
out = os.path.join(H, 'raw', 'firms')
def get(src, start, days, fn):
    if os.path.exists(fn) and os.path.getsize(fn) > 0:
        return
    url = f'https://firms.modaps.eosdis.nasa.gov/api/area/csv/{KEY}/{src}/{BOX}/{days}/{start}'
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                body = r.read()
            if not body.startswith(b'latitude'):
                raise RuntimeError('unexpected body: ' + body[:80].decode('latin1'))
            open(fn, 'wb').write(body)
            print('ok', os.path.basename(fn), body.count(b'\n') - 1, flush=True)
            return
        except Exception as e:
            msg = str(e).replace(KEY, '<KEY>')
            print('retry', os.path.basename(fn), msg, flush=True)
            time.sleep(10 * (attempt + 1))
    print('FAILED', fn, flush=True)
YEARS = [int(a) for a in " ".join(sys.argv[2:]).split()] or range(2001, 2027)
for year in YEARS:
    src = 'MODIS_SP' if year <= 2025 else 'MODIS_NRT'
    d = dt.date(year, 10, 1)
    end = dt.date(year, 11, 30) if year <= 2025 else dt.date(2026, 11, 2)
    while d <= end:
        days = min(5, (end - d).days + 1)
        fn = os.path.join(out, f'{src}_{d.isoformat()}_{days}d.csv')
        get(src, d.isoformat(), days, fn)
        time.sleep(1.5)
        d += dt.timedelta(days=days)
