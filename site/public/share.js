// Shareable "today's card": a branded PNG drawn in the browser from the live numbers,
// in square (Instagram/Facebook), story (9:16) and wide (X) sizes, in the reader's language.
(() => {
  "use strict";
  const HH = window.HH;
  const SITE = "hamarihawa.org";
  const URL_ = "https://hamarihawa.org/";
  const FORMATS = {
    square: { w: 1080, h: 1350 }, // 4:5, the tallest feed post Instagram and Facebook allow
    story: { w: 1080, h: 1920 },
    wide: { w: 1600, h: 900 },
  };
  const INK = "#1d1d1f", INK2 = "#4a4a4c", INK3 = "#7c7c80", FIRE = "#d62d20", HAIR = "#e6e3dc";
  const AQI = ["#5aa846", "#e3b52a", "#ec8a2b", "#d93b30", "#8b3fa8", "#7b1d2f"];
  const BOX = { s: 6, n: 37.5, w: 60.5, e: 97.5 }; // scripts/geo.py REGION
  const LABELS = [
    ["Lahore", 31.55, 74.34], ["Karachi", 24.86, 67.0], ["Islamabad", 33.69, 73.06], ["Delhi", 28.61, 77.21],
    ["Lucknow", 26.85, 80.95], ["Mumbai", 19.08, 72.88], ["Kolkata", 22.57, 88.36], ["Chennai", 13.08, 80.27], ["Bengaluru", 12.97, 77.59],
  ];
  const LABEL_I18N = {
    ur: { Lahore: "لاہور", Karachi: "کراچی", Islamabad: "اسلام آباد", Multan: "ملتان", Delhi: "دہلی", Lucknow: "لکھنؤ", Patna: "پٹنہ", Amritsar: "امرتسر", Jaipur: "جے پور", Mumbai: "ممبئی", Kolkata: "کولکاتہ", Chennai: "چنئی", Bengaluru: "بنگلور", PAKISTAN: "پاکستان", INDIA: "ہندوستان" },
    hi: { Lahore: "लाहौर", Karachi: "कराची", Islamabad: "इस्लामाबाद", Multan: "मुल्तान", Delhi: "दिल्ली", Lucknow: "लखनऊ", Patna: "पटना", Amritsar: "अमृतसर", Jaipur: "जयपुर", Mumbai: "मुंबई", Kolkata: "कोलकाता", Chennai: "चेन्नई", Bengaluru: "बेंगलुरु", PAKISTAN: "पाकिस्तान", INDIA: "भारत" },
  };

  let fmt = "square", feed = null, blob = null;
  const $ = (s) => document.querySelector(s);
  const t = (k, v) => HH.t(k, v);
  const lang = () => HH.state.lang;
  const fonts = () => {
    const l = lang();
    return {
      hand: l === "ur" ? '"Noto Nastaliq Urdu", serif' : '"Kalam", cursive',
      sans: l === "ur" ? '"Noto Nastaliq Urdu", serif' : '"Inter", system-ui, sans-serif',
      latinHand: '"Kalam", cursive',
    };
  };

  let no2 = null;
  async function loadNo2() {
    if (no2 === null) no2 = await fetch("/api/no2.json", { cache: "no-cache" }).then((r) => (r.ok ? r.json() : false)).catch(() => false);
    return no2 || null;
  }
  // Top 3 city-traffic NO2 hotspots; the reader's own city goes first when it has one.
  function trafficTop(n) {
    if (!n) return [];
    const list = n.hotspots.filter((h) => h[3] === "traffic");
    const me = HH.state.local;
    if (me && me.lat) {
      const mine = list.find((h) => Math.hypot(h[0] - me.lat, (h[1] - me.lon) * 0.87) * 111 < 30);
      if (mine) return [mine, ...list.filter((h) => h !== mine)].slice(0, 3);
    }
    return list.slice(0, 3);
  }
  function cityLabel(name) {
    const c = HH.CITIES.find((x) => x.name.en === name);
    return c ? c.name[lang()] : name;
  }

  async function loadFeed() {
    if (feed && Date.now() - feed._at < 5 * 60 * 1000) return feed;
    const r = await fetch("/api/fires?hours=24&v=2");
    feed = HH.expandFeed(await r.json());
    feed._at = Date.now();
    return feed;
  }

  function cityStats() {
    const s = HH.state;
    if (!s.air) return null;
    const rows = HH.CITIES.map((c, i) => ({ c, a: s.air[i] })).filter((r) => r.a);
    rows.forEach((r) => { r.h = HH.health(r.c, r.a.pm24); });
    rows.sort((a, b) => b.a.us_aqi - a.a.us_aqi);
    let unhealthy = 0, deaths = 0;
    for (const r of rows) { if (r.a.us_aqi > 150) unhealthy += r.c.pop; deaths += r.h.deaths; }
    return { worst: rows.slice(0, 3), unhealthy, deaths, best: rows[rows.length - 1] };
  }

  // ---------- drawing helpers ----------
  function roughRect(rc, x, y, w, h, seed, opts = {}) {
    if (rc) rc.rectangle(x, y, w, h, { roughness: 1.1, bowing: 0.8, stroke: "#2b2b2b", strokeWidth: 2.2, seed, ...opts });
  }
  function roughLine(rc, ctx, x1, y1, x2, y2, color, width, seed) {
    if (rc) rc.line(x1, y1, x2, y2, { roughness: 1.4, bowing: 1.5, stroke: color, strokeWidth: width, seed });
    else { ctx.strokeStyle = color; ctx.lineWidth = width; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); }
  }
  // Text helper that mirrors x for right-to-left languages so one layout serves all three.
  function makeText(ctx, W) {
    const rtl = lang() === "ur";
    return (str, x, y, font, color, align = "left", maxW) => {
      ctx.font = font;
      ctx.fillStyle = color;
      ctx.direction = rtl ? "rtl" : "ltr";
      let ax = x, al = align;
      if (rtl) { ax = W - x; al = align === "left" ? "right" : align === "right" ? "left" : "center"; }
      ctx.textAlign = al;
      ctx.textBaseline = "alphabetic";
      ctx.fillText(str, ax, y, maxW);
    };
  }
  function wrap(ctx, str, font, maxW) {
    ctx.font = font;
    const words = str.split(" "), lines = [];
    let line = "";
    for (const w of words) {
      const test = line ? line + " " + w : w;
      if (ctx.measureText(test).width > maxW && line) { lines.push(line); line = w; } else line = test;
    }
    if (line) lines.push(line);
    return lines;
  }
  function flame(ctx, x, y, s, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s / 32, s / 32);
    ctx.strokeStyle = color; ctx.lineWidth = 2.2; ctx.lineJoin = "round"; ctx.lineCap = "round";
    ctx.stroke(new Path2D("M16 3c2 6 9 9 9 17a9 9 0 0 1-18 0c0-5 3-7 4-11 1 3 2 4 3 4 0-4 0-7 2-10z"));
    ctx.lineWidth = 1.8;
    ctx.stroke(new Path2D("M5 24c4-2 7 2 11 0s7-2 11 0"));
    ctx.restore();
  }

  function drawMap(ctx, rc, x, y, w, h, pts, hot = []) {
    // Equirectangular with a cos(lat) squash, fitted to the box.
    const k = Math.cos((22 * Math.PI) / 180);
    const sx = w / ((BOX.e - BOX.w) * k), sy = h / (BOX.n - BOX.s), sc = Math.min(sx, sy);
    const ox = x + (w - (BOX.e - BOX.w) * k * sc) / 2, oy = y + (h - (BOX.n - BOX.s) * sc) / 2;
    const P = (lat, lon) => [ox + (lon - BOX.w) * k * sc, oy + (BOX.n - lat) * sc];
    // Text and marker size, independent of how many degrees the box spans.
    const u = Math.max(sc, Math.min(w, h) / 20);
    ctx.fillStyle = "#faf8f3";
    ctx.fillRect(x, y, w, h);
    // light pencil graticule
    ctx.save();
    ctx.strokeStyle = HAIR; ctx.lineWidth = 1; ctx.setLineDash([3, 6]);
    for (let lon = 64; lon <= 96; lon += 8) { const [a, b] = P(BOX.n, lon), [, d] = P(BOX.s, lon); ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(a, d); ctx.stroke(); }
    for (let lat = 10; lat <= 34; lat += 8) { const [a, b] = P(lat, BOX.w), [c] = P(lat, BOX.e); ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(c, b); ctx.stroke(); }
    ctx.restore();
    const L = LABEL_I18N[lang()] || {};
    const f = fonts();
    // country labels
    ctx.textAlign = "center"; ctx.direction = lang() === "ur" ? "rtl" : "ltr";
    ctx.font = `600 ${Math.round(u * 0.55)}px ${f.sans}`; ctx.fillStyle = "#c9c4b9";
    let [px, py] = P(28.2, 65.6); ctx.fillText(L.PAKISTAN || "PAKISTAN", px, py);
    [px, py] = P(21.5, 78.5); ctx.fillText(L.INDIA || "INDIA", px, py);
    // fires: oldest first so the newest sit on top
    const now = Date.now();
    const list = pts.slice().sort((a, b) => a[2] - b[2]);
    for (const p of list) {
      const [cx, cy] = P(p[0], p[1]);
      if (cx < x || cx > x + w || cy < y || cy > y + h) continue;
      const hrs = (now - p[2]) / 36e5;
      ctx.fillStyle = hrs < 3 ? "rgba(214,45,32,.85)" : hrs < 12 ? "rgba(240,138,36,.85)" : "rgba(160,116,84,.8)";
      const r = Math.max(2.5, Math.min(9, 2.4 + Math.sqrt(p[3]) * 0.6)) * (sc / 26);
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
    }
    // Traffic hotspots: numbered red rings matching the line under the map.
    hot.forEach((hs, i) => {
      const [cx, cy] = P(hs[0], hs[1]);
      const r = Math.max(10, u * 0.3);
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(255,255,255,.85)"; ctx.fill();
      ctx.lineWidth = 3; ctx.strokeStyle = FIRE; ctx.stroke();
      ctx.fillStyle = FIRE; ctx.font = `700 ${Math.round(r * 1.25)}px ${f.latinHand}`; ctx.textAlign = "center"; ctx.direction = "ltr";
      ctx.fillText(String(i + 1), cx, cy + r * 0.42);
    });
    // city reference points
    ctx.font = `600 ${Math.round(u * 0.5)}px ${f.sans}`;
    for (const [name, lat, lon] of LABELS) {
      const [cx, cy] = P(lat, lon);
      ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(cx, cy, u * 0.09, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = "#fff"; ctx.lineWidth = u * 0.12; ctx.lineJoin = "round";
      ctx.textAlign = "left"; ctx.direction = "ltr";
      const label = L[name] || name;
      ctx.strokeText(label, cx + u * 0.18, cy + u * 0.14);
      ctx.fillStyle = INK2; ctx.fillText(label, cx + u * 0.18, cy + u * 0.14);
    }
    roughRect(rc, x, y, w, h, 11);
  }

  // ---------- the card ----------
  async function render() {
    const F = FORMATS[fmt];
    const W = F.w, H = F.h;
    const cv = $("#shareCanvas");
    cv.width = W; cv.height = H;
    const ctx = cv.getContext("2d");
    const rc = window.rough ? rough.canvas(cv) : null;
    const f = fonts();
    await Promise.all([`700 80px Kalam`, `400 40px Inter`, `600 40px Inter`, lang() === "ur" ? `400 40px "Noto Nastaliq Urdu"` : null]
      .filter(Boolean).map((x) => document.fonts.load(x).catch(() => null)));
    const [d, n2] = await Promise.all([loadFeed(), loadNo2()]);
    const cs = cityStats();
    const hot = trafficTop(n2);
    const text = makeText(ctx, W);
    const s = d.stats;
    const day = new Intl.DateTimeFormat(HH.locale(), { day: "numeric", month: "long", year: "numeric" }).format(d.latest || d.generated);

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, W, H);

    const wide = fmt === "wide", story = fmt === "story";
    const M = wide ? 64 : 72;
    const big = (n) => Math.round(n * (wide ? 0.82 : 1));

    // header: brand + date
    const rtl = lang() === "ur";
    flame(ctx, rtl ? W - M - 56 : M, M - 6, 56, FIRE);
    ctx.direction = "ltr"; ctx.textAlign = rtl ? "right" : "left";
    ctx.font = `700 ${big(52)}px ${f.latinHand}`; ctx.fillStyle = INK;
    ctx.fillText("HamariHawa", rtl ? W - M - 70 : M + 70, M + 38);
    text(day, W - M, M + 36, `400 ${big(30)}px ${f.hand}`, INK3, "right");
    roughLine(rc, ctx, M, M + 76, W - M, M + 76, "#2b2b2b", 1.6, 3);

    // headline block
    const colW = wide ? 640 : W - 2 * M;
    let y = M + (story ? 300 : wide ? 200 : 230);
    const n = HH.nf(s.spots);
    ctx.direction = "ltr"; ctx.textAlign = rtl ? "right" : "left";
    ctx.font = `700 ${big(story ? 260 : 200)}px ${f.latinHand}`; ctx.fillStyle = FIRE;
    ctx.fillText(n, rtl ? W - M : M, y);
    y += big(lang() === "ur" ? 92 : 64);
    for (const line of wrap(ctx, t("cardFires"), `600 ${big(46)}px ${f.sans}`, colW)) {
      text(line, M, y, `600 ${big(46)}px ${f.sans}`, INK, "left"); y += big(rtl ? 78 : 58);
    }
    y += big(4);
    text(t("headSplit", { pk: HH.nf(s.pk), in: HH.nf(s.in) }), M, y, `400 ${big(34)}px ${f.sans}`, INK2, "left");

    // map
    let mx, my, mw, mh;
    const tl = hot.length ? 44 : 0; // room for the traffic line under the map key
    if (wide) { mx = 740; my = M + 110; mw = W - mx - M; mh = H - my - 150 - tl; }
    else { mx = M; my = y + (story ? 70 : 40); mw = W - 2 * M; mh = (story ? 700 : 400) - (lang() === "ur" ? (story ? 40 : 90) : 0) - tl; }
    drawMap(ctx, rc, mx, my, mw, mh, d.points, hot);
    // map key
    const keyY = my + mh + 34;
    ctx.font = `400 ${big(24)}px ${f.sans}`;
    const keys = [["rgba(214,45,32,.85)", t("age_3")], ["rgba(240,138,36,.85)", t("age_12")], ["rgba(160,116,84,.8)", t("age_old")]];
    let kx = rtl ? W - (wide ? M : mx) : mx;
    for (const [c, lbl] of keys) {
      ctx.fillStyle = c; ctx.beginPath(); ctx.arc(rtl ? kx - 9 : kx + 9, keyY - 8, 9, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = INK2; ctx.direction = rtl ? "rtl" : "ltr"; ctx.textAlign = rtl ? "right" : "left";
      ctx.fillText(lbl, rtl ? kx - 26 : kx + 26, keyY);
      const wdt = ctx.measureText(lbl).width + 60;
      kx += rtl ? -wdt : wdt;
    }

    // traffic line: "Worst traffic air (NO₂, 2 weeks): 1 Delhi 6.1×  2 Rawalpindi 4.6×  3 Lahore 3.8×"
    if (hot.length) {
      const ty = keyY + 40;
      const parts = hot.map((h, i) => `${i + 1} ${cityLabel(h[4])} ${HH.nf(h[2], { maximumFractionDigits: 1 })}×`);
      const line = `${t("cardTraffic")}  ${parts.join("   ")}`;
      ctx.direction = rtl ? "rtl" : "ltr"; ctx.textAlign = rtl ? "right" : "left";
      ctx.font = `600 ${big(story ? 30 : 24)}px ${f.sans}`; ctx.fillStyle = FIRE;
      ctx.fillText(line, rtl ? W - (wide ? M : mx) : (wide ? mx : mx), ty, wide ? mw : W - 2 * M);
    }

    // health stats
    if (cs) {
      const worst = cs.worst[0];
      const me = HH.state.local;
      const myCity = localCity(me);
      // Personal first: the reader's own city when we know it, otherwise the worst of our 17 cities.
      const stats = me && me.aqi != null && me.city ? [
        { n: HH.nf(Math.round(me.aqi)), color: AQI[HH.aqiBand(me.aqi)], l: t("cardMine", { city: myCity }) },
        { n: HH.nf(me.pm24 / 22, { maximumFractionDigits: 1 }), color: INK, l: t("cardMyCigs", { city: myCity }) },
        { n: "≈ " + HH.nf(Math.round(cs.deaths)), color: FIRE, l: t("cardDeaths") },
      ] : [
        { n: HH.nf(Math.round(worst.a.us_aqi)), color: AQI[HH.aqiBand(worst.a.us_aqi)], l: t("cardWorst", { city: worst.c.name[lang()] }) },
        { n: HH.nf(worst.h.cigs, { maximumFractionDigits: 1 }), color: INK, l: t("cardCigs", { city: worst.c.name[lang()] }) },
        { n: "≈ " + HH.nf(Math.round(cs.deaths)), color: FIRE, l: t("cardDeaths") },
      ];
      let sy, sx, sw, sh, gap = 24;
      if (wide) { sx = M; sy = y + 50; sw = colW; sh = 78; }
      else { sx = M; sy = keyY + (story ? 70 : 34) + tl; sw = W - 2 * M; sh = story ? 230 : 150; }
      if (wide) {
        stats.forEach((st, i) => {
          const yy = sy + i * (sh + 12);
          roughRect(rc, sx, yy, sw, sh, 30 + i, { strokeWidth: 1.6 });
          ctx.direction = "ltr"; ctx.textAlign = rtl ? "right" : "left";
          ctx.font = `700 ${big(62)}px ${f.latinHand}`; ctx.fillStyle = st.color;
          ctx.fillText(st.n, rtl ? W - sx - 24 : sx + 24, yy + 60);
          const nw = ctx.measureText(st.n).width + 48;
          const lines = wrap(ctx, st.l, `400 ${big(26)}px ${f.sans}`, sw - nw - 30);
          lines.slice(0, 2).forEach((ln, j) => text(ln, sx + nw, yy + (lines.length > 1 ? 34 : 48) + j * (rtl ? 34 : 26), `400 ${big(26)}px ${f.sans}`, INK2, "left"));
        });
      } else {
        const cw = (sw - gap * 2) / 3;
        stats.forEach((st, i) => {
          const xx = sx + i * (cw + gap);
          const lx = rtl ? W - xx - cw : xx; // physical x for the box
          roughRect(rc, lx, sy, cw, sh, 30 + i, { strokeWidth: 1.6 });
          ctx.direction = "ltr"; ctx.textAlign = "left";
          ctx.font = `700 ${story ? 78 : 60}px ${f.latinHand}`; ctx.fillStyle = st.color;
          ctx.fillText(st.n, lx + 22, sy + (story ? 88 : 66));
          const fz = story ? 26 : 21;
          const lines = wrap(ctx, st.l, `400 ${fz}px ${f.sans}`, cw - 40);
          ctx.direction = rtl ? "rtl" : "ltr"; ctx.textAlign = rtl ? "right" : "left";
          lines.slice(0, story ? 3 : 2).forEach((ln, j) => { ctx.fillStyle = INK2; ctx.font = `400 ${fz}px ${f.sans}`; ctx.fillText(ln, rtl ? lx + cw - 22 : lx + 22, sy + (story ? 126 : 100) + j * (rtl ? 34 : fz + 6)); });
        });
      }
    }

    // CTA band
    const bandH = wide ? 110 : story ? 250 : 150;
    const by = H - bandH;
    ctx.fillStyle = INK;
    ctx.fillRect(0, by, W, bandH);
    const ctaY = by + (story ? 95 : wide ? 48 : 58);
    text(t("cardCta"), M, ctaY, `600 ${big(story ? 44 : 36)}px ${f.sans}`, "#ffffff", "left", W - 2 * M);
    ctx.direction = "ltr"; ctx.textAlign = rtl ? "right" : "left";
    ctx.font = `700 ${big(story ? 72 : 56)}px ${f.latinHand}`; ctx.fillStyle = "#ffb3a8";
    ctx.fillText(SITE, rtl ? W - M : M, ctaY + (story ? 90 : wide ? 46 : 60));
    ctx.font = `400 ${big(22)}px ${f.sans}`; ctx.fillStyle = "#a9a9ad"; ctx.textAlign = rtl ? "left" : "right";
    ctx.fillText(t("cardSource"), rtl ? M : W - M, H - (story ? 40 : 22));

    blob = await new Promise((res) => cv.toBlob(res, "image/png"));
    $("#shareCaption").value = caption(d, cs);
  }

  // Use our translated city name when the visitor is in one of the 17 cities.
  function localCity(me) {
    if (!me || !me.city) return "";
    const c = HH.CITIES.find((x) => x.name.en.toLowerCase() === me.city.toLowerCase());
    return c ? c.name[lang()] : me.city;
  }

  function caption(d, cs) {
    const me = HH.state.local;
    if (me && me.aqi != null && me.city) {
      return t("cardCaptionMe", { city: localCity(me), aqi: HH.nf(Math.round(me.aqi)), cigs: HH.nf(me.pm24 / 22, { maximumFractionDigits: 1 }),
        n: HH.nf(d.stats.spots), traffic: trafficCaption() }) + `\n${URL_}\n#HamariHawa #AirPollution #Smog`;
    }
    const worst = cs?.worst[0];
    return t("cardCaption", {
      n: HH.nf(d.stats.spots), pk: HH.nf(d.stats.pk), in: HH.nf(d.stats.in),
      city: worst ? worst.c.name[lang()] : "", aqi: worst ? HH.nf(Math.round(worst.a.us_aqi)) : "",
      traffic: trafficCaption(),
    }) + `\n${URL_}\n#HamariHawa #AirPollution #Smog`;
  }
  function trafficCaption() {
    const hot = trafficTop(no2 || null);
    return hot.length ? t("cardTrafficCap", { list: hot.map((h) => `${cityLabel(h[4])} ${HH.nf(h[2], { maximumFractionDigits: 1 })}×`).join(", ") }) : "";
  }

  // ---------- dialog ----------
  async function open() {
    const dlg = $("#shareDlg");
    if (!dlg.open) dlg.showModal();
    $("#shareBusy").hidden = false;
    try { await render(); } catch (e) { console.warn("[hh] card", e); }
    $("#shareBusy").hidden = true;
    const canFiles = !!(navigator.canShare && blob && navigator.canShare({ files: [new File([blob], "x.png", { type: "image/png" })] }));
    $("#cardShare").hidden = !canFiles;
    const txt = encodeURIComponent($("#shareCaption").value);
    $("#cardX").href = `https://twitter.com/intent/tweet?text=${txt}`;
    $("#cardFb").href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(URL_)}`;
    $("#cardWa").href = `https://wa.me/?text=${txt}`;
  }
  function fileName() { return `hamarihawa-${new Date().toISOString().slice(0, 10)}-${fmt}.png`; }

  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-share-card]");
    if (b) { e.preventDefault(); open(); }
  });
  $("#shareClose").addEventListener("click", () => $("#shareDlg").close());
  $("#shareDlg").addEventListener("click", (e) => { if (e.target.id === "shareDlg") $("#shareDlg").close(); });
  document.querySelectorAll("#cardFormats button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("#cardFormats button").forEach((x) => x.classList.toggle("on", x === b));
    fmt = b.dataset.f;
    open();
  }));
  $("#cardDownload").addEventListener("click", () => {
    if (!blob) return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = fileName();
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  });
  $("#cardShare").addEventListener("click", async () => {
    try {
      await navigator.share({ files: [new File([blob], fileName(), { type: "image/png" })], text: $("#shareCaption").value });
    } catch { /* cancelled */ }
  });
  $("#cardCopy").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText($("#shareCaption").value); $("#cardCopy").textContent = t("copied"); }
    catch { $("#shareCaption").select(); }
    setTimeout(() => { $("#cardCopy").textContent = t("copyCaption"); }, 2000);
  });
  window.addEventListener("hh:lang", () => { if ($("#shareDlg").open) open(); });
})();
