# Evidence for "Delhi's air is polluted all year. Autumn crop fires add to it" (published 11 Nov 2026)

Paths are relative to the root of this ZIP, which mirrors the repository.

## Rerun the core analysis
```
sh scripts/reports/delhi-smog-fires/analysis/run_all.sh
```
Needs `python3` (3.9 or later; made with 3.12), the standard library only, and no network. It recomputes the PM2.5, fire, weather, back-path, matching, contrast and hourly-grid sensitivity extracts from `raw/`, rebuilds `data.json`, fills the article text and redraws the four charts, then compares the new `data.json` with the shipped one and prints `RESULT: data.json reproduced exactly`. It takes under a minute.

It does **not** redo three things: the aerosol (AOD) table, which is reused from the shipped `data/aod_daily.csv` because its image tiles are not bundled; the satellite figure and animations; and the PDF, which needs Google Chrome. A byte-identical result shows the computation is consistent. It does not validate the wind-path index or show cause. Logs go to `out/`. If an input folder is missing it stops and names it.

## Contents
- `scripts/reports/delhi-smog-fires/article.en.tmpl.html`: the draft text with `{{entry.key}}` tokens. `render_article.py` fills them from `data.json` and writes `article.en.html`, so no number in the text is typed by hand. `meta.json`: title and abstract.
- `site/public/report/delhi-smog-fires/data.json`: one entry per claim (value, source, source_url, period, place, method, inputs, status), plus `retired_analyses`. Written by `build_evidence.py`.
- `site/public/report/delhi-smog-fires/*.svg`, `smoke-november-2025.jpg`: the four charts (drawn from `data.json` by `charts.py`) and the satellite figure.
- `scripts/reports/delhi-smog-fires/analysis/data/`: the extracts every number is computed from.
  - `pm25_station_days.csv`, `pm25_daily.csv`, `pm25_monthly.csv`: station-days kept, the city value per day (median and mean of stations, station count, which record type), monthly means.
  - `openaq_regime_check.json`: the evidence for the completeness rule (see below).
  - `firms_detections_classified.csv`: every detection with id, UTC time, India time and date, satellite, country, state, distance from Delhi. `firms_daily.csv`, `firms_season_counts.csv`: counts by day and year (by state, satellite, day/night).
  - `era5_monthly.csv`: mixing height and wind climatology.
  - `traj_paths.csv`: every back-path (hours followed, why it stopped, hours inside the fire box, end point). `traj_daily.csv`: the upstream fire-detection index per day under three timing rules; blank when a path stopped for lack of wind data.
  - `match_weather.csv`, `match_controls.csv`: each target day with its paired winter mean, and every target-control pair.
  - `sensitivity_hourly_grid.json`, `pm25_daily_alt30.csv`, `contrast_alt30*.json`: the hourly-grid sensitivity.
  - `answer_daily.csv`, `contrast.json`: the joined days and every comparison, variant, leave-one-season-out and resampling result.
  - `aod_daily.csv`: aerosol optical depth decoded from image tiles (exploratory check only).
  - `entries_used_in_text.json`: which `data.json` entries the text uses.
  - In the site's repository, `firms_detections_classified.csv` (45 MB) and `raw/` are left out; `firms_analysis.py` rebuilds the file from the FIRMS downloads. The evidence ZIP has both.
- `scripts/reports/delhi-smog-fires/analysis/inputs/`: `in_states_box.json` (state polygons, geoBoundaries gbOpen IND ADM1, CC BY 2.5 IN), `borders.json` (country outlines), `day-summaries/` (HamariHawa daily fire summaries, with `SCHEMA.md`).
- `raw/`: the downloads, retrieved 11 November 2026. `MANIFEST.json` lists each folder's source, file count, bytes and hash, and the random seeds.
- `analysis/retired/`: scripts from drafts 1 and 2 that draft 3 does not use.

