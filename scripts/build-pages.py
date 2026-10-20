#!/usr/bin/env python3
"""Build the "Use the data" page, the "Fire trends" page and the rolling "Updates" page (plus its Atom feed).

To post an update: add an entry at the top of site/public/updates/updates.json
(id, date, title and body in en/ur/hi; body is HTML), then run this script and deploy.
The data and trends page text lives in scripts/pages/{data,trends}-{en,ur,hi}.html; the trends
charts are drawn by site/public/trends/trends.js into the [data-chart] placeholders.

Usage: python3 -I scripts/build-pages.py
Writes site/public/data/index.html, site/public/trends/index.html, site/public/updates/index.html,
site/public/updates/feed.xml.
"""
import html, json, os, re
from datetime import date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PUB = os.path.join(ROOT, "site", "public")
SITE = "https://hamarihawa.org"
CSS_V = re.search(r"app\.css\?v=(\d+)", open(os.path.join(PUB, "index.html")).read()).group(1)
LANGS = ("en", "ur", "hi")
MONTHS = {
    "en": "January February March April May June July August September October November December".split(),
    "ur": "جنوری فروری مارچ اپریل مئی جون جولائی اگست ستمبر اکتوبر نومبر دسمبر".split(),
    "hi": "जनवरी फ़रवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर अक्टूबर नवंबर दिसंबर".split(),
}
NAV = [("/", "map", "Live map", "تازہ نقشہ", "लाइव नक्शा"), ("/sites/", "sites", "Pollution sites", "آلودگی کے مقامات", "प्रदूषण के ठिकाने"),
       ("/trends/", "trends", "Fire trends", "آگ کا رجحان", "आग का रुझान"), ("/about/", "about", "About", "تعارف", "परिचय")]
FOOT = {
    "en": '<a href="/">← Back to the live map</a> · <a href="/data/">Use the data</a> · <a href="/updates/">Updates</a> · <a href="/about/">About</a>',
    "ur": '<a href="/">تازہ نقشے پر واپس →</a> · <a href="/data/">ڈیٹا استعمال کریں</a> · <a href="/updates/">نیا کیا ہے</a> · <a href="/about/">تعارف</a>',
    "hi": '<a href="/">← लाइव नक्शे पर वापस</a> · <a href="/data/">डेटा इस्तेमाल करें</a> · <a href="/updates/">नया क्या है</a> · <a href="/about/">परिचय</a>',
}


def fmt_date(iso, lang):
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[lang][d.month - 1]} {d.year}"


