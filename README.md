# Hamari Hawa

Live satellite map of fires, smoke and pollution over Pakistan and North India, with what it means for health in 17 cities. English, Urdu and Hindi. Live at https://hamarihawa.org.

- `site/`: Cloudflare Worker (`src/worker.js`) plus the static page (`public/`). Deploy with `cd site && npx wrangler deploy`.
- `scripts/build-feed.py`: downloads NASA FIRMS fire detections (VIIRS + MODIS), names each fire after the nearest GeoNames village, and writes the feed to Workers KV. Runs every 15 minutes from `.github/workflows/feed.yml`.
- `scripts/build-places.py`: rebuilds the village index in `site/public/places/` from GeoNames dumps.
- `report/`: the 24-month Lahore and Islamabad air report, also served at `/report/`.

The workflow needs a repo secret `CLOUDFLARE_API_TOKEN` (permission: Workers KV Storage, Edit) and a repo variable `CLOUDFLARE_ACCOUNT_ID`.
