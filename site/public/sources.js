// Known pollution sources on the map: brick kilns, landfills, industrial areas, Carbon Mapper
// methane/CO2 plumes, and (once built) persistent satellite hot spots. Each layer is a list of
// points drawn onto canvas tiles, so 50,000 kilns stay fast; clicks find the nearest symbol.
(() => {
  "use strict";
  const HH = window.HH, map = HH.map;
  const t = (k, v) => HH.t(k, v);
  const nf = (n, o) => HH.nf(n, o);
  const V = document.querySelector('script[src^="sources.js"]')?.src.split("?v=")[1] || "";

  const KILN_COLOR = "#7a4a2a";
  const LAYERS = {
    plumes: { file: "carbonmapper.json", on: true },
    landfill: { file: "osm-landfill.json", on: true },
    industrial: { file: "osm-industrial.json", on: false },
    kilns: { file: "kilns.json", on: false },
    hotspots: { file: "hotspots.json", on: true, optional: true },
    plants: { file: "plants.json", on: true, optional: true },
  };

  // ---- symbols (drawn in tile pixel space) ----
  const draw = {
    kilns(g, x, y, z) {
      // Kiln belts are dense (thousands around Delhi alone), so keep each one small and see-through.
      const s = z < 8 ? 1.1 : z < 10 ? 1.7 : z < 12 ? 2.6 : 3.6;
      g.fillStyle = z < 10 ? "rgba(122,74,42,.55)" : KILN_COLOR;
      g.fillRect(x - s, y - s, s * 2, s * 2);
    },
    landfill(g, x, y, z, it) {
      const s = Math.max(5, Math.min(14, 4 + Math.log2(it[3] / 100) * 2)) * (z < 7 ? 0.8 : 1);
      g.beginPath(); g.moveTo(x, y - s); g.lineTo(x + s * 0.9, y + s * 0.6); g.lineTo(x - s * 0.9, y + s * 0.6); g.closePath();
      g.fillStyle = "rgba(96,110,60,.85)"; g.fill();
      g.strokeStyle = "#fff"; g.lineWidth = 1.2; g.stroke();
    },
    industrial(g, x, y, z, it) {
      const s = Math.max(3, Math.min(10, 2 + Math.log2(it[3] / 100) * 1.6));
      g.strokeStyle = "rgba(90,80,140,.85)"; g.lineWidth = 1.6;
      g.strokeRect(x - s, y - s, s * 2, s * 2);
    },
    plumes(g, x, y, z, it) {
      const methane = it[2] === "CH4";
      const kg = it[4] || 0;
      const r = methane ? 4 + Math.min(10, Math.sqrt(kg) / 5) : 4 + Math.min(10, Math.sqrt(kg / 1000) / 3);
      g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2);
      g.fillStyle = methane ? "rgba(0,140,140,.25)" : "rgba(110,60,150,.22)"; g.fill();
      g.strokeStyle = methane ? "#007a7a" : "#6e3c96"; g.lineWidth = 2; g.stroke();
      g.beginPath(); g.arc(x, y, 2, 0, Math.PI * 2); g.fillStyle = g.strokeStyle; g.fill();
    },
    hotspots(g, x, y, z, it) {
      const r = 3 + Math.min(6, (it[2] || 1) / 6);
      g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2);
      g.strokeStyle = "#b3261e"; g.lineWidth = 2; g.stroke();
      g.beginPath(); g.moveTo(x - r - 3, y); g.lineTo(x + r + 3, y); g.moveTo(x, y - r - 3); g.lineTo(x, y + r + 3);
      g.lineWidth = 1; g.stroke();
    },
    plants(g, x, y, z, it) {
      const s = 7;
      g.fillStyle = it[2] === "coal" ? "#2b2b2b" : it[2] === "steel" ? "#4a5a6a" : it[2] === "gas" ? "#6a7f8a" : "#8a7f6a";
      g.beginPath(); g.moveTo(x - s, y + s); g.lineTo(x - s, y - 2); g.lineTo(x - 2, y - 2); g.lineTo(x - 2, y - s); g.lineTo(x + 2, y - s);
      g.lineTo(x + 2, y - 2); g.lineTo(x + s, y - 2); g.lineTo(x + s, y + s); g.closePath(); g.fill();
      g.strokeStyle = "#fff"; g.lineWidth = 1; g.stroke();
    },
  };

  // ---- data + spatial index ----
  const data = {}, loading = {};
  // One fetch per file even when several parts of the page ask at once.
  function load(kind) {
    if (data[kind] !== undefined) return Promise.resolve(data[kind]);
    return (loading[kind] ||= fetchLayer(kind));
  }
  async function fetchLayer(kind) {
    try {
      const r = await fetch(`/sources/${LAYERS[kind].file}?v=${V}`);
      if (!r.ok) throw new Error(r.status);
      const d = await r.json();
      const idx = new Map();
      for (const it of d.items) {
        const k = `${Math.floor(it[0])}_${Math.floor(it[1])}`;
        if (!idx.has(k)) idx.set(k, []);
        idx.get(k).push(it);
      }
      data[kind] = { ...d, idx };
    } catch (err) {
      data[kind] = null;
      if (!LAYERS[kind].optional) console.warn("[hh] sources", kind, err);
    }
    return data[kind];
  }
  function itemsIn(kind, s, w, n, e) {
    const d = data[kind];
    if (!d) return [];
    const out = [];
    for (let la = Math.floor(s); la <= Math.floor(n); la++)
      for (let lo = Math.floor(w); lo <= Math.floor(e); lo++) {
        const b = d.idx.get(`${la}_${lo}`);
        if (b) for (const it of b) if (it[0] >= s && it[0] <= n && it[1] >= w && it[1] <= e) out.push(it);
      }
    return out;
  }

  // ---- one canvas tile layer per kind ----
  map.createPane("sources").style.zIndex = 470;
  const SourceLayer = L.GridLayer.extend({
    createTile(coords) {
      const tile = document.createElement("canvas");
      const size = this.getTileSize();
      tile.width = size.x; tile.height = size.y;
      const g = tile.getContext("2d");
      const nw = map.unproject(coords.scaleBy(size), coords.z), se = map.unproject(coords.add([1, 1]).scaleBy(size), coords.z);
      const pad = 0.15;
      const items = itemsIn(this.options.kind, se.lat - pad, nw.lng - pad, nw.lat + pad, se.lng + pad);
      const origin = coords.scaleBy(size);
      for (const it of items) {
        const p = map.project([it[0], it[1]], coords.z).subtract(origin);
        draw[this.options.kind](g, p.x, p.y, coords.z, it);
      }
      return tile;
    },
  });
  const layers = {};
  async function setOn(kind, on) {
    LAYERS[kind].on = on;
    if (layers[kind]) { map.removeLayer(layers[kind]); delete layers[kind]; }
    if (!on) return;
    const d = await load(kind);
    if (!d || !LAYERS[kind].on) return;
    layers[kind] = new SourceLayer({ kind, pane: "sources", minZoom: kind === "kilns" ? 6 : 0, updateWhenZooming: false }).addTo(map);
  }

  // Carbon Mapper sources have no names; borrow the nearest named landfill / industrial area / plant.
  function nearestNamed(lat, lon, km) {
    let best = null, bestD = km;
    for (const kind of ["landfill", "industrial", "plants"]) {
      const d = 0.03 * km;
      for (const it of itemsIn(kind, lat - d, lon - d, lat + d, lon + d)) {
        const name = kind === "plants" ? it[3] : it[2];
        if (!name || name === "Industrial area" || name === "Landfill") continue;
        const dist = Math.hypot(it[0] - lat, (it[1] - lon) * Math.cos((lat * Math.PI) / 180)) * 111;
        if (dist < bestD) { bestD = dist; best = name; }
      }
    }
    return best;
  }

  // ---- popups ----
  function popup(kind, it) {
    const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
    if (kind === "kilns") {
      const type = data.kilns.types[it[2]];
      return `<b>${esc(t("srcKiln"))}</b><br>${esc(t("kilnType_" + type))}${it[3] != null ? `<br>≈ ${nf(it[3])} ${esc(t("kgPm25Day"))}` : ""}
        <br><span class="muted">${esc(t("srcKilnNote"))}</span>`;
    }
    if (kind === "landfill") return `<b>${esc(it[2] || t("srcLandfill"))}</b><br>${esc(t("srcLandfillNote"))}<br><span class="muted">OpenStreetMap</span>`;
    if (kind === "industrial") return `<b>${esc(it[2] || t("srcIndustrial"))}</b><br>${esc(t("srcIndustrialNote"))}<br><span class="muted">OpenStreetMap</span>`;
    if (kind === "plumes") {
      const gas = it[2] === "CH4" ? t("methane") : "CO₂";
      const site = nearestNamed(it[0], it[1], 2);
      const rate = it[2] === "CH4" ? `${nf(it[4])} kg/h` : `${nf(Math.round(it[4] / 1000))} t/h`;
      return `<b>${esc(t("plume_" + it[3]))}</b>${site ? `<br>${esc(site)}` : ""}<br>${esc(t("plumeLine", { gas, rate }))}<br>
        ${esc(t("plumeSeen", { n: nf(it[5]), pct: nf(it[6]), first: it[7] || "", last: it[8] || "" }))}
        <br><span class="muted">Carbon Mapper</span>`;
    }
    if (kind === "hotspots") return `<b>${esc(t("srcHotspot"))}</b><br>${esc(t("hotspotLine", { days: nf(it[2]), months: nf(it[3] || 0) }))}${it[4] ? `<br>${esc(HH.siteName(it[4]))}` : ""}`;
    if (kind === "plants") return `<b>${esc(it[3])}</b><br>${esc(t("plant_" + it[2]))}${it[4] ? ` · ${esc(it[4])}` : ""}<br><span class="muted">${esc(data.plants.source.split(";")[0])}</span>`;
    return "";
  }
  map.on("click", (e) => {
    const z = map.getZoom(), pt = map.project(e.latlng, z);
    let best = null, bestD = 12;
    for (const kind of Object.keys(LAYERS)) {
      if (!layers[kind] || !data[kind]) continue;
      const deg = 30 / Math.pow(2, z);
      for (const it of itemsIn(kind, e.latlng.lat - deg, e.latlng.lng - deg, e.latlng.lat + deg, e.latlng.lng + deg)) {
        const d = map.project([it[0], it[1]], z).distanceTo(pt);
        if (d < bestD) { bestD = d; best = { kind, it }; }
      }
    }
    if (best) L.popup({ maxWidth: 280 }).setLatLng([best.it[0], best.it[1]]).setContent(popup(best.kind, best.it)).openOn(map);
  });

  // ---- panel ----
  function counts(kind) {
    const d = data[kind];
    return d ? ` <span class="muted">(${nf(d.items.length)})</span>` : "";
  }
  // What date each layer's data reflects (not when we built the file).
  const fmtD = (iso, o) => new Intl.DateTimeFormat(HH.locale(), o || { day: "numeric", month: "short", year: "numeric" }).format(Date.parse(iso + "T12:00:00Z"));
  function asOf(kind) {
    const d = data[kind];
    if (!d && kind !== "kilns") return ""; // the 1.3 MB kiln file isn't loaded until needed; its date is fixed
    let txt = "";
    if (kind === "plumes") {
      const first = d.items.map((x) => x[7]).filter(Boolean).sort()[0], last = d.items.map((x) => x[8]).filter(Boolean).sort().pop();
      if (first && last) txt = t("asOfSeen", { a: first.slice(0, 4), b: fmtD(last, { month: "short", year: "numeric" }) });
    } else if (kind === "kilns") txt = t("asOfKilns");
    else if (kind === "hotspots") txt = t("asOfHot");
    else if (d.built) txt = t("asOfOsm", { d: fmtD(d.built) });
    return txt ? `<small class="asof">${txt}</small>` : "";
  }
  async function renderPanel() {
    const box = document.getElementById("sourceChecks");
    // Optional layers appear only once their data file exists.
    await Promise.all(Object.keys(LAYERS).filter((k) => k !== "kilns").map(load));
    if (LAYERS.kilns.on || data.kilns) await load("kilns");
    box.innerHTML = Object.keys(LAYERS).filter((k) => !LAYERS[k].optional || data[k]).map((k) =>
      `<label class="chk"><input type="checkbox" data-src="${k}" ${LAYERS[k].on ? "checked" : ""}> <span class="src-key src-${k}"></span><span>${t("src_" + k)}${counts(k)}${asOf(k)}</span></label>`).join("");
    box.querySelectorAll("input").forEach((c) => c.addEventListener("change", async () => {
      await setOn(c.dataset.src, c.checked);
      renderPanel();
    }));
  }
  if (window.HH_HASH_SRC && LAYERS[window.HH_HASH_SRC]) LAYERS[window.HH_HASH_SRC].on = true;
  Object.keys(LAYERS).forEach((k) => { if (LAYERS[k].on) setOn(k, true).then(renderPanel); });
  ["landfill", "industrial", "plants"].forEach(load);
  renderPanel();
  window.addEventListener("hh:lang", renderPanel);
})();
