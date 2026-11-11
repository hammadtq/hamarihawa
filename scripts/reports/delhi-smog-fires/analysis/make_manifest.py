# Write MANIFEST.json: for every input folder and extract, the file count, total bytes and a SHA-256 over the sorted file hashes, with where each
# input came from and whether it can be refetched without a key. python3 make_manifest.py H
import hashlib, json, os, sys, platform, time
H = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
def tree(p):
    hs = []; n = 0; size = 0
    for root, _, files in os.walk(p):
        for f in sorted(files):
            if f.startswith('.'): continue
            b = open(os.path.join(root, f), 'rb').read(); hs.append(hashlib.sha256(b).hexdigest() + ' ' + os.path.relpath(os.path.join(root, f), p)); n += 1; size += len(b)
    return dict(files=n, bytes=size, sha256_of_file_hashes=hashlib.sha256('\n'.join(sorted(hs)).encode()).hexdigest())
SRC = {
 'raw/openaq': ('OpenAQ API v3 /locations and /sensors/{id}/days, PM2.5 and CO, stripped to [date, value, observedCount] (draft 1 extract; kept for the station list and CO)', 'fetch_openaq.py, fetch_openaq_co.py', 'OpenAQ key'),
 'raw/openaq_hours': ('OpenAQ API v3 /sensors/{id}/hours, 1 Oct-31 Jan of seasons 2016-17 to 2022-23, as [from, to, value, observedCount, expectedCount]', 'fetch_openaq_hours.py', 'OpenAQ key'),
 'raw/openaq_days_full': ('OpenAQ API v3 /sensors/{id}/days, complete records (period, coverage, summary, flags), gzip', 'fetch_openaq_hours.py', 'OpenAQ key'),
 'raw/openaq_probe': ('OpenAQ API v3 complete responses for three sample station-days (days, hours, measurements)', 'see check_openaq_regime.py header', 'OpenAQ key'),
 'raw/firms': ('NASA FIRMS area API, MODIS_SP (2001-2025) and MODIS_NRT (2026), box 73.0,27.0,79.5,32.6, 1 Oct-30 Nov', 'fetch_firms.py', 'FIRMS map key'),
 'raw/era5': ('Open-Meteo archive API, ERA5, 28.61N 77.21E, hourly, 1980-2026, Asia/Kolkata', 'fetch_era5.py', 'no key'),
 'raw/windgrid': ('Open-Meteo archive API, ERA5 100 m wind, 0.5 degree grid 27.5-33N 72.5-78.5E, UTC', 'fetch_wind_grid.py', 'no key'),
 'raw/windouter': ('Open-Meteo archive API, ERA5 100 m wind, 1 degree grid 24-35N 69-83E, UTC', 'fetch_wind_outer.py', 'no key'),
 'raw/sat': ('NASA GIBS WMS image tiles: VIIRS NOAA-20 true colour and MODIS MAIAC AOD with its colour map (NOT in the ZIP: 16 MB; only the exploratory AOD check and the animation need them)', 'fetch_sat.py', 'no key'),
}
M = dict(made=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), python=platform.python_version(), platform=platform.platform(), retrieval_date='2026-11-11 (day summaries: 2026-11-09)', random_seeds=dict(day_resampling=11, season_resampling=12),
         raw={k: dict(source=v[0], fetched_by=v[1], needs=v[2], **(tree(os.path.join(H, k)) if os.path.isdir(os.path.join(H, k)) else dict(files=0))) for k, v in SRC.items()},
         inputs=tree(os.path.join(HERE, 'inputs')), extracts=tree(os.path.join(HERE, 'data')),
         boundaries=json.load(open(os.path.join(HERE, 'inputs', 'in_states_box.json')))['meta'],
         offline='Everything from pm25_daily.py onward runs offline from raw/ and inputs/ (see README). Only the fetch_*.py scripts and make_review_pdf.py (Google Chrome) need anything else.')
json.dump(M, open(os.path.join(HERE, 'MANIFEST.json'), 'w'), indent=1); print({k: v.get('files') for k, v in M['raw'].items()})
