#!/usr/bin/env python3
"""Build the report pages written by HamariHawa's research agent (agentville) and approved by a person.

Each report is a folder scripts/reports/<slug>/ holding the article body in the site's report markup, one
file per language (article.en.html, article.ur.html, article.hi.html), and meta.json (title, description,
date, abstract, translations). Its data file, with the evidence behind every number, is
site/public/report/<slug>/data.json. This only puts the articles into the site's page shell, like
build-report-punjabs.py does for Two Punjabs.

Usage: python3.12 -I scripts/build-reports.py
Writes site/public/report/<slug>/index.html for every folder. Then run build-pages.py (reports list, sitemap).
"""
import html, importlib.util, json, os, re
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("build_pages", os.path.join(HERE, "build-pages.py"))
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)

SRC = os.path.join(HERE, "reports")
AUTHOR = {"@type": "Person", "@id": "https://hammadtariq.com/#me", "name": "Hammad Tariq", "url": "https://hammadtariq.com/"}

# The report markup's styles: Two Punjabs' (build-report-punjabs.py), plus table captions, the chart legend
# and Urdu type for chart labels, captions and key-number labels.
CSS = """<style>
  .doc .kicker { font-family: var(--hand); color: var(--fire); font-size: 16px; margin-bottom: 4px; }
  .facts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 22px 0 26px; }
  .fact { padding: 14px 14px 12px; }
  .fact b { display: block; font-family: var(--hand); font-size: 34px; line-height: 1.1; color: var(--fire); }
  .fact span { display: block; font-size: 13.5px; color: var(--ink-2); line-height: 1.35; margin-top: 4px; }
  .fact b[dir="ltr"] { unicode-bidi: isolate; }
  @media (max-width: 760px) { .facts { grid-template-columns: repeat(2, 1fr); } }
  .rfig { margin: 18px 0 8px; }
  .rfig figcaption { font-size: 14px; color: var(--ink-2); margin-bottom: 4px; }
  .rchart { display: block; width: 100%; height: auto; overflow: visible; }
  .rchart .grid { stroke: var(--hair); }
  .rchart .tick { font: 13px var(--sans); fill: var(--ink-3); }
  .rchart .lab { font: 700 15px var(--hand); }
  .legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: 13px; color: var(--ink-2); margin-top: 4px; }
  .legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-inline-end: 6px; }
  .doc caption { text-align: start; color: var(--ink-3); font-size: 14px; padding-bottom: 4px; }
  .doc td, .doc th { white-space: nowrap; }
  .doc td:first-child, .doc th:first-child { white-space: normal; }
  .doc table.guide td, .doc table.guide th { white-space: normal; vertical-align: top; min-width: 8.5em; font-size: 14.5px; line-height: 1.4; }
  .doc table.guide td:first-child { min-width: 7em; }
  .doc p.note { font-size: 14px; color: var(--ink-2); }
  @media (max-width: 640px) {
    .doc table.guide, .doc table.guide tbody, .doc table.guide tr, .doc table.guide td { display: block; min-width: 0; }
    .doc table.guide thead { display: none; }
    .doc table.guide caption { display: block; width: auto; }
    .doc table.guide tr { padding: 10px 0; border-top: 1px solid var(--hair); }
    .doc table.guide td { border: 0; padding: 3px 0; }
    .doc table.guide td:first-child { font-size: 16px; }
    .doc table.guide td + td::before { content: attr(data-l); display: block; font-size: 12.5px; color: var(--ink-3); }
  }
  .rshare { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 14px 0 18px; }
  .rshare span { flex: none; min-width: 0; font-size: 14px; color: var(--ink-3); margin-inline-end: 2px; }
  .doc .rshare a, .rshare button { display: inline-block; flex: none; margin: 0; line-height: 1.4; border: 1.5px solid var(--line); background: var(--bg); border-radius: 99px; padding: 5px 14px; font: 600 14px var(--sans); text-decoration: none; cursor: pointer; color: var(--ink); }
  .doc .rshare a.wa { background: #1f9d55; border-color: #1f9d55; color: #fff; }
  html[lang="ur"] .rshare span, html[lang="ur"] .rshare a, html[lang="ur"] .rshare button { font-family: var(--urdu); }
  @media print { .rshare { display: none; } }
  html[lang="ur"] .doc .kicker, html[lang="ur"] .rchart .lab { font-family: var(--urdu); }
  html[lang="ur"] .rfig figcaption, html[lang="ur"] .fact span, html[lang="ur"] .doc caption { font-family: var(--urdu); line-height: 2; }
</style>
<script>
document.addEventListener("click", async (e) => {
  const b = e.target.closest && e.target.closest("[data-copy]");
  if (!b) return;
  const was = b.textContent;
  try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = b.dataset.done; } catch { b.textContent = b.dataset.copy; return; }
  setTimeout(() => (b.textContent = was), 2000);
});
</script>
"""

