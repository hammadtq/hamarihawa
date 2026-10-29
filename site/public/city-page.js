// The city page's moving parts (/air/<city>/; the layout is site/src/citypage.js): the wind rose picks out
// one direction's fires on the live map (near-map.js), the satellite views of the landfill, plant and kilns,
// the map of every mapped source within 50 km (/sources/city/<id>.json, written by scripts/build-pages.py),
// the copy-link button and the section chips. Each language has its own article; only the visible one is drawn.
(() => {
  const IMAGERY = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
  const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{style}/MapServer/tile/{z}/{y}/{x}";
  const ATTR = "Base map © Esri, HERE, Garmin, © OpenStreetMap contributors · Sources: kiln surveys, OpenStreetMap, Carbon Mapper, NASA FIRMS";
  const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const T = {
    en: { kilns: "Brick kilns", industry: "Industrial areas", plants: "Plants", landfills: "Landfills and dumps", hot: "Always-hot sites", no2: "NO₂ peak",
      kiln: ["Brick kiln (circular fixed chimney)", "Brick kiln (fixed chimney)", "Brick kiln (zigzag, the cleaner kind)"], km: (n) => `${n} km from the centre`,
      plant: { coal: "coal power plant", gas: "gas power plant", oil: "oil power plant", power: "power plant", industry: "industrial plant" }, co2: (n) => `${n} t/h of CO₂ measured (Carbon Mapper)`, mw: (n) => `${n} MW`, ind: "Industrial area (OpenStreetMap)",
      dump: "Landfill or dump site", ch4: (n) => `${n} kg/h of methane measured`, burn: (n) => `fire seen on ${n} days in 2025`, hotSite: "Always-hot site", no2Peak: (r) => `Strongest NO₂ peak: ${r}× the region's usual level` },
    ur: { kilns: "اینٹوں کے بھٹے", industry: "صنعتی علاقے", plants: "پلانٹ اور بجلی گھر", landfills: "کچرا کنڈیاں اور ڈھیر", hot: "ہمیشہ گرم جگہیں", no2: "NO₂ کی اونچی جگہ",
      kiln: ["اینٹوں کا بھٹہ (گول، مستقل چمنی)", "اینٹوں کا بھٹہ (مستقل چمنی)", "اینٹوں کا بھٹہ (زگ زیگ، صاف تر قسم)"], km: (n) => `مرکز سے ${n} کلومیٹر`,
      plant: { coal: "کوئلے کا بجلی گھر", gas: "گیس کا بجلی گھر", oil: "تیل کا بجلی گھر", power: "بجلی گھر", industry: "صنعتی پلانٹ" }, co2: (n) => `${n} ٹن فی گھنٹہ CO₂ ناپی گئی (کاربن میپر)`, mw: (n) => `${n} میگاواٹ`, ind: "صنعتی علاقہ (اوپن اسٹریٹ میپ)",
      dump: "کچرا کنڈی یا کوڑے کا ڈھیر", ch4: (n) => `${n} کلوگرام فی گھنٹہ میتھین ناپی گئی`, burn: (n) => `2025 میں ${n} دن آگ دیکھی گئی`, hotSite: "ہمیشہ گرم جگہ", no2Peak: (r) => `NO₂ کی سب سے اونچی جگہ: علاقے کی عام سطح سے ${r} گنا` },
    hi: { kilns: "ईंट भट्ठे", industry: "औद्योगिक इलाक़े", plants: "प्लांट और बिजलीघर", landfills: "लैंडफ़िल और ढेर", hot: "हमेशा गर्म जगहें", no2: "NO₂ का शिखर",
      kiln: ["ईंट भट्ठा (गोल, स्थिर चिमनी)", "ईंट भट्ठा (स्थिर चिमनी)", "ईंट भट्ठा (ज़िगज़ैग, साफ़ क़िस्म)"], km: (n) => `केंद्र से ${n} किमी`,
      plant: { coal: "कोयला बिजलीघर", gas: "गैस बिजलीघर", oil: "तेल बिजलीघर", power: "बिजलीघर", industry: "औद्योगिक प्लांट" }, co2: (n) => `${n} टन/घंटा CO₂ मापी गई (कार्बन मैपर)`, mw: (n) => `${n} मेगावाट`, ind: "औद्योगिक इलाक़ा (ओपनस्ट्रीटमैप)",
      dump: "लैंडफ़िल या कूड़े का ढेर", ch4: (n) => `${n} किलो/घंटा मीथेन मापी गई`, burn: (n) => `2025 में ${n} दिन आग दिखी`, hotSite: "हमेशा गर्म जगह", no2Peak: (r) => `NO₂ का सबसे ऊँचा शिखर: इलाक़े के सामान्य स्तर का ${r} गुना` },
  };
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const rad = Math.PI / 180;
  const dist = (a, b, c, d) => 2 * 6371 * Math.asin(Math.sqrt(Math.sin(((c - a) * rad) / 2) ** 2 + Math.cos(a * rad) * Math.cos(c * rad) * Math.sin(((d - b) * rad) / 2) ** 2));
  const visible = (el) => !!el.offsetParent;
  const whenNear = (el, fn) => {
    if (el._watched) return visible(el) && fn(el);
    el._watched = true;
    if (!("IntersectionObserver" in window)) return fn(el);
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting) && visible(el)) { io.disconnect(); fn(el); } }, { rootMargin: "300px" });
    io.observe(el);
  };

  // ---------- The wind rose and the live map ----------
  document.addEventListener("click", (e) => pickSector(e.target.closest?.(".cp-rose [data-sector]")));
  document.addEventListener("keydown", (e) => {
    const p = e.target.closest?.(".cp-rose [data-sector]");
    if (p && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); pickSector(p); }
  });
  function pickSector(p) {
    if (!p) return;
    const box = p.closest(".cp-smoke"), map = box?.querySelector(".ff-map[data-near]"), all = [...box.querySelectorAll("[data-sector]")];
    const i = p.getAttribute("aria-pressed") === "true" ? -1 : +p.dataset.sector;
    all.forEach((q) => { q.setAttribute("aria-pressed", String(+q.dataset.sector === i)); q.style.opacity = i < 0 || +q.dataset.sector === i ? "" : "0.35"; });
    if (!map) return;
    if (map._sector) map._sector(i);
    else map._pendingSector = i;
  }

  // ---------- Satellite views ----------
  function satView(fig) {
    if (fig._map || !window.L || !visible(fig)) return;
    const holder = document.createElement("div");
    fig.prepend(holder);
    const map = (fig._map = L.map(holder, { zoomControl: false, attributionControl: false, dragging: false, scrollWheelZoom: false, touchZoom: false,
      doubleClickZoom: false, boxZoom: false, keyboard: false, tap: false }));
    L.tileLayer(IMAGERY, { maxNativeZoom: 18, maxZoom: 18 }).addTo(map);
    map.setView([+fig.dataset.lat, +fig.dataset.lon], 16, { animate: false });
  }

  // ---------- Every mapped source within 50 km ----------
  const COLORS = { kilns: "#a0522d", industry: "#7d8590", plants: "#2f6f9f", landfills: "#5e7d2e", hot: "#d62d20", no2: "#7a3fa0" };
  function srcMap(el) {
    if (el._map || !window.L || !visible(el)) return;
    const l = el.dataset.lang, t = T[l] || T.en, lat = +el.dataset.lat, lon = +el.dataset.lon;
    const nf = new Intl.NumberFormat(LOC[l] || "en-GB", { maximumFractionDigits: 0 }), km = (a, b) => t.km(nf.format(dist(lat, lon, a, b)));
    const map = (el._map = L.map(el, { scrollWheelZoom: false, zoomSnap: 0.25 }));
    L.tileLayer(ESRI, { style: "World_Light_Gray_Base", attribution: ATTR, maxNativeZoom: 16 }).addTo(map);
    L.tileLayer(ESRI, { style: "World_Light_Gray_Reference", maxNativeZoom: 16 }).addTo(map);
    L.circle([lat, lon], { radius: 50000, color: "#777", weight: 1, dashArray: "4 4", fill: false, interactive: false }).addTo(map);
    map.fitBounds(L.latLng(lat, lon).toBounds(104000), { padding: [6, 6], animate: false });
    L.circleMarker([lat, lon], { radius: 7, weight: 3, color: "#fff", fillColor: "#1d1d1b", fillOpacity: 1, interactive: false }).addTo(map);
    fetch(el.dataset.srcmap).then((r) => (r.ok ? r.json() : Promise.reject(r.status))).then((d) => {
      const canvas = L.canvas({ padding: 0.3 }), groups = {};
      const add = (key, layer) => (groups[key] ||= L.layerGroup().addTo(map)).addLayer(layer);
      for (const [a, b, area] of d.i || []) add("industry", L.circleMarker([a, b], { renderer: canvas, radius: Math.min(7, 2 + Math.sqrt(area || 0) / 25), weight: 0, fillColor: COLORS.industry, fillOpacity: 0.45 }).bindTooltip(`${esc(t.ind)}<br>${km(a, b)}`));
      for (const [a, b, ty] of d.k || []) add("kilns", L.circleMarker([a, b], { renderer: canvas, radius: 3, weight: 0.6, color: "#5c2c12", fillColor: COLORS.kilns, fillOpacity: 0.85 }).bindTooltip(`${esc(t.kiln[ty] || t.kiln[1])}<br>${km(a, b)}`));
      for (const [a, b, name, rate, heat] of d.l || []) {
        const lines = [`<b>${esc(name || t.dump)}</b>`, rate ? esc(t.ch4(nf.format(rate))) : "", heat ? esc(t.burn(nf.format(heat))) : "", km(a, b)].filter(Boolean);
        add("landfills", L.circleMarker([a, b], { radius: rate ? 9 : 6, weight: 2, color: "#fff", fillColor: COLORS.landfills, fillOpacity: 0.95 }).bindTooltip(lines.join("<br>")));
      }
      for (const [a, b, fuel, name, mw, co2] of d.p || []) {
        const lines = [`<b>${esc(name || t.plant[fuel] || "")}</b>`, esc(t.plant[fuel] || ""), mw ? esc(t.mw(nf.format(mw))) : "", co2 ? esc(t.co2(nf.format(co2))) : "", km(a, b)].filter(Boolean);
        add("plants", L.circleMarker([a, b], { radius: 6 + Math.sqrt(mw || 100) / 5, weight: 2, color: "#fff", fillColor: COLORS.plants, fillOpacity: 0.95 }).bindTooltip(lines.join("<br>")));
      }
      for (const [a, b, days, name] of d.h || []) add("hot", L.circleMarker([a, b], { radius: 5 + Math.sqrt(days) / 1.5, weight: 2.5, color: COLORS.hot, fill: false }).bindTooltip(`<b>${esc(name || t.hotSite)}</b><br>${esc(t.burn(nf.format(days)))}<br>${km(a, b)}`));
      const [pa, pb, pr] = (el.dataset.no2 || "").split(",").map(Number);
      if (pr) add("no2", L.circle([pa, pb], { radius: 3000, weight: 2, dashArray: "4 4", color: COLORS.no2, fillColor: COLORS.no2, fillOpacity: 0.15 }).bindTooltip(`<b>${esc(t.no2Peak(new Intl.NumberFormat(LOC[l] || "en-GB", { maximumFractionDigits: 1 }).format(pr)))}</b><br>${km(pa, pb)}`));
      const counts = { kilns: d.k?.length, industry: d.i?.length, plants: d.p?.length, landfills: d.l?.length, hot: d.h?.length, no2: pr ? 1 : 0 };
      const bar = document.querySelector(`[data-layers-for="${el.id}"]`);
      if (bar) {
        bar.innerHTML = Object.keys(COLORS).filter((k) => groups[k]).map((k) =>
          `<button type="button" data-layer="${k}" aria-pressed="true"><i style="background:${COLORS[k]}"></i>${esc(t[k])}${k === "no2" ? "" : ` <b>${nf.format(counts[k] || 0)}</b>`}</button>`).join("");
        bar.addEventListener("click", (e) => {
          const b = e.target.closest("button[data-layer]");
          if (!b) return;
          const on = b.getAttribute("aria-pressed") !== "true";
          b.setAttribute("aria-pressed", String(on));
          if (on) groups[b.dataset.layer].addTo(map); else map.removeLayer(groups[b.dataset.layer]);
        });
      }
    }).catch((e) => {
      console.warn("[hh] sources map", e);
      const p = document.createElement("p");
      p.className = "muted"; p.textContent = el.dataset.fail || "";
      el.after(p);
    });
  }

  // ---------- Copy link ----------
  document.addEventListener("click", async (e) => {
    const b = e.target.closest?.("[data-copy]");
    if (!b) return;
    const was = b.textContent;
    try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = b.dataset.done; } catch { b.textContent = b.dataset.copy; return; }
    setTimeout(() => (b.textContent = was), 2000);
  });

  // ---------- Section chips: mark the section in view ----------
  function chips() {
    document.querySelectorAll(".cp-jump").forEach((nav) => {
      if (nav._done || !visible(nav)) return;
      nav._done = true;
      const links = [...nav.querySelectorAll("a")], io = new IntersectionObserver((es) => es.forEach((en) => {
        if (en.isIntersecting) links.forEach((a) => a.classList.toggle("on", a.getAttribute("href") === "#" + en.target.id));
      }), { rootMargin: "-35% 0px -60% 0px" });
      links.forEach((a) => { const s = document.getElementById(a.getAttribute("href").slice(1)); if (s) io.observe(s); });
    });
  }

  function watch() {
    document.querySelectorAll("figure[data-sat]").forEach((f) => whenNear(f, satView));
    document.querySelectorAll(".ff-map[data-srcmap]").forEach((m) => whenNear(m, srcMap));
    chips();
  }
  watch();
  addEventListener("hh:lang", () => setTimeout(watch, 0));
})();
