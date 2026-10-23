// Fire trends page: season lines, season totals, night share and a district bubble map, all drawn
// from the daily archive (/api/days, /api/districts). Charts render into the [data-chart]
// placeholders of whichever language's article is showing, and redraw on a language switch.
(() => {
  "use strict";
  const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const S = {
    en: {
      all: "All", pk: "Pakistan", in: "India",
      head: "So far this season (1 October to {d}), NASA's Suomi NPP satellite has seen {n} fire spots {where}. That is {vsLast} the same dates last year, and {vsAvg} the {y0}–{y1} average.",
      headShort: "So far this season (1 October to {d}), NASA's Suomi NPP satellite has seen {n} fire spots {where}.",
      where0: "across Pakistan and North India", where1: "in Pakistan", where2: "in India",
      more: "{p}% more than", less: "{p}% fewer than", same: "about the same as",
      axisSeason: "Fires a day, 7-day average (Suomi NPP)",
      soFar: "{y} so far", sameDates: "1 Oct to {d}", rest: "rest of the season", wholeSeason: "whole season",
      nightAxis: "Share of fires seen on the night pass (Suomi NPP)",
      play: "▶ Play", pause: "❚❚ Pause", slider: "Day of the season",
      bubbleDay: "{d}: {n} fire spots seen by all satellites", bubbleNone: "{d}: no fire spots recorded",
      tipDistrict: "{place}: {n} fire spots",
      err: "Couldn't load the archive. Please try again in a minute.",
    },
    ur: {
      all: "سب", pk: "پاکستان", in: "ہندوستان",
      head: "اس موسم میں اب تک (1 اکتوبر سے {d} تک) ناسا کے Suomi NPP سیٹلائٹ نے {where} {n} مقامات پر آگ دیکھی ہے۔ یہ تعداد پچھلے سال کی انہی تاریخوں {vsLast}، اور {y0} تا {y1} کی اوسط {vsAvg}۔",
      headShort: "اس موسم میں اب تک (1 اکتوبر سے {d} تک) ناسا کے Suomi NPP سیٹلائٹ نے {where} {n} مقامات پر آگ دیکھی ہے۔",
      where0: "پاکستان اور شمالی ہندوستان میں", where1: "پاکستان میں", where2: "ہندوستان میں",
      more: "سے {p}% زیادہ ہے", less: "سے {p}% کم ہے", same: "کے برابر ہے",
      axisSeason: "روزانہ آگ (7 دن کی اوسط، Suomi NPP)",
      soFar: "{y} (اب تک)", sameDates: "1 اکتوبر سے {d} تک", rest: "موسم کا باقی حصہ", wholeSeason: "پورا موسم",
      nightAxis: "رات والے چکر میں نظر آنے والی آگ کا حصہ (Suomi NPP)",
      play: "▶ چلائیں", pause: "❚❚ روکیں", slider: "موسم کا دن",
      bubbleDay: "{d}: تمام سیٹلائٹس نے {n} مقامات پر آگ دیکھی", bubbleNone: "{d}: کوئی آگ درج نہیں ہوئی",
      tipDistrict: "{place}: {n} مقامات پر آگ",
      err: "ریکارڈ لوڈ نہیں ہو سکا۔ ایک منٹ بعد دوبارہ کوشش کریں۔",
    },
    hi: {
      all: "सब", pk: "पाकिस्तान", in: "भारत",
      head: "इस मौसम में अब तक (1 अक्टूबर से {d} तक) नासा के Suomi NPP उपग्रह ने {where} {n} जगहों पर आग देखी है। यह संख्या पिछले साल की इन्हीं तारीख़ों {vsLast}, और {y0} से {y1} तक के औसत {vsAvg}।",
      headShort: "इस मौसम में अब तक (1 अक्टूबर से {d} तक) नासा के Suomi NPP उपग्रह ने {where} {n} जगहों पर आग देखी है।",
      where0: "पाकिस्तान और उत्तर भारत में", where1: "पाकिस्तान में", where2: "भारत में",
      more: "से {p}% ज़्यादा है", less: "से {p}% कम है", same: "के बराबर है",
      axisSeason: "रोज़ की आग (7 दिन का औसत, Suomi NPP)",
      soFar: "{y} (अब तक)", sameDates: "1 अक्टूबर से {d} तक", rest: "मौसम का बाक़ी हिस्सा", wholeSeason: "पूरा मौसम",
      nightAxis: "रात वाले चक्कर में दिखी आग का हिस्सा (Suomi NPP)",
      play: "▶ चलाएँ", pause: "❚❚ रोकें", slider: "मौसम का दिन",
      bubbleDay: "{d}: सभी उपग्रहों ने {n} जगहों पर आग देखी", bubbleNone: "{d}: कोई आग दर्ज नहीं हुई",
      tipDistrict: "{place}: {n} जगहों पर आग",
      err: "रिकॉर्ड लोड नहीं हो सका। एक मिनट बाद फिर कोशिश करें।",
    },
  };

  let lang = document.documentElement.lang in S ? document.documentElement.lang : "en";
  let cc = "";
  try { cc = localStorage.getItem("hh-trends-cc") || ""; } catch {}
  if (!["", "PK", "IN"].includes(cc)) cc = "";
  let days = null, model = null, dist = null, failed = false;

  const T = (k, v) => S[lang][k].replace(/\{(\w+)\}/g, (_, x) => (v && v[x] != null ? v[x] : ""));
  const nf = (n, o) => new Intl.NumberFormat(LOC[lang], o).format(n);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const here = (name) => document.querySelector(`article:not([hidden]) [data-chart="${name}"]`);
  const col = () => (cc === "PK" ? 1 : cc === "IN" ? 2 : 0);
  const NS = "http://www.w3.org/2000/svg";
  function el(tag, attrs, parent, text) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }

  // ---------- Season model: 61 days, 1 Oct (index 0) to 30 Nov (index 60) ----------
  const LEN = 61;
  const isoOf = (y, i) => (i < 31 ? `${y}-10-${String(i + 1).padStart(2, "0")}` : `${y}-11-${String(i - 30).padStart(2, "0")}`);
  const fmtDay = (y, i, withYear, month = "short") => new Intl.DateTimeFormat(LOC[lang], { day: "numeric", month, ...(withYear ? { year: "numeric" } : {}), timeZone: "UTC" })
    .format(Date.UTC(y, i < 31 ? 9 : 10, i < 31 ? i + 1 : i - 30));
  // Suomi NPP count for the chosen country. Days archived before the split existed only have the total.
  function val(e) {
    if (!e || e.partial) return null;
    // Suomi NPP returned no usable data (NASA's 2-6 Nov 2024 outage, dropped passes) when it saw almost
    // nothing on a day the other satellites saw plenty: missing, not zero.
    if (e.sn && e.sn[0] < 20 && e.spots >= 200 && e.sn[0] * 20 < e.spots) return null;
    // snc: the northern box every season covers (days since the region grew); older days only cover it.
    if (e.sn) return (e.snc || e.sn)[col()];
    return col() === 0 && e.snpp != null ? e.snpp : null;
  }
  function nightShare(entries) {
    let n = 0, night = 0;
    for (const e of entries) if (e && !e.partial && e.sn) { const c = e.snc || e.sn; n += c[col()]; night += c[3 + col()]; }
    return n ? night / n : null;
  }
  function build() {
    const years = [...new Set(Object.keys(days).filter((d) => /-1[01]-/.test(d)).map((d) => +d.slice(0, 4)))].sort();
    const series = {}, entries = {};
    for (const y of years) {
      entries[y] = Array.from({ length: LEN }, (_, i) => days[isoOf(y, i)]);
      series[y] = entries[y].map(val);
    }
    const cur = years[years.length - 1];
    let cutoff = -1;
    series[cur].forEach((v, i) => { if (v != null) cutoff = i; });
    const sum = (y, upto) => series[y].slice(0, upto + 1).reduce((a, v) => a + (v || 0), 0);
    model = { years, series, entries, cur, cutoff, sum };
  }

  // ---------- Headline ----------
  function cmp(a, b) {
    if (!b) return null;
    const p = Math.round(((a - b) / b) * 100);
    return Math.abs(p) < 5 ? T("same") : T(p > 0 ? "more" : "less", { p: nf(Math.abs(p)) });
  }
  function renderHeadline() {
    const box = here("headline");
    if (!box) return;
    if (failed) { box.textContent = T("err"); return; }
    if (!model) return;
    const { years, cur, cutoff, sum } = model;
    if (cutoff < 0) { box.textContent = ""; return; }
    const n = sum(cur, cutoff), past = years.filter((y) => y < cur);
    const last = past.includes(cur - 1) ? sum(cur - 1, cutoff) : 0;
    const avg = past.length ? past.reduce((a, y) => a + sum(y, cutoff), 0) / past.length : 0;
    const v = { d: fmtDay(cur, cutoff, false, "long"), n: nf(n), where: T("where" + col()), y0: past[0], y1: past[past.length - 1] };
    box.textContent = last && avg ? T("head", { ...v, vsLast: cmp(n, last), vsAvg: cmp(n, avg) }) : T("headShort", v);
  }

  // ---------- Country filter ----------
  function renderFilter() {
    const box = here("filter");
    if (!box) return;
    box.className = "chips tfilter";
    box.innerHTML = ["", "PK", "IN"].map((c) => `<button data-cc="${c}" class="${c === cc ? "on" : ""}">${esc(T(c === "PK" ? "pk" : c === "IN" ? "in" : "all"))}</button>`).join("");
    box.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
      cc = b.dataset.cc;
      try { localStorage.setItem("hh-trends-cc", cc); } catch {}
      build();
      renderAll();
    }));
  }

  // ---------- Chart helpers ----------
  // Axis: about four round steps that just clear the highest value.
  function axis(v) {
    v = v > 0 ? v : 1;
    const raw = v / 4, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
    const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p;
    return { max: step * Math.ceil(v / step - 1e-9), step };
  }
  function grid(svg, a, y, m, W, fmt) {
    for (let v = 0; v <= a.max + a.step / 2; v += a.step) {
      el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: "grid" }, svg);
      el("text", { x: m.l - 6, y: y(v) + 4, class: "tick", "text-anchor": "end" }, svg, fmt(v));
    }
  }
  // Charts are drawn at the width they're shown at, so labels stay readable on a phone.
  const width = (box) => Math.round(Math.max(300, Math.min(940, box.clientWidth || 760)));
  const narrow = (W) => W < 560;
  function frame(box, W, H) {
    box.innerHTML = "";
    box.className = "tchart";
    box.setAttribute("dir", "ltr");
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" }, box);
    return svg;
  }
  const yearColour = (y) => (y === model.cur ? "var(--fire)" : y === model.cur - 1 ? "var(--ink-2)" : "#c4bfb4");

  // ---------- Season lines ----------
  function renderSeason() {
    const box = here("season");
    if (!box || !model) return;
    const { years, series, cur } = model;
    const W = width(box), H = narrow(W) ? 250 : 320, m = { l: 42, r: narrow(W) ? 30 : 58, t: 16, b: 30 };
    const svg = frame(box, W, H);
    svg.setAttribute("aria-label", T("axisSeason"));
    // Trailing 7-day average, so this season's line doesn't lean on days that haven't happened.
    const smooth = {};
    for (const y of years) {
      smooth[y] = series[y].map((_, i) => {
        const w = series[y].slice(Math.max(0, i - 6), i + 1).filter((v) => v != null);
        return w.length >= Math.min(4, i + 1) && series[y][i] != null ? w.reduce((a, b) => a + b, 0) / w.length : null;
      });
    }
    const ax = axis(Math.max(1, ...years.flatMap((y) => smooth[y].filter((v) => v != null))));
    const x = (i) => m.l + (i / (LEN - 1)) * (W - m.l - m.r), y = (v) => H - m.b - (v / ax.max) * (H - m.t - m.b);
    grid(svg, ax, y, m, W, (v) => nf(v));
    for (const i of narrow(W) ? [0, 31, 60] : [0, 14, 31, 45, 60]) el("text", { x: x(i), y: H - 8, class: "tick", "text-anchor": "middle" }, svg, fmtDay(cur, i));
    el("text", { x: m.l, y: 10, class: "axis" }, svg, T("axisSeason"));
    const labels = [];
    for (const yr of years) {
      let d = "", pen = false, lastI = -1;
      smooth[yr].forEach((v, i) => {
        if (v == null) { pen = false; return; }
        d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
        pen = true; lastI = i;
      });
      if (!d) continue;
      el("path", { d, fill: "none", stroke: yearColour(yr), "stroke-width": yr === cur ? 3 : yr === cur - 1 ? 1.8 : 1.3, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
      // Past years are labelled at their peak, where the lines sit furthest apart; this year at its latest day.
      let at = lastI;
      if (yr !== cur) smooth[yr].forEach((v, i) => { if (v != null && v > smooth[yr][at]) at = i; });
      labels.push({ yr, lx: x(at), ly: y(smooth[yr][at]) - 6, end: yr === cur });
    }
    // Nudge labels up until none overlap (each about 30 x 12 px).
    const placed = [];
    for (const l of labels.sort((a, b) => b.ly - a.ly)) {
      if (l.end) l.lx += 18;
      while (placed.some((q) => Math.abs(q.lx - l.lx) < 32 && Math.abs(q.ly - l.ly) < 12)) l.ly -= 12;
      l.ly = Math.max(m.t + 10, l.ly);
      placed.push(l);
    }
    for (const l of labels) el("text", { x: Math.min(l.lx, W - m.r + 20), y: l.ly, class: "ylabel", fill: yearColour(l.yr), "text-anchor": "middle", "font-weight": l.yr === cur ? 700 : 400 }, svg, String(l.yr));

    // Hover or touch: a guide line and every year's value on that date.
    const guide = el("line", { y1: m.t, y2: H - m.b, class: "guide", visibility: "hidden" }, svg);
    const tip = document.createElement("div");
    tip.className = "ttip"; tip.hidden = true; box.appendChild(tip);
    const hit = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "transparent" }, svg);
    const move = (ev) => {
      const r = svg.getBoundingClientRect(), px = ((ev.clientX - r.left) / r.width) * W;
      const i = Math.max(0, Math.min(LEN - 1, Math.round(((px - m.l) / (W - m.l - m.r)) * (LEN - 1))));
      guide.setAttribute("x1", x(i)); guide.setAttribute("x2", x(i)); guide.setAttribute("visibility", "visible");
      const rows = years.slice().reverse().filter((yr) => smooth[yr][i] != null)
        .map((yr) => `<div${yr === cur ? ' class="cur"' : ""}><span>${yr}</span><b>${nf(Math.round(smooth[yr][i]))}</b></div>`).join("");
      tip.innerHTML = `<div class="td">${esc(fmtDay(cur, i))}</div>${rows}`;
      tip.hidden = false;
      const left = (x(i) / W) * r.width;
      tip.style.left = `${left > r.width / 2 ? left - tip.offsetWidth - 12 : left + 12}px`;
    };
    hit.addEventListener("pointermove", move);
    hit.addEventListener("pointerdown", move);
    hit.addEventListener("pointerleave", () => { tip.hidden = true; guide.setAttribute("visibility", "hidden"); });
  }

  // ---------- Season totals ----------
  function renderTotals() {
    const box = here("totals");
    if (!box || !model) return;
    const { years, cur, cutoff, sum } = model;
    const W = width(box), H = narrow(W) ? 230 : 270, m = { l: 42, r: 8, t: 30, b: 34 };
    const svg = frame(box, W, H);
    const full = (yr) => sum(yr, LEN - 1), same = (yr) => sum(yr, Math.max(0, cutoff));
    const ax = axis(Math.max(1, ...years.map(full)));
    const band = (W - m.l - m.r) / years.length, bw = Math.min(56, band * 0.58);
    const y = (v) => H - m.b - (v / ax.max) * (H - m.t - m.b);
    grid(svg, ax, y, m, W, (v) => nf(v, { notation: "compact" }));
    years.forEach((yr, k) => {
      const cx = m.l + band * k + band / 2, f = full(yr), s = same(yr), isCur = yr === cur;
      if (!isCur) el("rect", { x: cx - bw / 2, y: y(f), width: bw, height: Math.max(0, y(0) - y(f)), class: "bar-rest" }, svg);
      el("rect", { x: cx - bw / 2, y: y(s), width: bw, height: Math.max(0, y(0) - y(s)), class: isCur ? "bar-cur" : "bar-same" }, svg);
      el("text", { x: cx, y: y(isCur ? s : f) - 6, class: "val", "text-anchor": "middle" }, svg, nf(isCur ? s : f, { notation: "compact" }));
      el("text", { x: cx, y: H - 12, class: "tick", "text-anchor": "middle", "font-weight": isCur ? 700 : 400 }, svg, isCur && !narrow(W) ? T("soFar", { y: yr }) : String(yr));
    });
    const key = document.createElement("p");
    key.className = "tkey";
    key.innerHTML = `<i class="k-same"></i>${esc(T("sameDates", { d: fmtDay(cur, Math.max(0, cutoff)) }))} <i class="k-rest"></i>${esc(T("rest"))} <i class="k-cur"></i>${esc(T("soFar", { y: cur }))}`;
    box.appendChild(key);
  }

  // ---------- Night share ----------
  function renderNight() {
    const box = here("night");
    if (!box || !model) return;
    const { years, entries, cur, cutoff } = model;
    const W = width(box), H = narrow(W) ? 200 : 230, m = { l: 42, r: 8, t: 30, b: 34 };
    const svg = frame(box, W, H);
    // Early October has fewer daytime fires, so a part-season share isn't comparable with a whole one:
    // each past year also gets a dot for the same dates as this season so far.
    const done = cutoff >= LEN - 1;
    const share = years.map((yr) => nightShare(entries[yr]));
    const same = years.map((yr) => nightShare(entries[yr].slice(0, Math.max(0, cutoff) + 1)));
    // An archive copy from before the night split existed has nothing to draw; say so instead of an empty chart.
    if (!share.concat(same).some((v) => v != null)) { box.innerHTML = `<p class="tkey">${esc(T("err"))}</p>`; return; }
    const ax = axis(Math.max(0.05, ...share.concat(same).filter((v) => v != null)));
    const band = (W - m.l - m.r) / years.length, bw = Math.min(56, band * 0.58);
    const y = (v) => H - m.b - (v / ax.max) * (H - m.t - m.b);
    el("text", { x: m.l, y: 12, class: "axis" }, svg, T("nightAxis"));
    grid(svg, ax, y, m, W, (v) => nf(v, { style: "percent" }));
    const pct = (v) => nf(v, { style: "percent", maximumFractionDigits: 1 });
    years.forEach((yr, k) => {
      const isCur = yr === cur, v = isCur ? same[k] : share[k];
      if (v == null) return;
      const cx = m.l + band * k + band / 2;
      el("rect", { x: cx - bw / 2, y: y(v), width: bw, height: Math.max(0, y(0) - y(v)), class: isCur ? "bar-cur" : "bar-night" }, svg);
      if (!isCur && !done && same[k] != null) {
        const dot = el("circle", { cx, cy: y(same[k]), r: 5, class: "dot-same" }, svg);
        el("title", {}, dot, `${T("sameDates", { d: fmtDay(cur, cutoff) })}: ${pct(same[k])}`);
      }
      const top = Math.min(y(v), !isCur && !done && same[k] != null ? y(same[k]) - 6 : y(v));
      el("text", { x: cx, y: top - 6, class: "val", "text-anchor": "middle" }, svg, pct(v));
      el("text", { x: cx, y: H - 12, class: "tick", "text-anchor": "middle", "font-weight": isCur ? 700 : 400 }, svg, isCur && !narrow(W) ? T("soFar", { y: yr }) : String(yr));
    });
    if (!done) {
      const key = document.createElement("p");
      key.className = "tkey";
      key.innerHTML = `<i class="k-night"></i>${esc(T("wholeSeason"))} <i class="k-dot"></i>${esc(T("sameDates", { d: fmtDay(cur, cutoff) }))} <i class="k-cur"></i>${esc(T("soFar", { y: cur }))}`;
      box.appendChild(key);
    }
  }

  // ---------- District bubbles ----------
  // One map node, moved into whichever language's placeholder is showing.
  const bubble = { node: null, map: null, layer: null, year: null, i: 0, timer: 0 };
  function bubbleMax(yr) {
    let last = -1;
    for (let i = 0; i < LEN; i++) if (dist?.[isoOf(yr, i)] && !days[isoOf(yr, i)]?.partial) last = i;
    return last;
  }
  function drawBubbles() {
    const b = bubble;
    if (!b.map || !dist) return;
    b.layer.clearLayers();
    const rows = (dist[isoOf(b.year, b.i)] || []).filter((r) => !cc || r[2] === cc);
    let total = 0;
    for (const [d, st, c, n, lat, lon] of rows) {
      total += n;
      const place = [d, st].filter((v, k, a) => v && a.indexOf(v) === k).join(", ");
      L.circleMarker([lat, lon], { radius: Math.min(34, Math.max(3, Math.sqrt(n) * 1.15)), color: "#a3170d", weight: 0.8, fillColor: "#d62d20", fillOpacity: 0.42 })
        .bindTooltip(esc(T("tipDistrict", { place, n: nf(n) })), { direction: "top" })
        .addTo(b.layer);
    }
    const day = fmtDay(b.year, b.i, true);
    b.node.querySelector(".bdate").textContent = total ? T("bubbleDay", { d: day, n: nf(total) }) : T("bubbleNone", { d: day });
    const range = b.node.querySelector("input[type=range]");
    range.value = b.i;
  }
  function stopPlay() {
    clearInterval(bubble.timer); bubble.timer = 0;
    const btn = bubble.node?.querySelector(".bplay");
    if (btn) btn.textContent = T("play");
  }
  function renderBubbleControls() {
    const b = bubble, years = model.years.filter((yr) => bubbleMax(yr) >= 0);
    if (!years.length) { b.node.querySelector(".bctl").textContent = T("err"); return; }
    if (!years.includes(b.year)) b.year = years[years.length - 1];
    const max = bubbleMax(b.year);
    b.i = Math.min(b.i, max);
    const ctl = b.node.querySelector(".bctl");
    ctl.innerHTML = `<div class="chips">${years.map((yr) => `<button data-y="${yr}" class="${yr === b.year ? "on" : ""}">${yr}</button>`).join("")}</div>
      <div class="brow"><button class="bplay">${esc(b.timer ? T("pause") : T("play"))}</button>
      <input type="range" min="0" max="${max}" value="${b.i}" aria-label="${esc(T("slider"))}"></div>
      <p class="bdate" aria-live="polite"></p>`;
    ctl.querySelectorAll("[data-y]").forEach((btn) => btn.addEventListener("click", () => {
      stopPlay();
      b.year = +btn.dataset.y;
      b.i = bubbleMax(b.year);
      renderBubbleControls();
    }));
    ctl.querySelector("input").addEventListener("input", (e) => { stopPlay(); b.i = +e.target.value; drawBubbles(); });
    ctl.querySelector(".bplay").addEventListener("click", (e) => {
      if (b.timer) { stopPlay(); return; }
      if (b.i >= bubbleMax(b.year)) b.i = 0;
      e.target.textContent = T("pause");
      b.timer = setInterval(() => {
        if (b.i >= bubbleMax(b.year)) { stopPlay(); return; }
        b.i++; drawBubbles();
      }, 320);
    });
    drawBubbles();
  }
  function renderBubbles() {
    const box = here("bubbles");
    if (!box || !model) return;
    const b = bubble;
    if (!b.node) {
      b.node = document.createElement("div");
      b.node.className = "tbubbles";
      b.node.setAttribute("dir", "ltr");
      b.node.innerHTML = '<div class="bctl"></div><div class="bmap sketch"></div>';
      // Load the district file only when the map scrolls near.
      new IntersectionObserver((ents, io) => {
        if (!ents.some((e) => e.isIntersecting)) return;
        io.disconnect();
        // Tagged with the archive's latest day, so a browser never keeps a copy older than the index it just read.
        const last = Object.keys(days).sort().pop();
        fetch(`/api/districts?v=${last}-${days[last]?.spots ?? 0}`).then((r) => (r.ok ? r.json() : null)).catch(() => null).then((d) => {
          // An empty answer means the district file isn't there; say so rather than show a dead slider.
          if (!d || !Object.keys(d).length) { b.node.querySelector(".bctl").textContent = T("err"); return; }
          dist = d;
          b.year = model.cur;
          b.i = bubbleMax(b.year);
          renderBubbleControls();
        });
      }, { rootMargin: "300px" }).observe(b.node);
    }
    box.appendChild(b.node);
    if (!b.map) {
      b.map = L.map(b.node.querySelector(".bmap"), { zoomSnap: 0.25, scrollWheelZoom: false, attributionControl: true });
      const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{style}/MapServer/tile/{z}/{y}/{x}";
      L.tileLayer(ESRI, { style: "World_Light_Gray_Base", attribution: "Base map © Esri, HERE, Garmin, © OpenStreetMap contributors", maxNativeZoom: 16 }).addTo(b.map);
      b.map.createPane("labels").style.zIndex = 450;
      b.map.getPane("labels").style.pointerEvents = "none";
      L.tileLayer(ESRI, { style: "World_Light_Gray_Reference", pane: "labels", maxNativeZoom: 16 }).addTo(b.map);
      b.layer = L.layerGroup().addTo(b.map);
      b.map.fitBounds([[28.6, 70.2], [32.6, 78.6]]);
    } else {
      b.map.invalidateSize();
    }
    if (dist) renderBubbleControls();
  }

  function renderAll() {
    renderFilter();
    renderHeadline();
    if (!model) return;
    renderSeason();
    renderTotals();
    renderNight();
    renderBubbles();
  }

  addEventListener("hh:lang", (e) => { lang = e.detail in S ? e.detail : "en"; stopPlay(); renderAll(); });
  let resizeT = 0;
  let lastW = 0;
  addEventListener("resize", () => {
    clearTimeout(resizeT);
    resizeT = setTimeout(() => {
      bubble.map?.invalidateSize();
      const w = here("season")?.clientWidth || 0;
      if (model && Math.abs(w - lastW) > 20) { lastW = w; renderSeason(); renderTotals(); renderNight(); }
    }, 150);
  });
  renderFilter();
  // Always check with the server (it answers from Cloudflare's cache), so a stale browser copy can't break the charts.
  fetch("/api/days", { cache: "no-cache" }).then((r) => (r.ok ? r.json() : null)).catch(() => null).then((d) => {
    if (!d || !Object.keys(d).length) { failed = true; renderHeadline(); return; }
    days = d;
    build();
    renderAll();
  });
})();
