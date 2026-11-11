# Recompute every number in the report from data/*.csv and data/contrast.json (written by the analysis scripts) and write
# site/public/report/delhi-smog-fires/data.json: one entry per claim, with source, period, place, method, inputs and status .
# The article text is then filled from this file by render_article.py and the charts by charts.py. python3 build_evidence.py
import csv, json, os, glob, sys, statistics as st, datetime as dt, collections, calendar
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'data')
OUT = os.path.join(HERE, '..', '..', '..', '..', 'site', 'public', 'report', 'delhi-smog-fires', 'data.json')
def rd(n):
    p = os.path.join(D, n)
    if not os.path.exists(p): sys.exit('missing input ' + p)
    return list(csv.DictReader(open(p)))
date = dt.date.fromisoformat; E = []
def ev(id, claim, value, source, period, method, inputs, status='computed', place='Delhi (monitors within 25 km of 28.61N 77.21E)', url=''):
    E.append(dict(id=id, claim=claim, value=value, source=source, source_url=url, place=place, period=period, units_method=method, inputs=inputs, status=status))
PM = rd('pm25_daily.csv'); pm = {r['date']: (float(r['median']), int(r['stations'])) for r in PM}
S_PM = 'OpenAQ API v3, PM2.5 sensors of government reference monitors (CPCB CAAQMS network: DPCC, IMD, CPCB, IITM, UPPCB, HSPCB) within 25 km of central Delhi; hourly records for 2016-2022, daily records for 2025-2026; retrieved 11 Nov 2026'
U_PM = 'https://api.openaq.org/v3/ (sensors/{id}/hours, sensors/{id}/days); definitions: https://docs.openaq.org/resources/measurements'
M_PM = ('µg/m³. A station-day counts if it has at least 18 valid hourly aggregates on one regular non-overlapping grid (aggregates ending on the hour, India time) and 0 < value <= 1500. Historical daily counts can include overlapping hourly aggregates; choosing the :00 grid is a conservative restriction that excludes some available offset-hour (:30) observations (see entry sensitivity_hourly_grid). City value = median across stations, days with >= 5 stations. '
        'It is a median of monitors (some just outside Delhi), not a regulatory station average and not weighted by population. Period figures = mean of the daily city values that exist; missing days are not filled.')
I_PM = ['data/pm25_daily.csv', 'data/pm25_station_days.csv']
S_F = 'NASA FIRMS MODIS Collection 6.1 active-fire detections (Terra and Aqua): standard product to 2025, near real time for 2026; confidence >= 30, type 0 (presumed vegetation fire); box 73.0-79.5E, 27.0-32.6N'
U_F = 'https://firms.modaps.eosdis.nasa.gov/api/area/ ; fields: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html'
M_F = ('Counts are satellite detections of heat, by local (IST) date. They are not confirmed crop fires, not distinct fires, not burnt area and not emissions. State = geoBoundaries gbOpen IND ADM1 polygon (IND-ADM1-1811400). '
       'Terra and Aqua have drifted in orbit (NASA quality notice of 8 Jan 2026: effects significant from late 2024), and burning has moved later in the afternoon, so counts of different years are not sampled alike.')
S_E = 'ERA5 reanalysis (Copernicus Climate Change Service / ECMWF) via the Open-Meteo archive API, grid point nearest 28.61N 77.21E, hourly, local time (IST)'; U_E = 'https://archive-api.open-meteo.com/v1/archive'
def mean_between(a, b):
    v = [x[0] for d, x in pm.items() if a <= date(d) <= b]; return (round(st.mean(v)) if v else None, len(v))
