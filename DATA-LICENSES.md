# Data licences

The code in this repository is MIT-licensed (see `LICENSE`). The data files are not all under one licence, because they are built from sources with different terms. If you reuse a file, follow the licence listed here and credit both HamariHawa (hamarihawa.org) and the original source.

| Files | Licence | Built from |
|---|---|---|
| Fire feed and archive: `/api/fires`, `/api/days`, `/api/day`, `/api/districts`, `/fires.kml`, `site/public/report/two-punjabs/seasons.json` | CC BY 4.0, **except** the fire type value `kiln` (see the next row) | NASA FIRMS (VIIRS, MODIS), place names from GeoNames (CC BY 4.0) |
| Brick kilns: `site/public/sources/kilns.json`, and the Pollution sites list `site/public/sources/sites.json`; also a fire's type when it is `kiln` | CC BY-NC 4.0, non-commercial only | SentinelKilnDB (IIT Gandhinagar, CC BY-NC 4.0); Pakistan kiln emissions from the Brick Kiln Dataset for Pakistan's IGP Region (CC BY 4.0) |
| Landfills, industrial areas, power plants, roads: `osm-landfill.json`, `osm-industrial.json`, `plants.json`, `roads.json` | ODbL 1.0. A changed copy you share must stay under ODbL | © OpenStreetMap contributors |
| Village and town index: `site/public/places/`, `site/public/sources/towns.json`, `site/src/towns.json` | CC BY 4.0 | GeoNames |
| NO₂ hotspots and images: `/api/no2.json`, `/api/no2.png`, `/api/no2-geo.png`, `site/public/sources/hotspots.json` | CC BY 4.0 | Copernicus Sentinel-5P TROPOMI via NASA GIBS |
| Methane and CO₂ plumes: `site/public/sources/carbonmapper.json` | Carbon Mapper's own terms | Carbon Mapper |
| City air quality and wind (served live, not stored here) | CC BY 4.0 | Copernicus CAMS and weather models via Open-Meteo |
| `report/data/` (monthly PM2.5 for the Lahore & Islamabad Air Ledger) | Not licensed by us | Collected from IQAir's public city pages and CAMS. IQAir's figures remain subject to IQAir's terms; ask IQAir before reusing them |
| Text, charts and reports on the site | CC BY 4.0 | HamariHawa |

Please cite as: HamariHawa (hamarihawa.org), with the original sources above.
