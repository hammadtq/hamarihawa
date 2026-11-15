# Evidence for "Lahore got a trace of rain, Faisalabad and Multan none. Their air improved anyway"

The inputs and scripts behind the HamariHawa report of 16 November 2026. Paths are relative to this folder.

## Inputs (`data/`)

- `rainfall/ogimet/`: Pakistan Meteorological Department observatory reports (SYNOP) relayed by OGIMET, 10 to 15 November, with the decoding rules in its `README.txt`.
- `rainfall/iem-metar/`: airport weather reports (METAR) from the Iowa Environmental Mesonet archive, 9 November to midday on 15 November.
- `rainfall/pdf-imd-text/`: text of the India Meteorological Department bulletins issued on 15 November. The PDFs are not in the repository; their SHA-256 sums are in `rainfall/pdf-imd/SHA256SUMS.txt`.
- `iqair-before-*.json`, `iqair-after-*.json`, `iqair-rebound-*.json`: IQAir hourly histories for 14 cities and every station linked from them, captured on 11, 14 and 16 November. Each file's `note` and `method` fields say how it was read.
- `day-summaries/`: HamariHawa's daily fire summaries for 1 to 15 November (`fetch_days.py`).
- `series.json`: the hourly city series the charts draw, written by `build_evidence.py`.

## Scripts

Run in this order (Python 3.9 or later; `charts.py` was run with 3.12):

1. `python3 build_evidence.py` writes `site/public/report/punjab-rain-nov-2026/data.json`, one entry per claim with its value, source and method. It stops if one of its own checks fails (for example, that 12 to 13 November was the windiest of the six nights at five airports).
2. `python3 render_article.py` fills `article.<lang>.tmpl.html` with those values and writes `article.<lang>.html`. It stops if the three languages do not use the same values.
3. `python3 charts.py en`, `ur`, `hi` draw the charts.
4. `python3.12 -I scripts/build-reports.py` (from the repository root) builds the page.

## Limits

- One rain gauge per place; a shower can miss it. Sargodha sent empty reports.
- No IQAir hourly data from 1 am on 11 November to 7 pm on 12 November (Pakistan time).
- IQAir readings are as displayed and are revised after first display. The Indian Punjab feeds are single relayed government feeds.
- Fire counts are near-real-time detections, and cloud hides fires.
- The draft was checked once by an independent recomputation from the raw files before publication.
