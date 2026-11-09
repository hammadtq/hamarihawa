# Evidence for "This year, the highest fire count so far and Diwali fell on the same day"

This folder holds the retained inputs, the scripts and the claim ledger behind the HamariHawa report of 9 November 2026.
Paths are relative to the repository root (the root of the evidence ZIP).

## Contents

- `data/`: retained inputs, captured on 9 November 2026. The source, capture time and method of each file are in its own `source` or `note` field and in `ledger.md`.
  - **IQAir:**
    - `iqair-*.json`: city and station captures.
    - `iqair-*-recapture.json`: raw per-station histories.
  - **Fires:**
    - `day-summaries/`: HamariHawa's daily fire summaries, 2019–2026.
    - `day-2026-11-0*.json`: full fire-spot files.
  - **Weather and model:**
    - `wind-grid.json`, `wx-cities.json`: GFS weather.
    - `dw-*.json`: CAMS series.
  - **Derived results:**
    - `traj*.json`: modelled back-paths.
    - `*-stats.json`: station statistics.
- `frozen-draft6/`: draft 6 and its inputs' SHA-256 hashes, as audited.
- `ledger.md`: one row per claim, giving its source, geography, interval and timezone, units, method and status. Values are in `site/public/report/lahore-morning-after-diwali/data.json` under the same id.
- `CHANGES-draft7.md`: the audit change logs for drafts 7 and 8.
- `data/places/borders.json` (repository root): the Pakistan and India country outlines used by the map and the border-crossing test.
  - Pakistan: ODbL 1.0, © OpenStreetMap contributors, via geoBoundaries.
  - India: CC BY 2.5 IN, DataMeet, via geoBoundaries.

## Rerunning

You need Python 3.10 or later; the standard library is enough. Run these from this folder (`scripts/reports/lahore-morning-after-diwali/analysis/`):

```
python3 traj.py                # back-paths at 9 am Sun/Mon, 20 km fire screen  -> data/traj.json
python3 traj_sensitivity.py    # Lahore arrivals 00/03/06/09, 10/20/40 km, border test -> data/traj-sensitivity.json
python3 stations_lahore.py     # Lahore station statistics       -> data/lahore-stations-stats.json
python3 stations_delhi.py      # Delhi feed statistics by attribution -> data/delhi-stations-stats.json
python3 charts.py              # charts -> site/public/report/lahore-morning-after-diwali/*.svg
python3 build_evidence.py      # data.json and ledger.md, recomputed from the above
```

`fetch_summaries.py` downloads the daily fire summaries from https://hamarihawa.org/api/day. They are already in `data/day-summaries/`, so it only fetches days that are missing.

## Limits

Reproducing these results from the retained inputs does not independently check them:

- **IQAir:** the readings are what IQAir displayed, and IQAir revises some hours after first showing them.
- **Delhi feeds:** neither the CPCB-attributed nor the DPCC-attributed feeds were checked against official records.
- **Fire counts:** these are HamariHawa's merged spots from NASA FIRMS, not unique fires.
- **CAMS:** the series is the one retrieved on 9 November, not the run available on 8 November.
- **Back-paths:** these are horizontal paths from model winds, not a dispersion model.
