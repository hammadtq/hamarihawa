// "Breathe again" on a city page (/air/<city>/; markup in site/src/citypage.js): when the air should next get
// lighter, for the next 10 days. Smog cities rarely reach safe air, but rain, strong wind and a deep, breezy
// afternoon mixing layer give them a day or two of lighter smoke; this finds the next such break. "Smoke" in the wording is the whole of CAMS's PM2.5
// (fires, traffic, industry, kilns, dust), so it keeps working after the burning season, all winter.
//
// Two sources, both requested from the visitor's browser (the Worker never calls Open-Meteo):
// - Smoke: the Copernicus CAMS PM2.5 forecast (about 4 days ahead). CAMS reads low in winter, so a day is
//   compared with CAMS's own mean of the past 7 days, never with a safe limit: a "break" is a day forecast at
//   30% or more below that mean.
// - Weather, out to day 9: rain and wind from three models (ECMWF IFS, GFS, ICON), so the page can say how
//   many agree, and the afternoon ventilation (mixing-layer height x wind speed, GFS, the only one of the
//   three that serves the mixing layer). Past the smoke forecast's horizon, a day is a possible break when a
//   majority of models bring 2 mm of rain or more, the wind passes 20 km/h, or the ventilation is at least
//   6,000 m²/s and 1.5 times the city's own past week; it is still air below 2,000 m²/s (and 0.6 times).
//   Ventilation tracked the CAMS breaks in Lahore and Delhi in November 2026 (about 9,500 on break days,
//   1,000-2,000 on the days smoke built up).
// - Dust: strong dry wind does not always clear the air. Over Nov 2025-Oct 2026 in eight cities, when CAMS
//   dust had averaged 80 µg/m³ or more over the past week, windy dry days had a median PM2.5 1.17 times the
//   past week (dust storms: Lahore and Multan in May-June, Delhi and Jaipur March-August, Quetta most of the
//   year); below that, 0.85 times (Karachi's sea breeze, winter everywhere). So in a dusty week strong wind
//   counts as dust raised, not as a break.
// The share button draws the same answer as a square picture (canvas) for WhatsApp and status posts.
(() => {
  const els = [...document.querySelectorAll("[data-breathe]")];
  if (!els.length) return;
  const { lat, lon } = els[0].dataset;
  const MODELS = ["ecmwf_ifs025", "gfs_seamless", "icon_seamless"];
  const DAYS = 10;
  const aqUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&hourly=pm2_5,dust&past_days=7&forecast_days=6&timezone=auto`;
  const wxUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=precipitation_sum,wind_speed_10m_max` +
    `&hourly=boundary_layer_height,wind_speed_10m&models=${MODELS.join(",")}&past_days=7&forecast_days=${DAYS + 1}&timezone=auto`;
  const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const GREEN = "#2f8f46", GREEN_SOFT = "#e3f2e1";

  const T = {
    en: {
      wait: "Reading the weather models…", fail: "The forecast could not be loaded just now.",
      now: "Today", tomorrow: "Tomorrow", inDays: (d) => `In ${d} days`, maybe: (d) => (d === 1 ? "Maybe tomorrow" : `Maybe in ${d} days`), none: "Not in the next 10 days", light: "Already light",
      today: "Today", tmw: "Tomorrow", and: (a, b) => `${a} and ${b.replace(/^Tomorrow/, "tomorrow")}`, to: (a, b) => `${a} to ${b.replace(/^Tomorrow/, "tomorrow")}`,
      less: (p) => `about ${p}% less smoke than the past 7 days`, half: "about half the smoke of the past 7 days",
      spanLess: (s, x) => `${s}: ${x}.`, spanMaybe: (s) => `${s} could bring lighter air.`,
      why: { rain: (m, n, mm) => `Rain in ${m} of ${n} weather models, about ${mm} mm.`, wind: (k) => `Wind up to ${k} km/h.`, mix: "Breezy afternoons lift and spread the smoke.", none: "The smoke model expects it; the weather shows no single clear cause." },
      back: (d) => `Smoke starts building up again from ${d}.`, still: (d) => `Still air from ${d} may trap smoke near the ground.`,
      maybeNote: "This is past the smoke forecast's 4 days, so it comes from the weather alone and is less certain.",
      noneWhy: "No weather model shows rain or strong wind for the next 10 days.", lighterOnly: (d) => `${d} should be a little lighter, but not a real break.`, noneStill: (d) => `Still air from ${d} may trap smoke near the ground.`,
      lightTxt: (N) => `The smoke model has kept ${N}'s air fairly light this past week.`,
      legend: { brk: "break", lighter: "a little lighter", same: "about the same", worse: "smokier", base: "past 7 days" },
      airLbl: "Smoke forecast", wxLbl: "Weather only",
      outlook: (parts) => `After that, from the weather alone: ${parts.join("; ")}.`, outlook0: (parts) => `Past the smoke forecast, from the weather alone: ${parts.join("; ")}.`, later: (list) => `Another possible break: ${list}.`,
      ol: { dust: (s) => `${s}, strong dry wind may raise dust`, build: (s) => `${s}, still air, so smoke likely builds up`, flat: (s) => `${s}, about the same`, maybe: (s, c) => `${s}, ${c} may bring lighter air` },
      olCause: { rain: "rain", wind: "strong wind", mix: "breezy afternoons" }, olKey: "outlook from the weather",
      icon: { rain: "rain", wind: "strong wind", mix: "breezy, well mixed", still: "still air", dust: "dusty wind" },
      share: "Share picture", wa: "WhatsApp", copy: "Copy link", copied: "Link copied", saved: "Picture saved",
      q: (N) => `When can ${N} breathe again?`,
      src: "Smoke: Copernicus CAMS model via Open-Meteo, compared with its own past 7 days (it reads low in winter, so this shows the change, not the level). Weather: ECMWF, GFS and ICON models via Open-Meteo; mixing layer from GFS.",
      imgSrc: "Smoke: CAMS forecast vs its past 7 days. Weather: ECMWF, GFS, ICON.",
    },
    ur: {
      wait: "موسمی ماڈل دیکھے جا رہے ہیں…", fail: "پیش گوئی اس وقت نہیں مل سکی۔",
      now: "آج", tomorrow: "کل", inDays: (d) => `${d} دن میں`, maybe: (d) => (d === 1 ? "شاید کل" : `شاید ${d} دن میں`), none: "اگلے 10 دن میں نہیں", light: "ہوا پہلے ہی ہلکی",
      today: "آج", tmw: "کل", and: (a, b) => `${a} اور ${b}`, to: (a, b) => `${a} سے ${b} تک`,
      less: (p) => `پچھلے 7 دنوں سے لگ بھگ ${p} فیصد کم دھواں`, half: "پچھلے 7 دنوں کے مقابلے میں لگ بھگ آدھا دھواں",
      spanLess: (s, x) => `${s}: ${x}۔`, spanMaybe: (s) => `${s} کو ہوا کچھ ہلکی ہو سکتی ہے۔`,
      why: { rain: (m, n, mm) => `${n} میں سے ${m} موسمی ماڈل بارش دکھا رہے ہیں، لگ بھگ ${mm} ملی میٹر۔`, wind: (k) => `ہوا ${k} کلومیٹر فی گھنٹہ تک چلے گی۔`, mix: "دوپہر کی ہوا دھوئیں کو اوپر اٹھا کر بکھیر دے گی۔", none: "دھوئیں کا ماڈل یہی بتاتا ہے، اگرچہ موسم میں کوئی ایک واضح وجہ نظر نہیں آتی۔" },
      back: (d) => `${d} سے دھواں پھر بڑھنے لگے گا۔`, still: (d) => `${d} سے تھمی ہوا دھوئیں کو زمین کے قریب روک سکتی ہے۔`,
      maybeNote: "یہ دھوئیں کی 4 دن کی پیش گوئی سے آگے ہے، اس لیے صرف موسم کی بنیاد پر ہے اور اتنا یقینی نہیں۔",
      noneWhy: "اگلے 10 دنوں میں کسی موسمی ماڈل میں نہ بارش ہے نہ تیز ہوا۔", lighterOnly: (d) => `${d} ہوا کچھ ہلکی رہے گی، مگر کوئی خاص مہلت نہیں۔`, noneStill: (d) => `${d} سے تھمی ہوا دھوئیں کو زمین کے قریب روک سکتی ہے۔`,
      lightTxt: (N) => `دھوئیں کے ماڈل کے مطابق پچھلے ہفتے ${N} کی ہوا کافی ہلکی رہی ہے۔`,
      legend: { brk: "مہلت", lighter: "کچھ ہلکی", same: "تقریباً ویسی ہی", worse: "زیادہ دھواں", base: "پچھلے 7 دن" },
      airLbl: "دھوئیں کی پیش گوئی", wxLbl: "صرف موسم",
      outlook: (parts) => `اس کے بعد، صرف موسم کی بنیاد پر: ${parts.join("؛ ")}۔`, outlook0: (parts) => `دھوئیں کی پیش گوئی سے آگے، صرف موسم کی بنیاد پر: ${parts.join("؛ ")}۔`, later: (list) => `ایک اور ممکنہ مہلت: ${list}۔`,
      ol: { dust: (s) => `${s} تیز خشک ہوا سے گرد اڑنے کا امکان`, build: (s) => `${s} تھمی ہوا، دھواں بڑھنے کا امکان`, flat: (s) => `${s} تقریباً ویسا ہی`, maybe: (s, c) => `${s} ${c} سے ہوا کچھ ہلکی ہو سکتی ہے` },
      olCause: { rain: "بارش", wind: "تیز ہوا", mix: "ہوا دار دوپہر" }, olKey: "موسم کی بنیاد پر اندازہ",
      icon: { rain: "بارش", wind: "تیز ہوا", mix: "ہوا دار دوپہر", still: "تھمی ہوا", dust: "گرد آلود ہوا" },
      share: "تصویر شیئر کریں", wa: "واٹس ایپ", copy: "لنک کاپی کریں", copied: "لنک کاپی ہو گیا", saved: "تصویر محفوظ ہو گئی",
      q: (N) => `${N} میں سکھ کا سانس کب ملے گا؟`,
      src: "دھواں: کوپرنیکس CAMS ماڈل، اوپن میٹیو کے ذریعے، اپنے ہی پچھلے 7 دنوں سے موازنہ (سردیوں میں یہ کم بتاتا ہے، اس لیے یہاں سطح نہیں، تبدیلی دکھائی گئی ہے)۔ موسم: ECMWF، GFS اور ICON ماڈل، اوپن میٹیو کے ذریعے؛ ہوا کی ملاوٹ کی تہہ GFS سے۔",
      imgSrc: "دھواں: CAMS پیش گوئی، پچھلے 7 دنوں کے مقابلے میں۔ موسم: ECMWF، GFS، ICON۔",
    },
    hi: {
      wait: "मौसम के मॉडल पढ़े जा रहे हैं…", fail: "अनुमान अभी नहीं मिल सका।",
      now: "आज", tomorrow: "कल", inDays: (d) => `${d} दिन में`, maybe: (d) => (d === 1 ? "शायद कल" : `शायद ${d} दिन में`), none: "अगले 10 दिन में नहीं", light: "हवा पहले से हल्की",
      today: "आज", tmw: "कल", and: (a, b) => `${a} और ${b}`, to: (a, b) => `${a} से ${b} तक`,
      less: (p) => `पिछले 7 दिनों से लगभग ${p}% कम धुआँ`, half: "पिछले 7 दिनों के मुक़ाबले लगभग आधा धुआँ",
      spanLess: (s, x) => `${s}: ${x}।`, spanMaybe: (s) => `${s} को हवा कुछ हल्की हो सकती है।`,
      why: { rain: (m, n, mm) => `${n} में से ${m} मौसम मॉडल बारिश दिखा रहे हैं, लगभग ${mm} मिमी।`, wind: (k) => `हवा ${k} किमी/घंटा तक चलेगी।`, mix: "दोपहर की हवा धुएँ को ऊपर उठाकर बिखेर देगी।", none: "धुएँ का मॉडल यही बताता है, हालाँकि मौसम में कोई एक साफ़ वजह नहीं दिखती।" },
      back: (d) => `${d} से धुआँ फिर बढ़ने लगेगा।`, still: (d) => `${d} से थमी हवा धुएँ को ज़मीन के पास रोक सकती है।`,
      maybeNote: "यह धुएँ के 4 दिन के अनुमान से आगे है, इसलिए सिर्फ़ मौसम पर आधारित है और उतना पक्का नहीं।",
      noneWhy: "अगले 10 दिनों में किसी मौसम मॉडल में न बारिश है न तेज़ हवा।", lighterOnly: (d) => `${d} हवा कुछ हल्की रहेगी, पर कोई ख़ास राहत नहीं।`, noneStill: (d) => `${d} से थमी हवा धुएँ को ज़मीन के पास रोक सकती है।`,
      lightTxt: (N) => `धुएँ के मॉडल के मुताबिक़ पिछले हफ़्ते ${N} की हवा काफ़ी हल्की रही है।`,
      legend: { brk: "राहत", lighter: "कुछ हल्की", same: "लगभग वैसी ही", worse: "ज़्यादा धुआँ", base: "पिछले 7 दिन" },
      airLbl: "धुएँ का अनुमान", wxLbl: "सिर्फ़ मौसम",
      outlook: (parts) => `उसके बाद, सिर्फ़ मौसम के आधार पर: ${parts.join("; ")}।`, outlook0: (parts) => `धुएँ के अनुमान से आगे, सिर्फ़ मौसम के आधार पर: ${parts.join("; ")}।`, later: (list) => `एक और संभावित राहत: ${list}।`,
      ol: { dust: (s) => `${s} तेज़ सूखी हवा से धूल उड़ने की आशंका`, build: (s) => `${s} थमी हवा, धुआँ बढ़ने की आशंका`, flat: (s) => `${s} लगभग वैसा ही`, maybe: (s, c) => `${s} ${c} से हवा कुछ हल्की हो सकती है` },
      olCause: { rain: "बारिश", wind: "तेज़ हवा", mix: "हवादार दोपहर" }, olKey: "मौसम के आधार पर अंदाज़ा",
      icon: { rain: "बारिश", wind: "तेज़ हवा", mix: "हवादार दोपहर", still: "थमी हवा", dust: "धूल भरी हवा" },
      share: "तस्वीर शेयर करें", wa: "व्हाट्सऐप", copy: "लिंक कॉपी करें", copied: "लिंक कॉपी हो गया", saved: "तस्वीर सेव हो गई",
      q: (N) => `${N} में चैन की साँस कब मिलेगी?`,
      src: "धुआँ: कोपरनिकस CAMS मॉडल, ओपन-मेटियो से, अपने ही पिछले 7 दिनों से तुलना (सर्दियों में यह कम बताता है, इसलिए यहाँ स्तर नहीं, बदलाव दिखाया गया है)। मौसम: ECMWF, GFS और ICON मॉडल, ओपन-मेटियो से; मिक्सिंग लेयर GFS से।",
      imgSrc: "धुआँ: CAMS अनुमान, पिछले 7 दिनों के मुक़ाबले। मौसम: ECMWF, GFS, ICON।",
    },
  };

  const ICON = {
    rain: '<path d="M8 1.5C6 5 3.8 7.4 3.8 10a4.2 4.2 0 0 0 8.4 0C12.2 7.4 10 5 8 1.5z" fill="#3b82c4"/>',
    wind: '<g fill="none" stroke="#2f6f9f" stroke-width="1.6" stroke-linecap="round"><path d="M1.5 6h9a2.2 2.2 0 1 0-2.2-2.2"/><path d="M1.5 10.5h11a2 2 0 1 1-2 2"/></g>',
    mix: '<g fill="none" stroke="#2f8f46" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14V5M1.8 7.2 4 5l2.2 2.2"/><path d="M11 14V3M8.8 5.2 11 3l2.2 2.2"/></g>',
    still: '<g fill="none" stroke="#9a8f80" stroke-width="1.8" stroke-linecap="round"><path d="M2 5h12M3.5 8.5h9M2 12h12"/></g>',
    dust: '<g fill="#b07a3a"><path d="M1.5 5.5h7a2 2 0 1 0-2-2" fill="none" stroke="#b07a3a" stroke-width="1.6" stroke-linecap="round"/><circle cx="3" cy="10" r="1.2"/><circle cx="7" cy="12" r="1.2"/><circle cx="11" cy="9.5" r="1.2"/><circle cx="13.5" cy="13" r="1"/><circle cx="5" cy="14.5" r="0.9"/></g>',
  };
  const svg = (k, s = 15) => `<svg viewBox="0 0 16 16" width="${s}" height="${s}" aria-hidden="true">${ICON[k]}</svg>`;
  const COLOR = { brk: GREEN, lighter: "#8cc084", same: "#c9a86a", worse: "#d0594c", maybe: GREEN, flat: "#c9a86a", build: "#d0594c" };
  // Weather-only days are drawn at three fixed heights (an outlook, not a number): lighter, about the same, building.
  const WXH = { maybe: 0.7, flat: 1, build: 1.3 };
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const mean = (v) => (v.length ? v.reduce((s, x) => s + x, 0) / v.length : null);
  const median = (v) => { if (!v.length) return null; const s = [...v].sort((a, b) => a - b), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const addDays = (k, n) => new Date(Date.parse(k + "T00:00:00Z") + n * 864e5).toISOString().slice(0, 10);
  const get = (u) => fetch(u).then((r) => (r.ok ? r.json() : Promise.reject(r.status)));

  for (const el of els) el.querySelector("[data-breathe-body]").innerHTML = `<p class="muted">${T[el.dataset.lang]?.wait || T.en.wait}</p>`;

  Promise.all([get(aqUrl), get(wxUrl)]).then(([a, w]) => {
    const f = forecast(a, w);
    if (!f) throw new Error("not enough data");
    for (const el of els) draw(el, f);
  }).catch((err) => {
    console.warn("[hh] breathe", err);
    for (const el of els) el.querySelector("[data-breathe-body]").innerHTML = `<p class="muted">${T[el.dataset.lang]?.fail || T.en.fail}</p>`;
  });

  // ---------- The forecast ----------
  function forecast(a, w) {
    const off = (a.utc_offset_seconds || 0) * 1000, today = new Date(Date.now() + off).toISOString().slice(0, 10);
    const pm = {};
    a.hourly.time.forEach((t, i) => { const v = a.hourly.pm2_5[i]; if (v != null) (pm[t.slice(0, 10)] ||= []).push(v); });
    const dayPm = (k) => (pm[k] && pm[k].length >= 20 ? mean(pm[k]) : null);
    const past = [];
    for (let i = 1; i <= 7; i++) { const v = dayPm(addDays(today, -i)); if (v != null) past.push(v); }
    if (past.length < 4) return null;
    const base = mean(past);
    const dust = {};
    a.hourly.time.forEach((t, i) => { const v = a.hourly.dust?.[i]; if (v != null) (dust[t.slice(0, 10)] ||= []).push(v); });
    const pastDust = [];
    for (let i = 1; i <= 7; i++) { const v = dust[addDays(today, -i)]; if (v?.length >= 20) pastDust.push(mean(v)); }
    const dusty = pastDust.length >= 4 && mean(pastDust) >= 80;

    // Weather by local day.
    const di = (k) => w.daily.time.indexOf(k);
    const hours = {};
    w.hourly.time.forEach((t, i) => { const h = +t.slice(11, 13); if (h >= 10 && h <= 17) (hours[t.slice(0, 10)] ||= []).push(i); });
    const vcOf = (k) => {
      const blh = w.hourly.boundary_layer_height_gfs_seamless, ws = w.hourly.wind_speed_10m_gfs_seamless;
      const v = (hours[k] || []).map((i) => (blh?.[i] != null && ws?.[i] != null ? (blh[i] * ws[i]) / 3.6 : null)).filter((x) => x != null);
      return v.length ? Math.max(...v) : null;
    };
    const pastVc = [];
    for (let i = 1; i <= 7; i++) { const v = vcOf(addDays(today, -i)); if (v != null) pastVc.push(v); }
    const vcBase = median(pastVc);
    const wxOf = (k) => {
      const i = di(k);
      if (i < 0) return null;
      const rain = MODELS.map((m) => w.daily[`precipitation_sum_${m}`]?.[i]).filter((x) => x != null);
      const wind = MODELS.map((m) => w.daily[`wind_speed_10m_max_${m}`]?.[i]).filter((x) => x != null);
      const wet = rain.filter((x) => x >= 2);
      const rainy = rain.length > 0 && wet.length * 2 > rain.length;
      const windMax = median(wind), vc = vcOf(k);
      const windy = windMax != null && windMax >= 20;
      const mix = vc != null && vc >= Math.max(6000, 1.5 * (vcBase || 0));
      const still = vc != null && vc < Math.min(2000, 0.6 * (vcBase || Infinity)) && (windMax == null || windMax < 12);
      const cause = rainy ? "rain" : windy ? (dusty ? "dust" : "wind") : mix ? "mix" : still ? "still" : "";
      return { cause, rainM: wet.length, rainN: rain.length, mm: Math.round(median(wet) || 0), wind: Math.round(windMax || 0) };
    };

    const days = [];
    for (let i = 0; i < DAYS; i++) {
      const k = addDays(today, i), p = dayPm(k), wx = wxOf(k) || { cause: "" };
      const r = p == null ? null : p / base;
      let st;
      if (r != null) st = r <= 0.7 ? "brk" : r <= 0.87 ? "lighter" : r < 1.15 ? "same" : "worse";
      // Past the smoke forecast, every day still gets an outlook from the weather: lighter, about the same or building up.
      else st = wx.cause === "still" || wx.cause === "dust" ? "build" : wx.cause ? "maybe" : "flat";
      days.push({ k, i, r, st, air: r != null, wx });
    }
    // The first break: a smoke-forecast break, or past its horizon a weather-only one; then the run of such days.
    const isBrk = (d) => d.st === "brk" || d.st === "maybe";
    const s = days.findIndex(isBrk);
    let run = [];
    if (s >= 0) for (let i = s; i < DAYS && isBrk(days[i]) && days[i].air === days[s].air; i++) run.push(days[i]);
    const end = run.length ? run[run.length - 1].i : -1;
    const back = run.length && run[0].air ? days.find((d) => d.i > end && d.air && d.st !== "brk") : null;
    const stillDay = days.find((d) => d.i > end && d.wx.cause === "still");
    // Every break in the 10 days, not only the first; and the weather-only days grouped into runs of one outlook.
    const runs = [];
    days.forEach((d) => { if (!isBrk(d)) return; const r = runs[runs.length - 1]; if (r && r[r.length - 1].i === d.i - 1 && r[0].air === d.air) r.push(d); else runs.push([d]); });
    const outlook = [];
    days.filter((d) => !d.air).forEach((d) => { const g = outlook[outlook.length - 1]; if (g && g[0].st === d.st && g[0].wx.cause === d.wx.cause) g.push(d); else outlook.push([d]); });
    return { days, base, run, runs, outlook, back, stillDay, light: base < 25 && s < 0 };
  }

  // ---------- The widget ----------
  function names(l) {
    const t = T[l];
    const wd = new Intl.DateTimeFormat(LOC[l], { weekday: "short", timeZone: "UTC" });
    const dm = new Intl.DateTimeFormat(LOC[l], { day: "numeric", timeZone: "UTC" });
    const long = new Intl.DateTimeFormat(LOC[l], { weekday: "long", day: "numeric", month: l === "en" ? "short" : "long", timeZone: "UTC" });
    const nf = new Intl.NumberFormat(LOC[l]);
    const name = (d) => (d.i === 0 ? t.today : d.i === 1 ? t.tmw : long.format(Date.parse(d.k)));
    return { wdShort: (d) => wd.format(Date.parse(d.k)), wd: (d) => (d.i === 0 ? t.today : wd.format(Date.parse(d.k))), dm: (d) => dm.format(Date.parse(d.k)), name, nf };
  }

  function answer(f, l, N) {
    const t = T[l], { name, nf } = names(l), run = f.run;
    const spanOf = (g) => (g.length === 1 ? name(g[0]) : g.length === 2 ? t.and(name(g[0]), name(g[1])) : t.to(name(g[0]), name(g[g.length - 1])));
    // The weather-only days in words, leaving out the ones the headline already covers.
    const skip = new Set(run[0]?.air === false ? run.map((d) => d.i) : []);
    const parts = f.outlook.filter((g) => !skip.has(g[0].i)).map((g) => g[0].st === "maybe" ? t.ol.maybe(spanOf(g), t.olCause[g[0].wx.cause]) : g[0].wx.cause === "dust" ? t.ol.dust(spanOf(g)) : t.ol[g[0].st](spanOf(g)));
    const outlook = parts.length ? (run.length && !f.light ? t.outlook : t.outlook0)(parts) : "";
    const later = f.runs.slice(1);
    const out = { big: "", tone: "none", span: "", lines: [], note: "" };
    if (f.light) { out.big = t.light; out.tone = "brk"; out.lines.push(t.lightTxt(N)); return out; }
    if (!run.length) {
      out.big = t.none;
      const lt = f.days.find((d) => d.st === "lighter");
      if (lt) out.lines.push(t.lighterOnly(name(lt)));
      out.lines.push(t.noneWhy);
      if (outlook) out.lines.push(outlook);
      else if (f.stillDay) out.lines.push(t.noneStill(name(f.stillDay)));
      return out;
    }
    const a = run[0], z = run[run.length - 1];
    const span = run.length === 1 ? name(a) : run.length === 2 ? t.and(name(a), name(z)) : t.to(name(a), name(z));
    out.span = span;
    if (a.air) {
      out.big = a.i === 0 ? t.now : a.i === 1 ? t.tomorrow : t.inDays(nf.format(a.i));
      out.tone = "brk";
      const r = mean(run.map((d) => d.r)), p = Math.round((1 - r) * 10) * 10;
      out.p = p;
      out.lines.push(t.spanLess(span, p >= 45 && p <= 55 ? t.half : t.less(nf.format(p))));
    } else {
      out.big = t.maybe(nf.format(a.i));
      out.tone = "maybe";
      out.lines.push(t.spanMaybe(span));
      out.note = t.maybeNote;
    }
    const c = run.map((d) => d.wx).find((x) => x.cause && x.cause !== "still" && x.cause !== "dust");
    out.lines.push(!c ? t.why.none : c.cause === "rain" ? t.why.rain(nf.format(c.rainM), nf.format(c.rainN), nf.format(c.mm)) : c.cause === "wind" ? t.why.wind(nf.format(c.wind)) : t.why.mix);
    if (f.back) out.lines.push(t.back(name(f.back)));
    // The days after: the weather outlook (when the first break is in the smoke forecast), or any later breaks.
    if (outlook) out.lines.push(a.air ? outlook : t.outlook0(parts));
    else if (later.length) out.lines.push(t.later(later.map(spanOf).join(", ")));
    else if (!f.back && f.stillDay) out.lines.push(t.still(name(f.stillDay)));
    return out;
  }

  function draw(el, f) {
    const l = el.dataset.lang in T ? el.dataset.lang : "en", t = T[l], N = el.dataset.name;
    const { wd, dm, wdShort } = names(l), ans = answer(f, l, N);
    const H = 80, MAXR = 1.6, baseY = Math.round(H / MAXR);
    const nAir = f.days.filter((d) => d.air).length;
    const cols = f.days.map((d) => {
      const brk = d.st === "brk" || d.st === "maybe";
      const lbl = d.air ? t.legend[d.st] : d.st === "maybe" ? t.legend.brk + "?" : d.wx.cause ? t.icon[d.wx.cause] : t.legend.same + "?";
      const bar = d.air
        ? `<i class="bar" style="height:${Math.max(4, Math.round((Math.min(d.r, MAXR) / MAXR) * H))}px;background:${COLOR[d.st]}"></i>`
        : d.st in WXH ? `<i class="bar wx" style="height:${Math.round((WXH[d.st] / MAXR) * H)}px;--c:${COLOR[d.st]}"></i>` : "";
      return `<div class="cp-br-d${brk ? " brk" : ""}${d.air ? " air" : ""}" title="${esc(`${wd(d)} ${dm(d)}${lbl ? `: ${lbl}` : ""}`)}">` +
        `<span class="wd">${d.i === 0 ? `<span class="full">${t.today}</span><span class="short">${wdShort(d)}</span>` : wd(d)}</span><span class="dm">${dm(d)}</span>` +
        `<span class="plot" style="--b:${baseY}px">${bar}</span>` +
        `<span class="wx">${d.wx.cause ? svg(d.wx.cause) : ""}</span></div>`;
    }).join("");
    const used = [...new Set(f.days.map((d) => d.wx.cause).filter(Boolean))];
    const stUsed = ["brk", "lighter", "same", "worse"].filter((s) => f.days.some((d) => d.air && d.st === s));
    // The share link has its own path, so its preview says the same as this (see breatheMeta in citypage.js):
    // only numbers go in it, the start day, days, per cent less smoke, and smoke forecast or weather only.
    const run = f.run, qs = new URLSearchParams();
    if (f.light || !run.length) { qs.set("k", f.light ? "l" : "x"); qs.set("d", f.days[0].k); }
    else { qs.set("d", run[0].k); qs.set("n", run.length); if (run[0].air) qs.set("p", ans.p); qs.set("k", run[0].air ? "a" : "w"); }
    if (l !== "en") qs.set("lang", l);
    const url = `${new URL(el.dataset.url).origin}/air/${el.dataset.city}/breathe/?${qs}#breathe-${l}`;
    const shareTxt = `${t.q(N)} ${run.length && !f.light ? ans.lines[0] : f.light ? t.lightTxt(N) : t.none + (l === "ur" ? "۔" : l === "hi" ? "।" : ".")}`;
    el.querySelector("[data-breathe-body]").innerHTML =
      `<div class="cp-br-a ${ans.tone}"><b>${esc(ans.big)}</b></div>` +
      `<div class="cp-br-lines">${ans.lines.map((x, i) => `<p${i === 0 ? ' class="lead"' : ""}>${esc(x)}</p>`).join("")}${ans.note ? `<p class="muted">${esc(ans.note)}</p>` : ""}</div>` +
      `<div class="cp-br-strip" style="--na:${nAir}">${cols}</div>` +
      `<div class="cp-br-lbl"><span style="grid-column:1 / span ${nAir}">${t.airLbl}</span><span style="grid-column:${nAir + 1} / -1">${t.wxLbl}</span></div>` +
      `<p class="cp-br-key">${stUsed.map((s) => `<span><i style="background:${COLOR[s]}"></i>${t.legend[s]}</span>`).join("")}` +
      `<span><i class="base"></i>${t.legend.base}</span>${nAir < DAYS ? `<span><i class="wxk"></i>${t.olKey}</span>` : ""}${used.map((x) => `<span>${svg(x, 13)} ${t.icon[x]}</span>`).join("")}</p>` +
      `<div class="cp-share"><button type="button" class="wa" data-br-share>${t.share}</button>` +
      `<a href="https://wa.me/?text=${encodeURIComponent(`${shareTxt} ${url}`)}" target="_blank" rel="noopener">${t.wa}</a>` +
      `<button type="button" data-copy="${esc(url)}" data-done="${esc(t.copied)}">${t.copy}</button></div>` +
      `<p class="cp-br-src">${t.src}</p>`;
    // The teaser on the report card, in the same language's article.
    const tease = el.closest("article")?.querySelector("[data-breathe-tease]");
    if (tease) {
      tease.innerHTML = `<span class="k">${esc(el.querySelector(".cp-kicker")?.textContent || "")}</span><b class="${ans.tone === "none" ? "none" : ""}">${esc(ans.big)}</b>` +
        `<span class="m">${esc(ans.lines[0] || "")}</span>`;
      tease.hidden = false;
    }
    el._shareUrl = url;
    el.querySelector("[data-br-share]").addEventListener("click", (e) => sharePic(e.currentTarget, el, f, ans, shareTxt));
  }

  // ---------- The picture ----------
  async function sharePic(btn, el, f, ans, text) {
    const l = el.dataset.lang in T ? el.dataset.lang : "en", t = T[l], N = el.dataset.name, rtl = l === "ur";
    const fam = l === "ur" ? '"Noto Nastaliq Urdu", serif' : '"Kalam", "Inter", sans-serif', body = l === "ur" ? '"Noto Nastaliq Urdu", serif' : '"Inter", sans-serif';
    try { await Promise.all([document.fonts.load(`700 40px ${fam}`, N), document.fonts.load(`400 30px ${body}`, N)]); } catch {}
    const S = 1080, P = 72, c = document.createElement("canvas");
    c.width = c.height = S;
    const g = c.getContext("2d");
    g.fillStyle = "#fbf8f1"; g.fillRect(0, 0, S, S);
    g.direction = rtl ? "rtl" : "ltr"; g.textAlign = rtl ? "right" : "left"; g.textBaseline = "alphabetic";
    const X = rtl ? S - P : P, lh = rtl ? 1.9 : 1.3;
    const wrap = (s, font, size, y, color, maxW = S - 2 * P) => {
      g.font = `${font.replace("SZ", size)}`; g.fillStyle = color;
      const words = s.split(" "); let line = "";
      for (const wd of words) {
        const test = line ? line + " " + wd : wd;
        if (g.measureText(test).width > maxW && line) { g.fillText(line, X, y); y += size * lh; line = wd; } else line = test;
      }
      if (line) { g.fillText(line, X, y); y += size * lh; }
      return y;
    };
    let y = P + 30;
    y = wrap("hamarihawa.org", `600 SZpx ${body}`, 26, y, "#6b6560");
    y = wrap(t.q(N), `700 SZpx ${fam}`, 50, y + 20, "#1d1b19");
    const col = ans.tone === "brk" ? GREEN : ans.tone === "maybe" ? "#5d8f5a" : "#8a8580";
    y = wrap(ans.big, `700 SZpx ${fam}`, rtl ? 104 : 130, y + (rtl ? 70 : 100), col) - (rtl ? 60 : 40);
    // The picture keeps the answer, the reason and what comes next; the 10-day outlook is in the strip.
    for (const [i, s] of ans.lines.slice(0, 3).entries()) y = wrap(s, `${i === 0 ? 600 : 400} SZpx ${body}`, i === 0 ? 34 : 29, y + 6, i === 0 ? "#1d1b19" : "#47423d");
    // The strip, drawn in reading order.
    const top = Math.min(S - (rtl ? 330 : 300), Math.max(y + 30, rtl ? 660 : 690)), H = 150, gap = 10, cw = (S - 2 * P - gap * (DAYS - 1)) / DAYS, MAXR = 1.6;
    const { wd, dm } = names(l);
    f.days.forEach((d, j) => {
      const x = rtl ? S - P - (j + 1) * cw - j * gap : P + j * (cw + gap);
      if (d.st === "brk" || d.st === "maybe") { g.fillStyle = GREEN_SOFT; g.beginPath(); g.roundRect(x - 4, top - 6, cw + 8, H + (rtl ? 150 : 130), 12); g.fill(); }
      if (d.air) {
        const h = Math.max(6, (Math.min(d.r, MAXR) / MAXR) * H);
        g.fillStyle = COLOR[d.st]; g.beginPath(); g.roundRect(x + 6, top + H - h, cw - 12, h, 6); g.fill();
      } else if (d.st in WXH) {
        const h = (WXH[d.st] / MAXR) * H;
        g.globalAlpha = 0.35; g.fillStyle = COLOR[d.st]; g.beginPath(); g.roundRect(x + 8, top + H - h, cw - 16, h, 6); g.fill(); g.globalAlpha = 1;
        g.strokeStyle = COLOR[d.st]; g.setLineDash([8, 6]); g.lineWidth = 3; g.beginPath(); g.roundRect(x + 8, top + H - h, cw - 16, h, 6); g.stroke(); g.setLineDash([]);
      }
      g.textAlign = "center"; g.fillStyle = d.i === 0 ? "#1d1b19" : "#5a5550";
      g.font = `600 ${rtl ? 22 : 24}px ${body}`; g.fillText(wd(d), x + cw / 2, top + H + (rtl ? 48 : 40));
      g.font = `400 22px ${body}`; g.fillText(dm(d), x + cw / 2, top + H + (rtl ? 88 : 72));
      if (d.wx.cause) {
        const img = ICONIMG[d.wx.cause];
        if (img?.complete) g.drawImage(img, x + cw / 2 - 16, top + H + (rtl ? 106 : 88), 32, 32);
      }
    });
    // The past-week line over the smoke-forecast days.
    const nAir = f.days.filter((d) => d.air).length, by = top + H - H / MAXR;
    if (nAir) {
      const x0 = rtl ? S - P - nAir * (cw + gap) + gap : P, x1 = rtl ? S - P : P + nAir * (cw + gap) - gap;
      g.strokeStyle = "#1d1b19"; g.setLineDash([10, 8]); g.lineWidth = 2.5; g.beginPath(); g.moveTo(x0, by); g.lineTo(x1, by); g.stroke(); g.setLineDash([]);
      g.textAlign = rtl ? "right" : "left"; g.font = `400 20px ${body}`; g.fillStyle = "#47423d";
      g.fillText(t.legend.base, rtl ? x1 : x0, by - 8);
    }
    g.textAlign = rtl ? "right" : "left";
    wrap(t.imgSrc, `400 SZpx ${body}`, 21, S - 44, "#6b6560");
    const blob = await new Promise((r) => c.toBlob(r, "image/png"));
    if (!blob) return;
    const file = new File([blob], `breathe-${el.dataset.city || "city"}.png`, { type: "image/png" });
    try {
      if (navigator.canShare?.({ files: [file] })) { await navigator.share({ files: [file], text: `${text} ${el._shareUrl}` }); return; }
    } catch (e) { if (e?.name === "AbortError") return; }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = file.name; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    const old = btn.textContent; btn.textContent = t.saved; setTimeout(() => (btn.textContent = old), 2500);
  }
  // The weather icons as images for the canvas.
  const ICONIMG = {};
  for (const k in ICON) {
    const img = new Image();
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="64" height="64">${ICON[k]}</svg>`);
    ICONIMG[k] = img;
  }
})();
