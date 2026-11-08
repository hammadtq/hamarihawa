// City search: a search button in the header of every page, and an always-open box wherever a page has
// [data-city-search]. Matches English, Urdu and Hindi names (and the URL id), prefix matches first.
// The city list comes from /cities.js (window.HH_CITIES), loaded on first use if the page hasn't already.
(() => {
  const T = {
    en: { btn: "Search a city", ph: "Search a city…", none: "No city by that name.", all: "See all cities", pk: "Pakistan", in: "India" },
    ur: { btn: "شہر تلاش کریں", ph: "شہر تلاش کریں…", none: "اس نام کا کوئی شہر نہیں ملا۔", all: "تمام شہر دیکھیں", pk: "پاکستان", in: "بھارت" },
    hi: { btn: "शहर खोजें", ph: "शहर खोजें…", none: "इस नाम का कोई शहर नहीं मिला।", all: "सभी शहर देखें", pk: "पाकिस्तान", in: "भारत" },
  };
  const CSS = `
.cs { position: relative; display: flex; align-items: center; }
.cs .cs-ic { position: absolute; inset-inline-start: 10px; color: var(--ink-3, #7c7c80); display: grid; pointer-events: none; }
.cs input { width: 100%; font: inherit; font-size: 15px; line-height: 1.4; padding: 7px 12px; padding-inline-start: 36px; border: 1.3px solid var(--line, #2b2b2b); border-radius: 18px 14px 16px 12px; background: var(--bg, #fff); color: var(--ink, #1d1d1f); }
.cs input::-webkit-search-cancel-button { cursor: pointer; }
html[lang="ur"] .cs input { font-family: var(--urdu); font-size: 14px; line-height: 1.9; padding-top: 3px; padding-bottom: 3px; }
.cs-list { position: absolute; top: calc(100% + 4px); inset-inline: 0; z-index: 1001; margin: 0; padding: 4px; list-style: none; background: var(--bg, #fff); border: 1.3px solid var(--line, #2b2b2b); border-radius: 10px; box-shadow: 3px 4px 0 var(--hair, #e6e3dc); max-height: min(360px, 60vh); overflow-y: auto; }
.cs-list li a { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; padding: 7px 10px; border-radius: 7px; text-decoration: none; }
.cs-list li[aria-selected="true"] a { background: #f4f2ec; }
.cs-list li b { font-weight: 600; }
.cs-list li span { color: var(--ink-3, #7c7c80); font-size: 12.5px; white-space: nowrap; }
.cs-list .cs-none { padding: 8px 10px; color: var(--ink-2, #4a4a4c); font-size: 14px; }
.cs-head { position: relative; display: flex; }
.cs-btn { background: none; border: 1.3px solid var(--line, #2b2b2b); border-radius: 50%; width: 32px; height: 32px; display: grid; place-items: center; cursor: pointer; padding: 0; color: var(--ink, #1d1d1f); }
.cs-btn[aria-expanded="true"] { background: var(--ink, #1d1d1f); color: #fff; }
.cs-pop { position: absolute; top: calc(100% + 8px); inset-inline-end: 0; z-index: 1000; width: min(320px, calc(100vw - 32px)); }
.cs-pop[hidden] { display: none; }
.cp-find { max-width: 300px; margin: 0 0 10px; margin-inline-start: auto; }
@media (max-width: 860px) { .cp-find { max-width: none; } .cs-pop { position: fixed; top: 56px; inset-inline: 16px; width: auto; } }
`;
  const st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);
  const lang = () => (T[document.documentElement.lang] ? document.documentElement.lang : "en");
  const ICON = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

  // Fold case, accents, Hindi nukta and Arabic-script letter variants so "Multan", "multān", "ملتان" all match.
  const fold = (s) => String(s).toLowerCase().normalize("NFD").replace(/[̀-़ًͯ-ٰٟ]/g, "")
    .replace(/[يى]/g, "ی").replace(/ك/g, "ک").replace(/[ةه]/g, "ہ").replace(/[()\-.,]/g, " ").replace(/\s+/g, " ").trim();

  let list = null, loading = null;
  function cities() {
    if (list) return Promise.resolve(list);
    const build = () => (list = (window.HH_CITIES || []).map((c) => ({ c, keys: [c.id.replace(/-/g, " "), c.name.en, c.name.ur, c.name.hi].map(fold) })));
    if (window.HH_CITIES) return Promise.resolve(build());
    return (loading ||= new Promise((res) => {
      const s = document.createElement("script");
      s.src = "/cities.js?v=202610260000"; s.onload = () => res(build()); s.onerror = () => res((list = []));
      document.head.appendChild(s);
    }));
  }
  function match(q) {
    q = fold(q);
    if (!q) return [];
    const out = [];
    for (const r of list) {
      let best = 9;
      for (const k of r.keys) {
        if (k.startsWith(q)) best = Math.min(best, 0);
        else if (k.split(" ").some((w) => w.startsWith(q))) best = Math.min(best, 1);
        else if (k.includes(q)) best = Math.min(best, 2);
      }
      if (best < 9) out.push([best, -r.c.pop, r.c]);
    }
    return out.sort((a, b) => a[0] - b[0] || a[1] - b[1]).slice(0, 8).map((x) => x[2]);
  }

  // One search box: an input and a listbox under it. Arrow keys move, Enter opens, Escape clears/closes.
  let uid = 0;
  function box(root, { onClose } = {}) {
    const id = "cs-" + ++uid;
    root.classList.add("cs");
    root.innerHTML = `<span class="cs-ic">${ICON}</span><input type="search" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="${id}" autocomplete="off" spellcheck="false" enterkeyhint="go"><ul class="cs-list" id="${id}" role="listbox" hidden></ul>`;
    const inp = root.querySelector("input"), ul = root.querySelector("ul");
    let items = [], sel = -1;
    const label = () => { const t = T[lang()]; inp.placeholder = t.ph; inp.setAttribute("aria-label", t.btn); };
    label(); addEventListener("hh:lang", label);
    const go = (c) => { location.href = `/air/${c.id}/`; };
    const paint = (scroll) => {
      ul.querySelectorAll("li").forEach((li, i) => { li.setAttribute("aria-selected", i === sel); if (scroll && i === sel) li.scrollIntoView({ block: "nearest" }); });
      inp.setAttribute("aria-activedescendant", sel >= 0 ? `${id}-${sel}` : "");
    };
    const render = async () => {
      await cities();
      const l = lang(), t = T[l], q = inp.value;
      items = match(q); sel = items.length ? 0 : -1;
      if (!q.trim()) { ul.hidden = true; inp.setAttribute("aria-expanded", "false"); return; }
      ul.innerHTML = items.length
        ? items.map((c, i) => {
            const other = l === "en" ? c.name.ur : c.name.en;
            return `<li id="${id}-${i}" role="option"><a href="/air/${c.id}/"><b>${c.name[l] || c.name.en}</b><span>${other} · ${c.cc === "PK" ? t.pk : t.in}</span></a></li>`;
          }).join("")
        : `<li class="cs-none" role="presentation">${t.none} <a href="/air/">${t.all}</a></li>`;
      ul.hidden = false; inp.setAttribute("aria-expanded", "true"); paint();
    };
    inp.addEventListener("input", render);
    inp.addEventListener("focus", () => { cities(); if (inp.value) render(); });
    inp.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        if (!items.length) return;
        e.preventDefault(); sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length; paint(true);
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (sel >= 0 && items[sel]) go(items[sel]);
        else if (inp.value.trim()) render().then(() => items[0] && go(items[0])); // list still loading
      } else if (e.key === "Escape") {
        if (inp.value) { inp.value = ""; render(); } else onClose?.();
      }
    });
    ul.addEventListener("mousemove", (e) => { const li = e.target.closest("li[role=option]"); if (li) { sel = [...ul.children].indexOf(li); paint(); } });
    document.addEventListener("click", (e) => { if (!root.contains(e.target)) { ul.hidden = true; inp.setAttribute("aria-expanded", "false"); } });
    return inp;
  }

  // The header button: opens a small panel holding a box.
  // Pages with their own box (city pages) don't get a second one in the header.
  const right = document.querySelector("header.top .top-right");
  if (right && !right.querySelector(".cs-btn") && !document.querySelector("[data-city-search]")) {
    const wrap = document.createElement("div");
    wrap.className = "cs-head";
    wrap.innerHTML = `<button type="button" class="cs-btn" aria-expanded="false">${ICON}</button><div class="cs-pop" hidden></div>`;
    const btn = wrap.querySelector("button"), pop = wrap.querySelector(".cs-pop");
    const label = () => { const t = T[lang()].btn; btn.title = t; btn.setAttribute("aria-label", t); };
    label(); addEventListener("hh:lang", label);
    const close = () => { pop.hidden = true; btn.setAttribute("aria-expanded", "false"); btn.focus(); };
    const inp = box(pop, { onClose: close });
    btn.addEventListener("click", () => {
      const open = pop.hidden;
      pop.hidden = !open; btn.setAttribute("aria-expanded", String(open));
      if (open) inp.focus();
    });
    document.addEventListener("click", (e) => { if (!pop.hidden && !wrap.contains(e.target)) { pop.hidden = true; btn.setAttribute("aria-expanded", "false"); } });
    right.insertBefore(wrap, right.querySelector(".lang") || null);
  }
  document.querySelectorAll("[data-city-search]").forEach((el) => box(el));

  // "/" focuses search, as on most sites, unless the visitor is typing somewhere.
  addEventListener("keydown", (e) => {
    if (e.key !== "/" || e.ctrlKey || e.metaKey || /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName) || document.activeElement?.isContentEditable) return;
    const inline = document.querySelector("article:not([hidden]) [data-city-search] input");
    if (inline) { e.preventDefault(); inline.focus(); return; }
    const b = document.querySelector(".cs-btn");
    if (b) { e.preventDefault(); b.click(); }
  });
})();