# --- the PM2.5 series
days = sorted(pm); gap = max(zip(days, days[1:]), key=lambda p: (date(p[1]) - date(p[0])).days)
ev('pm_series', 'Days with a Delhi city value, first and last day, and the longest stretch with no eligible day', dict(days=len(days), first=days[0], last=days[-1],
   days_from_hourly_records_2016_2022=sum(r['input'] == 'hours' for r in PM), days_from_daily_records_2025_2026=sum(r['input'] == 'days' for r in PM), no_eligible_day_from=(date(gap[0]) + dt.timedelta(1)).isoformat(),
   no_eligible_day_to=(date(gap[1]) - dt.timedelta(1)).isoformat(), typical_stations_last_12_months=round(st.median(x[1] for d, x in pm.items() if '2025-11-01' <= d <= '2026-10-31')), typical_stations_in_november={y: round(st.median(x[1] for d, x in pm.items() if d[:7] == f'{y}-11')) for y in (2017, 2019, 2021, 2025)}), S_PM, '2016-2026',
   M_PM + ' The series covers 1 Oct-31 Jan of seasons 2016-17 to 2022-23 and every day from 2025. Other months of 2016-2022 were not processed. "No eligible day" means no day passed the rules; OpenAQ holds some incomplete station rows inside the gap.', I_PM, url=U_PM)
mon = collections.OrderedDict()
for ym in ['2025-11', '2025-12'] + [f'2026-{m:02d}' for m in range(1, 11)]:
    v = [x for d, x in pm.items() if d.startswith(ym)]; y, m = int(ym[:4]), int(ym[5:])
    mon[ym] = dict(mean=round(st.mean(x[0] for x in v)), days=len(v), days_in_month=calendar.monthrange(y, m)[1], typical_stations=round(st.median(x[1] for x in v)))
ev('pm_monthly_12', 'Monthly mean PM2.5, November 2025 to October 2026, with the number of days that have a city value', mon, S_PM, 'Nov 2025-Oct 2026', M_PM, I_PM, url=U_PM)
allv = [x[0] for d, x in pm.items() if '2025-11-01' <= d <= '2026-10-31']
ev('pm_12_months', 'Mean of the daily city values available in the 12 months, and days above benchmark values', dict(mean=round(st.mean(allv)), mean_exact=round(st.mean(allv), 2), days_with_value=len(allv), calendar_days=365,
   days_over_60=sum(v > 60 for v in allv), days_over_15=sum(v > 15 for v in allv), lowest_day=round(min(allv)), highest_day=round(max(allv)), times_annual_standard=round(st.mean(allv) / 40, 1)), S_PM, '1 Nov 2025-31 Oct 2026',
   M_PM + ' Not a complete 365-day annual mean. The 60 and 15 are 24-hour benchmark values (India NAAQS, WHO guideline) applied to a city median, not a regulatory compliance test.', I_PM, url=U_PM)
fs_ = [x[0] for d, x in pm.items() if '2026-02-01' <= d <= '2026-09-30']; ms_ = [x[0] for d, x in pm.items() if '2026-06-01' <= d <= '2026-09-30']
ev('pm_outside_autumn', 'Mean of daily city values February-September 2026 and June-September 2026', dict(feb_sep=round(st.mean(fs_)), feb_sep_days=len(fs_), jun_sep=round(st.mean(ms_)), jun_sep_days=len(ms_)), S_PM, 'Feb-Sep 2026',
   M_PM + ' February-September is outside the main autumn rice-residue burning weeks; it includes late winter and the April-May wheat-residue burning season.', I_PM, url=U_PM)
ev('standards', "India's National Ambient Air Quality Standards (2009) for PM2.5: 40 µg/m³ annual, 60 µg/m³ 24-hour. WHO 2021 guideline: 5 annual, 15 24-hour", dict(india_annual=40, india_24h=60, who_annual=5, who_24h=15),
   'Government of India, Press Information Bureau release of 23 Aug 2011 reproducing the NAAQS notified in November 2009 (Annexure I); WHO, Types of pollutants page (2021 guideline values)', 'n/a',
   'Quoted. The Indian annual standard is defined as the mean of at least 104 measurements a year at one site, and the 24-hour value must be met 98% of the time; they are used here only as benchmarks.', [], status='quoted; both pages read on 11 Nov 2026', place='India; global',
   url='https://www.pib.gov.in/newsite/PrintRelease.aspx?lang=2&reg=48&relid=74889 ; https://www.who.int/teams/environment-climate-change-and-health/air-quality-and-health/health-impacts/types-of-pollutants')
sw = collections.OrderedDict()
for y in range(2016, 2026):
    a = mean_between(dt.date(y, 10, 15), dt.date(y, 11, 30)); b = mean_between(dt.date(y, 12, 1), dt.date(y + 1, 1, 31))
    if a[1] >= 25 and b[1] >= 30: sw[f'{y}-{(y + 1) % 100:02d}'] = dict(oct15_nov30=a[0], oct15_nov30_days=a[1], dec_jan=b[0], dec_jan_days=b[1])