# Share buttons, at the top (under the byline) and at the end of each language's article. The Urdu and
# Hindi links carry ?lang= so whoever opens them lands in that language.
SHARE = {
    "en": {"label": "Share this report", "wa": "WhatsApp", "x": "X", "fb": "Facebook", "copy": "Copy link", "copied": "Link copied"},
    "ur": {"label": "یہ رپورٹ شیئر کریں", "wa": "واٹس ایپ", "x": "X", "fb": "فیس بک", "copy": "لنک کاپی کریں", "copied": "لنک کاپی ہو گیا"},
    "hi": {"label": "यह रिपोर्ट शेयर करें", "wa": "व्हाट्सऐप", "x": "X", "fb": "फ़ेसबुक", "copy": "लिंक कॉपी करें", "copied": "लिंक कॉपी हो गया"},
}


def share_row(L, url, title):
    t, u = SHARE[L], url + ("" if L == "en" else f"?lang={L}")
    a = lambda s: html.escape(s, quote=True)
    return (f'<div class="rshare"><span>{t["label"]}</span>'
            f'<a class="wa" href="https://wa.me/?text={a(quote(f"{title} {u}"))}" target="_blank" rel="noopener">{t["wa"]}</a>'
            f'<a href="https://x.com/intent/post?text={a(quote(title))}&amp;url={a(quote(u, safe=""))}" target="_blank" rel="noopener">{t["x"]}</a>'
            f'<a href="https://www.facebook.com/sharer/sharer.php?u={a(quote(u, safe=""))}" target="_blank" rel="noopener">{t["fb"]}</a>'
            f'<button type="button" data-copy="{a(u)}" data-done="{a(t["copied"])}">{t["copy"]}</button></div>')


def with_share(art, L, url, title):
    row = share_row(L, url, title)
    art, n = re.subn(r'(<p class="byline">.*?</p>)', lambda m: m.group(1) + "\n  " + row, art, count=1)
    assert n == 1, "no byline to put the share row under"
    return art + "\n  " + row


def build(slug):
    folder = os.path.join(SRC, slug)
    meta = json.load(open(os.path.join(folder, "meta.json"), encoding="utf-8"))
    arts = {L: open(os.path.join(folder, f"article.{L}.html"), encoding="utf-8").read().rstrip() for L in bp.LANGS}
    path, url = f"/report/{slug}/", f"{bp.SITE}/report/{slug}/"
    titles = {"en": meta["title"], **{L: meta.get("translations", {}).get(L, {}).get("title") or meta["title"] for L in ("ur", "hi")}}
    arts = {L: with_share(arts[L], L, url, titles[L]) for L in arts}
    jsonld = {"@context": "https://schema.org", "@type": "Report", "@id": f"{url}#report", "name": meta["title"],
              "headline": meta["title"], "url": url, "datePublished": meta["date_published"],
              "inLanguage": list(bp.LANGS), "author": AUTHOR, "publisher": bp.ORG,
              "isPartOf": {"@id": f"{bp.SITE}/#website"}, "abstract": meta["abstract"],
              "isBasedOn": {"@type": "Dataset", "name": f"Evidence for \"{meta['title']}\"", "url": f"{url}data.json",
                            "license": "https://creativecommons.org/licenses/by/4.0/"}}
    out = bp.page(path, meta["title"], meta["description"], arts, jsonld, extra_head=CSS, wide=True,
                  og_alt=meta["description"],
                  **({"og_image": meta["og_image"]} if meta.get("og_image") else {}))
    os.makedirs(os.path.join(bp.PUB, "report", slug), exist_ok=True)
    open(os.path.join(bp.PUB, "report", slug, "index.html"), "w", encoding="utf-8").write(out)
    print(f"report written: {path}")


def main():
    for slug in sorted(os.listdir(SRC)):
        if os.path.isfile(os.path.join(SRC, slug, "meta.json")):
            build(slug)


if __name__ == "__main__":
    main()