## Inputs (`raw/`)
| Folder | What | Refetch with | Key |
|---|---|---|---|
| `openaq_hours` | OpenAQ v3 hourly records, 1 Oct–31 Jan, seasons 2016–17 to 2022–23 | `fetch_openaq_hours.py` | OpenAQ |
| `openaq_days_full` | OpenAQ v3 daily records, complete, gzip | `fetch_openaq_hours.py` | OpenAQ |
| `openaq_probe` | complete API responses for sample station-days | see `check_openaq_regime.py` | OpenAQ |
| `openaq` | draft 1 daily extract; used only for the station list and carbon monoxide | `fetch_openaq.py`, `fetch_openaq_co.py` | OpenAQ |
| `firms` | NASA FIRMS MODIS, box 73.0,27.0,79.5,32.6 | `fetch_firms.py` | FIRMS |
| `era5` | ERA5 hourly at central Delhi (Open-Meteo archive) | `fetch_era5.py` | none |
| `windgrid`, `windouter` | ERA5 100 m wind, 0.5° inner and 1° outer grid | `fetch_wind_grid.py`, `fetch_wind_outer.py` | none |

Not bundled: the satellite image tiles (16 MB; `fetch_sat.py`), needed only to redo the animation (`make_frames.py`, `make_animation.sh`) and `aod_boxes.py`. `run_all.sh` reuses the shipped `aod_daily.csv`. Keys are not included. `make_review_pdf.py` needs Google Chrome.

## Rules that changed in draft 3
- **PM2.5 completeness.** Historical daily counts can include overlapping hourly aggregates (one set ending on the hour, one on the half hour), so a day can show up to 48 and the count cannot be read as hours. For the historical seasons we select one consistent grid of non-overlapping hourly aggregates, those ending on the hour in India time, and require at least 18 valid aggregates on it. This is a conservative restriction: it excludes some available offset-hour observations, and a rejected station-day is not necessarily one with fewer than 18 hours of measurements. From 2025 the daily records are used (the count never exceeds 24; the script stops if it does). Historical data are limited to 1 October–31 January.
- **Hourly-grid sensitivity (draft 4).** `sensitivity_hourly_grid.py` reruns the chain with the :30 grid: 424 historical city days instead of 239, 238 days with an index instead of 161, 81 paired days in four seasons instead of 57 in three. Results are in `data/sensitivity_hourly_grid.json` and the `data.json` entry `sensitivity_hourly_grid`. The :30 grid shifts the historical averaging window by half an hour; it is a diagnostic, not a replacement series.
- **Back-paths.** A path that runs out of wind data makes the day invalid (blank), never zero. A second, wider wind grid means paths rarely leave the domain; those that do are recorded with their duration.
- **Fire timing.** Detections keep their UTC acquisition time. The index counts detections acquired from 24 h before to 3 h after the air passed a point. Alternatives (none after passage; the calendar-day rule of draft 2) are in `contrast.json`.
- **States.** Assigned by boundary polygons, not nearest settlement.
- **Ventilation.** Averaged over the same India-time calendar day as the PM2.5 value.
- **No source share.** The draft 2 "22% / 35%" is withdrawn. Its arithmetic survives as `exploratory_contrast` with variants and resampling, labelled exploratory.

## Known limits
- The differences from paired winter days depend on the hourly grid: the few-category difference is +1 on the main grid and +33 or +36 on the other.
- Resampling ranges in `contrast.json` are conditional on accepted draws (710 of 4,000 season draws and 76 of 4,000 day draws are rejected); with three seasons there are only 27 season combinations.
- Diwali dates in `contrast.py` are from general knowledge, not an official calendar; they affect two days of one exploratory variant and nothing in the article.
- 161 days have both an index and a Delhi value; 153 of them are in 2018, 2019, 2021, 2025 and 2026. The winter comparison has 57 days in three seasons, and the few-detections category has 10 of them, from two seasons.
- Back-paths are horizontal, on ERA5 100 m wind, with no dispersion, and were not compared with HYSPLIT.
- MODIS detections are affected by later burning and by orbit drift (NASA notice of 8 Jan 2026); yearly counts are not comparable across the record.
- Ventilation matching uses one scalar. The winter level is not a no-fire counterfactual.
- Carbon monoxide is used for 2025–26 only and was not refetched hourly; that check and the aerosol check are inconclusive.
- `day-summaries` key `snpp` holds NOAA-20 data (see `inputs/day-summaries/SCHEMA.md`).