ev('season_vs_winter', 'Mean PM2.5 in 15 Oct-30 Nov and in the December-January after it, seasons with at least 25 and 30 days of data', dict(seasons=sw, dec_jan_min=min(v['dec_jan'] for v in sw.values()), dec_jan_max=max(v['dec_jan'] for v in sw.values()),
   n=len(sw)), S_PM, 'seasons 2016-17 to 2025-26', M_PM + ' December-January is after the main rice-residue burning weeks. The fire archive used here stops on 30 November, so this does not show that no crop residue burns in those months.', I_PM, url=U_PM)
# --- fires by year
fc = {r['year']: r for r in rd('firms_season_counts.csv')}; fy = collections.OrderedDict()
for y in range(2016, 2027):
    r = fc[str(y)]; v = [x[0] for d, x in pm.items() if d.startswith(f'{y}-11')]
    fy[str(y)] = dict(punjab_haryana=int(r['Punjab']) + int(r['Haryana']), punjab=int(r['Punjab']), haryana=int(r['Haryana']), terra=int(r['PbHr_Terra']), aqua=int(r['PbHr_Aqua']), partial=r['partial'],
                      delhi_nov_mean=round(st.mean(v)) if len(v) >= 15 else None, delhi_nov_days=len(v))
ev('fires_by_year', 'MODIS detections in Indian Punjab + Haryana, 1 Oct-30 Nov (2026: to 10 Nov), by satellite, with Delhi mean PM2.5 for November where at least 15 days have a value', fy, S_F + '; ' + S_PM, '2016-2026', M_F, ['data/firms_season_counts.csv', 'data/pm25_daily.csv'], url=U_F)
lo = min(v['punjab_haryana'] for k, v in fy.items() if '2016' <= k <= '2021'); hi = max(v['punjab_haryana'] for k, v in fy.items() if '2016' <= k <= '2021')
ev('fires_range', 'Range of yearly MODIS detections in Punjab + Haryana 2016-2021, and the 2021 and 2025 totals', dict(min_2016_2021=lo, max_2016_2021=hi, y2021=fy['2021']['punjab_haryana'], y2025=fy['2025']['punjab_haryana'],
   delhi_nov_2021=fy['2021']['delhi_nov_mean'], delhi_nov_2021_days=fy['2021']['delhi_nov_days'], delhi_nov_2025=fy['2025']['delhi_nov_mean'], delhi_nov_2025_days=fy['2025']['delhi_nov_days']), S_F + '; ' + S_PM, '1 Oct-30 Nov', M_F, ['data/firms_season_counts.csv', 'data/pm25_daily.csv'], url=U_F)
ds = os.path.join(HERE, 'inputs', 'day-summaries'); files = glob.glob(os.path.join(ds, '20*.json'))
if not files: sys.exit('missing inputs/day-summaries (needed for the NOAA-20 cross-check)')
ss = collections.defaultdict(lambda: [0, 0])
for f in files:
    d = json.load(open(f)); Dd = date(d['date'])
    if not (dt.date(Dd.year, 10, 1) <= Dd <= dt.date(Dd.year, 11, 10)): continue
    s = d['summary'].get('states', {})
    for k in ('IN|Punjab', 'IN|Haryana'): ss[Dd.year][0] += s.get(k, [0, 0, 0, 0])[2]
    ss[Dd.year][1] += 1
if any(v[1] != 41 for v in ss.values()): sys.exit('day summaries incomplete: ' + str({y: v[1] for y, v in ss.items()}))
ev('fires_second_sensor', 'Fire spots in Indian Punjab + Haryana seen by the VIIRS instrument on NOAA-20, 1 Oct-10 Nov', {str(y): v[0] for y, v in sorted(ss.items())}, 'HamariHawa daily fire summaries built from NASA FIRMS VIIRS data', '1 Oct-10 Nov, 2019-2026',
   'Fire spots (merged detections), not detections. The summaries store this count under the legacy key "snpp", which has carried NOAA-20 since the archive was rebuilt on 2 Nov 2026 (inputs/day-summaries/SCHEMA.md). NOAA-20 passes in the early afternoon like Aqua, '
   'so it shares the blind spot for late-afternoon burning: agreement with MODIS shows both detection series fell, not how much burning fell.', ['inputs/day-summaries/*.json'], place='Indian Punjab + Haryana', url='https://hamarihawa.org/api/day?d=YYYY-MM-DD ; https://hamarihawa.org/data/')