def page(path, title, desc, articles, jsonld, extra_head="", scripts="", wide=False):
    url = f"{SITE}{path}"
    t, dsc = html.escape(title), html.escape(desc)
    nav = "\n".join(f'    <a href="{h}" data-nav="{k}"{' aria-current="page"' if h == path else ""} data-en="{en}" data-ur="{ur}" data-hi="{hi}">{en}</a>'
                     for h, k, en, ur, hi in NAV)
    arts = "\n".join(f'<article data-lang="{l}"{"" if l == "en" else " hidden"}>\n{articles[l]}\n  <p class="foot-links">{FOOT[l]}</p>\n</article>'
                     for l in LANGS)
    return f"""<!doctype html>
<html lang="en" dir="ltr">
<head>
<!-- Google tag (gtag.js), only on the real site so local and preview traffic isn't counted -->
<script>
  if (location.hostname === "hamarihawa.org") {{
    var s = document.createElement("script");
    s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=G-JQFHSTFN9H";
    document.head.appendChild(s);
  }}
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-JQFHSTFN9H');
</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t} · HamariHawa</title>
<meta name="description" content="{dsc}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{url}?lang=en">
<link rel="alternate" hreflang="ur" href="{url}?lang=ur">
<link rel="alternate" hreflang="hi" href="{url}?lang=hi">
<link rel="alternate" hreflang="x-default" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{t} · HamariHawa">
<meta property="og:description" content="{dsc}">
<meta property="og:site_name" content="HamariHawa">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og/map-v2.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="HamariHawa: live fire and air map of Pakistan and North India">
<meta property="og:locale" content="en_GB">
<meta property="og:locale:alternate" content="ur_PK">
<meta property="og:locale:alternate" content="hi_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@hammadtariq">
<meta name="twitter:title" content="{t} · HamariHawa">
<meta name="twitter:description" content="{dsc}">
<meta name="twitter:image" content="{SITE}/og/map-v2.png">
<meta name="twitter:image:alt" content="HamariHawa: live fire and air map of Pakistan and North India">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="alternate" type="application/atom+xml" title="HamariHawa updates" href="/updates/feed.xml">
{extra_head}<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=1)}
</script>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M16 3c2 6 9 9 9 17a9 9 0 0 1-18 0c0-5 3-7 4-11 1 3 2 4 3 4 0-4 0-7 2-10z' fill='none' stroke='%23d62d20' stroke-width='2.4' stroke-linejoin='round'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&family=Inter:wght@400;500;600&family=Noto+Nastaliq+Urdu:wght@400;600&display=swap">
<link rel="stylesheet" href="/app.css?v={CSS_V}">
<style>
  .doc {{ max-width: 760px; margin: 0 auto; padding: 36px 20px 60px; }}
  .doc h1 {{ font-family: var(--hand); font-size: clamp(32px, 5vw, 44px); }}
  .doc h2 {{ font-size: 23px; margin: 34px 0 8px; }}
  .doc h3 {{ font-size: 18px; margin: 20px 0 6px; }}
  .doc p, .doc li {{ color: var(--ink-2); font-size: 16.5px; line-height: 1.65; }}
  .doc p + p {{ margin-top: 10px; }}
  .doc ul, .doc ol {{ padding-inline-start: 22px; margin: 8px 0; }}
  .doc li + li {{ margin-top: 6px; }}
  .doc code {{ font-size: 14px; background: #f4f2ec; padding: 1px 5px; border-radius: 4px; overflow-wrap: anywhere; }}
  .doc.wide {{ max-width: 980px; }}
  .doc .lede {{ font-size: 18px; color: var(--ink); margin-top: 8px; }}
  .doc .callout {{ padding: 16px 20px; margin: 22px 0; }}
  .doc .callout p {{ color: var(--ink); }}
  .doc .entry {{ padding: 18px 0; border-top: 1px dashed var(--hair); }}
  .doc .entry time {{ font-family: var(--hand); color: var(--ink-3); font-size: 15px; }}
  .doc .entry h2 {{ margin: 2px 0 6px; font-size: 21px; }}
  .doc .entry h2 a {{ color: inherit; text-decoration: none; }}
  .doc .foot-links {{ margin-top: 40px; font-size: 14px; }}
  .doc table {{ border-collapse: collapse; width: 100%; font-size: 14.5px; margin: 10px 0; }}
  .doc th, .doc td {{ text-align: start; padding: 6px 8px; border-bottom: 1px solid var(--hair); vertical-align: top; color: var(--ink-2); }}
  .doc .table-wrap {{ overflow-x: auto; }}
  article[hidden] {{ display: none; }}
  html[lang="ur"] .doc p, html[lang="ur"] .doc li, html[lang="ur"] .doc td {{ line-height: 2.2; font-size: 15.5px; }}
  html[lang="ur"] .doc h1, html[lang="ur"] .doc h2, html[lang="ur"] .doc h3 {{ font-family: var(--urdu); line-height: 1.9; }}
  @media (max-width: 860px) {{ .doc {{ padding: 24px 16px 48px; }} }}
</style>
</head>
<body>
<header class="top">
  <a class="brand" href="/" aria-label="HamariHawa home">
    <span class="mark" aria-hidden="true"><svg viewBox="0 0 32 32" width="30" height="30"><path d="M16 3c2 6 9 9 9 17a9 9 0 0 1-18 0c0-5 3-7 4-11 1 3 2 4 3 4 0-4 0-7 2-10z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M5 24c4-2 7 2 11 0s7-2 11 0" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg></span>
    <span class="word">HamariHawa</span>
  </a>
  <nav class="menu" aria-label="Pages">
{nav}
  </nav>
  <div class="top-right">
    <div class="lang" role="group" aria-label="Language">
      <button data-lang="en">EN</button><button data-lang="ur" lang="ur">اردو</button><button data-lang="hi" lang="hi">हिन्दी</button>
    </div>
  </div>
</header>

<main class="doc{" wide" if wide else ""}">
{arts}
</main>

<script src="https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.js"></script>
<script>
(() => {{
  let lang = "en";
  try {{ lang = localStorage.getItem("hh-lang") || "en"; }} catch {{}}
  const qLang = new URLSearchParams(location.search).get("lang");
  if (qLang) lang = qLang;
  if (!["en", "ur", "hi"].includes(lang)) lang = "en";
  function apply() {{
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ur" ? "rtl" : "ltr";
    document.querySelectorAll("article[data-lang]").forEach((a) => {{ a.hidden = a.dataset.lang !== lang; }});
    document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));
    document.querySelectorAll("[data-en]").forEach((el) => {{ el.textContent = el.dataset[lang] || el.dataset.en; }});
    sketch();
    dispatchEvent(new CustomEvent("hh:lang", {{ detail: lang }}));
  }}
  function sketch() {{
    if (!window.rough) return;
    document.querySelectorAll("article:not([hidden]) .sketch").forEach((el) => {{
      const w = el.clientWidth, h = el.clientHeight;
      el.querySelector("svg.rough")?.remove();
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("class", "rough"); svg.setAttribute("viewBox", `0 0 ${{w}} ${{h}}`);
      svg.appendChild(rough.svg(svg).rectangle(1.5, 1.5, w - 3, h - 3, {{ roughness: 1, bowing: 0.8, stroke: "#2b2b2b", strokeWidth: 1.1, seed: 5 }}));
      el.appendChild(svg);
    }});
  }}
  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {{
    lang = b.dataset.lang;
    try {{ localStorage.setItem("hh-lang", lang); }} catch {{}}
    apply();
  }}));
  addEventListener("resize", sketch);
  if (!window.rough) document.documentElement.classList.add("no-rough");
  apply();
}})();
</script>
{scripts}</body>
</html>
"""


