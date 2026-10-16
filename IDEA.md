# Hamari Hawa: live fire and air map (idea, not built yet)

Captured 14 Sep 2026. Status: **built 17 Oct 2026** in `site/` (Cloudflare Worker + static assets; see `site/` and `scripts/build-places.py`). Notes below kept for history; the GIBS layer names here were wrong, the working ones are in `site/public/app.js`. The daily TROPOMI SO₂ layer was dropped as too noisy, and CARTO tiles now need a key, so the base map is Esri Light Gray. The 24-month Lahore/Islamabad report in `report/` is done; this file records the next thing we want to build so nothing is lost.

## The idea, in the words it was pitched

Host the report as a proper website, and put a live map on top of it with a sidebar:

- Pull real-time fire detections from NASA satellites. Whenever a fire is detected, approximate its location with a map/geocoder and say "fire has been detected at Chak Shehzad". This is mainly for crop-residue fires.
- Make it interactive: people should see how many farm fields are burning simultaneously, and that these fires are one contributor to the pollution.
- Alongside that, an honest reflection of the city's own emissions: NO₂ and the other gases that come mainly from vehicles, and what the air looks like over the industrial areas.
- Plot all of this on one map so people can see what is going on in the air.

## Why it works: every layer has a free, live source

| Layer | Source | Cost / key | Notes |
|---|---|---|---|
| Active fires, points with time and intensity | NASA FIRMS. Public 24h/48h/7d CSVs per region (VIIRS SNPP, VIIRS NOAA-20/21, MODIS), e.g. `SUOMI_VIIRS_C2_South_Asia_24h.csv`. The Area API (`/api/area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/{bbox}/{days}`) gives a bounding box and up to 10 days | Free. The public CSVs need no key; the Area API needs a free MAP_KEY (registered by us, 5,000 requests per 10 min) | Not CORS-enabled, so fetch from a small server-side proxy, cache 10–15 min. Fields: lat, lon, acq_date, acq_time, confidence, frp (fire radiative power), daynight. VIIRS latency is roughly 3 hours; NRT passes over Punjab around 13:30 and 01:30 local |
| Fire heat map as a tile layer (no processing) | NASA GIBS WMTS layers `VIIRS_SNPP_Thermal_Anomalies_375m_Day` / `_Night`, `MODIS_Combined_Thermal_Anomalies_All` | Free, no key, CORS-friendly | Quick win for a first version: drop into Leaflet as a tile layer with a date parameter |
| NO₂ over the city and industrial areas | Sentinel-5P TROPOMI NO₂ tropospheric column via GIBS WMTS layer `S5P_L2_NO2_Tropospheric_Column` (daily, ~5.5 km) | Free, no key | The honest "vehicle emissions" picture: a heat map of NO₂ across Lahore, the GT Road belt, Sundar and Kot Lakhpat industrial estates, Islamabad I-9/I-10 and Rawalpindi. Also `S5P_L2_SO2`, `S5P_L2_CO`, `S5P_L2_Aerosol_Index` for kilns and smoke |
| Point readings of NO₂, SO₂, CO, O₃, PM2.5 at named places | Open-Meteo Air Quality API (Copernicus CAMS, ~11 km) | Free, no key, CORS-enabled | Coarse; fine for "city centre vs industrial estate vs farmland" comparisons and for the sidebar numbers. Winter under-read vs ground sensors is 1.5–1.6× (see report method) |
| Ground PM2.5 at stations | IQAir community API (free tier, city-level AQI only), OpenAQ v3 (free key, US-mission monitors), aqi.in (no public API) | Free with registration | Optional. IQAir's free tier gives no NO₂; use it for a live PM2.5 headline only |
| Place names for alerts ("near Chak Shehzad") | GeoNames PK dump (populated places, free CC-BY) bundled as JSON and matched client-side by nearest point; or Nominatim reverse geocoding (free, 1 request per second, attribution required) | Free | Bundling GeoNames avoids rate limits and works for village names ("Chak" numbering) that Google often lacks. Google Maps Platform needs a billing account; not needed |
| Base map | Leaflet + OpenStreetMap tiles (or MapLibre + a free vector tile provider) | Free | Google Maps was mentioned but is not required and costs money past the free quota |
| Farmland mask (is this fire on a field?) | ESA WorldCover 10 m land-cover (cropland class) or the Punjab crop maps from SUPARCO | Free | Lets us say "farm fire" vs "kiln/industrial/urban fire" and count burning fields honestly |

## Proposed shape (v1, a weekend of work)

- Static site (the existing `report/index.html` becomes `/report`) plus `/` for the map. Host on Cloudflare Pages.
- One Cloudflare Worker: `/api/fires?hours=24` fetches the FIRMS South Asia CSV, filters to a Pakistan Punjab + Islamabad bounding box (roughly 28.5–34.5 N, 69.5–75.5 E), tags each point with land cover and nearest GeoNames place, caches for 10 minutes, returns GeoJSON. Optional MAP_KEY lets us go back up to 10 days.
- Map: Leaflet, OSM base, three toggleable overlays: fires (points sized by FRP, coloured by age), TROPOMI NO₂, TROPOMI aerosol index. A date slider for the last 7 days.
- Sidebar: live counters ("142 fires in the last 24 h, 119 on cropland, 61 within 60 km of Lahore"), a feed of alerts ("Fire detected near Chak Shehzad, 14:05, high confidence, on cropland"), and the honest city panel: NO₂ / SO₂ / CO / PM2.5 now at Lahore centre, Kot Lakhpat, Sundar, Shahdara kiln belt, Islamabad Blue Area, I-10 industrial, Rawalpindi Rawat.
- Attribution bar for NASA FIRMS, Copernicus, OpenStreetMap, GeoNames.

## Things to decide before building

1. Bounding box and season: show all of Punjab year-round, or focus Oct–Nov on the rice belt (Sheikhupura, Kasur, Gujranwala, Nankana) and Apr–May on wheat stubble?
2. Cross-border: include Indian Punjab fires in the count? They matter for Lahore's air but the framing needs care (see the transboundary numbers in the report: 13–30%).
3. Alerts: on-page feed only, or also a WhatsApp/Telegram channel or email digest (Kit is connected) for the daily fire count?
4. Whether to register a FIRMS MAP_KEY (needs an email sign-up at firms.modaps.eosdis.nasa.gov/api/map_key) for the 10-day history, or start with the keyless 24h/48h/7d files.
5. Hosting name: this repo path suggests `hamarihawa`; domain not yet chosen.

## Related work already in this repo

- `report/index.html`, `report/Lahore-Islamabad-Air-Ledger.pdf`: the 24-month side-by-side report (also published as a private Claude artifact).
- `report/data/`: the IQAir monthly series (CSV and JSON), CAMS monthly pollutant means, and the three research notes on sources, projections and data provenance with all URLs.