yrs = [str(y) for y in range(2016, 2026)]
b100 = sum(int(fc[y]['IN_0-100km']) for y in yrs); ball = sum(sum(int(fc[y][k]) for k in fc[y] if k.startswith('IN_')) for y in yrs)
ev('fire_distance', 'Median distance from central Delhi of Punjab and Haryana detections (range of the yearly medians, 2016-2025) and share of Indian detections in the box within 100 km of Delhi',
   dict(punjab_km_min=min(int(fc[y]['Punjab_median_km']) for y in yrs), punjab_km_max=max(int(fc[y]['Punjab_median_km']) for y in yrs), haryana_km_min=min(int(fc[y]['Haryana_median_km']) for y in yrs),
        haryana_km_max=max(int(fc[y]['Haryana_median_km']) for y in yrs), within_100km_pct=round(100 * b100 / ball, 1)), S_F, '1 Oct-30 Nov, 2016-2025', 'great-circle km from 28.61N 77.21E. ' + M_F, ['data/firms_season_counts.csv'], url=U_F)
# --- weather
em = rd('era5_monthly.csv'); clim = {}
for m in range(1, 13):
    sel = [r for r in em if int(r['month']) == m and 2016 <= int(r['year']) <= 2025]
    clim[str(m)] = dict(blh=round(st.mean(float(r['blh']) for r in sel)), blh_night=round(st.mean(float(r['blh_night']) for r in sel)), from_nw_pct=round(st.mean(float(r['nw_pct']) for r in sel)))
clim['night_oct_dec_min'] = min(clim[m]['blh_night'] for m in ('10', '11', '12')); clim['night_oct_dec_max'] = max(clim[m]['blh_night'] for m in ('10', '11', '12'))
clim['nw_monsoon_min'] = min(clim[m]['from_nw_pct'] for m in ('6', '7', '8', '9')); clim['nw_monsoon_max'] = max(clim[m]['from_nw_pct'] for m in ('6', '7', '8', '9'))
ev('weather_climatology', 'Average mixing height by month (all hours; night 20-06h) and share of hours with the 100 m wind from the west-to-north quarter (270-360 degrees)', clim, S_E, 'average of 2016-2025 (a climatology, not the weather of 2025-26)',
   'metres; percent of hours', ['data/era5_monthly.csv'], url=U_E)
# --- upstream fire-detection index and the comparisons built on it
cp = os.path.join(D, 'contrast.json')
if not os.path.exists(cp): sys.exit('missing data/contrast.json (run contrast.py)')
C = json.load(open(cp))
S_T = S_PM + '; ' + S_F + '; ERA5 100 m wind via the Open-Meteo archive API on a 0.5 degree grid (27.5-33N, 72.5-78.5E) inside a 1 degree grid (24-35N, 69-83E)'
M_T = ('Upstream fire-detection index: air arriving over central Delhi at 03, 09, 15 and 21 IST is traced back 48 hours along the ERA5 100 m wind (horizontal only; no dispersion or vertical motion). The index is the number of distinct MODIS '
       'detections within 25 km of an hourly path point that were acquired between 24 hours before and 3 hours after the air passed. A day is used only if no path stopped for lack of wind data. Categories are thirds of all usable days. '
       'Detection time is the overpass, not ignition: the index does not show that the air crossed a burning field.')
I_T = ['data/answer_daily.csv', 'data/traj_daily.csv', 'data/traj_paths.csv', 'data/contrast.json']
ev('path_index_days', 'Days with a Delhi value and a valid index; limits of the three categories; where the counted detections were', dict(days=C['days'], by_year=C['days_by_year'], seasons_with_20_days_or_more=[y for y, n in C['days_by_year'].items() if n >= 20], days_in_2016_2017_2020=sum(C['days_by_year'].get(y, 0) for y in ('2016', '2017', '2020')), not_used=C['not_used'], last_day=C['last_day'], few_max=C['cut_few_max'],
   many_above=C['cut_many_above'], days_with_four_complete_paths=C['four_complete_paths_days'], where_pct=C['where_pct']), S_T, '15 Oct-30 Nov; 2016-2021, 2025, 2026', M_T, I_T, url=U_F + ' ; ' + U_E)
