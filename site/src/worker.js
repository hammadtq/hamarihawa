// Hamari Hawa: serves the static site and the fire feed.
// The feed itself is built every 15 minutes by scripts/build-feed.py (GitHub Actions)
// and stored in KV, because naming every fire after its village is too much work
// for one request on the free Workers plan. Satellites only pass a few times a day anyway.

const WINDOWS = new Set(["24", "48", "168"]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === "www.hamarihawa.org") {
      url.hostname = "hamarihawa.org";
      return Response.redirect(url.toString(), 301);
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
