// The air right now on a city page (/air/<city>/): Open-Meteo requests from the visitor's browser, so the
// Worker never calls Open-Meteo. The card shows US AQI now and PM2.5 averaged over the past 24 hours, as the
// city cards on the live map do. What is coming next is /breathe.js ("Breathe again").
(() => {
  const els = [...document.querySelectorAll("[data-air]")];
  if (!els.length) return;
  const { lat, lon } = els[0].dataset;
  const url = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}` +
    "&current=us_aqi,pm2_5,pm10&hourly=pm2_5&past_days=1&forecast_days=1&timezone=auto";
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

  const air = fetch(url).then((r) => (r.ok ? r.json() : Promise.reject(r.status)));

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
  }).catch((err) => console.warn("[hh] city air", err));
})();