ev('pm_by_path_index', 'Median Delhi PM2.5 by upstream fire-detection category within each part of the season; the same with thirds taken within each year', dict(pooled_thirds=C['median_by_part'], thirds_within_each_year=C['median_by_part_within_year_thirds']),
   S_T, '15 Oct-30 Nov', M_T + ' Median of daily city values. An association between categories of days, not a measured contribution.', I_T, url=U_F)
M_MW = ('Each day of 25 Oct-20 Nov is paired with up to 5 December-January days of the same season (at least 3) whose ventilation is within a factor of 1.25. Ventilation = mean over the same local calendar day of ERA5 mixing height x 100 m wind speed. '
        'This matches ONE scalar; temperature, humidity, rain, wind direction, chemistry and the mix of sources are not held constant. The December-January level is not a no-fire counterfactual and the difference is not a fire contribution.')
m = C['exploratory_contrast']['main']
if m is None: sys.exit('main contrast could not be computed')
ev('matched_comparison', 'Peak fire weeks (25 Oct-20 Nov) against ventilation-matched December-January days: mean PM2.5, mean of matched days and the difference, all days and by upstream fire-detection category',
   dict(days=m['days'], by_year=C['matched_days']['by_year'], mean_pm=round(m['mean_pm']), matched_winter=round(m['mean_matched_winter']), difference=round(m['excess_all']),
        few=dict(days=m['days_few'], mean_pm=round(m['pm_few']), matched_winter=round(m['winter_few']), difference=round(m['excess_few'])),
        some=dict(days=m['days_some'], mean_pm=round(m['pm_some']), matched_winter=round(m['winter_some']), difference=round(m['excess_some'])),
        many=dict(days=m['days_many'], mean_pm=round(m['pm_many']), matched_winter=round(m['winter_many']), difference=round(m['excess_many'])), by_season=C['by_year'], days_by_season_and_category=C['matched_days_by_year_and_category'], control_reuse=C['control_reuse']),
   S_T + '; ' + S_E, '25 Oct-20 Nov and the following Dec-Jan; seasons ' + ', '.join(C['matched_days']['by_year']), M_T + ' ' + M_MW, I_T + ['data/match_weather.csv', 'data/match_controls.csv'], status='computed; observational comparison', url=U_E)
ev('exploratory_contrast', 'EXPLORATORY: the difference from matched winter days in each category minus the difference in the few-detections category, as a share of mean PM2.5, under alternative choices. Not a source share',
   dict(all_minus_few_pct_lowest=min(v['all_minus_few_pct_of_pm'] for v in C['exploratory_contrast'].values() if v), all_minus_few_pct_highest=max(v['all_minus_few_pct_of_pm'] for v in C['exploratory_contrast'].values() if v),
        variants_computed=sum(1 for v in C['exploratory_contrast'].values() if v), variants=C['exploratory_contrast'], leave_one_season_out=C['leave_one_season_out'], resampling_5th_95th_percentile=C['resampling'], diwali_days_removed=C['diwali_days_removed'], seeds=C['seeds']), S_T + '; ' + S_E, '25 Oct-20 Nov',
   'all_minus_few = mean difference over all days minus mean difference on few-detection days; many_minus_few likewise for many-detection days; _pct_of_pm divides by the mean PM2.5 of those days. This equals a crop-fire contribution only if the few-detection days carry no '
   'crop smoke, the non-fire background is the same in every category, ventilation matching removes confounding and the categories are right. None of these is established. Resampling intervals hold the inputs, the matching and the categories fixed and are not uncertainty bounds '
   'on a source share. Control days are shared between target days (see control_reuse in matched_comparison). The percentiles are conditional on accepted draws (see resampling note). The variants are not an exhaustive robustness envelope: the hourly-grid sensitivity gives about 17% and 16% (entry sensitivity_hourly_grid). None of these numbers is printed in the article.', I_T + ['data/match_weather.csv', 'data/match_controls.csv'], status='exploratory; not used as a finding')
