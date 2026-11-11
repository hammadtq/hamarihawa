# Same as fetch_openaq.py but for carbon monoxide (CO) sensors at the same monitors. Units differ by sensor (ppb or µg/m³) and are stored.
# (CPCB's CAAQMS network: CPCB, DPCC, IMD, IITM, UPPCB, HSPCB stations). One file per sensor: [local date, daily mean, hours observed].
# Key: ~/.config/hamarihawa/openaq_key. Limits: 60 requests a minute.
import json, os, sys, time, urllib.request
H = sys.argv[1]
KEY = open(os.path.expanduser('~/.config/hamarihawa/openaq_key')).read().strip()
out = os.path.join(H, 'raw', 'openaq'); os.makedirs(out, exist_ok=True)
def get(url):
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers={'X-API-Key': KEY})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            print('retry', url.split('/v3/')[1][:60], str(e)[:80], flush=True); time.sleep(15 * (attempt + 1))
    raise SystemExit('failed ' + url)
locfn = os.path.join(out, 'locations_delhi_25km.json')
if not os.path.exists(locfn):
    json.dump(get('https://api.openaq.org/v3/locations?coordinates=28.61,77.21&radius=25000&parameters_id=2&limit=1000'), open(locfn, 'w'))
locs = [x for x in json.load(open(locfn))['results'] if x['isMonitor'] and x['provider']['name'] in ('CPCB', 'caaqm')]
for x in locs:
    for s in x['sensors']:
        if s['parameter']['name'] != 'co': continue
        fn = os.path.join(out, f"co_{x['id']}_{s['id']}.json")
        if os.path.exists(fn): continue
        rows = []; page = 1
        while True:
            d = get(f"https://api.openaq.org/v3/sensors/{s['id']}/days?limit=1000&page={page}")
            for r in d['results']:
                rows.append([r['period']['datetimeFrom']['local'][:10], r['value'], r['coverage']['observedCount']])
            time.sleep(1.1)
            if len(d['results']) < 1000: break
            page += 1
        json.dump(dict(location=x['id'], name=x['name'], sensor=s['id'], units=s['parameter']['units'], provider=x['provider']['name'], owner=(x.get('owner') or {}).get('name'),
                       lat=x['coordinates']['latitude'], lon=x['coordinates']['longitude'], rows=rows), open(fn, 'w'))
        print('ok', x['id'], x['name'][:40], s['id'], len(rows), rows[0][0] if rows else '', rows[-1][0] if rows else '', flush=True)
