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
import importlib.util, json, os

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
  html[lang="ur"] .doc .kicker, html[lang="ur"] .rchart .lab { font-family: var(--urdu); }
  html[lang="ur"] .rfig figcaption, html[lang="ur"] .fact span, html[lang="ur"] .doc caption { font-family: var(--urdu); line-height: 2; }
</style>
"""


def build(slug):
    folder = os.path.join(SRC, slug)
    meta = json.load(open(os.path.join(folder, "meta.json"), encoding="utf-8"))
    arts = {L: open(os.path.join(folder, f"article.{L}.html"), encoding="utf-8").read().rstrip() for L in bp.LANGS}
    path, url = f"/report/{slug}/", f"{bp.SITE}/report/{slug}/"
    jsonld = {"@context": "https://schema.org", "@type": "Report", "@id": f"{url}#report", "name": meta["title"],
              "headline": meta["title"], "url": url, "datePublished": meta["date_published"],
              "inLanguage": list(bp.LANGS), "author": AUTHOR, "publisher": bp.ORG,
              "isPartOf": {"@id": f"{bp.SITE}/#website"}, "abstract": meta["abstract"],
              "isBasedOn": {"@type": "Dataset", "name": f"Evidence for \"{meta['title']}\"", "url": f"{url}data.json",
                            "license": "https://creativecommons.org/licenses/by/4.0/"}}
    out = bp.page(path, meta["title"], meta["description"], arts, jsonld, extra_head=CSS, wide=True,
                  og_alt=meta["description"])
    os.makedirs(os.path.join(bp.PUB, "report", slug), exist_ok=True)
    open(os.path.join(bp.PUB, "report", slug, "index.html"), "w", encoding="utf-8").write(out)
    print(f"report written: {path}")


def main():
    for slug in sorted(os.listdir(SRC)):
        if os.path.isfile(os.path.join(SRC, slug, "meta.json")):
            build(slug)


if __name__ == "__main__":
    main()