# --- satellite figure caption: November 2025
fd = {r['date']: r for r in rd('firms_daily.csv')}; GR = ['Punjab', 'Haryana', 'Uttar Pradesh', 'Delhi', 'Rajasthan', 'IN other', 'PK']
cap = collections.OrderedDict()
for i in range(1, 31):
    d = f'2025-11-{i:02d}'; r = fd.get(d); cap[d] = dict(whole_map_box=sum(int(r[g]) for g in GR) if r else 0, punjab_haryana=int(r['Punjab']) + int(r['Haryana']) if r else 0, delhi_pm25=round(pm[d][0]) if d in pm else None)
last = [v for d, v in cap.items() if d >= '2025-11-21']
ev('november_2025_frames', 'For each day of November 2025: MODIS detections in the whole fire box (the number shown on each frame), in Punjab + Haryana, and Delhi PM2.5; summary of 21-30 November',
   dict(days=cap, last_ten_days=dict(max_whole_box=max(v['whole_map_box'] for v in last), max_punjab_haryana=max(v['punjab_haryana'] for v in last), pm_min=min(v['delhi_pm25'] for v in last if v['delhi_pm25']),
        pm_max=max(v['delhi_pm25'] for v in last if v['delhi_pm25']))), S_F + '; ' + S_PM + '; images: NASA GIBS, VIIRS (NOAA-20) corrected reflectance true colour', 'November 2025',
   'Counts by local (IST) date. The frames in the published figure print the count by UTC acquisition date as drawn when the animation was made; the two can differ by a few detections. True-colour images are visual context, not an identification of what the haze is made of.',
   ['data/firms_daily.csv', 'data/pm25_daily.csv'], url='https://worldview.earthdata.nasa.gov/')
ev('tracers_exploratory', 'EXPLORATORY and inconclusive: carbon monoxide at Delhi monitors (each sensor relative to its own median) and aerosol optical depth over Delhi, by upstream fire-detection category', C['tracers_exploratory'],
   'OpenAQ v3 CO sensors within 25 km of central Delhi; NASA GIBS rendered image tiles of MODIS MAIAC aerosol optical depth, decoded through the layer colour map', '15 Oct-30 Nov',
   'Neither separates the categories clearly, and neither is a sound test. CO: before 2023 the daily records count overlapping half-hour bins, so the completeness filter is not reliable; CO was not refetched hourly. AOD: values are colour bins of rendered images, which NASA advises '
   'against using for quantitative analysis; no quality flags; AOD is the whole air column and is not specific to crop smoke.', I_T, status='exploratory; inconclusive', url='https://nasa-gibs.github.io/gibs-api-docs/python-usage/')
# --- what others have published (quoted, read at source)
ev('published_iforest', 'iFOREST, Stubble Burning Status Report 2025 (summary): share of large farm fires in Punjab detected after 3 pm by a geostationary sensor; Sentinel-2 burnt area; decline in MODIS/VIIRS active-fire counts',
   dict(punjab_large_fires_after_3pm_2024_2025_pct_more_than=90, punjab_large_fires_after_3pm_2021_pct=3, punjab_burnt_area_km2_2022_peak=31447, punjab_burnt_area_km2_2025_about=20000, punjab_burnt_area_change_pct=-37,
        haryana_burnt_area_km2_2019_peak=11633, haryana_burnt_area_km2_2025=8812, haryana_burnt_area_change_pct=-25, active_fire_counts_change_2021_to_2025_pct=dict(punjab=-92, haryana=-90)),
   'International Forum for Environment, Sustainability and Technology (iFOREST), December 2025', 'kharif seasons 2019-2025', 'Quoted from the two-page summary. Burnt area is compared with each state\'s own peak year (Punjab 2022, Haryana 2019), fire counts with 2021, so the two falls have different base years and are not a like-for-like pair. Large fires seen by SEVIRI; not all fires.',
   [], status='quoted; summary PDF read on 11 Nov 2026', place='Punjab and Haryana', url='https://iforest.global/wp-content/uploads/2025/12/Summary-English.pdf')
