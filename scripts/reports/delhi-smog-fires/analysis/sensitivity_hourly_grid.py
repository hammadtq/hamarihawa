# Sensitivity of the historical PM2.5 series to the choice of hourly grid (draft 4, asked for by the external review of draft 3).
# The main series keeps the hourly aggregates ending on :00 (India time). This reruns the chain with the other regular grid, the aggregates
# ending on :30, leaving the 2025-26 daily-record series, the upstream index and the matching rule unchanged. The :30 grid shifts the historical
# averaging window by half an hour (a "day" runs 00:30-00:30) while ventilation stays on the calendar day, so this is a diagnostic, not a
# better or "corrected" series. Categories are computed twice: thirds re-estimated on the larger sample, and the main run's cut-offs kept.
# Output: out/sensitivity_hourly_grid.json (+ pm25_daily_alt30.csv, match_*_alt30.csv, contrast_alt30*.json). python3 sensitivity_hourly_grid.py H
import csv, json, os, subprocess, sys, collections, statistics as st
H = sys.argv[1]; A = os.path.dirname(os.path.abspath(__file__)); O = lambda n: os.path.join(H, 'out', n)
def run(*a): subprocess.run([sys.executable, os.path.join(A, a[0])] + list(a[1:]), check=True, stdout=subprocess.DEVNULL)
main = json.load(open(O('contrast.json'))); cut = f"{main['cut_few_max']},{main['cut_many_above']}"
run('pm25_daily.py', H, '30'); run('match_weather.py', H, '_alt30'); run('contrast.py', H, '_alt30'); run('contrast.py', H, '_alt30', cut)
def hist(fn): return sum(1 for r in csv.DictReader(open(O(fn))) if r['input'] == 'hours')
def summ(c, fn):
    rows = list(csv.DictReader(open(O(fn)))); B = [r for r in rows if r['excess'] != '']; q1, q2 = c['cut_few_max'], c['cut_many_above']
    g = lambda r: 'few' if int(r['upwind']) <= q1 else 'many' if int(r['upwind']) > q2 else 'some'
    return dict(days_with_pm_and_index=c['days'], matched_days=c['matched_days']['days'], matched_days_by_season=c['matched_days']['by_year'], cut_few_max=q1, cut_many_above=q2,
                median_pm_by_period={p: {k: dict(median=round(st.median(float(r['pm']) for r in rows if r['part'] == p and g(r) == k), 1), days=sum(1 for r in rows if r['part'] == p and g(r) == k)) for k in ('few', 'some', 'many')} for p in ('15-31 Oct', '1-15 Nov', '16-30 Nov')},
                mean_difference_from_matched_winter={k: dict(mean=round(st.mean(float(r['excess']) for r in B if g(r) == k), 2), days=sum(1 for r in B if g(r) == k)) for k in ('few', 'some', 'many')},
                exploratory_all_minus_few_pct_of_pm=(c['exploratory_contrast']['main'] or {}).get('all_minus_few_pct_of_pm'))
R = dict(what='Historical (2016-2022) city days built from the hourly aggregates ending on :00 (main) or on :30 (alternative). Everything else is unchanged.',
         caution='The :30 series shifts the historical averaging window by half an hour and is a diagnostic only. Neither grid was chosen for its results; :00 stays the main series because it is the clock-hour grid the 2025-26 records use.',
         historical_city_days=dict(main_00=hist('pm25_daily.csv'), alternative_30=hist('pm25_daily_alt30.csv')),
         main_00=summ(main, 'answer_daily.csv'),
         alternative_30_thirds_re_estimated=summ(json.load(open(O('contrast_alt30.json'))), 'answer_daily_alt30.csv'),
         alternative_30_main_cutoffs_kept=summ(json.load(open(O('contrast_alt30_fixedcuts.json'))), 'answer_daily_alt30_fixedcuts.csv'))
json.dump(R, open(O('sensitivity_hourly_grid.json'), 'w'), indent=1); print(json.dumps(R, indent=1))
