// Close-up fire maps: the last 24 hours of fires around one point, from the same feed as the live map.
// City pages (/air/<city>/) give the point in data-lat/data-lon, with data-wind (where the wind comes from)
// to shade the upwind side. /near-me/ uses the visitor's approximate location (Cloudflare's IP lookup via
// /api/where, never stored) or, on request, the browser's exact location, and also writes the answer in words.
// One map per language article; only the visible one is drawn, and only when it scrolls near.
(() => {
  const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{style}/MapServer/tile/{z}/{y}/{x}";
  const ATTR = "Base map © Esri, HERE, Garmin, © OpenStreetMap contributors · Fires: NASA FIRMS";
  const UPWIND = 45; // degrees either side, as the city pages count it
  const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const T = {
    en: { dirs: ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"],
      ago: (h) => (h < 1 ? "under an hour ago" : `${h} h ago`), km: (n) => `${n} km away`, here: "You are about here",
      windFrom: (d, v) => `Wind from the <b>${d}</b>${v ? `, ${v} km/h` : ""}`, keyUp: "upwind: smoke heading here", keyOther: "other directions",
      kind: { crop: "likely crop burning", urban: "near a town: waste or industry?", open: "open land", forest: "likely forest fire", shifting: "forest or shifting cultivation",
        mixed: "mixed land: farms, scrub or trees", kiln: "at a brick kiln", industrial: "in an industrial area", hotspot: "at an always-hot spot" },
      nearest: (km, dir, place, ago) => `The nearest fire NASA's satellites saw in the last 24 hours was <b>${km} km ${dir}</b> of you, near ${place} (${ago}).`,
      counts: (a, b, c) => ` There were <b>${a}</b> fires within 25 km, <b>${b}</b> within 50 km and <b>${c}</b> within 100 km.`,
      none: (r) => `NASA's satellites saw <b>no fires within ${r} km</b> of you in the last 24 hours. Haze today is more likely local: traffic, industry, brick kilns, burning rubbish and dust.`,
      where: (p) => `Your approximate location: ${p}, from your internet connection, so it can be tens of kilometres off.`,
      exact: "Your location from your device.", outside: "This page covers Pakistan and India, and your connection appears to be outside them. Open a city instead:",
      unknown: "We couldn't tell where you are. Use the button below, or open a city:", city: (a) => `Where the smoke is coming from in your nearest city: ${a}.`,
      denied: "Location wasn't shared, so this still uses your connection's approximate location.", fail: "The fire feed didn't load. Try again in a minute." },
    ur: { dirs: ["شمال", "شمال مشرق", "مشرق", "جنوب مشرق", "جنوب", "جنوب مغرب", "مغرب", "شمال مغرب"],
      ago: (h) => (h < 1 ? "ایک گھنٹے سے کم پہلے" : `${h} گھنٹے پہلے`), km: (n) => `${n} کلومیٹر دور`, here: "آپ تقریباً یہاں ہیں",
      windFrom: (d, v) => `ہوا <b>${d}</b> سے${v ? `، ${v} کلومیٹر فی گھنٹہ` : ""}`, keyUp: "ہوا کے رخ پر: دھواں اس طرف آ رہا ہے", keyOther: "دوسری سمتیں",
      kind: { crop: "غالباً فصل کی باقیات جلائی جا رہی ہیں", urban: "شہر کے قریب: کچرا یا صنعت؟", open: "کھلی زمین پر", forest: "غالباً جنگل میں آگ", shifting: "جنگل یا جھوم کاشت",
        mixed: "ملی جلی زمین: کھیت، جھاڑیاں یا درخت", kiln: "اینٹوں کے بھٹے پر", industrial: "صنعتی علاقے میں", hotspot: "ہمیشہ گرم جگہ پر" },
      nearest: (km, dir, place, ago) => `پچھلے 24 گھنٹوں میں ناسا کے سیٹلائٹس کو سب سے قریب آگ آپ سے <b>${km} کلومیٹر ${dir}</b> میں ${place} کے قریب نظر آئی (${ago})۔`,
      counts: (a, b, c) => ` 25 کلومیٹر کے اندر <b>${a}</b>، 50 کلومیٹر کے اندر <b>${b}</b> اور 100 کلومیٹر کے اندر <b>${c}</b> جگہ آگ دیکھی گئی۔`,
      none: (r) => `پچھلے 24 گھنٹوں میں ناسا کے سیٹلائٹس کو آپ سے <b>${r} کلومیٹر کے اندر کوئی آگ نظر نہیں آئی</b>۔ آج کی دھند غالباً مقامی ہے: ٹریفک، صنعت، اینٹوں کے بھٹے، کچرا جلانا اور گرد۔`,
      where: (p) => `آپ کا اندازاً مقام: ${p}، آپ کے انٹرنیٹ کنکشن سے، اس لیے یہ دسیوں کلومیٹر غلط ہو سکتا ہے۔`,
      exact: "آپ کا مقام آپ کے آلے سے۔", outside: "یہ صفحہ پاکستان اور بھارت کا احاطہ کرتا ہے، اور آپ کا کنکشن ان سے باہر لگتا ہے۔ اس کے بجائے کوئی شہر کھولیں:",
      unknown: "ہم آپ کا مقام نہیں جان سکے۔ نیچے والا بٹن استعمال کریں یا کوئی شہر کھولیں:", city: (a) => `آپ کے قریب ترین شہر میں دھواں کہاں سے آ رہا ہے: ${a}۔`,
      denied: "مقام شیئر نہیں ہوا، اس لیے یہ صفحہ اب بھی کنکشن کا اندازاً مقام استعمال کر رہا ہے۔", fail: "آگ کی فیڈ لوڈ نہیں ہوئی۔ ایک منٹ بعد دوبارہ کوشش کریں۔" },
    hi: { dirs: ["उत्तर", "उत्तर-पूर्व", "पूर्व", "दक्षिण-पूर्व", "दक्षिण", "दक्षिण-पश्चिम", "पश्चिम", "उत्तर-पश्चिम"],
      ago: (h) => (h < 1 ? "एक घंटे से कम पहले" : `${h} घंटे पहले`), km: (n) => `${n} किमी दूर`, here: "आप लगभग यहाँ हैं",
      windFrom: (d, v) => `हवा <b>${d}</b> से${v ? `, ${v} किमी/घंटा` : ""}`, keyUp: "हवा के रुख़ पर: धुआँ इधर आ रहा है", keyOther: "दूसरी दिशाएँ",
      kind: { crop: "शायद पराली जल रही है", urban: "शहर के पास: कचरा या उद्योग?", open: "खुली ज़मीन", forest: "शायद जंगल की आग", shifting: "जंगल या झूम खेती",
        mixed: "मिली-जुली ज़मीन: खेत, झाड़ियाँ या पेड़", kiln: "ईंट भट्ठे पर", industrial: "औद्योगिक इलाक़े में", hotspot: "हमेशा गर्म जगह पर" },
      nearest: (km, dir, place, ago) => `पिछले 24 घंटों में नासा के उपग्रहों को सबसे नज़दीकी आग आपसे <b>${km} किमी ${dir}</b> में, ${place} के पास दिखी (${ago})।`,
      counts: (a, b, c) => ` 25 किमी के भीतर <b>${a}</b>, 50 किमी के भीतर <b>${b}</b> और 100 किमी के भीतर <b>${c}</b> आग दिखीं।`,
      none: (r) => `पिछले 24 घंटों में नासा के उपग्रहों को आपसे <b>${r} किमी के भीतर कोई आग नहीं दिखी</b>। आज की धुंध शायद स्थानीय है: ट्रैफ़िक, उद्योग, ईंट भट्ठे, कचरा जलाना और धूल।`,
      where: (p) => `आपकी अनुमानित जगह: ${p}, आपके इंटरनेट कनेक्शन से, इसलिए यह दसियों किलोमीटर ग़लत हो सकती है।`,
      exact: "आपकी जगह आपके डिवाइस से।", outside: "यह पन्ना पाकिस्तान और भारत को कवर करता है, और आपका कनेक्शन इनके बाहर लगता है। इसकी जगह कोई शहर खोलें:",
      unknown: "हम आपकी जगह नहीं जान पाए। नीचे का बटन इस्तेमाल करें या कोई शहर खोलें:", city: (a) => `आपके सबसे नज़दीकी शहर में धुआँ कहाँ से आ रहा है: ${a}।`,
      denied: "जगह साझा नहीं की गई, इसलिए यह पन्ना अब भी कनेक्शन की अनुमानित जगह इस्तेमाल कर रहा है।", fail: "आग का फ़ीड लोड नहीं हुआ। एक मिनट बाद फिर कोशिश करें।" },
  };
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const rad = Math.PI / 180;
  const dist = (a, b, c, d) => 2 * 6371 * Math.asin(Math.sqrt(Math.sin(((c - a) * rad) / 2) ** 2 + Math.cos(a * rad) * Math.cos(c * rad) * Math.sin(((d - b) * rad) / 2) ** 2));
  const bearing = (a, b, c, d) => {
    const y = Math.sin((d - b) * rad) * Math.cos(c * rad), x = Math.cos(a * rad) * Math.sin(c * rad) - Math.sin(a * rad) * Math.cos(c * rad) * Math.cos((d - b) * rad);
    return (Math.atan2(y, x) / rad + 360) % 360;
  };
  // A point `km` from (lat, lon) towards `deg`, flat-earth: fine for drawing 250 km.
  const toward = (lat, lon, deg, km) => [lat + (km / 111.2) * Math.cos(deg * rad), lon + (km / (111.2 * Math.cos(lat * rad))) * Math.sin(deg * rad)];

  // The 24-hour feed, expanded to {lat, lon, t, place, district, state, kind}. One fetch per page.
  let feed;
  const fires = () => (feed ||= fetch("/api/fires?hours=24&v=2").then((r) => (r.ok ? r.json() : Promise.reject(r.status))).then((d) => {
    const P = d.dict.place, D = d.dict.district, K = d.dict.kind;
    return d.points.map((r) => ({ lat: r[0], lon: r[1], t: d.t0 + r[2] * 60000, place: P[r[5]], district: D[r[6]][0], state: D[r[6]][1], kind: K[r[7]] }));
  }));
  const around = (all, lat, lon, km) => all.map((f) => ({ ...f, km: dist(lat, lon, f.lat, f.lon) })).filter((f) => f.km <= km).sort((a, b) => a.km - b.km);

  const angle = (a, b) => { const d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d; };
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Wind streaks, as on the live map, but only inside the upwind wedge: they drift with the wind towards
  // the city and are respawned when they leave the wedge or grow old.
  function streaks(map, lat, lon, wind, km, speed) {
    map.createPane("streaks").style.zIndex = 390; // under the fire dots
    const pane = map.getPane("streaks");
    pane.style.pointerEvents = "none";
    const canvas = L.DomUtil.create("canvas", "", pane), ctx = canvas.getContext("2d");
    const step = Math.min(2.4, 0.7 + (speed || 5) * 0.09), MAX_AGE = 120;
    const go = ((wind + 180) * Math.PI) / 180, vx = Math.sin(go) * step, vy = -Math.cos(go) * step; // screen y points down
    let W = 0, H = 0, wedge = [], parts = [], raf = 0, frames = 0, visible = true;
    const inside = (x, y) => { // point in polygon
      let c = false;
      for (let i = 0, j = wedge.length - 1; i < wedge.length; j = i++) {
        const [xi, yi] = wedge[i], [xj, yj] = wedge[j];
        if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
      }
      return c;
    };
    const spawn = (p) => {
      for (let k = 0; k < 30; k++) { p.x = Math.random() * W; p.y = Math.random() * H; if (inside(p.x, p.y)) break; }
      p.age = Math.floor(Math.random() * MAX_AGE);
    };
    function build() {
      const size = map.getSize(), dpr = Math.min(2, window.devicePixelRatio || 1);
      W = size.x; H = size.y;
      canvas.width = W * dpr; canvas.height = H * dpr;
      canvas.style.width = W + "px"; canvas.style.height = H + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      L.DomUtil.setPosition(canvas, map.containerPointToLayerPoint([0, 0]));
      const pt = (ll) => { const q = map.latLngToContainerPoint(ll); return [q.x, q.y]; };
      wedge = [pt([lat, lon])];
      for (let a = -UPWIND; a <= UPWIND; a += 5) wedge.push(pt(toward(lat, lon, wind + a, km)));
      const area = Math.abs(wedge.reduce((s, [x, y], i) => { const [x2, y2] = wedge[(i + 1) % wedge.length]; return s + x * y2 - x2 * y; }, 0)) / 2;
      const vis = Math.min(area, W * H);
      parts = Array.from({ length: Math.round(Math.min(600, vis / 650)) }, () => { const p = {}; spawn(p); return p; });
      ctx.clearRect(0, 0, W, H);
      frames = 0;
    }
    function frame() {
      raf = 0;
      if (!document.hidden && visible) {
        ctx.globalCompositeOperation = "destination-in";
        ctx.fillStyle = "rgba(0,0,0,0.92)";
        ctx.fillRect(0, 0, W, H);
        ctx.globalCompositeOperation = "source-over";
        ctx.strokeStyle = "rgba(38,58,92,0.5)";
        ctx.lineWidth = 1.1;
        ctx.lineCap = "round";
        ctx.beginPath();
        for (const p of parts) {
          const nx = p.x + vx, ny = p.y + vy;
          if (++p.age > MAX_AGE || !inside(nx, ny)) { spawn(p); p.age = 0; continue; }
          ctx.moveTo(p.x, p.y); ctx.lineTo(nx, ny);
          p.x = nx; p.y = ny;
        }
        ctx.stroke();
        frames++;
      }
      if (reduced && frames > 60) return;
      raf = requestAnimationFrame(frame);
    }
    const start = () => { build(); if (!raf) raf = requestAnimationFrame(frame); };
    const stop = () => { if (raf) cancelAnimationFrame(raf); raf = 0; ctx.clearRect(0, 0, W, H); };
    map.on("movestart zoomstart", stop);
    map.on("moveend zoomend resize", start);
    // Pause while the map is scrolled out of view.
    if ("IntersectionObserver" in window) new IntersectionObserver((es) => { visible = es.some((e) => e.isIntersecting); }).observe(map.getContainer());
    start();
    map.on("unload", stop);
  }

  function draw(el, pts, lat, lon, km, wind, l) {
    if (el._map) { el._map.remove(); el._map = null; }
    const t = T[l] || T.en, nf = new Intl.NumberFormat(LOC[l] || "en-GB", { maximumFractionDigits: 0 });
    const map = (el._map = L.map(el, { scrollWheelZoom: false }));
    L.tileLayer(ESRI, { style: "World_Light_Gray_Base", attribution: ATTR, maxNativeZoom: 16 }).addTo(map);
    L.tileLayer(ESRI, { style: "World_Light_Gray_Reference", maxNativeZoom: 16 }).addTo(map);
    // With a wind, the fires upwind (whose smoke the wind is bringing) are red and the rest are faded;
    // without one (the near-me page), red is likely crop burning and brown anything else.
    const up = (f) => wind != null && angle(bearing(lat, lon, f.lat, f.lon), wind) <= UPWIND;
    if (wind != null) {
      const wedge = [[lat, lon]];
      for (let a = -UPWIND; a <= UPWIND; a += 5) wedge.push(toward(lat, lon, wind + a, km));
      L.polygon(wedge, { stroke: false, fillColor: "#2f6f9f", fillOpacity: 0.07, interactive: false }).addTo(map);
    }
    L.circle([lat, lon], { radius: km * 1000, color: "#777", weight: 1, dashArray: "4 4", fill: false, interactive: false }).addTo(map);
    const canvas = L.canvas({ padding: 0.3 }), now = Date.now();
    // Faded fires first, so the upwind ones sit on top.
    const order = [...pts].reverse().sort((a, b) => up(a) - up(b));
    for (const f of order) {
      const style = wind == null
        ? (f.kind === "crop" ? { color: "#a3170d", fillColor: "#e8452f", fillOpacity: 0.8 } : { color: "#5a4630", fillColor: "#8a7356", fillOpacity: 0.8 })
        : up(f) ? { color: "#8f140b", fillColor: "#e3321f", fillOpacity: 0.9 } : { color: "#9a9a9a", fillColor: "#c4c4c4", fillOpacity: 0.55 };
      L.circleMarker([f.lat, f.lon], { renderer: canvas, radius: wind != null && up(f) ? 4.5 : 3.5, weight: 0.8, ...style })
        .bindTooltip(`<b>${esc(f.place)}</b>, ${esc(f.district)}<br>${esc(t.kind[f.kind] || "")}<br>${esc(t.km(nf.format(f.km)))} · ${esc(t.ago(Math.floor((now - f.t) / 36e5)))}`, { direction: "top" })
        .addTo(map);
    }
    L.circleMarker([lat, lon], { radius: 7, weight: 3, color: "#fff", fillColor: "#1d1d1b", fillOpacity: 1 }).bindTooltip(el.dataset.label || t.here, { permanent: !el.dataset.label, direction: "right" }).addTo(map);
    // Frame the nearest fires that matter: the 25th nearest upwind one when there is a wind, otherwise the
    // 25th nearest of all; at least 40 km out and at most the page's radius.
    const key = wind != null && pts.some(up) ? pts.filter(up) : pts;
    const r = Math.max(40, Math.min(km, key.length ? key[Math.min(key.length, 25) - 1].km * 1.15 : km));
    map.fitBounds(L.latLng(lat, lon).toBounds(r * 2000), { padding: [8, 8] });
    if (wind != null) {
      // Streaks drifting into the city inside the upwind wedge, and the wind in words in the corner.
      map.whenReady(() => streaks(map, lat, lon, wind, km, +el.dataset.speed));
      const box = L.control({ position: "topright" });
      box.onAdd = () => {
        const d = L.DomUtil.create("div", "near-wind");
        d.innerHTML = `<span>${t.windFrom(t.dirs[Math.round(wind / 45) % 8], el.dataset.speed ? nf.format(+el.dataset.speed) : "")}</span>` +
          `<span class="k"><i style="background:#e3321f"></i>${t.keyUp}</span><span class="k"><i style="background:#c4c4c4"></i>${t.keyOther}</span>`;
        return d;
      };
      box.addTo(map);
    }
  }

  // City pages: a fixed point.
  function city(el) {
    if (el._done || !window.L || !el.offsetParent) return;
    el._done = true;
    const lat = +el.dataset.lat, lon = +el.dataset.lon, km = +el.dataset.km || 250;
    const wind = el.dataset.wind === "" || el.dataset.wind == null ? null : +el.dataset.wind;
    fires().then((all) => draw(el, around(all, lat, lon, km), lat, lon, km, wind, el.dataset.lang)).catch((e) => console.warn("[hh] near map", e));
  }

  // /near-me/: the visitor's location, then the answer in words and the map, in every language article.
  const R = 250, BOX = [5.5, 37.5, 60.5, 97.5]; // s, n, w, e: roughly Pakistan and India
  let here = null;
  const cityLink = (lat, lon, l) => {
    const c = (window.HH_CITIES || []).map((c) => ({ c, km: dist(lat, lon, c.lat, c.lon) })).sort((a, b) => a.km - b.km)[0];
    return c ? `<a href="/air/${c.c.id}/">${esc(c.c.name[l] || c.c.name.en)}</a>` : "";
  };
  function answer() {
    const boxes = [...document.querySelectorAll("[data-near-me]")];
    if (!boxes.length || !here) return;
    const inside = here.lat >= BOX[0] && here.lat <= BOX[1] && here.lon >= BOX[2] && here.lon <= BOX[3];
    fires().then((all) => {
      const pts = inside ? around(all, here.lat, here.lon, R) : [];
      for (const box of boxes) {
        const l = box.dataset.lang, t = T[l] || T.en, nf = new Intl.NumberFormat(LOC[l] || "en-GB", { maximumFractionDigits: 0 });
        const out = box.querySelector("[data-answer]"), mapEl = box.querySelector(".ff-map");
        let h = `<span class="muted">${here.exact ? t.exact : t.where(esc(here.label))}${here.note ? " " + t.denied : ""}</span><br>`;
        if (!inside) { out.innerHTML = h + t.outside; mapEl.hidden = true; continue; }
        if (pts.length) {
          const f = pts[0], dir = t.dirs[Math.round(bearing(here.lat, here.lon, f.lat, f.lon) / 45) % 8];
          const place = `${esc(f.place)}, ${esc(f.district)}`;
          h += t.nearest(nf.format(f.km), dir, place, t.ago(Math.floor((Date.now() - f.t) / 36e5)));
          const n = (k) => nf.format(pts.filter((p) => p.km <= k).length);
          h += t.counts(n(25), n(50), n(100));
        } else h += t.none(nf.format(R));
        h += " " + t.city(cityLink(here.lat, here.lon, l));
        out.innerHTML = h;
        mapEl.hidden = false;
        if (mapEl.offsetParent && window.L) draw(mapEl, pts, here.lat, here.lon, R, null, l);
        else mapEl._pending = true;
      }
    }).catch((e) => { console.warn("[hh] near me", e); for (const b of boxes) b.querySelector("[data-answer]").textContent = (T[b.dataset.lang] || T.en).fail; });
  }
  function nearMe() {
    const boxes = [...document.querySelectorAll("[data-near-me]")];
    if (!boxes.length || nearMe.started) return;
    nearMe.started = true;
    fetch("/api/where").then((r) => r.json()).then((w) => {
      if (here?.exact) return;
      if (w && w.lat) here = { lat: w.lat, lon: w.lon, label: [w.city, w.region, w.country].filter(Boolean).join(", ") };
      if (here) answer();
      else for (const b of boxes) b.querySelector("[data-answer]").textContent = (T[b.dataset.lang] || T.en).unknown;
    }).catch(() => {});
    for (const b of boxes) b.querySelector("[data-exact]")?.addEventListener("click", () => {
      navigator.geolocation?.getCurrentPosition(
        (p) => { here = { lat: p.coords.latitude, lon: p.coords.longitude, exact: true }; answer(); },
        () => { if (here) { here.note = true; answer(); } },
        { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 });
    });
  }

  function watch() {
    document.querySelectorAll(".ff-map[data-near]").forEach((el) => {
      if (el._watched) return city(el);
      el._watched = true;
      if (!("IntersectionObserver" in window)) return city(el);
      const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); city(el); } }, { rootMargin: "300px" });
      io.observe(el);
    });
    // A language switch shows another article; draw its near-me map if it was waiting.
    document.querySelectorAll("[data-near-me] .ff-map").forEach((el) => { if (el._pending && el.offsetParent) { el._pending = false; answer(); } });
    nearMe();
  }
  watch();
  addEventListener("hh:lang", () => setTimeout(watch, 0));
})();
