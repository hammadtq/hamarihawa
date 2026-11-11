# Delhi daily PM2.5 from OpenAQ (CPCB CAAQMS network), draft 3. One completeness rule for every year:
#   a station-day counts if at least 18 of its 24 clock-hour bins (bins ending on the hour, local time) hold data,
#   and its value is above 0 and no higher than 1,500 µg/m³.
# Why two inputs. Before 2023 OpenAQ's hourly records overlap: there is an hourly aggregate ending on :00 and another ending on :30, so a
# complete day has 48 and the /days "observedCount" cannot be read as hours. For those years this script reads the hourly records themselves
# (raw/openaq_hours, 1 Oct-31 Jan of seasons 2016-17 to 2022-23) and keeps ONE regular, non-overlapping grid: the aggregates ending on the hour
# in India time. This is a conservative choice of grid. It leaves out the offset (:30) aggregates, which can hold observations for hours the
# :00 grid lacks, so a station-day rejected here is not necessarily a day with fewer than 18 hours of measurements.
# Sensitivity: `python3 pm25_daily.py H 30` uses the :30 grid instead and writes pm25_daily_alt30.csv etc. (see sensitivity_hourly_grid.py).
# From 2025 the hourly bins do not overlap (checked by check_openaq_regime.py: expectedCount 24, observedCount never above 24, and the mean of
# the hour bins equals the /days value), so the /days records (raw/openaq_days_full) are used with observedCount >= 18.
# Months of 2016-2022 outside October-January are NOT in the series: their hourly records were not fetched and the report does not use them.
# City value = median across stations, days with >= 5 stations. Output: out/pm25_daily.csv, pm25_monthly.csv, pm25_station_days.csv
import json, glob, gzip, os, sys, csv, collections, statistics as st
H = sys.argv[1]; GRID = sys.argv[2] if len(sys.argv) > 2 else '00'; SUF = '' if GRID == '00' else '_alt' + GRID; day = collections.defaultdict(dict); dropped = collections.Counter(); sd = []
hf = glob.glob(os.path.join(H, 'raw', 'openaq_hours', 'hours_*.json')); df = glob.glob(os.path.join(H, 'raw', 'openaq_days_full', 'days_*.json.gz'))
if not hf or not df: sys.exit('missing raw/openaq_hours or raw/openaq_days_full (run fetch_openaq_hours.py)')
for fn in hf:
    s = json.load(open(fn)); by = collections.defaultdict(dict)
    for frm, to, v, n, exp in s['rows']:
        if to[14:16] != GRID: continue                       # keep one regular grid (default: aggregates ending on the hour); drop the overlapping set
        if v is None or v <= 0 or v > 1500: dropped['hour value'] += 1; continue
        by[frm[:10]][to[11:13]] = v                          # local date of the hour's start, hour of its end
    for d, hrs in by.items():
        if not (f"{s['season']}-10-01" <= d <= f"{s['season'] + 1}-01-31"): continue
        if len(hrs) < 18: dropped['station-day <18 clock hours (hourly records)'] += 1; continue
        v = st.mean(hrs.values()); day[d].setdefault(s['location'], []).append(v); sd.append((d, s['location'], s['sensor'], round(v, 1), len(hrs), 'hours'))
over24 = 0
for fn in df:
    with gzip.open(fn, 'rt') as f: s = json.load(f)
    for r in s['results']:
        d = r['period']['datetimeFrom']['local'][:10]; c = r['coverage']; v = r['value']
        if d < '2025-01-01': continue
        if c['observedCount'] > 24 or c['expectedCount'] != 24: over24 += 1; continue
        if v is None or v <= 0 or v > 1500: dropped['day value'] += 1; continue
        if c['observedCount'] < 18: dropped['station-day <18 hours (daily records)'] += 1; continue
        day[d].setdefault(s['location'], []).append(v); sd.append((d, s['location'], s['sensor'], round(v, 1), c['observedCount'], 'days'))
if over24: sys.exit(f'{over24} station-days from 2025 on have more than 24 hourly bins: the daily records cannot be used as they are')
rows = []
for d in sorted(day):
    vals = [st.mean(v) for v in day[d].values()]
    if len(vals) < 5: dropped['day <5 stations'] += 1; continue
    rows.append((d, round(st.median(vals), 1), round(st.mean(vals), 1), len(vals), 'hours' if d < '2025-01-01' else 'days'))
with open(os.path.join(H, 'out', f'pm25_daily{SUF}.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['date', 'median', 'mean', 'stations', 'input']); w.writerows(rows)
with open(os.path.join(H, 'out', f'pm25_station_days{SUF}.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['date', 'location', 'sensor', 'value', 'clock_hours', 'input']); w.writerows(sorted(sd))
mon = collections.defaultdict(list)
for d, med, mean, n, src in rows: mon[d[:7]].append((med, n))
with open(os.path.join(H, 'out', f'pm25_monthly{SUF}.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['month', 'mean_of_daily_median', 'days', 'median_stations'])
    for m in sorted(mon): w.writerow([m, round(st.mean(x[0] for x in mon[m]), 1), len(mon[m]), st.median(x[1] for x in mon[m])])
print('dropped', dict(dropped), 'days kept', len(rows), rows[0][0], rows[-1][0])
for m in sorted(mon): print(m, '|', round(st.mean(x[0] for x in mon[m])), '|', len(mon[m]), '|', st.median(x[1] for x in mon[m]))
