import { airKml, trafficKml, satelliteKml, kmlResponse } from "./kml.js";
import { pages } from "./pages.js";
// Hamari Hawa: serves the static site and the fire feed.
// The feed itself is built every 15 minutes by scripts/build-feed.py (GitHub Actions)
// and stored in KV, because naming every fire after its village is too much work
// for one request on the free Workers plan. Satellites only pass a few times a day anyway.

const WINDOWS = new Set(["24", "48", "168"]);
const WIND = { s: 24, n: 36, w: 66, e: 89 };

// GitHub's runners can't reach NASA FIRMS directly, so the feed builder fetches the
// public CSVs through here. Only these exact files are allowed, cached for 10 minutes.
const FIRMS = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/";
const FIRMS_FILES = new Set(
  ["suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2", "noaa-20-viirs-c2/csv/J1_VIIRS_C2", "noaa-21-viirs-c2/csv/J2_VIIRS_C2", "modis-c6.1/csv/MODIS_C6_1"]
    .flatMap((p) => ["24h", "48h", "7d"].map((w) => `${p}_South_Asia_${w}.csv`))
);

export default {
  // Backup trigger: GitHub's own cron is unreliable, so every 15 minutes the Worker asks GitHub
  // to run the feed workflow. Needs a GH_TOKEN secret (fine-grained, Actions: write on this repo).
  // The workflow exits early when NASA hasn't published anything new.
  async scheduled(event, env, ctx) {
    if (!env.GH_TOKEN) return;
    const r = await fetch("https://api.github.com/repos/hammadtq/hamarihawa/actions/workflows/feed.yml/dispatches", {
      method: "POST",
      headers: { authorization: `Bearer ${env.GH_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "hamarihawa-worker" },
      body: JSON.stringify({ ref: "main" }),
    });
    if (!r.ok) console.log("feed dispatch failed", r.status, await r.text());
  },

  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    // Always HTTPS, always the bare domain.
    // `wrangler dev --var DEV:1` serves plain http locally, so the redirect is skipped there.
    if ((url.protocol === "http:" && !env.DEV) || url.hostname === "www.hamarihawa.org") {
      url.protocol = "https:";
      if (url.hostname === "www.hamarihawa.org") url.hostname = "hamarihawa.org";
      return Response.redirect(url.toString(), 301);
    }
    const res = await handle(request, env, url, ctx);
    if (url.hostname !== "hamarihawa.org") return res;
    const r = new Response(res.body, res);
    r.headers.set("strict-transport-security", "max-age=31536000; includeSubDomains");
    return r;
  },
};

async function handle(request, env, url, ctx) {
  {
    // Approximate visitor location from Cloudflare's IP lookup, so the page can show "your air".
    // Computed per request, never stored or logged by us.
    if (url.pathname === "/api/where") {
      const cf = request.cf || {};
      const body = cf.latitude ? { city: cf.city || "", region: cf.region || "", country: cf.country || "", lat: +cf.latitude, lon: +cf.longitude } : {};
      return new Response(JSON.stringify(body), { headers: { "content-type": "application/json", "cache-control": "private, no-store" } });
    }
    if (url.pathname.startsWith("/api/firms/")) {
      const file = url.pathname.slice("/api/firms/".length);
      if (!FIRMS_FILES.has(file) || !["GET", "HEAD"].includes(request.method)) return new Response("not found", { status: 404 });
      const r = await fetch(FIRMS + file, { method: request.method, cf: { cacheTtl: 600, cacheEverything: true } });
      const h = new Headers({ "content-type": "text/csv; charset=utf-8", "cache-control": "public, max-age=600" });
      if (r.headers.get("last-modified")) h.set("last-modified", r.headers.get("last-modified"));
      return new Response(request.method === "HEAD" ? null : r.body, { status: r.status, headers: h });
    }
    if (url.pathname === "/api/no2.png" || url.pathname === "/api/no2.json") {
      const png = url.pathname.endsWith(".png");
      const body = await env.FEED.get(png ? "no2-png" : "no2-json", { type: png ? "arrayBuffer" : "text", cacheTtl: 300 });
      if (!body) return new Response("not built yet", { status: 503 });
      return new Response(body, { headers: { "content-type": png ? "image/png" : "application/json", "cache-control": "public, max-age=900" } });
    }
    // The fire feed as KML for Google Earth / My Maps (built with the JSON feed, in the GitHub Action).
    if (url.pathname === "/fires.kml") {
      const hours = WINDOWS.has(url.searchParams.get("hours")) ? url.searchParams.get("hours") : "24";
      const body = await env.FEED.get(`kml-${hours}`, { type: "arrayBuffer", cacheTtl: 120 });
      if (!body) return new Response("The KML feed hasn't been built yet. Try again in a few minutes.", { status: 503 });
      return new Response(body, { headers: {
        "content-type": "application/vnd.google-earth.kml+xml; charset=utf-8",
        "content-disposition": `inline; filename="hamarihawa-fires-${hours}h.kml"`,
        "cache-control": "public, max-age=300", "access-control-allow-origin": "*" } });
    }
    if (url.pathname === "/api/no2-geo.png") {
      const body = await env.FEED.get("no2-geo-png", { type: "arrayBuffer", cacheTtl: 300 });
      if (!body) return new Response("not built yet", { status: 503 });
      return new Response(body, { headers: { "content-type": "image/png", "cache-control": "public, max-age=900", "access-control-allow-origin": "*" } });
    }
    // Wind right now on a 1° grid over the plains (Open-Meteo, one request for all points, cached at the edge).
    // Daily archive: the index of per-day totals, and each Pakistan-time day's distinct fire spots.
    if (url.pathname === "/api/days") {
      return edgeCached(ctx, "/api/days", 300, async () => {
        const body = await env.FEED.get("days");
        return body ? json(body, 200, 300) : json(JSON.stringify({}), 200, 60);
      });
    }
    // The busiest districts per day, one KV key per year (dist-YYYY). ?y=YYYY gives one year; without it
    // the years are joined as strings, so the Worker never parses the whole archive.
    if (url.pathname === "/api/districts") {
      const y = url.searchParams.get("y") || "", last = new Date().getUTCFullYear();
      if (y && !(/^\d{4}$/.test(y) && +y >= 2019 && +y <= last)) return json(JSON.stringify({ error: "Use ?y=YYYY, 2019 or later" }), 400, 3600);
      return edgeCached(ctx, y ? `/api/districts?y=${y}` : "/api/districts", 900, async () => {
        const years = y ? [+y] : Array.from({ length: last - 2018 }, (_, i) => 2019 + i);
        const parts = (await Promise.all(years.map((k) => env.FEED.get(`dist-${k}`)))).filter((b) => b && b.length > 2);
        if (parts.length) return json(`{${parts.map((b) => b.slice(1, -1)).join(",")}}`, 200, 900);
        const old = y ? null : await env.FEED.get("dist");  // before the split into years
        return old ? json(old, 200, 900) : json(JSON.stringify({}), 200, 60);
      });
    }
    if (url.pathname === "/api/day") {
      const d = url.searchParams.get("d") || "";
      if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return json(JSON.stringify({ error: "Use ?d=YYYY-MM-DD" }), 400, 3600);
      return edgeCached(ctx, `/api/day?d=${d}`, 900, async () => {
        const body = await env.FEED.get(`day-${d}`);
        return body ? json(body, 200, 900) : json(JSON.stringify({ error: "No archive for that day" }), 404, 300);
      });
    }

    if (url.pathname === "/api/wind") {
      const lats = [], lons = [];
      for (let la = WIND.s; la <= WIND.n; la++) for (let lo = WIND.w; lo <= WIND.e; lo++) { lats.push(la); lons.push(lo); }
      const r = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lats}&longitude=${lons}` +
        "&current=wind_speed_10m,wind_direction_10m&wind_speed_unit=kmh&timezone=GMT", { cf: { cacheTtl: 1800, cacheEverything: true } });
      if (!r.ok) return new Response("wind unavailable", { status: 503 });
      const rows = await r.json();
      const body = { time: rows[0]?.current?.time, lat0: WIND.s, lon0: WIND.w, nx: WIND.e - WIND.w + 1, ny: WIND.n - WIND.s + 1,
        speed: rows.map((x) => x.current.wind_speed_10m), dir: rows.map((x) => x.current.wind_direction_10m),
        source: "Open-Meteo forecast (best-match weather models), 10 m wind, km/h; dir is where the wind comes from" };
      return json(JSON.stringify(body), 200, 900);
    }
    if (url.pathname === "/kml/air.kml") {
      const body = await airKml();
      return body ? kmlResponse(body, 1800) : new Response("City air is unavailable right now.", { status: 503 });
    }
    if (url.pathname === "/kml/traffic.kml") {
      const meta = await env.FEED.get("no2-json", { type: "json", cacheTtl: 300 });
      return meta ? kmlResponse(trafficKml(meta), 3600) : new Response("not built yet", { status: 503 });
    }
    if (url.pathname === "/kml/satellite.kml") return kmlResponse(satelliteKml(), 3600);
    if (url.pathname !== "/api/fires") {
      // Daily fire and district pages, rendered from the archive in KV.
      const res = (await pages(url, env, ctx, edgeCached)) || (await env.ASSETS.fetch(request));
      // hamarihawa.org is the canonical site; keep the workers.dev copy out of search results.
      if (url.hostname.endsWith(".workers.dev")) {
        const r = new Response(res.body, res);
        r.headers.set("x-robots-tag", "noindex");
        return r;
      }
      return res;
    }

    const hours = WINDOWS.has(url.searchParams.get("hours")) ? url.searchParams.get("hours") : "24";
    return edgeCached(ctx, `/api/fires?hours=${hours}`, 120, async () => {
      const body = await env.FEED.get(`fires-${hours}`, { cacheTtl: 120 });
      if (!body) {
        return json(JSON.stringify({ error: "The fire feed hasn't been built yet. Try again in a few minutes." }), 503, 30);
      }
      return json(body, 200, 120);
    });
  }
}

// Answer from this data centre's cache when we can, so repeat requests (and scrapers adding junk
// query strings) don't each cost a KV read. Only successful answers are kept, for `ttl` seconds.
async function edgeCached(ctx, path, ttl, make) {
  const key = new Request(`https://cache.hamarihawa.org${path}`);
  const cache = caches.default;
  const hit = await cache.match(key);
  if (hit) return hit;
  const res = await make();
  if (res.status === 200) {
    const copy = new Response(res.clone().body, res);
    copy.headers.set("cache-control", `public, max-age=${ttl}`);
    ctx.waitUntil(cache.put(key, copy));
  }
  return res;
}

function json(body, status, maxAge) {
  return new Response(body, {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": `public, max-age=${maxAge}`,
      "access-control-allow-origin": "*",
    },
  });
}
