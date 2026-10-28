// "Share this map": a picture of the map exactly as the visitor sees it (their zoom, layers and filters),
// drawn in their browser, with a link back to the same view on hamarihawa.org. Nothing is uploaded or
// stored by us: the image only leaves the device through the app the visitor shares it with, and the
// link is always ours, built from the map's state (numbers checked again when the link is opened).
(() => {
  "use strict";
  const SITE = "https://hamarihawa.org";
  const T = {
    en: { btn: "Share this map", title: "Share this map", hint: "A picture of the map as you see it now, with a link that opens this same view.",
      share: "Share…", copy: "Copy link", copied: "Copied", dl: "Download image", busy: "Taking the picture…",
      fail: "The picture couldn't be made, but you can still share the link.", desk: "On a computer, X, Facebook and WhatsApp Web share the link only: download the image and attach it to your post.",
      main: "Live fire and air map of Pakistan and India", src: "Fires: NASA FIRMS · Map © Esri, HERE, Garmin, OpenStreetMap" },
    ur: { btn: "یہ نقشہ شیئر کریں", title: "یہ نقشہ شیئر کریں", hint: "نقشے کی تصویر جیسا آپ اسے ابھی دیکھ رہے ہیں، اور ایک لنک جو یہی منظر کھولتا ہے۔",
      share: "شیئر کریں…", copy: "لنک کاپی کریں", copied: "کاپی ہو گیا", dl: "تصویر ڈاؤن لوڈ کریں", busy: "تصویر بن رہی ہے…",
      fail: "تصویر نہیں بن سکی، لیکن آپ لنک شیئر کر سکتے ہیں۔", desk: "کمپیوٹر پر X، فیس بک اور واٹس ایپ ویب صرف لنک شیئر کرتے ہیں: تصویر ڈاؤن لوڈ کر کے پوسٹ کے ساتھ لگائیں۔",
      main: "پاکستان اور بھارت میں آگ اور ہوا کا تازہ نقشہ", src: "آگ: ناسا FIRMS · نقشہ © Esri, HERE, Garmin, OpenStreetMap" },
    hi: { btn: "यह नक्शा शेयर करें", title: "यह नक्शा शेयर करें", hint: "नक्शे की तस्वीर जैसा आप इसे अभी देख रहे हैं, और एक लिंक जो यही दृश्य खोलता है।",
      share: "शेयर करें…", copy: "लिंक कॉपी करें", copied: "कॉपी हो गया", dl: "तस्वीर डाउनलोड करें", busy: "तस्वीर बन रही है…",
      fail: "तस्वीर नहीं बन पाई, पर आप लिंक शेयर कर सकते हैं।", desk: "कंप्यूटर पर X, फ़ेसबुक और व्हाट्सऐप वेब सिर्फ़ लिंक शेयर करते हैं: तस्वीर डाउनलोड करके पोस्ट के साथ लगाएँ।",
      main: "पाकिस्तान और भारत में आग और हवा का लाइव नक्शा", src: "आग: नासा FIRMS · नक्शा © Esri, HERE, Garmin, OpenStreetMap" },
  };
  const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const lang = () => (T[document.documentElement.lang] ? document.documentElement.lang : "en");
  const t = (k) => T[lang()][k];
  const isMain = () => !!(window.HH && window.HH.map);
  let current = null, blob = null;

  // ---------- The link: our page, and on the live map the view itself ----------
  // ?s= changes every 3 hours, as the link-preview images do (src/og.js): WhatsApp and the others keep the
  // preview they first saw for an address, so a new address gets today's picture. Pages ignore it otherwise.
  function link() {
    const q = `?${lang() === "en" ? "" : `lang=${lang()}&`}s=${Math.floor(Date.now() / 10800000)}b`; // "b": src/og.js OG_REV
    if (!isMain()) return `${SITE}${location.pathname}${q}`;
    const m = window.HH.map, c = m.getCenter(), s = window.HH.state;
    const p = [`view=${c.lat.toFixed(3)},${c.lng.toFixed(3)},${m.getZoom()}`];
    if (s.layer && s.layer !== "none") p.push(`layer=${s.layer}`);
    if (s.hours && s.hours != 24) p.push(`hours=${s.hours}`);
    if (s.cc) p.push(`cc=${s.cc}`);
    if (document.getElementById("windOn")?.checked) p.push("wind=1");
    return `${SITE}/${q}#${p.join("&")}`;
  }
  function headline() {
    if (isMain()) return t("main");
    const h = document.querySelector("article:not([hidden]) h1");
    return (h ? h.textContent : document.title).trim();
  }
  const caption = () => `${headline()}\n${link()}`;

  // ---------- The picture: each Leaflet layer drawn onto one canvas, in the order the map stacks them ----------
  const images = new Map();
  const load = (src) => {
    if (!images.has(src)) images.set(src, fetch(src, { mode: "cors", credentials: "omit" }).then((r) => (r.ok ? r.blob() : null))
      .then((b) => (b ? createImageBitmap(b) : null)).catch(() => null));
    return images.get(src);
  };
  const svgImage = (svg, w, h) => {
    const c = svg.cloneNode(true);
    c.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    c.setAttribute("width", w); c.setAttribute("height", h);
    c.removeAttribute("style"); // Leaflet positions its SVG with a CSS transform; the rectangle we draw into already does that
    const color = getComputedStyle(svg).color;
    const src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(c).replace(/currentColor/g, color));
    return new Promise((res) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => res(null); i.src = src; });
  };
  function opacity(el, stop) {
    let o = 1;
    for (let e = el; e && e !== stop; e = e.parentElement) o *= +getComputedStyle(e).opacity || 1;
    return o;
  }
  async function drawMap(ctx, map) {
    const box = map.getContainer(), R = box.getBoundingClientRect();
    const panes = [...box.querySelectorAll(".leaflet-map-pane > .leaflet-pane")]
      .filter((p) => !/tooltip|popup|shadow/.test(p.className))
      .map((p, i) => ({ p, z: +getComputedStyle(p).zIndex || 0, i }))
      .sort((a, b) => a.z - b.z || a.i - b.i);
    for (const { p } of panes) {
      const els = p.querySelectorAll("img.leaflet-tile, img.leaflet-image-layer, canvas, svg.leaflet-zoom-animated, .leaflet-marker-icon");
      for (const el of els) {
        if (el.closest(".leaflet-marker-icon") && el !== el.closest(".leaflet-marker-icon")) continue; // drawn with its icon
        const r = el.getBoundingClientRect(), x = r.left - R.left, y = r.top - R.top;
        if (!r.width || !r.height || x > R.width || y > R.height || x + r.width < 0 || y + r.height < 0) continue;
        ctx.globalAlpha = opacity(el, box);
        if (el.tagName === "IMG") { const b = await load(el.src); if (b) ctx.drawImage(b, x, y, r.width, r.height); }
        else if (el.tagName === "CANVAS") { try { ctx.drawImage(el, x, y, r.width, r.height); } catch {} }
        else if (el.tagName.toLowerCase() === "svg") { const i = await svgImage(el, r.width, r.height); if (i) ctx.drawImage(i, x, y, r.width, r.height); }
        else {
          // A divIcon: its coloured disc, then any SVG drawn inside it.
          for (const d of [el, ...el.querySelectorAll("*")]) {
            if (d.tagName.toLowerCase() === "svg") {
              const q = d.getBoundingClientRect(), i = await svgImage(d, q.width, q.height);
              if (i) ctx.drawImage(i, q.left - R.left, q.top - R.top, q.width, q.height);
              continue;
            }
            const cs = getComputedStyle(d), bg = cs.backgroundColor;
            if (bg && bg !== "transparent" && !/rgba\(.*,\s*0\)$/.test(bg)) {
              const q = d.getBoundingClientRect();
              ctx.fillStyle = bg;
              ctx.beginPath(); ctx.arc(q.left - R.left + q.width / 2, q.top - R.top + q.height / 2, Math.min(q.width, q.height) / 2, 0, 7); ctx.fill();
            }
          }
        }
      }
    }
    ctx.globalAlpha = 1;
    return R;
  }
  async function picture(map) {
    const W = 1200, BAND = 132, R = map.getContainer().getBoundingClientRect(), S = W / R.width;
    const MH = Math.round(Math.min(R.height * S, 1500));
    const cv = document.getElementById("smCanvas");
    cv.width = W; cv.height = MH + BAND;
    const ctx = cv.getContext("2d");
    ctx.fillStyle = "#f4f2ec"; ctx.fillRect(0, 0, W, MH);
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, MH); ctx.clip(); ctx.scale(S, S);
    await drawMap(ctx, map);
    ctx.restore();
    // The band: what it is, when, and where to see more.
    const l = lang(), rtl = l === "ur", M = 36;
    await Promise.all(["700 40px Kalam", "400 20px Inter", rtl ? '400 30px "Noto Nastaliq Urdu"' : null].filter(Boolean).map((f) => document.fonts.load(f).catch(() => null)));
    ctx.fillStyle = "#ffffff"; ctx.fillRect(0, MH, W, BAND);
    ctx.fillStyle = "#1d1d1f"; ctx.fillRect(0, MH, W, 3);
    const hand = rtl ? '"Noto Nastaliq Urdu", serif' : '"Kalam", cursive', sans = rtl ? '"Noto Nastaliq Urdu", serif' : '"Inter", system-ui, sans-serif';
    ctx.font = '700 46px "Kalam", cursive';
    const brandW = ctx.measureText("hamarihawa.org").width;
    ctx.direction = "ltr"; ctx.textAlign = rtl ? "left" : "right"; ctx.fillStyle = "#d62d20";
    ctx.fillText("hamarihawa.org", rtl ? M : W - M, MH + 80);
    ctx.direction = rtl ? "rtl" : "ltr"; ctx.textAlign = rtl ? "right" : "left"; ctx.fillStyle = "#1d1d1f";
    const maxW = W - 2 * M - brandW - 30;
    let head = headline();
    ctx.font = `700 ${rtl ? 30 : 36}px ${hand}`;
    while (ctx.measureText(head).width > maxW && head.length > 8) head = head.slice(0, -2).trimEnd() + "…";
    ctx.fillText(head, rtl ? W - M : M, MH + (rtl ? 58 : 56));
    const when = new Intl.DateTimeFormat(LOC[l], { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date());
    ctx.font = `400 ${rtl ? 17 : 19}px ${sans}`; ctx.fillStyle = "#7c7c80";
    ctx.fillText(`${when} · ${t("src")}`, rtl ? W - M : M, MH + 104);
    return new Promise((res) => cv.toBlob(res, "image/jpeg", 0.88));
  }

  // ---------- The dialog ----------
  function dialog() {
    let d = document.getElementById("smDlg");
    if (d) return d;
    d = document.createElement("dialog");
    d.id = "smDlg"; d.className = "share-dlg";
    d.innerHTML = `<div class="dlg-inner"><div class="dlg-head"><h2 data-sm="title"></h2><button class="x" data-sm-close aria-label="Close">×</button></div>
      <div class="dlg-body"><div class="preview"><canvas id="smCanvas" width="1200" height="760"></canvas><div class="busy" data-sm="busy"></div></div>
      <div class="dlg-side"><p class="hint" data-sm="hint"></p>
        <button class="btn primary" data-sm-act="share" data-sm="share" hidden></button>
        <a class="btn wa" data-sm-link="wa" target="_blank" rel="noopener">WhatsApp</a>
        <a class="btn" data-sm-link="x" target="_blank" rel="noopener">X / Twitter</a>
        <a class="btn" data-sm-link="fb" target="_blank" rel="noopener">Facebook</a>
        <a class="btn" data-sm-link="li" target="_blank" rel="noopener">LinkedIn</a>
        <a class="btn" data-sm-link="tg" target="_blank" rel="noopener">Telegram</a>
        <button class="btn" data-sm-act="dl" data-sm="dl"></button>
        <button class="btn" data-sm-act="copy" data-sm="copy"></button>
        <p class="hint small" data-sm="desk"></p></div></div></div>`;
    document.body.append(d);
    d.addEventListener("click", (e) => {
      if (e.target === d || e.target.closest("[data-sm-close]")) return d.close();
      const a = e.target.closest("[data-sm-act]")?.dataset.smAct;
      if (a === "dl" && blob) {
        const x = document.createElement("a");
        x.href = URL.createObjectURL(blob); x.download = `hamarihawa-map-${new Date().toISOString().slice(0, 10)}.jpg`; x.click();
        setTimeout(() => URL.revokeObjectURL(x.href), 5000);
      }
      if (a === "copy") {
        const b = e.target.closest("button");
        navigator.clipboard?.writeText(link()).then(() => { b.textContent = t("copied"); setTimeout(() => { b.textContent = t("copy"); }, 2000); }).catch(() => {});
      }
      if (a === "share") {
        const file = blob && new File([blob], "hamarihawa-map.jpg", { type: "image/jpeg" });
        const withFile = file && navigator.canShare?.({ files: [file] });
        navigator.share(withFile ? { files: [file], text: caption() } : { title: headline(), text: headline(), url: link() }).catch(() => {});
      }
    });
    return d;
  }
  function fill(d) {
    d.querySelectorAll("[data-sm]").forEach((e) => { if (e.dataset.sm !== "busy") e.textContent = t(e.dataset.sm); });
    const u = encodeURIComponent(link()), h = encodeURIComponent(headline()), c = encodeURIComponent(caption());
    const hrefs = { wa: `https://wa.me/?text=${c}`, x: `https://twitter.com/intent/tweet?text=${h}&url=${u}&hashtags=HamariHawa`,
      fb: `https://www.facebook.com/sharer/sharer.php?u=${u}`, li: `https://www.linkedin.com/sharing/share-offsite/?url=${u}`,
      tg: `https://t.me/share/url?url=${u}&text=${h}` };
    d.querySelectorAll("[data-sm-link]").forEach((a) => { a.href = hrefs[a.dataset.smLink]; });
    d.querySelector('[data-sm-act="share"]').hidden = !navigator.share;
  }
  async function open(map) {
    current = map;
    const d = dialog();
    fill(d);
    if (!d.open) d.showModal();
    const busy = d.querySelector('[data-sm="busy"]');
    busy.textContent = t("busy"); busy.hidden = false;
    blob = null;
    try { blob = await picture(map); busy.hidden = true; }
    catch (e) { console.warn("[hh] share map", e); busy.textContent = t("fail"); }
  }
  addEventListener("hh:lang", () => { const d = document.getElementById("smDlg"); if (d?.open && current) open(current); });

  // ---------- The button, as a map control ----------
  function control(map) {
    const c = L.control({ position: "topright" });
    c.onAdd = () => {
      const b = L.DomUtil.create("button", "btn map-share");
      b.type = "button";
      b.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7M16 6l-4-4-4 4M12 2v13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg><span>${t("btn")}</span>`;
      L.DomEvent.disableClickPropagation(b);
      b.addEventListener("click", () => open(map));
      addEventListener("hh:lang", () => { b.querySelector("span").textContent = t("btn"); });
      return b;
    };
    c.addTo(map);
  }
  window.HHShareMap = { control };

  // The live map: the button, and the rest of a shared view (the wind layer loads after app.js reads the link).
  if (isMain()) {
    control(window.HH.map);
    if (new URLSearchParams(location.hash.slice(1)).get("wind") === "1") {
      const w = document.getElementById("windOn");
      if (w && !w.checked) { w.checked = true; w.dispatchEvent(new Event("change")); }
    }
  }
})();
