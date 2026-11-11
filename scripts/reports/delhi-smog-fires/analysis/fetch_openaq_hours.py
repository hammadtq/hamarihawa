# Refetch what the completeness rule needs (draft 3). Two things, both from OpenAQ v3 with the key in ~/.config/hamarihawa/openaq_key:
# 1. raw/openaq_hours/hours_<sensor>_<season>.json: the HOURLY records of every PM2.5 sensor for 1 Oct-31 Jan of seasons 2016-17 to 2022-23,
#    as [period from (local), period to (local), value, observedCount, expectedCount]. Before 2023 OpenAQ returns overlapping hourly bins
#    (ending on :00 and on :30), so /days observedCount runs to 48 and cannot be read as hours. pm25_daily.py keeps only bins ending on the hour.
# 2. raw/openaq_days_full/days_<location>_<sensor>.json.gz: the /days records again with the complete period, coverage, summary and flag objects.
# Limits: 60 requests a minute, 2,000 an hour: about one request a second. python3 fetch_openaq_hours.py H
import json, glob, gzip, os, sys, time, urllib.request, urllib.error
H = sys.argv[1]; KEY = open(os.path.expanduser('~/.config/hamarihawa/openaq_key')).read().strip()
OH = os.path.join(H, 'raw', 'openaq_hours'); OD = os.path.join(H, 'raw', 'openaq_days_full'); os.makedirs(OH, exist_ok=True); os.makedirs(OD, exist_ok=True)
def get(path):
    for a in range(10):
        try:
            with urllib.request.urlopen(urllib.request.Request('https://api.openaq.org/v3/' + path, headers={'X-API-Key': KEY}), timeout=180) as r:
                d = json.load(r); time.sleep(1.05); return d
        except urllib.error.HTTPError as e:
            print('http', e.code, path[:70], flush=True); time.sleep(70 if e.code == 429 else 20 * (a + 1))
        except Exception as e:
            print('retry', path[:70], str(e)[:80], flush=True); time.sleep(20 * (a + 1))
    raise SystemExit('failed ' + path)
sensors = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(H, 'raw', 'openaq', 'days_*.json')))]
for s in sensors:
    for y in range(2016, 2023):
        a, b = f'{y}-10-01', f'{y + 1}-02-01'
        if not any(a <= d < b for d, v, n in s['rows']): continue
        fn = os.path.join(OH, f"hours_{s['sensor']}_{y}.json")
        if os.path.exists(fn): continue
        rows = []; page = 1
        while True:
            d = get(f"sensors/{s['sensor']}/hours?datetime_from={y}-09-30T18:30:00Z&datetime_to={y + 1}-01-31T18:30:00Z&limit=1000&page={page}")
            for r in d['results']:
                rows.append([r['period']['datetimeFrom']['local'], r['period']['datetimeTo']['local'], r['value'], r['coverage']['observedCount'], r['coverage']['expectedCount']])
            if len(d['results']) < 1000: break
            page += 1
        json.dump(dict(location=s['location'], name=s['name'], sensor=s['sensor'], season=y, fetched=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), rows=rows), open(fn, 'w'))
        print('hours', s['sensor'], y, len(rows), flush=True)
for s in sensors:
    fn = os.path.join(OD, f"days_{s['location']}_{s['sensor']}.json.gz")
    if os.path.exists(fn): continue
    res = []; page = 1
    while True:
        d = get(f"sensors/{s['sensor']}/days?limit=1000&page={page}"); res += d['results']
        if len(d['results']) < 1000: break
        page += 1
    with gzip.open(fn, 'wt') as f: json.dump(dict(location=s['location'], name=s['name'], sensor=s['sensor'], lat=s['lat'], lon=s['lon'], provider=s['provider'], owner=s['owner'],
                                                  fetched=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), results=res), f)
    print('days', s['sensor'], len(res), flush=True)
print('DONE', flush=True)
