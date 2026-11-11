#!/bin/sh
# Recompute the core analysis (every extract except the aerosol table, data.json, the article text and the charts) from the bundled raw
# downloads, then compare data.json with the shipped copy. NOT redone here: the aerosol (AOD) table, the satellite figure and animations (their
# image tiles are not bundled; the shipped aod_daily.csv is reused) and the PDF (needs Google Chrome).
# Usage (from anywhere):  sh run_all.sh [H]      H = folder that holds raw/ (default: the root of the evidence ZIP). Needs python3 (3.9+), no packages, no network.
set -e
A=$(cd "$(dirname "$0")" && pwd); H=${1:-$A/../../../..}; H=$(cd "$H" && pwd); PY=${PYTHON:-python3}
SITE="$A/../../../../site/public/report/delhi-smog-fires"
for d in openaq openaq_hours openaq_days_full openaq_probe firms era5 windgrid windouter; do
  [ -d "$H/raw/$d" ] || { echo "run_all: missing input folder $H/raw/$d (see README: 'Inputs')" >&2; exit 1; }
done
[ -f "$A/inputs/in_states_box.json" ] && [ -d "$A/inputs/day-summaries" ] || { echo "run_all: missing $A/inputs" >&2; exit 1; }
mkdir -p "$H/out" "$SITE"
# The exploratory aerosol check needs 16 MB of image tiles that are not bundled; its decoded daily table is, so reuse it unless tiles were refetched.
[ -f "$H/out/aod_daily.csv" ] || cp "$A/data/aod_daily.csv" "$H/out/aod_daily.csv"
[ -f "$SITE/data.json" ] && cp "$SITE/data.json" "$H/out/data.shipped.json"
cd "$A"
for s in check_openaq_regime pm25_daily firms_analysis era5_analysis traj_delhi match_weather contrast; do
  echo "== $s"; "$PY" "$s.py" "$H" > "$H/out/$s.log" 2>&1 || { echo "run_all: $s.py failed; see $H/out/$s.log" >&2; tail -5 "$H/out/$s.log" >&2; exit 1; }
done
echo "== sensitivity_hourly_grid"; "$PY" sensitivity_hourly_grid.py "$H" > "$H/out/sensitivity_hourly_grid.log" 2>&1 || { echo "run_all: sensitivity_hourly_grid.py failed; see $H/out/sensitivity_hourly_grid.log" >&2; tail -5 "$H/out/sensitivity_hourly_grid.log" >&2; exit 1; }
for f in pm25_daily pm25_daily_alt30 pm25_station_days pm25_monthly era5_monthly firms_daily firms_season_counts firms_detections_classified traj_paths traj_daily match_weather match_controls answer_daily aod_daily; do cp "$H/out/$f.csv" data/; done
cp "$H/out/contrast.json" "$H/out/contrast_alt30.json" "$H/out/contrast_alt30_fixedcuts.json" "$H/out/sensitivity_hourly_grid.json" "$H/out/openaq_regime_check.json" data/
echo "== build_evidence"; "$PY" build_evidence.py > "$H/out/build_evidence.log" 2>&1 || { echo "run_all: build_evidence.py failed; see $H/out/build_evidence.log" >&2; tail -5 "$H/out/build_evidence.log" >&2; exit 1; }
echo "== render_article"; "$PY" render_article.py
echo "== charts"; "$PY" charts.py en > "$H/out/charts.log" 2>&1 || { echo "run_all: charts.py failed; see $H/out/charts.log" >&2; tail -5 "$H/out/charts.log" >&2; exit 1; }
if [ -f "$H/out/data.shipped.json" ]; then
  if cmp -s "$SITE/data.json" "$H/out/data.shipped.json"; then echo "RESULT: data.json reproduced exactly (byte-identical to the shipped file)"; else echo "RESULT: data.json DIFFERS from the shipped file; compare $SITE/data.json with $H/out/data.shipped.json"; exit 2; fi
fi
