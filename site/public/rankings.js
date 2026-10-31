// /rankings/: "show all" for the long tables, and the air-quality table, which loads only when asked: one
// batched Open-Meteo request for every city (each city counts against Open-Meteo's free daily quota, so it
// doesn't run on every page view). Readings are Copernicus CAMS model estimates, fetched by the browser.
(() => {
  document.addEventListener("click", (e) => {
    const more = e.target.closest("[data-more]");
    if (more) {
      more.closest("p").previousElementSibling.querySelectorAll("tr.more").forEach((tr) => { tr.hidden = false; });
      more.closest("p").remove();
      return;
    }
    const load = e.target.closest("[data-rk-load]");
    if (load) airTable(load);
  });
  const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const COUNTRY = { en: { PK: "Pakistan", IN: "India" }, ur: { PK: "پاکستان", IN: "ہندوستان" }, hi: { PK: "पाकिस्तान", IN: "भारत" } };
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
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
  let pending = null;
  function fetchAir() {
    const C = window.HH_RK || [];
    const url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=" + C.map((c) => c[1]).join(",") +
      "&longitude=" + C.map((c) => c[2]).join(",") + "&current=us_aqi,pm2_5,pm10&timezone=GMT";
    return (pending ||= fetch(url).then((r) => (r.ok ? r.json() : Promise.reject(r.status))).then((a) => {
      const list = Array.isArray(a) ? a : [a];
      return C.map((c, i) => ({ c, aqi: list[i] && (aqiNow(list[i].current?.pm2_5, list[i].current?.pm10) ?? list[i].current?.us_aqi), pm: list[i]?.current?.pm2_5 })).filter((x) => x.aqi != null);
    }).catch((err) => { pending = null; throw err; }));
  }
  function airTable(btn) {
    btn.disabled = true;
    const boxes = [...document.querySelectorAll("[data-rk-air]")];
    fetchAir().then((rows) => {
      rows.sort((a, b) => b.aqi - a.aqi);
      for (const box of boxes) {
        const l = box.dataset.lang, th = box.dataset.th.split("|"), nf = new Intl.NumberFormat(LOC[l] || "en-GB", { maximumFractionDigits: 0 });
        box.innerHTML = `<div class="table-wrap"><table><thead><tr><th class="n">#</th><th>${esc(th[0])}</th><th>${esc(th[1])}</th><th class="n">${esc(th[2])}</th><th class="n">${esc(th[3])}</th></tr></thead><tbody>` +
          rows.map((r, i) => `<tr><td class="n">${nf.format(i + 1)}</td><td><a href="/air/${r.c[0]}/">${esc(r.c[3][l] || r.c[3].en)}</a></td><td>${COUNTRY[l][r.c[4]]}</td>` +
            `<td class="n">${nf.format(Math.round(r.aqi))}</td><td class="n">${r.pm == null ? "–" : nf.format(Math.round(r.pm))}</td></tr>`).join("") + "</tbody></table></div>";
      }
    }).catch((err) => {
      console.warn("[hh] rankings air", err);
      for (const box of boxes) {
        const p = document.createElement("p");
        p.className = "muted"; p.textContent = box.dataset.fail;
        box.append(p);
        box.querySelector("[data-rk-load]")?.removeAttribute("disabled");
      }
    });
  }
})();
