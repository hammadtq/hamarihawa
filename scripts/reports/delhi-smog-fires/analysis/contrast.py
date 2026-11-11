# Join the pieces and compute the comparisons the report describes (draft 3): Delhi PM2.5 by upstream fire-detection category, and an
# EXPLORATORY contrast against ventilation-matched December-January days. Nothing here is a source apportionment.
# Inputs (out/): pm25_daily.csv, traj_daily.csv, match_weather.csv, match_controls.csv, aod_daily.csv (optional); raw/openaq/co_*.json (optional).
# Output: out/answer_daily.csv and out/contrast.json. python3 contrast.py H
import csv, json, glob, os, sys, random, statistics as st, datetime as dt, collections
H = sys.argv[1]; SUF = sys.argv[2] if len(sys.argv) > 2 else ''; FIX = tuple(int(x) for x in sys.argv[3].split(',')) if len(sys.argv) > 3 else None   # sensitivity: suffix, fixed cut-offs
O = lambda n: os.path.join(H, 'out', n); rd = lambda n: list(csv.DictReader(open(O(n))))
pm = {r['date']: float(r['median']) for r in rd(f'pm25_daily{SUF}.csv')}
tr = {r['date']: r for r in rd('traj_daily.csv')}
mw = {r['date']: r for r in rd(f'match_weather{SUF}.csv') if r['control'] == 'dec_jan'}
aod = {r['date']: r for r in rd('aod_daily.csv')} if os.path.exists(O('aod_daily.csv')) else {}
co_day = collections.defaultdict(list)
for fn in glob.glob(os.path.join(H, 'raw', 'openaq', 'co_*.json')):
    s = json.load(open(fn)); v = [(d, x) for d, x, n in s['rows'] if x is not None and x > 0 and n >= 18 and d >= '2025-01-01']   # 2025 onward only: before 2023 the count is of overlapping bins, not hours (see pm25_daily.py), and CO was not refetched hourly
    if len(v) < 100: continue
    m = st.median(x for d, x in v)
    for d, x in v: co_day[d].append(x / m)
co = {d: st.median(v) for d, v in co_day.items() if len(v) >= 5}
DIWALI = {2016: '2016-10-30', 2017: '2017-10-19', 2018: '2018-11-07', 2019: '2019-10-27', 2020: '2020-11-14', 2021: '2021-11-04', 2022: '2022-10-24', 2025: '2025-10-20', 2026: '2026-11-08'}
rows = []; missing = collections.Counter()
for d, t in sorted(tr.items()):
    if d not in pm: missing['no PM2.5 value'] += 1; continue
    if t['valid'] != '1': missing['back-paths incomplete (no wind data)'] += 1; continue
    D = dt.date.fromisoformat(d); a = aod.get(d, {}); m = mw.get(d); dw = dt.date.fromisoformat(DIWALI[D.year])
    rows.append(dict(date=d, year=D.year, part=('15-31 Oct' if D.month == 10 else '1-15 Nov' if D.day <= 15 else '16-30 Nov'), pm=pm[d], upwind=int(t['upwind']), upwind_strict=int(t['upwind_strict']),
                     upwind_calendar=int(t['upwind_calendar']), paths_complete=int(t['paths_complete']), path_hours=float(t['path_hours']), hours_in_fire_box=float(t['hours_in_fire_box']),
                     diwali_0_2=int(0 <= (D - dw).days <= 2), matched_winter_pm=float(m['control_pm']) if m else '', excess=float(m['diff']) if m else '',
                     co_rel=round(co[d], 2) if d in co else '', aod_delhi=a.get('delhi', '') if a and float(a.get('delhi_cover') or 0) >= 0.3 else ''))