ORG = {"@id": f"{SITE}/#org"}


def updates():
    entries = json.load(open(os.path.join(PUB, "updates", "updates.json"), encoding="utf-8"))
    entries.sort(key=lambda e: e["date"], reverse=True)
    head = {
        "en": ("What's new", "Everything we add or fix on HamariHawa, newest first. Follow along with the <a href=\"/updates/feed.xml\">feed</a>."),
        "ur": ("نیا کیا ہے", "ہماری ہوا میں جو کچھ شامل یا درست ہوتا ہے، تازہ ترین سب سے پہلے۔ <a href=\"/updates/feed.xml\">فیڈ</a> سے باخبر رہیں۔"),
        "hi": ("नया क्या है", "हमारी हवा में जो भी जुड़ता या ठीक होता है, सबसे नया सबसे पहले। <a href=\"/updates/feed.xml\">फ़ीड</a> से जुड़े रहें।"),
    }
    arts = {}
    for l in LANGS:
        items = "\n".join(
            f'  <section class="entry" id="{e["id"]}"><time datetime="{e["date"]}">{fmt_date(e["date"], l)}</time>'
            f'<h2><a href="#{e["id"]}">{html.escape(e["title"][l])}</a></h2>{e["body"][l]}</section>' for e in entries)
        arts[l] = f'  <h1>{head[l][0]}</h1>\n  <p class="lede">{head[l][1]}</p>\n{items}'
    plain = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()
    jsonld = {"@context": "https://schema.org", "@type": "Blog", "@id": f"{SITE}/updates/#blog", "name": "HamariHawa updates",
              "url": f"{SITE}/updates/", "inLanguage": ["en", "ur", "hi"], "publisher": ORG,
              "blogPost": [{"@type": "BlogPosting", "headline": e["title"]["en"], "datePublished": e["date"],
                            "url": f"{SITE}/updates/#{e['id']}", "description": plain(e["body"]["en"])[:300],
                            "author": ORG, "publisher": ORG, "image": f"{SITE}/og/map-v2.png"} for e in entries]}
    out = page("/updates/", "What's new", "Updates to HamariHawa, the live satellite fire and air map of Pakistan and North India: new layers, data and fixes, newest first.",
               arts, jsonld)
    open(os.path.join(PUB, "updates", "index.html"), "w", encoding="utf-8").write(out)
    # Atom feed (English).
    feed = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom">',
            "<title>HamariHawa updates</title>", f'<link href="{SITE}/updates/"/>', f'<link rel="self" href="{SITE}/updates/feed.xml"/>',
            f"<id>{SITE}/updates/</id>", f"<updated>{entries[0]['date']}T00:00:00Z</updated>", "<author><name>HamariHawa</name></author>"]
    for e in entries:
        feed.append(f"<entry><title>{html.escape(e['title']['en'])}</title><link href=\"{SITE}/updates/#{e['id']}\"/>"
                    f"<id>{SITE}/updates/#{e['id']}</id><updated>{e['date']}T00:00:00Z</updated>"
                    f"<content type=\"html\">{html.escape(e['body']['en'].replace('href=\"/', f'href=\"{SITE}/'))}</content></entry>")
    feed.append("</feed>")
    open(os.path.join(PUB, "updates", "feed.xml"), "w", encoding="utf-8").write("\n".join(feed))
    print(f"updates: {len(entries)} entries")
    return entries[0]["date"]


