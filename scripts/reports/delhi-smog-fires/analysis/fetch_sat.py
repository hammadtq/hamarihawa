# Fetch NASA GIBS daily images for the Punjab-Haryana-Delhi box (72.0-79.5E, 26.5-33.0N):
#  truecolor: VIIRS NOAA-20 corrected reflectance (early-afternoon pass), 1200x1040 JPEG, for the animation months
#  aod: MODIS Terra+Aqua MAIAC aerosol optical depth, 150x130 PNG (0.05 deg), 15 Oct-30 Nov of every study year
import os, sys, time, datetime as dt, urllib.request, concurrent.futures as cf
H = sys.argv[1]; out = os.path.join(H, 'raw', 'sat')
WMS = 'https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES=&CRS=EPSG:4326&BBOX=26.5,72,33,79.5'
AOD = 'MODIS_Combined_MAIAC_L2G_AerosolOpticalDepth'
jobs = []
def span(a, b):
    while a <= b: yield a; a += dt.timedelta(1)
for a, b in ((dt.date(2025, 11, 1), dt.date(2025, 11, 30)), (dt.date(2021, 11, 1), dt.date(2021, 11, 30)), (dt.date(2026, 11, 1), dt.date(2026, 11, 10))):
    for d in span(a, b):
        jobs.append((f'{WMS}&FORMAT=image/jpeg&LAYERS=VIIRS_NOAA20_CorrectedReflectance_TrueColor&WIDTH=1200&HEIGHT=1040&TIME={d}', os.path.join(out, 'truecolor', f'{d}.jpg'), b'\xff\xd8'))
for y in (2016, 2017, 2018, 2019, 2020, 2021, 2025, 2026):
    for d in span(dt.date(y, 10, 15), min(dt.date(y, 11, 30), dt.date(2026, 11, 9))):
        jobs.append((f'{WMS}&FORMAT=image/png&LAYERS={AOD}&WIDTH=150&HEIGHT=130&TIME={d}', os.path.join(out, 'aod', f'{d}.png'), b'\x89PNG'))
for sub in ('truecolor', 'aod'): os.makedirs(os.path.join(out, sub), exist_ok=True)
cm = os.path.join(out, f'cmap_{AOD}.xml')
if not os.path.exists(cm): open(cm, 'wb').write(urllib.request.urlopen('https://gibs.earthdata.nasa.gov/colormaps/v1.3/MODIS_VIIRS_AOD.xml', timeout=60).read())
def get(job):
    url, fn, magic = job
    if os.path.exists(fn) and os.path.getsize(fn) > 0: return
    for a in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r: b = r.read()
            if not b.startswith(magic): raise RuntimeError(b[:150])
            open(fn, 'wb').write(b); return
        except Exception as e:
            print('retry', os.path.basename(fn), str(e)[:120], flush=True); time.sleep(5 * (a + 1))
    print('FAILED', fn, flush=True)
with cf.ThreadPoolExecutor(4) as ex: list(ex.map(get, jobs))
print('done', len(jobs))
