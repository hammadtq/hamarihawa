// The air right now on a city page (/air/<city>/): Open-Meteo requests from the visitor's browser, so the
// Worker never calls Open-Meteo. The card shows US AQI now and PM2.5 averaged over the past 24 hours, as the
// city cards on the live map do. The week strip under it ([data-week]) shows the past 3 days, today and the
// model's next 4 days as coloured dots, the weather that moves smoke (rain, wind, still air), and one or two
// short lines: how today compares with last week and what is coming.
(() => {
  const els = [...document.querySelectorAll("[data-air]")];
  if (!els.length) return;
  const weeks = [...document.querySelectorAll("[data-week]")];
  const { lat, lon } = els[0].dataset;
  const url = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}` +
    "&current=us_aqi,pm2_5,pm10&hourly=pm2_5,us_aqi&past_days=7&forecast_days=5&timezone=auto";
  const wxUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
    "&daily=precipitation_sum,wind_speed_10m_max&hourly=boundary_layer_height&past_days=3&forecast_days=10&timezone=auto";
  const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const band = (a) => (a <= 50 ? 0 : a <= 100 ? 1 : a <= 150 ? 2 : a <= 200 ? 3 : a <= 300 ? 4 : 5);
  // US AQI from this hour's PM2.5 and PM10 (EPA breakpoints of May 2024, the higher of the two), the "now"
  // figure ground-station sites such as IQAir show. Open-Meteo's own us_aqi is a 24-hour average and lags the
  // smog by hours. The same function is in app.js, city-air.js, rankings.js and src/kml.js.
  const AQI_BP = [
    [[0, 9, 0, 50], [9.1, 35.4, 51, 100], [35.5, 55.4, 101, 150], [55.5, 125.4, 151, 200], [125.5, 225.4, 201, 300], [225.5, 325.4, 301, 500]],
    [[0, 54, 0, 50], [55, 154, 51, 100], [155, 254, 101, 150], [255, 354, 151, 200], [355, 424, 201, 300], [425, 604, 301, 500]],
  ];
  const aqiOf = (c, bp) => {
    if (c == null || !(c >= 0)) return null;
    const [lo, hi, a, b] = bp.find((s) => c <= s[1]) || bp[bp.length - 1];
    return Math.round(a + ((b - a) * (c - lo)) / (hi - lo));
  };
  const aqiNow = (pm25, pm10) => {
    const v = [aqiOf(pm25 == null ? null : Math.floor(pm25 * 10) / 10, AQI_BP[0]), aqiOf(pm10 == null ? null : Math.floor(pm10), AQI_BP[1])];
    return v.some((x) => x != null) ? Math.max(...v.filter((x) => x != null)) : null;
  };
  const mean = (v) => (v.length ? v.reduce((s, x) => s + x, 0) / v.length : null);

  const T = {
    en: {
      today: "Today", past: "Last 3 days", next: "Model forecast",
      cmp: ["Much cleaner than last week", "Cleaner than last week", "About the same as last week", "Smokier than last week", "Much smokier than last week"],
      why: { rain: "Rain is washing smoke out of the air.", wind: "Strong wind is blowing smoke away.", still: "Still air is trapping smoke near the ground." },
      better: (d) => `Cleaner air expected from ${d}.`, worse: (d) => `Smokier air expected from ${d}.`, same: "Not much change expected in the next 4 days.",
      rainOn: (d) => `Rain on ${d} may clear the air.`, stillFrom: (d) => `Still air from ${d} may let smoke build up.`,
      key: { rain: "rain", wind: "wind", still: "still air" },
      src: "Air: Copernicus CAMS model via Open-Meteo. Weather: Open-Meteo.",
    },
    ur: {
      today: "آج", past: "پچھلے 3 دن", next: "ماڈل کی پیش گوئی",
      cmp: ["ہوا پچھلے ہفتے سے کہیں صاف", "ہوا پچھلے ہفتے سے صاف", "ہوا پچھلے ہفتے جیسی", "پچھلے ہفتے سے زیادہ دھواں", "پچھلے ہفتے سے کہیں زیادہ دھواں"],
      why: { rain: "بارش ہوا سے دھواں دھو رہی ہے۔", wind: "تیز ہوا دھواں اڑا لے جا رہی ہے۔", still: "تھمی ہوا دھوئیں کو زمین کے قریب روکے ہوئے ہے۔" },
      better: (d) => `${d} سے ہوا صاف ہونے کی توقع ہے۔`, worse: (d) => `${d} سے دھواں بڑھنے کی توقع ہے۔`, same: "اگلے 4 دنوں میں زیادہ تبدیلی کی توقع نہیں۔",
      rainOn: (d) => `${d} کو بارش ہوا صاف کر سکتی ہے۔`, stillFrom: (d) => `${d} سے تھمی ہوا میں دھواں جمع ہو سکتا ہے۔`,
      key: { rain: "بارش", wind: "ہوا", still: "تھمی ہوا" },
      src: "ہوا: کوپرنیکس CAMS ماڈل، اوپن میٹیو کے ذریعے۔ موسم: اوپن میٹیو۔",
    },
    hi: {
      today: "आज", past: "पिछले 3 दिन", next: "मॉडल का अनुमान",
      cmp: ["हवा पिछले हफ़्ते से कहीं साफ़", "हवा पिछले हफ़्ते से साफ़", "हवा पिछले हफ़्ते जैसी", "पिछले हफ़्ते से ज़्यादा धुआँ", "पिछले हफ़्ते से कहीं ज़्यादा धुआँ"],
      why: { rain: "बारिश हवा से धुआँ धो रही है।", wind: "तेज़ हवा धुआँ उड़ा ले जा रही है।", still: "थमी हवा धुएँ को ज़मीन के पास रोके हुए है।" },
      better: (d) => `${d} से हवा साफ़ होने की उम्मीद है।`, worse: (d) => `${d} से धुआँ बढ़ने की उम्मीद है।`, same: "अगले 4 दिनों में ज़्यादा बदलाव की उम्मीद नहीं।",
      rainOn: (d) => `${d} को बारिश हवा साफ़ कर सकती है।`, stillFrom: (d) => `${d} से थमी हवा में धुआँ जमा हो सकता है।`,
      key: { rain: "बारिश", wind: "हवा", still: "थमी हवा" },
      src: "हवा: कोपरनिकस CAMS मॉडल, ओपन-मेटियो से। मौसम: ओपन-मेटियो।",
    },
  };
  // Small drawn icons: a raindrop, two wind lines, three flat haze lines.
  const ICON = {
    rain: '<svg viewBox="0 0 16 16" width="15" height="15"><path d="M8 1.5C6 5 3.8 7.4 3.8 10a4.2 4.2 0 0 0 8.4 0C12.2 7.4 10 5 8 1.5z" fill="#3b82c4"/></svg>',
    wind: '<svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="#2f6f9f" stroke-width="1.6" stroke-linecap="round"><path d="M1.5 6h9a2.2 2.2 0 1 0-2.2-2.2"/><path d="M1.5 10.5h11a2 2 0 1 1-2 2"/></svg>',
    still: '<svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="#9a8f80" stroke-width="1.8" stroke-linecap="round"><path d="M2 5h12M3.5 8.5h9M2 12h12"/></svg>',
  };
  // A day's weather, as one word: rain (2 mm or more), wind (gusting past 20 km/h) or still air (light wind
  // and a mixing layer under 1 km, so smoke stays near the ground).
  const wxOf = (rain, wind, blh) => (rain >= 2 ? "rain" : wind >= 20 ? "wind" : wind < 10 && blh != null && blh < 1000 ? "still" : "");

  const air = fetch(url).then((r) => (r.ok ? r.json() : Promise.reject(r.status)));
  const wx = weeks.length ? fetch(wxUrl).then((r) => (r.ok ? r.json() : null)).catch(() => null) : Promise.resolve(null);

  air.then((a) => {
    const off = (a.utc_offset_seconds || 0) * 1000, now = Date.now();
    const times = a.hourly.time.map((x) => Date.parse(x + "Z") - off);
    const vals = a.hourly.pm2_5.filter((v, i) => v != null && times[i] <= now && times[i] > now - 24 * 36e5);
    const pm = vals.length ? mean(vals) : a.current.pm2_5;
    const aqi = aqiNow(a.current.pm2_5, a.current.pm10) ?? a.current.us_aqi;
    if (aqi == null || pm == null) return;
    for (const el of els) {
      const nf = new Intl.NumberFormat(LOC[el.dataset.lang] || "en-GB", { maximumFractionDigits: 1 });
      const vals = { aqi: nf.format(Math.round(aqi)), band: el.dataset.bands.split("|")[band(aqi)],
        pm: nf.format(Math.round(pm)), who: nf.format(pm / 15), cigs: nf.format(pm / 22) };
      const line = el.dataset.line.replace(/\{(\w+)\}/g, (m, k) => (k in vals ? `<b>${vals[k]}</b>` : m));
      if (el.dataset.card != null) {
        // The city page's report card: the AQI as a big coloured number, the band, the line, cigarettes drawn.
        const b = band(aqi), cigs = Math.min(12, Math.round(pm / 22));
        el.innerHTML = `<div class="cp-aqi-num${b === 1 ? " dark" : ""}" style="background:var(--aqi-${b}, #999)"><b>${vals.aqi}</b><span>${el.dataset.unit}</span></div>` +
          `<div class="cp-aqi-txt"><div class="cp-aqi-band" style="color:var(--aqi-${b}, #999)">${vals.band}</div><div>${line}` +
          (cigs ? `<span class="cp-cigs" aria-hidden="true">${"<i class=\"cp-cig\"></i>".repeat(cigs)}</span>` : "") +
          `</div><div class="muted" style="font-size:12.5px">${el.dataset.src}</div></div>`;
        continue;
      }
      el.innerHTML = line;
      el.style.borderInlineStart = `4px solid var(--aqi-${band(aqi)}, #999)`;
      el.style.paddingInlineStart = "10px";
    }
    if (!weeks.length) return;

    // Local days: mean hourly AQI and PM2.5 for each, keyed YYYY-MM-DD.
    const day = {};
    a.hourly.time.forEach((t, i) => {
      const k = t.slice(0, 10), d = (day[k] ||= { aqi: [], pm: [], all: [] });
      if (a.hourly.us_aqi[i] != null) d.aqi.push(a.hourly.us_aqi[i]);
      if (a.hourly.pm2_5[i] != null) { d.all.push(a.hourly.pm2_5[i]); if (times[i] <= now) d.pm.push(a.hourly.pm2_5[i]); }
    });
    const todayKey = new Date(now + off).toISOString().slice(0, 10);
    const keys = Object.keys(day).sort(), ti = keys.indexOf(todayKey);
    if (ti < 3) return;
    const lastWeek = mean(keys.slice(Math.max(0, ti - 7), ti).map((k) => mean(day[k].pm)).filter((v) => v != null));
    const strip = keys.slice(ti - 3, ti + 5).map((k, j) => {
      const v = k === todayKey ? aqi : mean(day[k].aqi), p = k === todayKey ? pm : mean(day[k].all);
      return { k, p, b: v == null || p == null ? null : band(v), when: j < 3 ? "past" : j === 3 ? "today" : "next" };
    }).filter((d) => d.b != null);
    // Each dot's size follows the day's PM2.5, so a smokier day is a bigger dot; its colour is the AQI band.
    const top = Math.max(...strip.map((d) => d.p), 1);
    for (const d of strip) d.s = Math.round(10 + 18 * Math.sqrt(d.p / top));
    const r = lastWeek ? pm / lastWeek : 1, cmp = r <= 0.7 ? 0 : r <= 0.88 ? 1 : r < 1.12 ? 2 : r < 1.4 ? 3 : 4;

    wx.then((w) => {
      const wxDay = {};
      if (w?.daily) w.daily.time.forEach((k, i) => {
        const blh = (w.hourly?.boundary_layer_height || []).slice(i * 24, i * 24 + 24).filter((x) => x != null);
        wxDay[k] = wxOf(w.daily.precipitation_sum[i] || 0, w.daily.wind_speed_10m_max[i] || 0, blh.length ? Math.max(...blh) : null);
      });
      const tb = band(aqi), ahead = keys.slice(ti + 1, ti + 5).map((k) => ({ k, b: day[k].aqi.length ? band(mean(day[k].aqi)) : null }));
      const wxKeys = Object.keys(wxDay).sort().filter((k) => k > todayKey);
      for (const el of weeks) {
        const l = el.dataset.lang in T ? el.dataset.lang : "en", t = T[l];
        const wd = new Intl.DateTimeFormat(LOC[l], { weekday: "short", timeZone: "UTC" });
        const wdLong = new Intl.DateTimeFormat(LOC[l], { weekday: "long", timeZone: "UTC" });
        const name = (k) => wdLong.format(Date.parse(k));
        const bands = el.dataset.bands.split("|");
        // Today's weather explains the change only when it points the same way (rain or wind with cleaner air,
        // still air with smokier air), today or yesterday.
        const recent = [wxDay[todayKey], wxDay[keys[ti - 1]]];
        const why = cmp <= 1 ? recent.find((x) => x === "rain" || x === "wind") : cmp >= 3 ? recent.find((x) => x === "still") : null;
        const arrow = cmp <= 1 ? ["#3c9a3c", "M8 3v10M3.5 8.5 8 13l4.5-4.5"] : cmp >= 3 ? ["#d93b30", "M8 13V3M3.5 7.5 8 3l4.5 4.5"] : ["#7c7c80", "M3 8h10M9 4l4 4-4 4"];
        let lines = [];
        const change = ahead.find((d) => d.b != null && d.b !== tb);
        lines.push(change ? (change.b < tb ? t.better : t.worse)(name(change.k)) : t.same);
        const rainK = wxKeys.find((k) => wxDay[k] === "rain");
        const stillK = wxKeys.find((k, i) => wxDay[k] === "still" && wxDay[wxKeys[i + 1]] === "still");
        if (rainK && !(change && change.b < tb && rainK <= change.k)) lines.push(t.rainOn(name(rainK)));
        else if (stillK) lines.push(t.stillFrom(name(stillK)));
        const used = new Set(strip.map((d) => wxDay[d.k]).filter(Boolean));
        el.innerHTML =
          `<div class="cp-wk-h"><svg viewBox="0 0 16 16" width="20" height="20" fill="none" stroke="${arrow[0]}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${arrow[1]}"/></svg>` +
          `<span>${t.cmp[cmp]}</span></div>` + (why ? `<p class="cp-wk-why">${ICON[why]} ${t.why[why]}</p>` : "") +
          `<div class="cp-wk-row">` + strip.map((d) => {
            const label = d.when === "today" ? t.today : wd.format(Date.parse(d.k));
            const x = wxDay[d.k];
            return `<div class="cp-wk-d ${d.when}" title="${label}: ${bands[d.b]}${d.when === "next" ? ` (${t.next})` : ""}">` +
              `<span>${label}</span><span class="dw"><i class="dot" style="--c:var(--aqi-${d.b}, #999);--s:${d.s}px"></i></span><span class="wx">${x ? ICON[x] : ""}</span></div>`;
          }).join("") + `</div>` +
          `<div class="cp-wk-lbl"><span>${t.past}</span><span>${t.next}</span></div>` +
          `<p class="cp-wk-next">${lines.join(" ")}</p>` +
          (used.size ? `<p class="cp-wk-key">${[...used].map((x) => `${ICON[x]} ${t.key[x]}`).join(" &nbsp; ")}</p>` : "") +
          `<p class="cp-wk-src">${t.src}</p>`;
        el.hidden = false;
      }
    });
  }).catch((err) => console.warn("[hh] city air", err));
})();
