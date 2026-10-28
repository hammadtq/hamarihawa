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
  let pending = null;
  function fetchAir() {
    const C = window.HH_RK || [];
    const url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=" + C.map((c) => c[1]).join(",") +
      "&longitude=" + C.map((c) => c[2]).join(",") + "&current=us_aqi,pm2_5&timezone=GMT";
    return (pending ||= fetch(url).then((r) => (r.ok ? r.json() : Promise.reject(r.status))).then((a) => {
      const list = Array.isArray(a) ? a : [a];
      return C.map((c, i) => ({ c, aqi: list[i]?.current?.us_aqi, pm: list[i]?.current?.pm2_5 })).filter((x) => x.aqi != null);
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
