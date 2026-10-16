// Hamari Hawa: serves the static site and the fire feed.
// The feed itself is built every 15 minutes by scripts/build-feed.py (GitHub Actions)
// and stored in KV, because naming every fire after its village is too much work
// for one request on the free Workers plan. Satellites only pass a few times a day anyway.

const WINDOWS = new Set(["24", "48", "168"]);

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

  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === "www.hamarihawa.org") {
      url.hostname = "hamarihawa.org";
      return Response.redirect(url.toString(), 301);
    }
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
    if (url.pathname !== "/api/fires") {
      const res = await env.ASSETS.fetch(request);
      // hamarihawa.org is the canonical site; keep the workers.dev copy out of search results.
      if (url.hostname.endsWith(".workers.dev")) {
        const r = new Response(res.body, res);
        r.headers.set("x-robots-tag", "noindex");
        return r;
      }
      return res;
    }

    const hours = WINDOWS.has(url.searchParams.get("hours")) ? url.searchParams.get("hours") : "24";
    const body = await env.FEED.get(`fires-${hours}`, { cacheTtl: 120 });
    if (!body) {
      return json(JSON.stringify({ error: "The fire feed hasn't been built yet. Try again in a few minutes." }), 503, 30);
    }
    return json(body, 200, 120);
  },
};

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
