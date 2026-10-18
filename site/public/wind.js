// Wind right now: ink streaks drifting the way the wind blows (Open-Meteo 10 m wind on a 1° grid,
// via /api/wind), and a "from X towards Y" line under the Your-air box.
(() => {
  "use strict";
  const HH = window.HH, map = HH.map;
  const t = (k, v) => HH.t(k, v);
  const nf = (n, o) => HH.nf(n, o);
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const RAD = Math.PI / 180;

  let grid = null, loading = null, towns = null;
  function load() {
    loading = loading || fetch("/api/wind").then((r) => (r.ok ? r.json() : null)).catch(() => null).then((g) => {
      if (!g) { loading = null; return null; }
      // dir is where the wind comes from; u (east) and v (north) point where it goes.
      g.u = g.speed.map((s, i) => -s * Math.sin(g.dir[i] * RAD));
      g.v = g.speed.map((s, i) => -s * Math.cos(g.dir[i] * RAD));
      grid = g;
      return g;
    });
    return loading;
  }
  // Bilinear wind [u, v] in km/h at a point, or null outside the grid.
  function sample(lat, lon) {
    const g = grid, x = lon - g.lon0, y = lat - g.lat0;
    if (x < 0 || y < 0 || x > g.nx - 1 || y > g.ny - 1) return null;
    const x0 = Math.min(g.nx - 2, Math.floor(x)), y0 = Math.min(g.ny - 2, Math.floor(y)), fx = x - x0, fy = y - y0;
    const at = (a, yy, xx) => a[yy * g.nx + xx];
    const lerp = (a) => (at(a, y0, x0) * (1 - fx) + at(a, y0, x0 + 1) * fx) * (1 - fy) + (at(a, y0 + 1, x0) * (1 - fx) + at(a, y0 + 1, x0 + 1) * fx) * fy;
    return [lerp(g.u), lerp(g.v)];
  }

  // ---------- Streaks on the map ----------
  map.createPane("wind").style.zIndex = 430; // above the pollution layers and clouds, under fires and labels' popups
  const pane = map.getPane("wind");
  pane.style.pointerEvents = "none";
  const canvas = L.DomUtil.create("canvas", "wind-canvas", pane);
  const ctx = canvas.getContext("2d");
  const CELL = 8, PX_PER_KMH = 0.035, MAX_AGE = 90;
  let on = false, raf = 0, field = null, cols = 0, rows = 0, W = 0, H = 0, parts = [], frames = 0;

  function fieldAt(x, y) {
    const c = Math.round(x / CELL), r = Math.round(y / CELL);
    if (c < 0 || r < 0 || c >= cols || r >= rows) return null;
    const i = (r * cols + c) * 2;
    return Number.isNaN(field[i]) ? null : [field[i], field[i + 1]];
  }
  function spawn(p) {
    for (let k = 0; k < 20; k++) {
      p.x = Math.random() * W; p.y = Math.random() * H;
      if (fieldAt(p.x, p.y)) break;
    }
    p.age = Math.floor(Math.random() * MAX_AGE);
  }
  function build() {
    const size = map.getSize(), dpr = Math.min(2, window.devicePixelRatio || 1);
    W = size.x; H = size.y;
    canvas.width = W * dpr; canvas.height = H * dpr;
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    L.DomUtil.setPosition(canvas, map.containerPointToLayerPoint([0, 0]));
    cols = Math.ceil(W / CELL) + 1; rows = Math.ceil(H / CELL) + 1;
    field = new Float32Array(cols * rows * 2);
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const ll = map.containerPointToLatLng([c * CELL, r * CELL]);
        const w = sample(ll.lat, ll.lng), i = (r * cols + c) * 2;
        // Screen speed doesn't depend on zoom, so streaks read the same at every scale.
        if (w) { field[i] = w[0] * PX_PER_KMH; field[i + 1] = -w[1] * PX_PER_KMH; }
        else { field[i] = NaN; field[i + 1] = NaN; }
      }
    }
    const n = Math.round(Math.min(2200, (W * H) / 520));
    parts = Array.from({ length: n }, () => { const p = {}; spawn(p); return p; });
    ctx.clearRect(0, 0, W, H);
    frames = 0;
  }
  function frame() {
    raf = 0;
    if (!on || !field) return;
    if (!document.hidden) {
      // Fade the previous frame so each streak leaves a short pencil trail.
      ctx.globalCompositeOperation = "destination-in";
      ctx.fillStyle = "rgba(0,0,0,0.92)";
      ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = "source-over";
      ctx.strokeStyle = "rgba(38,38,52,0.6)";
      ctx.lineWidth = 1.1;
      ctx.lineCap = "round";
      ctx.beginPath();
      for (const p of parts) {
        const v = fieldAt(p.x, p.y);
        if (!v || ++p.age > MAX_AGE) { spawn(p); p.age = 0; continue; }
        const nx = p.x + v[0], ny = p.y + v[1];
        ctx.moveTo(p.x, p.y); ctx.lineTo(nx, ny);
        p.x = nx; p.y = ny;
      }
      ctx.stroke();
      frames++;
    }
    // With reduced motion, draw a short run of frames and then hold still.
    if (reduced && frames > 45) return;
    raf = requestAnimationFrame(frame);
  }
  function start() {
    if (!on || !grid) return;
    build();
    if (!raf) raf = requestAnimationFrame(frame);
  }
  function stop() {
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
    ctx.clearRect(0, 0, W, H);
  }
  map.on("movestart zoomstart", () => { if (on) stop(); });
  map.on("moveend zoomend resize", () => { if (on) start(); });

  async function setOn(v) {
    on = v;
    canvas.style.display = v ? "" : "none";
    if (!v) { stop(); renderNote(); return; }
    await load();
    start();
    renderNote();
  }

  // ---------- Panel checkbox ----------
  const box = document.getElementById("windOn");
  const note = document.getElementById("windNote");
  const fmtTime = (iso) => new Intl.DateTimeFormat(HH.locale(), { hour: "2-digit", minute: "2-digit" }).format(Date.parse(iso + "Z"));
  function renderNote() {
    if (!note) return;
    note.textContent = on && grid?.time ? t("windNote", { t: fmtTime(grid.time) }) : "";
  }
  box.checked = false; // off by default; visitors opt in
  box.addEventListener("change", () => setOn(box.checked));
  setOn(box.checked);

  // ---------- "From X towards Y" for the visitor ----------
  const dist = (a, b, c, d) => Math.hypot(a - c, (b - d) * Math.cos(a * RAD)) * 111.2;
  const bearing = (a, b, c, d) => {
    const y = Math.sin((d - b) * RAD) * Math.cos(c * RAD);
    const x = Math.cos(a * RAD) * Math.sin(c * RAD) - Math.sin(a * RAD) * Math.cos(c * RAD) * Math.cos((d - b) * RAD);
    return (Math.atan2(y, x) / RAD + 360) % 360;
  };
  // Nearest big town (over 100k people) 8–90 km away in the given compass direction (±35°).
  function townToward(lat, lon, deg) {
    let best = null, bd = 1e9;
    for (const [la, lo, name] of towns) {
      const d = dist(lat, lon, la, lo);
      if (d < 8 || d > 90) continue;
      let diff = Math.abs(bearing(lat, lon, la, lo) - deg);
      if (diff > 180) diff = 360 - diff;
      if (diff <= 35 && d < bd) { best = name; bd = d; }
    }
    return best;
  }
  const dirName = (deg) => window.HH_DIRS[HH.state.lang][Math.round(deg / 45) % 8];
  async function renderMyWind() {
    const el = document.getElementById("myWind"), me = HH.state.local;
    if (!el) return;
    if (!me || me.lat == null || !(await load())) { el.hidden = true; return; }
    if (!towns) towns = await fetch("sources/towns.json").then((r) => (r.ok ? r.json() : [])).catch(() => []);
    const w = sample(me.lat, me.lon);
    if (!w) { el.hidden = true; return; }
    const speed = Math.hypot(w[0], w[1]);
    if (speed < 3) { el.textContent = t("windCalmShort"); el.hidden = false; return; }
    const from = (Math.atan2(-w[0], -w[1]) / RAD + 360) % 360;
    const a = townToward(me.lat, me.lon, from), b = townToward(me.lat, me.lon, (from + 180) % 360);
    const arrow = HH.state.lang === "ur" ? " ← " : " → ";
    const route = a && b ? a + arrow + b : a ? a + arrow : b ? arrow.trim() + " " + b : "";
    // The towns already show the direction, so the compass word is only used when there are none.
    const v = nf(Math.round(speed));
    el.textContent = a && b ? t("windRoute", { route, v }) : t("windShort", { dir: dirName(from), v }) + (route ? ` · ${route}` : "");
    el.hidden = false;
  }
  window.addEventListener("hh:local", renderMyWind);
  renderMyWind();
  window.addEventListener("hh:lang", () => { renderNote(); renderMyWind(); });
  setInterval(() => { loading = null; load().then(() => { if (on) start(); renderNote(); renderMyWind(); }); }, 30 * 60 * 1000);
})();
