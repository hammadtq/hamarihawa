// Map on the daily fire pages (/fires/YYYY-MM-DD/): every distinct spot that day from /api/day,
// loaded only when the map scrolls near. One map per language article; only the visible one is drawn.
(() => {
  const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{style}/MapServer/tile/{z}/{y}/{x}";
  const cache = {};
  const data = (d) => (cache[d] ||= fetch(`/api/day?d=${d}`).then((r) => (r.ok ? r.json() : null)).catch(() => null));

  function draw(el) {
    if (el._drawn || !window.L || !el.offsetParent) return;
    el._drawn = true;
    const map = L.map(el, { scrollWheelZoom: false, attributionControl: true }).setView([30.5, 74], 6);
    L.tileLayer(ESRI, { style: "World_Light_Gray_Base", attribution: "Base map © Esri, HERE, Garmin, © OpenStreetMap contributors · Fires: NASA FIRMS", maxNativeZoom: 16 }).addTo(map);
    data(el.dataset.day).then((day) => {
      if (!day?.spots?.length) return;
      const f = Object.fromEntries(day.fields.map((k, i) => [k, i]));
      // v2 day files store each district once, as [name, state, cc] in dict.district.
      const D = day.dict?.district;
      const where = (s) => (D ? D[s[f.district]] || [] : [s[f.district], s[f.state]]);
      const canvas = L.canvas({ padding: 0.3 });
      const pts = [];
      for (const s of day.spots) {
        const ll = [s[f.lat], s[f.lon]];
        pts.push(ll);
        L.circleMarker(ll, { renderer: canvas, radius: 3, weight: 0.6, color: s[f.night] ? "#5b1a14" : "#a3170d", fillColor: s[f.night] ? "#7a2a22" : "#d62d20", fillOpacity: 0.7 })
          .bindTooltip(((w) => `${w[0] || ""}${w[1] ? ", " + w[1] : ""}`)(where(s)), { direction: "top" })
          .addTo(map);
      }
      // Frame where most fires were, so a few far-off spots don't zoom the map out.
      const lat = pts.map((p) => p[0]).sort((a, b) => a - b), lon = pts.map((p) => p[1]).sort((a, b) => a - b);
      const q = (a, x) => a[Math.min(a.length - 1, Math.floor(a.length * x))];
      map.fitBounds([[q(lat, 0.03), q(lon, 0.03)], [q(lat, 0.97), q(lon, 0.97)]], { padding: [16, 16], maxZoom: 9 });
    });
  }

  function watch() {
    document.querySelectorAll(".ff-map[data-day]").forEach((el) => {
      if (el._watched) return draw(el);
      el._watched = true;
      if (!("IntersectionObserver" in window)) return draw(el);
      const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); draw(el); } }, { rootMargin: "300px" });
      io.observe(el);
    });
  }
  watch();
  addEventListener("hh:lang", () => setTimeout(watch, 0));
})();