ev('published_jethva_2026', '"Timing the Flames: Geostationary Satellite Detection of Diurnally Shifting Stubble Burning in Northwestern India", Remote Sensing 18(10), 1506 (2026): peak burning moved from about 1-2 pm to 4-5 pm local time; hotspots detected over Punjab by a geostationary sensor; drift of Aqua\'s overpass time',
   dict(aqua_modis_vs_2016_2021_avg_pct={'2022': -20, '2023': -39, '2024': -67, '2025': -71}, geostationary_punjab_2024_vs_2021_pct=-49, geostationary_punjab_2025_vs_2024_pct=45, geostationary_pixel_km=4, aqua_mean_overpass_local_time={'2021': '1:44 pm', '2022': '1:53 pm', '2023': '2:05 pm', '2024': '2:32 pm', '2025': '3:12 pm'}, aqua_overpass_projected_august_2026='about 3:50 pm', author='Hiren Jethva'),
   'Remote Sensing (MDPI), 2026', '2019-2025', 'Quoted from the abstract and sections 3.1, 4.4, 4.5. SCOPE: the -49% and +45% are hotspots detected over PUNJAB by the geostationary sensor; the Aqua-MODIS percentages are for the wider north-west India study region against its 2016-2021 average and are NOT used in the text. Overpass times are Aqua\'s seasonal means over the study region. The geostationary counts are at about 4 km resolution and, by the paper\'s own account, under-represent fires and cannot be compared directly with MODIS or VIIRS counts.',
   [], status='quoted; article read on 11 Nov 2026', place='Punjab and Haryana', url='https://www.mdpi.com/2072-4292/18/10/1506')
ev('published_nasa_drift', 'NASA quality notice "MODIS - Terra/Aqua Drift" (8 Jan 2026): orbit drift has changed diurnal sampling and widened scan gaps, with significant effects in late 2024; effects on the fire products under investigation', dict(notice_date='2026-01-08'),
   'NASA LANCE/MODAPS land product quality notice 1254', 'from late 2024', 'Quoted.', [], status='quoted; notice read on 11 Nov 2026', place='global', url='https://landweb.modaps.eosdis.nasa.gov/displayissue?id=1254')
ev('published_cse_safar', "Centre for Science and Environment (30 Mar 2022), from SAFAR's daily modelled estimates for 10 Oct-30 Nov 2021: stubble smoke's daily share of Delhi's PM2.5", dict(days=52, daily_share_min_pct=1, daily_share_max_pct=48, peak_date='2021-11-07',
   days_above_40pct=2, mean_concentration_ug_m3=28, non_stubble_share_of_daily_pm25_more_than_pct=80), 'CSE analysis of winter 2021-22; underlying model: SAFAR (Ministry of Earth Sciences), which provided daily model estimates for that season', '10 Oct-30 Nov 2021',
   'Quoted. A model result for one season. iFOREST argues such models understate the share in 2024-25 because they take in MODIS/VIIRS fire counts. Shown for context only; it does not validate, and is not validated by, anything computed here.', [],
   status='quoted; CSE release read on 11 Nov 2026', place='Delhi, as defined by SAFAR and CSE (not this report\'s 25 km monitor selection)', url='https://www.cseindia.org/cse-releases-analysis-of-winter-air-pollution-trends-for-delhi-ncr-11208')
ev('published_moefcc_2024', 'Ministry of Environment, Forest and Climate Change, written reply in Parliament (PIB release, 25 Nov 2024): air pollution in Delhi and NCR comes from many sectors (vehicles, industry, construction and demolition dust, road and open-area dust, biomass burning, municipal solid waste burning, landfill fires, dispersed sources); in post-monsoon and winter months weather traps pollutants; episodic events such as stubble burning and firecrackers aggravate this; paddy stubble burning affects NCR air quality particularly in October and November',
   dict(release_date='2024-11-25'), 'Press Information Bureau, Government of India', 'n/a', 'Quoted; no number from it is used. It is the source for the list of year-round sources and for the general statement that autumn crop fires add to the region\'s pollution.', [],
   status='quoted; release read on 11 Nov 2026', place='Delhi and NCR', url='https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=2076918&lang=2&reg=48')
