// The air right now on a city page (/air/<city>/): one Open-Meteo request from the visitor's browser,
// worked out as the city cards on the live map do (US AQI now, PM2.5 averaged over the past 24 hours).
(() => {
  const els = [...document.querySelectorAll("[data-air]")];
  if (!els.length) return;
  const { lat, lon } = els[0].dataset;
  const url = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}` +
    "&current=us_aqi,pm2_5&hourly=pm2_5&past_days=1&forecast_days=1&timezone=GMT";
  const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const band = (a) => (a <= 50 ? 0 : a <= 100 ? 1 : a <= 150 ? 2 : a <= 200 ? 3 : a <= 300 ? 4 : 5);
  fetch(url).then((r) => (r.ok ? r.json() : Promise.reject(r.status))).then((a) => {
    const now = Date.now(), times = a.hourly.time.map((x) => Date.parse(x + "Z"));
    const vals = a.hourly.pm2_5.filter((v, i) => v != null && times[i] <= now && times[i] > now - 24 * 36e5);
    const pm = vals.length ? vals.reduce((s, v) => s + v, 0) / vals.length : a.current.pm2_5;
    const aqi = a.current.us_aqi;
    if (aqi == null || pm == null) return;
    for (const el of els) {
      const nf = new Intl.NumberFormat(LOC[el.dataset.lang] || "en-GB", { maximumFractionDigits: 1 });
      const vals = { aqi: nf.format(Math.round(aqi)), band: el.dataset.bands.split("|")[band(aqi)],
        pm: nf.format(Math.round(pm)), who: nf.format(pm / 15), cigs: nf.format(pm / 22) };
      el.innerHTML = el.dataset.line.replace(/\{(\w+)\}/g, (m, k) => (k in vals ? `<b>${vals[k]}</b>` : m));
      el.style.borderInlineStart = `4px solid var(--aqi-${band(aqi)}, #999)`;
      el.style.paddingInlineStart = "10px";
    }
  }).catch((err) => console.warn("[hh] city air", err));
})();
