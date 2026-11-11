# Checks behind the PM2.5 completeness rule (draft 3). Reads what fetch_openaq_hours.py stored; no network.
# 1. In the 2016-2022 hourly records: how many bins end on the hour and how many on the half hour, and the most bins in one station-day.
# 2. In the daily records from 2025: the largest observedCount, any expectedCount other than 24, and the spread of percentCoverage.
# 3. In the saved probe responses (raw/openaq_probe, fetched 11 Nov 2026): for one 2025 station-day, the mean of the 24 hour bins against the
#    /days value; for one 2019 station-day, 48 overlapping bins over 96 quarter-hour measurements; for 4 Nov 2020, 19 hourly aggregates between 05:00 and 23:30, 4 of them on the :00 grid
#    and 15 on the :30 grid. That shows the two grids can differ a lot for one day; it does NOT show that the day had only 4 hours of measurements
#    (the probe holds no raw measurements for that date).
# Output: out/openaq_regime_check.json. python3 check_openaq_regime.py H
import json, glob, gzip, os, sys, collections, statistics as st
H = sys.argv[1]; R = {}
on = half = other = 0; per_day = collections.Counter(); exp = collections.Counter()
for fn in glob.glob(os.path.join(H, 'raw', 'openaq_hours', 'hours_*.json')):
    s = json.load(open(fn))
    for frm, to, v, n, e in s['rows']:
        mm = to[14:16]; on += mm == '00'; half += mm == '30'; other += mm not in ('00', '30'); per_day[(s['sensor'], frm[:10])] += 1; exp[e] += 1
R['hourly_records_2016_2022'] = dict(bins_ending_on_the_hour=on, bins_ending_on_the_half_hour=half, other=other, most_bins_in_one_station_day=max(per_day.values()),
                                     station_days_with_more_than_24_bins=sum(v > 24 for v in per_day.values()), station_days=len(per_day), expected_measurements_per_bin=dict(exp))
mx = 0; odd = 0; n = 0; cov = collections.Counter(); old_over = 0
for fn in glob.glob(os.path.join(H, 'raw', 'openaq_days_full', 'days_*.json.gz')):
    with gzip.open(fn, 'rt') as f: s = json.load(f)
    for r in s['results']:
        c = r['coverage']
        if r['period']['datetimeFrom']['local'][:10] < '2025-01-01': old_over += c['observedCount'] > 24; continue
        n += 1; mx = max(mx, c['observedCount']); odd += c['expectedCount'] != 24; cov[min(100, int(c['percentCoverage'] // 25 * 25))] += 1
R['daily_records_from_2025'] = dict(station_days=n, largest_observedCount=mx, expectedCount_not_24=odd, percentCoverage_by_quarter=dict(sorted(cov.items())))
R['daily_records_before_2025'] = dict(station_days_with_observedCount_above_24=old_over)
P = os.path.join(H, 'raw', 'openaq_probe')
def j(n): return json.load(open(os.path.join(P, n)))
if os.path.exists(os.path.join(P, 'hours_2025.json')):
    h = j('hours_2025.json')['results']; R['probe_2025_11_12_bawana'] = dict(hour_bins=len(h), all_end_on_the_hour=all(r['period']['datetimeTo']['local'][14:16] == '00' for r in h), mean_of_hour_bins=round(st.mean(r['value'] for r in h), 2))
    R['probe_2019_11_13_shadipur'] = dict(hour_bins=len(j('hours_14959_2019-11-13.json')['results']), quarter_hour_measurements=len(j('meas_14959_2019-11-13.json')['results']))
    b = j('hours_14959_2020-11-04.json')['results']; R['probe_2020_11_04_shadipur'] = dict(hour_bins=len(b), bins_ending_on_the_hour=sum(r['period']['datetimeTo']['local'][14:16] == '00' for r in b), bins_ending_on_the_half_hour=sum(r['period']['datetimeTo']['local'][14:16] == '30' for r in b),
                                         first_bin_start=min(r['period']['datetimeFrom']['local'] for r in b)[11:16], last_bin_end=max(r['period']['datetimeTo']['local'] for r in b)[11:16],
                                         note='Counts on two overlapping grids of hourly aggregates. Not a count of hours with measurements: the raw measurements for this date were not fetched.')
json.dump(R, open(os.path.join(H, 'out', 'openaq_regime_check.json'), 'w'), indent=1); print(json.dumps(R, indent=1))
