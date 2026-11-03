# Fetch GIBS WMS PNGs (MERRA-2 monthly AOD; MODIS Terra/Aqua Deep Blue combined daily AOD) around Lahore.
import os, sys, time, datetime as dt, urllib.request, concurrent.futures as cf
H = sys.argv[1]; which = sys.argv[2]
out = os.path.join(H, 'raw', 'aod', which); os.makedirs(out, exist_ok=True)
WMS = 'https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES=&CRS=EPSG:4326&FORMAT=image/png'
jobs = []
if which == 'merra2':
    L = 'MERRA2_Total_Aerosol_Optical_Thickness_550nm_Extinction_Monthly'
    for y in range(1980, 2026):
        for m in (10, 11, 12):
            jobs.append((f'{WMS}&LAYERS={L}&BBOX=30.55,73.34,32.55,75.34&WIDTH=20&HEIGHT=20&TIME={y}-{m:02d}-01', os.path.join(out, f'{y}-{m:02d}.png')))
else:
    L = {'terra_db': 'MODIS_Terra_AOD_Deep_Blue_Combined', 'aqua_db': 'MODIS_Aqua_AOD_Deep_Blue_Combined'}[which]
    for y in range(2000, 2027):
        d = dt.date(y, 10, 15)
        while d <= min(dt.date(y, 11, 30), dt.date(2026, 11, 1)):
            # ~0.25 deg box (about 25 km half-width) centred on Lahore, ~2 km pixels
            jobs.append((f'{WMS}&LAYERS={L}&BBOX=31.33,74.08,31.77,74.60&WIDTH=26&HEIGHT=22&TIME={d.isoformat()}', os.path.join(out, f'{d.isoformat()}.png')))
            d += dt.timedelta(1)
def get(job):
    url, fn = job
    if os.path.exists(fn) and os.path.getsize(fn) > 0: return
    for a in range(5):
        try:
            with urllib.request.urlopen(url, timeout=60) as r: b = r.read()
            if b[:4] != b'\x89PNG': raise RuntimeError(b[:200])
            open(fn, 'wb').write(b); return
        except Exception as e:
            print('retry', fn, str(e)[:150], flush=True); time.sleep(5 * (a + 1))
    print('FAILED', fn, flush=True)
with cf.ThreadPoolExecutor(4) as ex: list(ex.map(get, jobs))
print('done', which, len(jobs))