def data_page():
    arts = {l: open(os.path.join(ROOT, "scripts", "pages", f"data-{l}.html"), encoding="utf-8").read().strip() for l in LANGS}
    jsonld = {"@context": "https://schema.org", "@type": "WebPage", "@id": f"{SITE}/data/#page", "name": "Use HamariHawa's data",
              "url": f"{SITE}/data/", "inLanguage": ["en", "ur", "hi"], "publisher": ORG, "isPartOf": {"@id": f"{SITE}/#website"},
              "about": ["Google Earth KML feed of fires and air pollution in Pakistan and North India", "Open air-quality data APIs"]}
    out = page("/data/", "Use the data", "Open HamariHawa's live fires, city air, traffic NO₂, haze and pollution sites in Google Earth, QGIS, ArcGIS or Civil 3D, or use the JSON feeds. Why Google Maps can't show live layers, and the licence for each dataset.",
               arts, jsonld)
    open(os.path.join(PUB, "data", "index.html"), "w", encoding="utf-8").write(out)
    print("data page written")


def trends_page():
    arts = {l: open(os.path.join(ROOT, "scripts", "pages", f"trends-{l}.html"), encoding="utf-8").read().strip() for l in LANGS}
    js_v = int(os.path.getmtime(os.path.join(PUB, "trends", "trends.js")))
    jsonld = {"@context": "https://schema.org", "@type": "WebPage", "@id": f"{SITE}/trends/#page",
              "name": "Crop fire trends in Pakistan and North India since 2019", "url": f"{SITE}/trends/",
              "inLanguage": ["en", "ur", "hi"], "publisher": ORG, "isPartOf": {"@id": f"{SITE}/#website"},
              "about": ["Crop residue burning in Punjab and Haryana", "Satellite fire counts by season, district, day and night"],
              "mainEntity": {"@type": "Dataset", "name": "HamariHawa daily fire archive",
                             "description": "Daily counts of satellite fire spots over Pakistan and North India (25-35.5 N, 66-88.5 E) from NASA FIRMS, "
                                            "October-November 2019 onwards and every day since 1 October 2026, split by country, day/night pass and district.",
                             "url": f"{SITE}/trends/", "license": "https://creativecommons.org/licenses/by/4.0/",
                             "creator": ORG, "temporalCoverage": "2019-10-01/..",
                             "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{SITE}/api/days"},
                                              {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{SITE}/api/districts"}]}}
    head = ('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">\n'
            f'<link rel="stylesheet" href="/trends/trends.css?v={js_v}">\n')
    scripts = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>\n'
               f'<script src="/trends/trends.js?v={js_v}"></script>\n')
    out = page("/trends/", "Fire trends", "How crop burning in Pakistan and North India has changed since 2019: every October-November season compared, "
               "this year against last, where in Punjab and Haryana the fires move, and the day and night satellite passes. From NASA FIRMS data.",
               arts, jsonld, extra_head=head, scripts=scripts, wide=True)
    open(os.path.join(PUB, "trends", "index.html"), "w", encoding="utf-8").write(out)
    print("trends page written")


if __name__ == "__main__":
    data_page()
    trends_page()
    updates()
