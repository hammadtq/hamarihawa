(() => {
  "use strict";

  const I18N = window.HH_I18N, CITIES = window.HH_CITIES, DIRS = window.HH_DIRS;
  const LOCALES = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const POLL_MS = 5 * 60 * 1000;
  const PAGE = 60;
  const SATS = ["Suomi NPP", "NOAA-20", "NOAA-21", "Aqua", "Terra"];

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
  };

  const state = {
    // ?lang=ur in the URL wins (shareable language links), then the saved choice, then the browser's.
    lang: I18N[new URLSearchParams(location.search).get("lang")] ? new URLSearchParams(location.search).get("lang")
      : I18N[store.get("hh-lang")] ? store.get("hh-lang") : guessLang(),
    hours: 24,
    cc: "",
    layer: "none",
    dayOffset: 0,
    data: null,
    seen: new Set(),
    shown: PAGE,
    air: null,
    wind: null,
    sort: "aqi",
    allCards: false,
    me: null,
  };

  function guessLang() {
    const l = (navigator.language || "en").toLowerCase();
    return l.startsWith("ur") ? "ur" : l.startsWith("hi") ? "hi" : "en";
  }

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const t = (k, vars) => {
    let s = I18N[state.lang][k] ?? I18N.en[k] ?? k;
    if (vars) for (const [a, b] of Object.entries(vars)) s = s.split(`{${a}}`).join(b);
    return s;
  };
  const nf = (n, opts) => new Intl.NumberFormat(LOCALES[state.lang], opts).format(n);
  const compact = (n) => nf(n, { notation: "compact", maximumFractionDigits: 1 });

  // ---------- Sketch borders ----------
  const hasRough = typeof window.rough !== "undefined";
  if (!hasRough) document.documentElement.classList.add("no-rough");
  const sketchObs = hasRough ? new ResizeObserver((entries) => entries.forEach((e) => drawSketch(e.target))) : null;

  function drawSketch(el) {
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    let svg = el.querySelector(":scope > svg.rough");
    if (!svg) {
      svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("class", "rough");
      svg.setAttribute("aria-hidden", "true");
      el.appendChild(svg);
    }
    if (svg.dataset.size === `${w}x${h}`) return;
    svg.dataset.size = `${w}x${h}`;
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.innerHTML = "";
    const rc = rough.svg(svg);
    const seed = +el.dataset.seed || 1 + ((w * 7 + h * 13) % 97);
    svg.appendChild(rc.rectangle(1.5, 1.5, w - 3, h - 3, {
      roughness: Math.min(1.6, 0.6 + 300 / Math.max(w, h)), bowing: 0.8, stroke: "#2b2b2b", strokeWidth: 1.1, seed,
    }));
  }
  function sketchAll(root = document) {
    if (!hasRough) return;
    $$(".sketch", root).forEach((el) => { if (!el.dataset.sk) { el.dataset.sk = 1; sketchObs.observe(el); } });
  }

  // ---------- Map ----------
  // All of Pakistan and India (scripts/geo.py REGION), and the northern plains the stubble season is about.
  const REGION = [[6, 60.5], [37.5, 97.5]], NORTH = [[28.5, 68], [33.5, 78]];
  const map = L.map("map", { zoomControl: false, preferCanvas: true, minZoom: 3, maxZoom: 13, scrollWheelZoom: false,
    zoomSnap: 0.25, maxBounds: [[0, 50], [44, 106]], maxBoundsViscosity: 0.8 });
  // Wheel-zoom only after the reader clicks the map, so scrolling the page doesn't get trapped.
  map.on("click focus", () => map.scrollWheelZoom.enable());
  map.getContainer().addEventListener("mouseleave", () => map.scrollWheelZoom.disable());

  // Trackpad pinch always zooms the map, never the page. Chrome/Edge/Brave/Firefox send it as
  // wheel events with ctrlKey set; Safari sends gesture events.
  (() => {
    const el = map.getContainer();
    const clampZ = (z) => Math.max(map.getMinZoom(), Math.min(map.getMaxZoom(), z));
    let pending = 0, at = null, raf = 0;
    el.addEventListener("wheel", (e) => {
      if (!e.ctrlKey || map.scrollWheelZoom.enabled()) return; // ordinary scrolling, or Leaflet already handles it
      e.preventDefault();
      pending += e.deltaY;
      at = map.mouseEventToContainerPoint(e);
      if (!raf) raf = requestAnimationFrame(() => {
        raf = 0;
        const z = clampZ(map.getZoom() - pending * 0.015);
        pending = 0;
        map.setZoomAround(at, z, { animate: false });
      });
    }, { passive: false });
    let startZoom = null;
    el.addEventListener("gesturestart", (e) => { e.preventDefault(); startZoom = map.getZoom(); }, { passive: false });
    el.addEventListener("gesturechange", (e) => {
      e.preventDefault();
      if (startZoom == null) return;
      map.setZoomAround(map.mouseEventToContainerPoint(e), clampZ(startZoom + Math.log2(e.scale)), { animate: false });
    }, { passive: false });
    el.addEventListener("gestureend", (e) => { e.preventDefault(); startZoom = null; }, { passive: false });
  })();
  const zoomCtl = L.control.zoom({ position: "topright" }).addTo(map);
  // Phones open on the north in the burning season (October to February), when that is where the fires are.
  const season = [9, 10, 11, 0, 1].includes(new Date().getMonth());
  map.fitBounds(window.innerWidth < 860 && season ? NORTH : REGION);
  map.createPane("roads").style.zIndex = 340; // under the NO2 overlay
  map.getPane("roads").style.pointerEvents = "none";
  map.createPane("overlay").style.zIndex = 350;
  map.createPane("labels").style.zIndex = 450;
  map.getPane("labels").style.pointerEvents = "none";
  map.createPane("fires").style.zIndex = 500;

  const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{style}/MapServer/tile/{z}/{y}/{x}";
  const esriAttr = "Base map © <a href='https://www.esri.com/'>Esri</a>, HERE, Garmin, © <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>";
  L.tileLayer(ESRI, { style: "World_Light_Gray_Base", attribution: esriAttr, maxNativeZoom: 16, maxZoom: 19 }).addTo(map);
  L.tileLayer(ESRI, { style: "World_Light_Gray_Reference", pane: "labels", maxNativeZoom: 16, maxZoom: 19 }).addTo(map);

  const LAYERS = {
    none: null,
    no2: { id: "TROPOMI_L2_Nitrogen_Dioxide_Tropospheric_Column", lvl: 6, ext: "png", op: 0.6, lag: 1, fill: 3,
      grad: ["#fffcc7", "#ffde6a", "#ffb339", "#ff7c20", "#fe3612", "#ed1c0d", "#7f000e"], ticks: ["0", "1", "2 ×10¹⁶ molec/cm²"] },
    aod: { id: "MODIS_Combined_Value_Added_AOD", lvl: 6, ext: "png", op: 0.65, lag: 1, fill: 2,
      grad: ["#fffdcd", "#ffdf6c", "#ffaf36", "#ff701e", "#f52810", "#c7030d", "#7d000e"], ticks: ["0", "0.3", "0.6", "1+"] },
    // OMPS on Suomi NPP: OMI on the ageing Aura satellite began serving corrupt tiles in Oct 2026. Same colour scale.
    smoke: { id: "OMPS_Aerosol_Index", lvl: 6, ext: "png", op: 0.65, lag: 1, fill: 2,
      grad: ["#ffffff", "#dada7f", "#fcfc07", "#cfcb00", "#fa2300", "#cc0100", "#730019"], ticks: ["0", "2.5", "5"] },
    truecolor: { id: "VIIRS_SNPP_CorrectedReflectance_TrueColor", lvl: 9, ext: "jpg", op: 1, lag: 1, fill: 2, grad: null, ticks: null },
    // Our own 14-day NO2 average and its labelled hotspots (scripts/build-no2.py), not a GIBS layer.
    traffic: { custom: true, op: 0.85, grad: ["rgba(255,200,80,.5)", "#f07828", "#cd281e", "#781446"], ticks: ["2×", "3×", "5×+"] },
  };
  const order = ["none", "traffic", "no2", "aod", "smoke", "truecolor"];
  const HOT_ICONS = {
    traffic: '<path d="M5 15h14l-1.5-5h-11zM7 15v3M17 15v3M8 18h0M16 18h0M6.5 10l1.5-3h8l1.5 3" />',
    plant: '<path d="M4 20V11l5 3V11l5 3V6h3v14zM15 6V3h2v3" />',
    industry: '<path d="M4 20V11l5 3V11l5 3V8h5v12z" />',
    kilns: '<path d="M7 20V8h4v12M13 20V5h4v15M5 20h14" />',
    corridor: '<path d="M8 21l3-18M16 21l-3-18M12 6v2M12 11v2M12 16v2" />',
  };
  const HOT_COLORS = { traffic: "#cd281e", plant: "#2b2b2b", industry: "#5a508c", kilns: "#7a4a2a", corridor: "#8a7f6a" };
  let trafficMeta = null;
  let trafficLoading = null;
  function loadTrafficMeta() {
    trafficLoading = trafficLoading || fetch("/api/no2.json", { cache: "no-cache" }).then((r) => (r.ok ? r.json() : null)).catch(() => null)
      .then((m) => { trafficMeta = m; if (!m) trafficLoading = null; return m; });
    return trafficLoading;
  }
  // Major roads from OpenStreetMap, drawn under the NO2 so people can see which corridors line up
  // with the hotspots. Context only: the satellite can't resolve single roads (~5 km pixels).
  let roadsLoading = null;
  const ROAD_STYLE = [{ weight: 1.8, opacity: 0.75 }, { weight: 1.3, opacity: 0.65 }, { weight: 0.8, opacity: 0.55 }];
  const roadLines = (d, renderer) => {
    const byClass = [[], [], []];
    for (const [c, f] of d.items) {
      const line = [];
      for (let i = 0; i < f.length; i += 2) line.push([f[i + 1], f[i]]);
      byClass[c].push(line);
    }
    return byClass.map((ls, c) => L.polyline(ls, { renderer, color: "#4a4a4f", interactive: false, smoothFactor: 1.5, ...ROAD_STYLE[c] }));
  };
  function roadsLayer() {
    roadsLoading = roadsLoading || fetch("sources/roads.json").then((r) => (r.ok ? r.json() : null)).catch(() => null).then((d) => {
      if (!d) { roadsLoading = null; return null; }
      const renderer = L.canvas({ pane: "roads", padding: 0.3 });
      const lines = roadLines(d, renderer);
      const g = L.layerGroup([lines[0], lines[1]]);
      // Primary roads only once zoomed in, so the regional view stays readable; their file is fetched then too.
      let primary = null;
      const loadPrimary = () => (primary = primary || fetch("sources/roads-primary.json").then((r) => (r.ok ? r.json() : null)).catch(() => null)
        .then((p) => (p ? roadLines(p, renderer)[2] : (primary = null))));
      const refresh = () => {
        if (map.getZoom() < 8) { primary?.then((l) => l && g.removeLayer(l)); return; }
        loadPrimary().then((l) => { if (l && map.getZoom() >= 8 && map.hasLayer(g)) g.addLayer(l); });
      };
      g.on("add", () => { refresh(); map.on("zoomend", refresh); });
      g.on("remove", () => map.off("zoomend", refresh));
      return g;
    });
    return roadsLoading;
  }
  async function trafficLayer() {
    const [, roads] = await Promise.all([loadTrafficMeta(), roadsLayer()]);
    const g = L.layerGroup();
    if (roads) g.addLayer(roads);
    if (!trafficMeta) return g;
    L.imageOverlay(`/api/no2.png?b=${encodeURIComponent(trafficMeta.built)}`, trafficMeta.bounds, { pane: "overlay", opacity: 1, className: "no2-img",
      attribution: "Sentinel-5P TROPOMI via <a href='https://earthdata.nasa.gov/gibs'>NASA GIBS</a>" }).addTo(g);
    // Hotspots are sorted strongest first; show the top 15 regionally and the rest as you zoom in.
    const markers = [];
    const showFor = (z) => (z <= 6 ? 15 : z <= 7 ? 30 : 60);
    trafficMeta.hotspots.forEach((h, rank) => {
      const [lat, lon, ratio, kind, site, km, town] = h;
      const icon = L.divIcon({ className: "", iconSize: [22, 22], iconAnchor: [11, 11],
        html: `<div class="no2-hot" style="--c:${HOT_COLORS[kind]}"><svg viewBox="0 0 24 24">${HOT_ICONS[kind]}</svg></div>` });
      const m = L.marker([lat, lon], { icon, pane: "fires", keyboard: false })
        .bindPopup(() => `<b>${esc(t("hot_" + kind))}</b><br>${esc(kind === "kilns" ? t("hotKilns", { n: site.split(" ")[0], town }) : siteName(site))}
          <br>${esc(t("hotLine", { x: nf(ratio, { maximumFractionDigits: 1 }), d: nf(trafficMeta.days.length) }))}
          <br><span class="muted">${esc(t("hotWhy_" + kind))}</span>`, { maxWidth: 270 });
      markers.push([rank, m]);
    });
    const markerGroup = L.layerGroup().addTo(g);
    const refresh = () => {
      markerGroup.clearLayers();
      const n = showFor(map.getZoom());
      for (const [rank, m] of markers) if (rank < n) markerGroup.addLayer(m);
    };
    refresh();
    g.on("add", () => map.on("zoomend", refresh));
    g.on("remove", () => map.off("zoomend", refresh));
    return g;
  }
  let overlay = null;

  // GIBS days are UTC days; a layer with lag publishes a day late.
  const lagOf = () => LAYERS[state.layer]?.lag || 0;
  // Today's tiles are often still processing (hatched grey), so lagged layers start a day back.
  function gibsDate(extra = 0) {
    return new Date(Date.now() - (state.dayOffset + lagOf() + extra) * 864e5).toISOString().slice(0, 10);
  }
  function setLayer(name) {
    state.layer = name;
    if (overlay) { map.removeLayer(overlay); overlay = null; }
    const L1 = LAYERS[name];
    if (L1 && L1.custom) {
      map.getPane("overlay").style.opacity = L1.op;
      trafficLayer().then((g) => { if (state.layer === name) { overlay = g.addTo(map); renderPanel(); } });
    } else if (L1) {
      // Satellites miss strips (orbit gaps, clouds). For "fill" layers, stack earlier days
      // underneath so the gaps show the most recent earlier reading; the newest day draws on top.
      overlay = L.layerGroup().addTo(map);
      const pane = name === "truecolor" ? "tilePane" : "overlay";
      if (pane === "overlay") map.getPane("overlay").style.opacity = L1.op;
      for (let back = (L1.fill || 1) - 1; back >= 0; back--) {
        L.tileLayer(
          `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${L1.id}/default/${gibsDate(back)}/GoogleMapsCompatible_Level${L1.lvl}/{z}/{y}/{x}.${L1.ext}`,
          { pane, maxNativeZoom: L1.lvl, maxZoom: 13, opacity: 1, bounds: [[-85, -180], [85, 180]],
            attribution: back === 0 ? "<a href='https://earthdata.nasa.gov/gibs'>NASA GIBS</a>" : "" }
        ).addTo(overlay);
      }
    }
    renderPanel();
  }

  function renderPanel() {
    const box = $("#layerRadios");
    box.innerHTML = order.map((k) =>
      `<label><input type="radio" name="layer" value="${k}" ${state.layer === k ? "checked" : ""}> <span>${esc(t(k))}</span></label>`).join("");
    $$("input", box).forEach((r) => r.addEventListener("change", () => setLayer(r.value)));
    const L1 = LAYERS[state.layer];
    $("#daystep").hidden = !L1 || !!L1.custom;
    const off = state.dayOffset;
    const gd = gibsDate();
    const back = Math.round((Date.parse(new Date().toISOString().slice(0, 10)) - Date.parse(gd)) / 864e5);
    const rel = back === 0 ? t("today") : back === 1 ? t("yesterday") : t("daysAgo", { n: nf(back) });
    $("#dayLabel").textContent = `${fmtDay(Date.parse(gd + "T12:00:00Z"))} · ${rel}`;
    const filled = L1 && L1.custom && trafficMeta ? t("trafficDays", { from: fmtDay(Date.parse(trafficMeta.days[0] + "T12:00:00Z")), to: fmtDay(Date.parse(trafficMeta.days[trafficMeta.days.length - 1] + "T12:00:00Z")) })
      : L1 && L1.fill > 1 ? t("gapsFrom", { days: [...Array(L1.fill - 1)].map((_, i) => fmtDay(Date.parse(gibsDate(i + 1) + "T12:00:00Z"))).reverse().join(" – ") }) : "";
    $("#dayPrev").disabled = off >= 6;
    $("#dayNext").disabled = off <= 0;
    $("#legend").innerHTML = L1 && L1.grad
      ? `<div class="bar" style="background:linear-gradient(90deg,${L1.grad.join(",")})"></div><div class="ticks">${L1.ticks.map((x) => `<span>${x}</span>`).join("")}</div>`
      : "";
    $("#layerNote").textContent = L1 ? `${t(state.layer + "_note")}${filled ? " " + filled : ""}${state.layer === "traffic" ? " " + t("roadsNote") : ""}` : t("fires_note");
    window.dispatchEvent(new Event("hh:layer"));
    $("#ageKey").innerHTML = `<span><i style="background:var(--fire)"></i>${esc(t("age_3"))}</span><span><i style="background:var(--fire-2)"></i>${esc(t("age_12"))}</span><span><i style="background:var(--fire-3)"></i>${esc(t("age_old"))}</span>`;
  }
  $("#dayPrev").addEventListener("click", () => { state.dayOffset = Math.min(6, state.dayOffset + 1); setLayer(state.layer); });
  $("#dayNext").addEventListener("click", () => { state.dayOffset = Math.max(0, state.dayOffset - 1); setLayer(state.layer); });
  $(".panel-h").addEventListener("click", () => { if (window.innerWidth < 860) $("#panel").classList.toggle("collapsed"); });
  if (window.innerWidth < 860) $("#panel").classList.add("collapsed");

  // Clouds at the last satellite pass, redrawn as pencil hatching.
  // GIBS serves MODIS cloud fraction in a rainbow palette; we look each pixel up in NASA's
  // colour table (0-100 percent) and paint only real cloud, so the white map stays readable.
  const CF_PAL = "660077660177660277660377660477660577b70f8db7108db7118db7128db7138db7148d0000640001640002640003640004640005640006640000aa0001aa0002aa0003aa0004aa0005aa0000ff0001ff0002ff0003ff0004ff0005ff0088ee0188ee0288ee0388ee0488ee0588ee0688ee00500001500002500003500004500005500000880001880002880003880004880005880000dc0001dc0002dc0003dc0004dc0005dc0006dc00ffff00ffff01ffff02ffff03ffff04ffff05f0be40f0be41f0be42f0be43f0be44f0be45bb8800bb8801bb8802bb8803bb8804bb8805bb88067a5a037a5a047a5a057a5a067a5a077a5a086e00006e00016e00026e00036e00046e0005aa0000aa0001aa0002aa0003aa0004aa0005aa0006ff0000ff0001ff0002ff0003ff0004ff0005";
  const cfValue = new Map();
  for (let i = 0; i < CF_PAL.length / 6; i++) cfValue.set(parseInt(CF_PAL.slice(i * 6, i * 6 + 6), 16), i);
  const hatch = (() => {
    const c = document.createElement("canvas");
    c.width = c.height = 10;
    const g = c.getContext("2d");
    g.fillStyle = "rgba(120,130,145,0.35)";
    g.fillRect(0, 0, 10, 10);
    g.strokeStyle = "rgba(70,78,90,0.55)";
    g.lineWidth = 1;
    g.beginPath(); g.moveTo(-2, 12); g.lineTo(12, -2); g.moveTo(-2, 2); g.lineTo(2, -2); g.moveTo(8, 12); g.lineTo(12, 8); g.stroke();
    return c;
  })();
  const CloudLayer = L.TileLayer.extend({
    createTile(coords, done) {
      const tile = document.createElement("canvas");
      tile.width = tile.height = 256;
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        const g = tile.getContext("2d");
        g.drawImage(img, 0, 0);
        const d = g.getImageData(0, 0, 256, 256), px = d.data;
        for (let i = 0; i < px.length; i += 4) {
          const f = px[i + 3] ? cfValue.get((px[i] << 16) | (px[i + 1] << 8) | px[i + 2]) : undefined;
          // Under ~50 percent cloud the satellite still sees most of the ground: leave it clear.
          px[i + 3] = f == null || f < 50 ? 0 : Math.round(Math.min(1, (f - 50) / 40) * 255);
        }
        g.putImageData(d, 0, 0);
        g.globalCompositeOperation = "source-in";
        g.fillStyle = g.createPattern(hatch, "repeat");
        g.fillRect(0, 0, 256, 256);
        done(null, tile);
      };
      img.onerror = () => done(null, tile);
      img.src = this.getTileUrl(coords);
      return tile;
    },
  });
  map.createPane("clouds").style.zIndex = 420;
  map.getPane("clouds").style.pointerEvents = "none";
  let cloudLayer = null;
  function cloudPass() {
    // Match the clouds to the newest pass in the feed: day passes use Aqua's day product, night passes its night one.
    const d = state.data;
    const ts = d?.latest || Date.now() - 864e5;
    const ev = d?.events?.find((e) => e.t === d.latest);
    return { date: new Date(ts).toISOString().slice(0, 10), night: !!ev?.night };
  }
  function renderClouds() {
    if (cloudLayer) { map.removeLayer(cloudLayer); cloudLayer = null; }
    if (!$("#cloudsOn").checked) { $("#cloudNote").textContent = ""; return; }
    const p = cloudPass();
    const id = p.night ? "MODIS_Aqua_Cloud_Fraction_Night" : "MODIS_Aqua_Cloud_Fraction_Day";
    cloudLayer = new CloudLayer(
      `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${id}/default/${p.date}/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png`,
      { pane: "clouds", maxNativeZoom: 6, maxZoom: 13, opacity: 0.6 }
    ).addTo(map);
    $("#cloudNote").textContent = t("clouds_note", { day: fmtDay(Date.parse(p.date + "T12:00:00Z")), when: p.night ? t("nightPass") : t("daytime") });
  }
  $("#cloudsOn").addEventListener("change", renderClouds);

  // Fire points
  const fireRenderer = L.canvas({ pane: "fires", padding: 0.3 });
  const fireLayer = L.layerGroup().addTo(map);
  const pulseLayer = L.layerGroup().addTo(map);
  $("#firesOn").addEventListener("change", (e) => {
    if (e.target.checked) { fireLayer.addTo(map); pulseLayer.addTo(map); } else { map.removeLayer(fireLayer); map.removeLayer(pulseLayer); }
  });

  function ageColor(ts) {
    const h = (Date.now() - ts) / 36e5;
    return h < 3 ? "#d62d20" : h < 12 ? "#f08a24" : "#a07454";
  }

  function renderFires() {
    fireLayer.clearLayers();
    pulseLayer.clearLayers();
    const d = state.data;
    if (!d) return;
    const pts = d.mapPoints.filter((p) => !state.cc || p[7] === state.cc).slice().reverse(); // oldest first, newest drawn on top
    for (const p of pts) {
      const [lat, lon, ts, frp, sat, place, district, cc, kind] = p;
      L.circleMarker([lat, lon], {
        renderer: fireRenderer, radius: Math.min(10, 2.6 + Math.sqrt(frp) * 0.7), color: "#ffffff", weight: 0.6,
        fillColor: ageColor(ts), fillOpacity: 0.82,
      }).bindPopup(() => popupHtml({ place, district, cc, t: ts, frp, sat: SATS[sat], kind }), { maxWidth: 260 }).addTo(fireLayer);
    }
    const latest = d.latest;
    if (latest && Date.now() - latest < 6 * 36e5) {
      d.events.filter((e) => latest - e.t < 30 * 60 * 1000 && (!state.cc || e.cc === state.cc)).slice(0, 40).forEach((e) =>
        L.marker([e.flat, e.flon], { icon: L.divIcon({ className: "", html: '<div class="fire-pulse"></div>', iconSize: [22, 22] }), interactive: false, pane: "fires" }).addTo(pulseLayer));
    }
  }

  function popupHtml(x) {
    return `<b>${esc(x.place || "—")}</b><br>${esc([x.district, x.cc === "PK" ? t("pk") : x.cc === "IN" ? t("in") : ""].filter(Boolean).join(", "))}<br>
      ${esc(fmtTime(x.t))} · ${esc(ago(x.t))}<br>${esc(kindLabel(x.kind, x.sites))}<br>
      <span class="muted">${esc(t("by", { sat: x.sat }))} · FRP ${nf(x.frp)} MW</span>`;
  }

  // ---------- Feed ----------
  function fmtTime(ts) {
    return new Intl.DateTimeFormat(LOCALES[state.lang], { hour: "2-digit", minute: "2-digit", hour12: false }).format(ts);
  }
  function fmtDay(ts) {
    return new Intl.DateTimeFormat(LOCALES[state.lang], { day: "numeric", month: "short" }).format(ts);
  }
  function ago(ts) {
    const m = Math.max(1, Math.round((Date.now() - ts) / 6e4));
    if (m < 60) return t("ago_m", { n: nf(m) });
    const h = Math.round(m / 60);
    if (h < 48) return t("ago_h", { n: nf(h) });
    return t("ago_d", { n: nf(Math.round(h / 24)) });
  }
  // Build scripts use a few generic English labels for unnamed sites; show them in the reader's language.
  const GENERIC = { "Brick kiln": "gen_brick_kiln", "Industrial area": "gen_industrial_area", "Landfill": "gen_landfill",
    "Power plant": "gen_power_plant", "Industrial plant": "gen_industrial_plant" };
  const siteName = (s) => (GENERIC[s] ? t(GENERIC[s]) : s);

  // "at a landfill" becomes "at a landfill: Lakho Der Landfill" when we know the site's name.
  function kindLabel(kind, sites) {
    const base = t("kind_" + kind);
    const named = (sites || []).filter((s) => !GENERIC[s]);
    return named.length ? `${base}: ${named[0]}` : base;
  }
  const evKey = (e) => `${e.sat}|${e.t}|${e.district}|${e.state}`;

  // The v2 feed stores names once (dict) and points as rows of numbers; expand them to the v1 row
  // [lat, lon, t, frp, sat, place, district, cc, kind] the rest of the page uses. "mapPoints" are the
  // points drawn on the map: the distinct spots on the 7-day view, every detection otherwise.
  function expandFeed(d) {
    if (d.v !== 2) { d.mapPoints = d.points; return d; }
    const P = d.dict.place, D = d.dict.district, K = d.dict.kind;
    d.points = d.points.map((r) => [r[0], r[1], d.t0 + r[2] * 60000, r[3], r[4], P[r[5]], D[r[6]][0], D[r[6]][2], K[r[7]]]);
    d.events = d.events.map((r) => {
      const kinds = {};
      for (let i = 0; i < r[10].length; i += 2) kinds[K[r[10][i]]] = r[10][i + 1];
      return { t: d.t0 + r[0] * 60000, sat: SATS[r[1]], district: D[r[2]][0], state: D[r[2]][1], cc: D[r[2]][2], night: !!r[3],
        n: r[4], high: r[5], frpMax: r[6], frpSum: r[7], lat: r[8], lon: r[9], kinds, places: r[11].map((i) => P[i]), sites: r[12],
        place: P[r[13]], placeKm: r[14], town: r[15] < 0 ? null : P[r[15]], townKm: r[16], flat: r[17], flon: r[18], kind: K[r[19]] };
    });
    d.mapPoints = d.spots ? d.spots.map((i) => d.points[i]) : d.points;
    return d;
  }

  async function loadFires(first) {
    try {
      const r = await fetch(`/api/fires?hours=${state.hours}&v=2`, { cache: "no-store" });
      const d = await r.json();
      if (!r.ok || d.error) throw new Error(d.error || r.status);
      expandFeed(d);
      const fresh = new Set();
      if (!first && state.data && state.data.hours === d.hours) for (const e of d.events) if (!state.seen.has(evKey(e))) fresh.add(evKey(e));
      state.seen = new Set(d.events.map(evKey));
      state.data = d;
      state.fresh = fresh;
      renderFires();
      renderFeed();
      renderCards();
      renderClouds();
      $("#updated").textContent = t("updated", { t: fmtTime(d.generated) });
    } catch (err) {
      console.warn("[hh] fires", err);
      if (!state.data) $("#events").innerHTML = `<li class="empty">${esc(t("errFires"))}</li>`;
    }
  }

  function placeLine(e) {
    const place = `<b>${esc(e.place || e.district || "—")}</b>`;
    let s = e.n > 1 ? t("evMany", { n: nf(e.n), place }) : t("evOne", { place });
    const others = (e.places || []).filter((p) => p !== e.place).slice(0, 2);
    if (others.length) s += ` ${t("evMore", { list: others.map(esc).join(", ") })}`;
    return s;
  }

  // "↑ 55% on the 24 h before" plus a bar per day from the daily archive. Follows the country chip.
  function renderTrend(d, total, w) {
    const box = $("#hTrend"), tr = d.trend;
    const pick = (o) => (state.cc === "PK" ? o.pk : state.cc === "IN" ? o.in : o.spots);
    const days = (tr?.days || []).map(([date, spots, pk, inn, , partial]) => ({ date, n: pick({ spots, pk, in: inn }), partial }));
    if (!tr || (!tr.prev && days.length < 2)) { box.hidden = true; return; }
    let txt = "";
    // Compare like with like: both windows come from the same points and end at the newest detection.
    if (tr.prev && pick(tr.prev) > 0) {
      const pct = Math.round(((pick(tr.cur || { spots: total, pk: total, in: total }) - pick(tr.prev)) / pick(tr.prev)) * 100);
      txt = Math.abs(pct) < 5 ? t("trendSame", { w }) : t(pct > 0 ? "trendUp" : "trendDown", { p: nf(Math.abs(pct)), w });
      box.classList.toggle("up", pct >= 5);
    } else {
      txt = t("trendDays", { n: nf(days.length) });
      box.classList.remove("up");
    }
    $("#hTrendTxt").textContent = txt;
    box.title = t("trendNote");
    const svg = $("#hSpark"), max = Math.max(1, ...days.map((x) => x.n)), bw = 5, gap = 2, h = 18;
    svg.setAttribute("viewBox", `0 0 ${days.length * (bw + gap) - gap} ${h}`);
    svg.style.width = `${days.length * (bw + gap) - gap}px`;
    const fmt = new Intl.DateTimeFormat(LOCALES[state.lang], { day: "numeric", month: "short", timeZone: "Asia/Karachi" });
    svg.innerHTML = days.map((x, i) => {
      const bh = Math.max(1, Math.round((x.n / max) * h));
      return `<rect x="${i * (bw + gap)}" y="${h - bh}" width="${bw}" height="${bh}" rx="1"${x.partial ? ' class="partial"' : ""}><title>${esc(fmt.format(Date.parse(x.date + "T12:00:00+05:00")))}: ${nf(x.n)}</title></rect>`;
    }).join("");
    box.hidden = false;
  }

  function renderFeed() {
    const d = state.data;
    if (!d) return;
    const s = d.stats;
    const total = state.cc === "PK" ? s.pk : state.cc === "IN" ? s.in : s.spots;
    $("#hFires").textContent = nf(total);
    const w = state.hours == 24 ? t("window24") : state.hours == 48 ? t("window48") : t("window7d");
    $("#hFiresLbl").textContent = t("headLbl", { w });
    $("#hSplit").textContent = t("headSplit", { pk: nf(s.pk), in: nf(s.in) });
    renderTrend(d, total, w);

    let evs = d.events.filter((e) => !state.cc || e.cc === state.cc);
    if (state.me) evs = evs.map((e) => ({ ...e, _km: distKm(state.me, [e.lat, e.lon]) })).filter((e) => e._km < 150);
    const list = $("#events");
    if (!evs.length) { list.innerHTML = `<li class="empty">${esc(t("noFires"))}</li>`; $("#more").hidden = true; return; }
    list.innerHTML = evs.slice(0, state.shown).map((e, i) => {
      const day = fmtDay(e.t) !== fmtDay(Date.now()) ? fmtDay(e.t) : "";
      const isNew = state.fresh && state.fresh.has(evKey(e));
      const country = e.cc === "PK" ? t("pk") : e.cc === "IN" ? t("in") : "";
      const where = [e.district, e.state, country].filter(Boolean).filter((v, j, a) => a.indexOf(v) === j).join(", ");
      const near = e.town && e.townKm > 2 ? ` · ${t("kmFrom", { km: nf(e.townKm), town: esc(e.town) })}` : "";
      const meKm = e._km != null ? ` · ${nf(Math.round(e._km))} km` : "";
      return `<li data-i="${i}" class="${isNew ? "fresh" : ""}" tabindex="0">
        <div class="when">${esc(fmtTime(e.t))}<small>${esc(day ? day + " · " : "")}${esc(ago(e.t))}</small></div>
        <div class="what"><span class="flame" style="background:${ageColor(e.t)}"></span>${placeLine(e)}
          <div class="meta">${esc(where)}${near}${meKm}</div>
          <div class="meta">${esc(t("by", { sat: e.sat }))}${e.night ? " · " + esc(t("night")) : ""}
            <span class="tag ${e.kind}">${esc(kindLabel(e.kind, e.sites))}</span>${isNew ? `<span class="tag new">${esc(t("newTag"))}</span>` : ""}</div>
        </div></li>`;
    }).join("");
    $$("li[data-i]", list).forEach((li) => {
      const go = () => {
        const e = evs[+li.dataset.i];
        map.flyTo([e.flat, e.flon], Math.max(map.getZoom(), 10), { duration: 1.2 });
        L.popup({ maxWidth: 260 }).setLatLng([e.flat, e.flon]).setContent(popupHtml({ ...e, frp: e.frpMax })).openOn(map);
        if (window.innerWidth < 860) $(".map-wrap").scrollIntoView({ behavior: "smooth", block: "start" });
      };
      li.addEventListener("click", go);
      li.addEventListener("keydown", (k) => { if (k.key === "Enter") go(); });
    });
    $("#more").hidden = evs.length <= state.shown;

    const top = s.topDistricts.filter((x) => !state.cc || x.cc === state.cc).slice(0, 6);
    const max = top[0]?.n || 1;
    $("#districts").innerHTML = top.length ? `<h3>${esc(t("topDistricts"))}</h3>` + top.map((x) =>
      `<div class="row"><span>${esc(x.district || x.state)}<span class="muted">${x.state && x.district ? ", " + esc(x.state) : ""}</span></span><span class="num">${nf(x.n)}</span>
       <div class="bar" style="width:${Math.max(4, (x.n / max) * 100)}%"></div></div>`).join("") : "";
  }

  $("#more").addEventListener("click", () => { state.shown += PAGE; renderFeed(); });
  $$("#winChips button").forEach((b) => b.addEventListener("click", () => {
    $$("#winChips button").forEach((x) => x.classList.toggle("on", x === b));
    state.hours = +b.dataset.w; state.shown = PAGE; state.data = null;
    $("#events").innerHTML = `<li class="loading">${esc(t("loading"))}</li>`;
    loadFires(true);
  }));
  $$("#ccChips button[data-cc]").forEach((b) => b.addEventListener("click", () => {
    $$("#ccChips button[data-cc]").forEach((x) => x.classList.toggle("on", x === b));
    state.cc = b.dataset.cc; state.shown = PAGE;
    renderFires(); renderFeed();
  }));

  let meMarker = null;
  $("#locate").addEventListener("click", () => {
    if (state.me) {
      state.me = null; $("#locate").classList.remove("on");
      if (meMarker) map.removeLayer(meMarker);
      renderFeed(); return;
    }
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => {
      state.me = [pos.coords.latitude, pos.coords.longitude];
      $("#locate").classList.add("on");
      meMarker = L.marker(state.me, { icon: L.divIcon({ className: "", html: '<div class="me-dot"></div>', iconSize: [14, 14] }) })
        .bindTooltip(t("you")).addTo(map);
      map.flyTo(state.me, 8);
      loadMyAir(exactSpot(state.me[0], state.me[1]));
      state.shown = PAGE; renderFeed();
    }, (err) => console.warn("[hh] geolocation", err.message), { timeout: 10000 });
  });

  // ---------- Health ----------
  function distKm(a, b) {
    const R = 6371, toR = Math.PI / 180;
    const dLat = (b[0] - a[0]) * toR, dLon = (b[1] - a[1]) * toR;
    const x = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * toR) * Math.cos(b[0] * toR) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(x));
  }
  function bearing(a, b) {
    const toR = Math.PI / 180;
    const y = Math.sin((b[1] - a[1]) * toR) * Math.cos(b[0] * toR);
    const x = Math.cos(a[0] * toR) * Math.sin(b[0] * toR) - Math.sin(a[0] * toR) * Math.cos(b[0] * toR) * Math.cos((b[1] - a[1]) * toR);
    return (Math.atan2(y, x) / toR + 360) % 360;
  }
  function aqiBand(a) { return a <= 50 ? 0 : a <= 100 ? 1 : a <= 150 ? 2 : a <= 200 ? 3 : a <= 300 ? 4 : 5; }

  // Health maths, explained in the "How we calculate" box.
  function health(c, pm24) {
    const pm = Math.max(0, pm24);
    const rr = Math.pow(1.0068, Math.max(0, pm - 15) / 10);
    return {
      cigs: pm / 22,
      who: pm / 15,
      years: Math.max(0, pm - 5) * 0.098,
      deaths: (c.pop * c.cdr / 1000 / 365) * (1 - 1 / rr),
    };
  }

  async function loadAir() {
    const lat = CITIES.map((c) => c.lat).join(","), lon = CITIES.map((c) => c.lon).join(",");
    const airUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}` +
      "&current=us_aqi,pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide,ozone,dust&hourly=pm2_5&past_days=1&forecast_days=1&timezone=GMT";
    const windUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=wind_speed_10m,wind_direction_10m&timezone=GMT`;
    try {
      const [air, wind] = await Promise.all([
        fetch(airUrl).then((r) => r.json()),
        fetch(windUrl).then((r) => r.json()).catch(() => null),
      ]);
      const now = Date.now();
      state.air = (Array.isArray(air) ? air : [air]).map((a) => {
        const times = a.hourly.time.map((x) => Date.parse(x + "Z"));
        const vals = a.hourly.pm2_5.filter((v, i) => v != null && times[i] <= now && times[i] > now - 24 * 36e5);
        const pm24 = vals.length ? vals.reduce((s, v) => s + v, 0) / vals.length : a.current.pm2_5;
        return { ...a.current, pm24, at: Date.parse(a.current.time + "Z") };
      });
      state.wind = wind ? (Array.isArray(wind) ? wind : [wind]).map((w) => w.current) : null;
      renderCards();
    } catch (err) {
      console.warn("[hh] air", err);
    }
  }

  function upwindFires(c, w) {
    if (!state.data || !w || w.wind_speed_10m < 3) return null;
    let n = 0;
    for (const p of state.data.points) {
      if (Math.abs(p[0] - c.lat) > 2.5 || Math.abs(p[1] - c.lon) > 3) continue;
      const d = distKm([c.lat, c.lon], [p[0], p[1]]);
      if (d > 250 || d < 1) continue;
      let diff = Math.abs(bearing([c.lat, c.lon], [p[0], p[1]]) - w.wind_direction_10m);
      if (diff > 180) diff = 360 - diff;
      if (diff <= 45) n++;
    }
    return n;
  }

  function cigIcons(n) {
    const whole = Math.min(10, Math.floor(n)), part = Math.min(1, n - Math.floor(n));
    // One upright cigarette per cigarette-a-day, the last one cut to the fraction. Max 10.
    let s = "", x = 2;
    const count = Math.min(10, Math.ceil(n));
    for (let i = 0; i < count; i++) {
      const h = i < whole ? 22 : Math.max(4, 22 * part);
      const top = 26 - h;
      const tilt = ((i * 37) % 7) - 3;
      s += `<g transform="rotate(${tilt} ${x + 3} 26)"><rect x="${x}" y="${top}" width="6" height="${h}" rx="1.2" fill="#fff" stroke="#2b2b2b" stroke-width="1"/>
        <rect x="${x}" y="${Math.max(top, 19)}" width="6" height="${26 - Math.max(top, 19)}" rx="1" fill="#e3954a" stroke="#2b2b2b" stroke-width="1"/>
        ${i < whole ? `<path d="M${x + 1} ${top - 1} q2 -3 4 0" stroke="#999" fill="none" stroke-width=".9"/>` : ""}</g>`;
      x += 10;
    }
    return `<svg width="${Math.max(12, x)}" height="28" viewBox="0 0 ${Math.max(12, x)} 28" aria-hidden="true">${s}</svg>`;
  }

  const CARDS = 12;
  function renderCards() {
    const at = state.air && state.air[0] && state.air[0].at;
    $("#healthSub").textContent = t("healthSub", { n: nf(CITIES.length) }) + (at ? " " + t("airAsOf", { t: `${fmtDay(at)}, ${fmtTime(at)}` }) : "");
    const box = $("#cards");
    if (!state.air) {
      box.innerHTML = CITIES.slice(0, 6).map(() => `<div class="card sketch skel">${esc(t("loading"))}</div>`).join("");
      sketchAll(box);
      return;
    }
    const rows = CITIES.map((c, i) => ({ c, a: state.air[i], w: state.wind?.[i] })).filter((r) => r.a);
    rows.forEach((r) => { r.h = health(r.c, r.a.pm24); r.up = upwindFires(r.c, r.w); });
    const sorters = { aqi: (a, b) => b.a.us_aqi - a.a.us_aqi, pop: (a, b) => b.c.pop - a.c.pop, cc: (a, b) => b.c.cc.localeCompare(a.c.cc) || b.a.us_aqi - a.a.us_aqi };
    rows.sort(sorters[state.sort]);

    let unhealthy = 0, deaths = 0, cigW = 0, popW = 0;
    for (const r of rows) {
      if (r.a.us_aqi > 150) unhealthy += r.c.pop;
      deaths += r.h.deaths;
      cigW += r.h.cigs * r.c.pop; popW += r.c.pop;
    }
    $("#tUnhealthy").textContent = compact(unhealthy);
    $("#tDeaths").textContent = "≈ " + nf(Math.round(deaths));
    $("#tCigs").textContent = nf(cigW / popW, { maximumFractionDigits: 1 });

    const dirName = (deg) => DIRS[state.lang][Math.round(deg / 45) % 8];
    // The first 12 in the chosen order (the worst air, by default); the rest behind a button.
    const more = $("#cardsMore");
    more.hidden = rows.length <= CARDS;
    more.textContent = state.allCards ? t("cardsFewer") : t("cardsAll", { n: nf(rows.length) });
    box.innerHTML = rows.slice(0, state.allCards ? rows.length : CARDS).map(({ c, a, w, h, up }, i) => {
      const band = aqiBand(a.us_aqi);
      const upTxt = up == null ? (w ? t("windFrom", { dir: dirName(w.wind_direction_10m) }) : "")
        : up > 0 ? `${t("firesNear", { n: nf(up) })} · ${t("windFrom", { dir: dirName(w.wind_direction_10m) })}`
        : `${t("firesNearNone")} · ${t("windFrom", { dir: dirName(w.wind_direction_10m) })}`;
      return `<article class="card sketch" data-seed="${60 + i}">
        <div class="c-head"><span class="c-name">${esc(c.name[state.lang])}</span><span class="cc">${esc(c.cc === "PK" ? t("pk") : t("in"))}</span></div>
        <div class="aqi"><span class="aqi-n num" style="color:var(--aqi-${band})">${nf(Math.round(a.us_aqi))}</span>
          <span class="aqi-l">${esc(t("aqi_" + band))}<small>US AQI · PM2.5 ${nf(Math.round(a.pm24))} µg/m³ (24 h)</small></span></div>
        <div class="aqi-band" style="background:var(--aqi-${band})"></div>
        <div class="cigs">${cigIcons(h.cigs)}<span><b class="num">${nf(h.cigs, { maximumFractionDigits: 1 })}</b> ${esc(t("cigs"))}</span></div>
        <div class="stats">
          <div class="stat"><b class="num">${nf(h.who, { maximumFractionDigits: 1 })}×</b><span>${esc(t("whoTimes").replace(/^×\s*/, ""))}</span></div>
          <div class="stat"><b class="num">${nf(h.years, { maximumFractionDigits: 1 })}</b><span>${esc(t("yearsLost"))}</span></div>
          <div class="stat"><b class="num red">≈ ${nf(h.deaths < 1 ? Math.round(h.deaths * 10) / 10 : Math.round(h.deaths))}</b><span>${esc(t("deathsToday"))}</span></div>
          <div class="stat"><b class="num">${compact(c.pop)}</b><span>${esc(t("popLbl"))}</span></div>
        </div>
        <div class="polls">
          <span>PM10 <b>${nf(Math.round(a.pm10))}</b></span><span>NO₂ <b>${nf(Math.round(a.nitrogen_dioxide))}</b></span>
          <span>SO₂ <b>${nf(Math.round(a.sulphur_dioxide))}</b></span><span>O₃ <b>${nf(Math.round(a.ozone))}</b></span>
          <span>CO <b>${nf(Math.round(a.carbon_monoxide))}</b></span><span>${esc(t("dust"))} <b>${nf(Math.round(a.dust))}</b></span><span class="muted">µg/m³</span>
        </div>
        ${upTxt ? `<div class="upwind ${up > 0 ? "hot" : ""}">${esc(upTxt)}</div>` : ""}
      </article>`;
    }).join("");
    sketchAll(box);
  }
  $("#sort").addEventListener("change", (e) => { state.sort = e.target.value; renderCards(); });
  $("#cardsMore").addEventListener("click", () => { state.allCards = !state.allCards; renderCards(); });

  // ---------- Your air ----------
  // City estimated from the visitor's connection (Cloudflare), a city they picked, or their exact position.
  // IP lookups in Pakistan often land in Karachi whatever the real city, so the picker lets people correct it,
  // and the choice is kept in this browser only.
  const CITY_KEY = "hh-city";
  const cityPos = (c) => ({ lat: c.lat, lon: c.lon, city: c.name.en, cityId: c.id, approx: false });
  function nearestCity(lat, lon, maxKm = 60) {
    let best = null, bd = maxKm;
    for (const c of CITIES) { const d = distKm([lat, lon], [c.lat, c.lon]); if (d < bd) { best = c; bd = d; } }
    return best;
  }
  function exactSpot(lat, lon) {
    const c = nearestCity(lat, lon);
    return { lat, lon, city: c ? c.name.en : "", cityId: c ? c.id : "", approx: false };
  }
  function locateMe() {
    return new Promise((ok, fail) => {
      if (!navigator.geolocation) return fail(new Error("no geolocation"));
      navigator.geolocation.getCurrentPosition((p) => ok(exactSpot(p.coords.latitude, p.coords.longitude)), fail, { timeout: 10000 });
    });
  }
  async function startMyAir() {
    const saved = store.get(CITY_KEY);
    const picked = saved && CITIES.find((c) => c.id === saved);
    if (picked) return loadMyAir(cityPos(picked));
    if (saved === "gps") {
      // Only reuse the exact location if the browser already allows it, so a visit never opens a prompt by itself.
      const perm = await navigator.permissions?.query({ name: "geolocation" }).catch(() => null);
      if (perm?.state === "granted") return locateMe().then(loadMyAir, () => loadMyAir());
    }
    return loadMyAir();
  }
  function fillCityPicker() {
    const sel = $("#myCity"), L0 = state.local;
    if (!sel) return;
    const cur = L0?.cityId || (L0?.city && CITIES.find((c) => c.name.en.toLowerCase() === L0.city.toLowerCase())?.id) || "";
    const group = (cc) => `<optgroup label="${esc(t(cc === "PK" ? "pk" : "in"))}">` +
      CITIES.filter((c) => c.cc === cc).map((c) => `<option value="${c.id}"${c.id === cur ? " selected" : ""}>${esc(c.name[state.lang])}</option>`).join("") + "</optgroup>";
    sel.innerHTML = (cur ? "" : '<option value="" selected>—</option>') + group("PK") + group("IN") + `<option value="gps">📍 ${esc(t("myAirGps"))}</option>`;
  }
  $("#myCity")?.addEventListener("change", async (e) => {
    const v = e.target.value;
    if (v === "gps") {
      try { const me = await locateMe(); store.set(CITY_KEY, "gps"); loadMyAir(me); }
      catch (err) { console.warn("[hh] geolocation", err.message); fillCityPicker(); }
      return;
    }
    const c = CITIES.find((x) => x.id === v);
    if (c) { store.set(CITY_KEY, c.id); loadMyAir(cityPos(c)); }
  });
  async function loadMyAir(pos) {
    try {
      let me = pos;
      if (!me) {
        const w = await fetch("/api/where").then((r) => r.json());
        if (!w.lat) return;
        me = { lat: w.lat, lon: w.lon, city: w.city || w.region, country: w.country, approx: true };
      }
      const a = await fetch(`https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${me.lat}&longitude=${me.lon}` +
        "&current=us_aqi,pm2_5&hourly=pm2_5&past_days=1&forecast_days=1&timezone=GMT").then((r) => r.json());
      const now = Date.now();
      const times = a.hourly.time.map((x) => Date.parse(x + "Z"));
      const vals = a.hourly.pm2_5.filter((v, i) => v != null && times[i] <= now && times[i] > now - 24 * 36e5);
      const pm24 = vals.length ? vals.reduce((x, v) => x + v, 0) / vals.length : a.current.pm2_5;
      state.local = { ...me, city: me.city || state.local?.city || "", aqi: a.current.us_aqi, pm24 };
      renderMyAir();
      window.dispatchEvent(new Event("hh:local"));
    } catch (err) {
      console.warn("[hh] my air", err);
    }
  }
  function renderMyAir() {
    const L0 = state.local, box = $("#myAir");
    if (!L0 || L0.aqi == null) { box.hidden = true; return; }
    const band = aqiBand(L0.aqi);
    box.hidden = false;
    box.style.setProperty("--band", `var(--aqi-${band})`);
    const known = L0.city && CITIES.find((c) => c.name.en.toLowerCase() === L0.city.toLowerCase());
    const cityName = known ? known.name[state.lang] : L0.city;
    $("#myAirLbl").textContent = cityName ? t("myAirLbl", { city: cityName }) : t("myAirHere");
    $("#myAirN").textContent = nf(Math.round(L0.aqi));
    $("#myAirSub").textContent = `${t("aqi_" + band)} · ${t("myAirCigs", { n: nf(L0.pm24 / 22, { maximumFractionDigits: 1 }) })}`;
    $("#myAirNote").textContent = L0.approx ? t("myAirApprox") : "";
    $("#myPick").hidden = false;
    fillCityPicker();
  }

  // ---------- Share ----------
  function updateShare() {
    const n = state.data ? state.data.stats.spots : "";
    const text = t("shareText", { n: nf(n || 0) });
    const url = location.origin + "/";
    $("#shareWa").href = `https://wa.me/?text=${encodeURIComponent(text + " " + url)}`;
    $("#shareX").href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
  }
  $("#shareNative").addEventListener("click", async () => {
    const text = t("shareText", { n: nf(state.data?.stats.spots || 0) });
    try {
      if (navigator.share) await navigator.share({ title: "Hamari Hawa", text, url: location.origin + "/" });
      else { await navigator.clipboard.writeText(`${text} ${location.origin}/`); $("#shareNative").textContent = "✓"; }
    } catch { /* cancelled */ }
  });

  // ---------- Language ----------
  function applyLang() {
    const L0 = I18N[state.lang];
    document.documentElement.lang = state.lang;
    document.documentElement.dir = L0.dir;
    zoomCtl.setPosition(L0.dir === "rtl" ? "topleft" : "topright");
    $$("[data-i]").forEach((el) => { el.textContent = t(el.dataset.i); });
    $$("[data-en]").forEach((el) => { el.textContent = el.dataset[state.lang] || el.dataset.en; });
    $$(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === state.lang));
    renderPanel();
    renderFeed();
    renderCards();
    renderClouds();
    renderMyAir();
    updateShare();
    if (state.data) $("#updated").textContent = t("updated", { t: fmtTime(state.data.generated) });
    $$(".sketch svg.rough").forEach((s) => { s.dataset.size = ""; });
    $$(".sketch").forEach((el) => hasRough && drawSketch(el));
    window.dispatchEvent(new Event("hh:lang"));
  }
  $$(".lang button").forEach((b) => b.addEventListener("click", () => { state.lang = b.dataset.lang; store.set("hh-lang", state.lang); applyLang(); }));

  window.addEventListener("hh:sketch", () => sketchAll());

  // Shared with share.js (the shareable card).
  window.HH = { state, t, nf, health, aqiBand, CITIES, map, siteName, setLayer, trafficMeta: loadTrafficMeta, expandFeed, locale: () => LOCALES[state.lang] };

  // Deep links from the Pollution sites page: /#at=lat,lon,zoom&layer=traffic&src=kilns
  function applyHash() {
    const p = new URLSearchParams(location.hash.slice(1));
    const at = (p.get("at") || "").split(",").map(Number);
    if (at.length >= 2 && at.every(Number.isFinite)) {
      map.setView([at[0], at[1]], at[2] || 10);
      L.circleMarker([at[0], at[1]], { radius: 18, color: "#d62d20", weight: 2, fill: false, dashArray: "4 4", interactive: false }).addTo(map);
    }
    if (p.get("layer") && LAYERS[p.get("layer")] !== undefined) setLayer(p.get("layer"));
    return p.get("src");
  }

  // ---------- Boot ----------
  applyLang();
  sketchAll();
  setLayer("none");
  window.HH_HASH_SRC = applyHash();
  loadFires(true).then(updateShare);
  loadAir();
  startMyAir();
  setInterval(() => loadFires(false).then(updateShare), POLL_MS);
  setInterval(loadAir, 30 * 60 * 1000);
  setInterval(() => { if (state.data) renderFeed(); }, 60 * 1000); // keep "x min ago" fresh
})();