ev('published_caqm_2026', 'Commission for Air Quality Management, statutory direction on wheat stubble burning (PIB release, 16 Feb 2026): the wheat harvesting season is 1 April to 31 May; fire events were recorded in Punjab, Haryana and NCR districts of Uttar Pradesh in that season of 2025',
   dict(release_date='2026-02-16', wheat_season='1 April-31 May'), 'Press Information Bureau, Government of India', 'April-May', 'Quoted; source for the statement that crop residue is also burnt in April and May. This report does not analyse that season.', [],
   status='quoted; release read on 11 Nov 2026', place='Punjab, Haryana, NCR districts of Uttar Pradesh', url='https://www.pib.gov.in/PressReleasePage.aspx?PRID=2228743&lang=1&reg=1')
# --- sensitivity of the historical series to the hourly grid (asked for by the review of draft 3)
sp = os.path.join(D, 'sensitivity_hourly_grid.json')
if not os.path.exists(sp): sys.exit('missing data/sensitivity_hourly_grid.json (run sensitivity_hourly_grid.py)')
SG = json.load(open(sp)); a3 = SG['alternative_30_thirds_re_estimated']; a3f = SG['alternative_30_main_cutoffs_kept']; rnd = lambda t: {k: dict(v, **({'median': round(v['median'])} if 'median' in v else {'mean': round(v['mean'])})) for k, v in t.items()}
ev('sensitivity_hourly_grid', 'SENSITIVITY: the same comparisons with the 2016-2022 city days built from the other regular hourly grid (aggregates ending on :30 instead of :00). Days available, median PM2.5 by category and period, and mean difference from paired winter days',
   dict(historical_city_days_main=SG['historical_city_days']['main_00'], historical_city_days_alternative=SG['historical_city_days']['alternative_30'], days_with_index_alternative=a3['days_with_pm_and_index'], matched_days_alternative=a3['matched_days'],
        matched_days_by_season_alternative=a3['matched_days_by_season'], seasons_alternative=len(a3['matched_days_by_season']),
        thirds_re_estimated=dict(few_max=a3['cut_few_max'], many_above=a3['cut_many_above'], median_pm={p: rnd(v) for p, v in a3['median_pm_by_period'].items()}, difference_from_winter=rnd(a3['mean_difference_from_matched_winter'])),
        main_cutoffs_kept=dict(few_max=a3f['cut_few_max'], many_above=a3f['cut_many_above'], median_pm={p: rnd(v) for p, v in a3f['median_pm_by_period'].items()}, difference_from_winter=rnd(a3f['mean_difference_from_matched_winter'])), unrounded=SG),
   S_T + '; ' + S_E, '15 Oct-30 Nov; seasons 2016-17 to 2022-23 recomputed, 2025-26 unchanged', SG['what'] + ' ' + SG['caution'] + ' ' + M_T + ' ' + M_MW, ['data/sensitivity_hourly_grid.json', 'data/pm25_daily_alt30.csv'], status='sensitivity check; diagnostic only', url=U_PM)
RET = ['Median PM2.5 by same-day fire-count tercile (draft 1 chart fire-days.svg) and by ventilation or wind-direction tercile: retired, replaced by the upstream index.',
       'The "22% / 35% fire-linked share" of draft 2 and its 13-30% range: retired as a finding; the arithmetic survives only as the exploratory contrast.',
       'Visibility at Safdarjung and Palam since 1973 (draft 1-2 section): retired; unhomogenised records, fog and humidity confounding, last decade mislabelled.',
       'Early-October control and the regression in join_daily.py: retired, never used in the text.',
       'The numerical values of the exploratory contrast (draft 3 text: 26.5%, 39.6%, ranges) are no longer printed in the article; they stay in the entry exploratory_contrast.']
json.dump(dict(report="Delhi's air and the crop fires", status='published 11 November 2026', version='2026-11-11f', centre=dict(lat=28.61, lon=77.21, name='central Delhi'),
               inputs=dict(note='Scripts and extracts in scripts/reports/delhi-smog-fires/analysis/ (data/, inputs/); raw downloads and how to refetch them are listed in analysis/README.md and analysis/MANIFEST.json'),
               retired_analyses=RET, evidence=E), open(OUT, 'w'), indent=1, ensure_ascii=False)
for e in E: print(e['id'], '=>', json.dumps(e['value'], ensure_ascii=False)[:700], '\n')