with open(O(f'answer_daily{SUF}{"_fixedcuts" if FIX else ""}.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def cuts(vals):
    if FIX: return FIX
    s = sorted(vals); return s[len(s) // 3], s[2 * len(s) // 3]
def grouper(key='upwind', within_year=False):
    if within_year:
        c = {y: cuts([r[key] for r in rows if r['year'] == y]) for y in {r['year'] for r in rows}}
        return lambda r: 'few' if r[key] <= c[r['year']][0] else 'many' if r[key] > c[r['year']][1] else 'some'
    q1, q2 = cuts([r[key] for r in rows]); return lambda r: 'few' if r[key] <= q1 else 'many' if r[key] > q2 else 'some'
G = grouper(); q1, q2 = cuts([r['upwind'] for r in rows]); B = [r for r in rows if r['excess'] != '']
def med(x): return dict(median=round(st.median(x)), days=len(x)) if x else dict(median=None, days=0)
def contrast(S, g):
    few = [r for r in S if g(r) == 'few']; many = [r for r in S if g(r) == 'many']; some = [r for r in S if g(r) == 'some']
    if len(few) < 5 or len(many) < 5: return None
    f = st.mean(r['excess'] for r in few); a = st.mean(r['excess'] for r in S); m = st.mean(r['excess'] for r in many)
    return dict(days=len(S), days_few=len(few), days_some=len(some), days_many=len(many), mean_pm=round(st.mean(r['pm'] for r in S), 1), mean_matched_winter=round(st.mean(r['matched_winter_pm'] for r in S), 1),
                excess_all=round(a, 1), excess_few=round(f, 1), excess_some=round(st.mean(r['excess'] for r in some), 1) if some else None, excess_many=round(m, 1),
                pm_few=round(st.mean(r['pm'] for r in few), 1), pm_some=round(st.mean(r['pm'] for r in some), 1) if some else None, pm_many=round(st.mean(r['pm'] for r in many), 1),
                winter_few=round(st.mean(r['matched_winter_pm'] for r in few), 1), winter_some=round(st.mean(r['matched_winter_pm'] for r in some), 1) if some else None, winter_many=round(st.mean(r['matched_winter_pm'] for r in many), 1),
                all_minus_few=round(a - f, 1), all_minus_few_pct_of_pm=round(100 * (a - f) / st.mean(r['pm'] for r in S), 1),
                many_minus_few=round(m - f, 1), many_minus_few_pct_of_pm=round(100 * (m - f) / st.mean(r['pm'] for r in many), 1))
out = dict(days=len(rows), days_by_year=dict(sorted(collections.Counter(r['year'] for r in rows).items())), not_used=dict(missing), last_day=rows[-1]['date'], cut_few_max=q1, cut_many_above=q2,
           four_complete_paths_days=sum(r['paths_complete'] == 4 for r in rows),
           where_pct={k: round(100 * sum(int(tr[r['date']][c]) for r in rows) / max(1, sum(r['upwind'] for r in rows))) for k, c in (('indian_punjab', 'upwind_punjab'), ('haryana', 'upwind_haryana'), ('pakistan', 'upwind_pk'))})
out['median_by_part'] = {p: {k: med([r['pm'] for r in rows if r['part'] == p and G(r) == k]) for k in ('few', 'some', 'many')} for p in ('15-31 Oct', '1-15 Nov', '16-30 Nov')}
gy = grouper(within_year=True)
if not FIX: out['median_by_part_within_year_thirds'] = {p: {k: med([r['pm'] for r in rows if r['part'] == p and gy(r) == k]) for k in ('few', 'some', 'many')} for p in ('15-31 Oct', '1-15 Nov', '16-30 Nov')}
out['matched_days'] = dict(days=len(B), by_year=dict(sorted(collections.Counter(r['year'] for r in B).items())))
V = {'main': contrast(B, G), 'timing_strict_no_detections_after_passage': contrast(B, grouper('upwind_strict')), 'timing_calendar_day_rule_of_draft_2': contrast(B, grouper('upwind_calendar')),
     'only_days_with_four_complete_paths': contrast([r for r in B if r['paths_complete'] == 4], G), 'thirds_within_each_year': contrast(B, gy),   # removed below in fixed-cut-off mode
     'without_diwali_day_and_two_days_after': contrast([r for r in B if not r['diwali_0_2']], G)}
if FIX:   # fixed cut-offs override every grouping, so variants defined by their own thirds would only repeat the main calculation under a wrong name
    for k in ('thirds_within_each_year', 'timing_strict_no_detections_after_passage', 'timing_calendar_day_rule_of_draft_2'): V.pop(k, None)
    out['fixed_cutoffs_note'] = 'Cut-offs fixed at few <= %d, many > %d. Within-year thirds and the alternative timing rules are omitted: they need their own thirds and do not apply here.' % FIX
out['exploratory_contrast'] = V
out['diwali_days_removed'] = sorted(r['date'] for r in B if r['diwali_0_2'])
out['matched_days_by_year_and_category'] = {str(y): {k: sum(1 for r in B if r['year'] == y and G(r) == k) for k in ('few', 'some', 'many')} for y in sorted({r['year'] for r in B})}
out['leave_one_season_out'] = {str(y): (lambda c: dict(all_minus_few_pct_of_pm=c['all_minus_few_pct_of_pm'], many_minus_few_pct_of_pm=c['many_minus_few_pct_of_pm']) if c else 'not reported: %d few-category and %d many-category days remain, below the chosen minimum of 5 in each' % (sum(1 for r in B if r['year'] != y and G(r) == 'few'), sum(1 for r in B if r['year'] != y and G(r) == 'many')))(contrast([r for r in B if r['year'] != y], G)) for y in sorted({r['year'] for r in B})}
out['by_year'] = {str(y): dict(days=len(s), mean_pm=round(st.mean(r['pm'] for r in s)), matched_winter=round(st.mean(r['matched_winter_pm'] for r in s)), excess=round(st.mean(r['excess'] for r in s)),
                               many_days=sum(G(r) == 'many' for r in s), excess_many=(lambda x: round(st.mean(x)) if x else None)([r['excess'] for r in s if G(r) == 'many']),
                               excess_not_many=(lambda x: round(st.mean(x)) if x else None)([r['excess'] for r in s if G(r) != 'many'])) for y in sorted({r['year'] for r in B}) for s in [[r for r in B if r['year'] == y]]}
def pct(v, q): v = sorted(v); return round(v[int(q * (len(v) - 1))], 1)
random.seed(11); day_bs = [c for c in (contrast(random.choices(B, k=len(B)), G) for _ in range(4000)) if c]
years = sorted({r['year'] for r in B}); random.seed(12); yr_bs = []
for _ in range(4000):
    S = [r for y in random.choices(years, k=len(years)) for r in B if r['year'] == y]; c = contrast(S, G)
    if c: yr_bs.append(c)
out['resampling'] = {name: dict({k: [pct([c[k] for c in bs], .05), pct([c[k] for c in bs], .95)] for k in ('all_minus_few_pct_of_pm', 'many_minus_few_pct_of_pm')}, resamples=len(bs), draws=4000, draws_rejected=4000 - len(bs))
                     for name, bs in (('days_resampled_independently', day_bs), ('whole_seasons_resampled', yr_bs))}
import itertools
combos = [contrast([r for y in cmb for r in B if r['year'] == y], G) for cmb in itertools.product(years, repeat=len(years))]
out['resampling']['note'] = ('Percentiles are over ACCEPTED draws only: a draw is rejected when the few or the many category has under 5 days. With %d seasons there are only %d ordered season combinations; %d fail that rule and the rest give %d distinct values. '
                             'This is limited cluster support, not a comprehensive uncertainty assessment.') % (len(years), len(combos), sum(c is None for c in combos), len({c['all_minus_few_pct_of_pm'] for c in combos if c}))
out['resampling']['season_combinations'] = dict(ordered_combinations=len(combos), rejected=sum(c is None for c in combos), distinct_values=len({c['all_minus_few_pct_of_pm'] for c in combos if c}))
pairs = [r for r in rd(f'match_controls{SUF}.csv') if r['control'] == 'dec_jan' and r['date'] in {x['date'] for x in B}]; use = collections.Counter(r['control_date'] for r in pairs)
out['control_reuse'] = dict(target_days=len(B), control_slots=len(pairs), distinct_control_days=len(use), control_days_used_more_than_once=sum(v > 1 for v in use.values()), most_uses_of_one_day=max(use.values()))
out['tracers_exploratory'] = {k: (lambda s: dict(co_relative_median=round(st.median(x['co_rel'] for x in s if x['co_rel'] != ''), 2) if any(x['co_rel'] != '' for x in s) else None, co_days=sum(x['co_rel'] != '' for x in s),
                                                 aod_delhi_median=round(st.median(float(x['aod_delhi']) for x in s if x['aod_delhi'] != ''), 2) if any(x['aod_delhi'] != '' for x in s) else None,
                                                 aod_days=sum(x['aod_delhi'] != '' for x in s)))([r for r in rows if G(r) == k]) for k in ('few', 'some', 'many')}
out['seeds'] = dict(days=11, seasons=12, resamples=4000)
json.dump(out, open(O(f'contrast{SUF}{"_fixedcuts" if FIX else ""}.json'), 'w'), indent=1)
print(json.dumps(out, indent=1)[:6000])
