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
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === "www.hamarihawa.org") {
      url.hostname = "hamarihawa.org";
      return Response.redirect(url.toString(), 301);
    }
    if (url.pathname.startsWith("/api/firms/")) {
      const file = url.pathname.slice("/api/firms/".length);
      if (!FIRMS_FILES.has(file) || !["GET", "HEAD"].includes(request.method)) return new Response("not found", { status: 404 });
      const r = await fetch(FIRMS + file, { method: request.method, cf: { cacheTtl: 600, cacheEverything: true } });
      const h = new Headers({ "content-type": "text/csv; charset=utf-8", "cache-control": "public, max-age=600" });
      if (r.headers.get("last-modified")) h.set("last-modified", r.headers.get("last-modified"));
      return new Response(request.method === "HEAD" ? null : r.body, { status: r.status, headers: h });
    }
    if (url.pathname !== "/api/fires") return env.ASSETS.fetch(request);

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
