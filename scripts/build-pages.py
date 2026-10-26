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
NAV = [("/", "map", "Live map", "تازہ نقشہ", "लाइव नक्शा"), ("/air/", "air", "City air", "شہروں کی ہوا", "शहरों की हवा"), ("/sites/", "sites", "Pollution sites", "آلودگی کے مقامات", "प्रदूषण के ठिकाने"),
       ("/trends/", "trends", "Fire trends", "آگ کا رجحان", "आग का रुझान"), ("/reports/", "reports", "Reports", "رپورٹس", "रिपोर्ट"),
       ("/about/", "about", "About", "تعارف", "परिचय")]
FOOT = {
    "en": '<a href="/">← Back to the live map</a> · <a href="/fires/">Daily fires</a> · <a href="/data/">Use the data</a> · <a href="/updates/">Updates</a> · <a href="/about/">About</a> · <a href="https://github.com/hammadtq/hamarihawa">GitHub</a>',
    "ur": '<a href="/">تازہ نقشے پر واپس →</a> · <a href="/fires/">روزانہ آگ</a> · <a href="/data/">ڈیٹا استعمال کریں</a> · <a href="/updates/">نیا کیا ہے</a> · <a href="/about/">تعارف</a> · <a href="https://github.com/hammadtq/hamarihawa">GitHub</a>',
    "hi": '<a href="/">← लाइव नक्शे पर वापस</a> · <a href="/fires/">रोज़ की आग</a> · <a href="/data/">डेटा इस्तेमाल करें</a> · <a href="/updates/">नया क्या है</a> · <a href="/about/">परिचय</a> · <a href="https://github.com/hammadtq/hamarihawa">GitHub</a>',
}


def fmt_date(iso, lang):
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[lang][d.month - 1]} {d.year}"


def page(path, title, desc, articles, jsonld, extra_head="", scripts="", wide=False,
         og_image="/og/map-v3.png", og_alt="HamariHawa: live fire and air map of Pakistan and India", current=None):
    url = f"{SITE}{path}"
    t, dsc = html.escape(title), html.escape(desc)
    on = lambda h, k: k == current if current else h == path or (k == "reports" and path.startswith("/report"))
    nav = "\n".join(f'    <a href="{h}" data-nav="{k}"{' aria-current="page"' if on(h, k) else ""} data-en="{en}" data-ur="{ur}" data-hi="{hi}">{en}</a>'
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
<meta property="og:type" content="website">
<meta property="og:title" content="{t} · HamariHawa">
<meta property="og:description" content="{dsc}">
<meta property="og:site_name" content="HamariHawa">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{html.escape(og_alt)}">
<meta property="og:locale" content="en_GB">
<meta property="og:locale:alternate" content="ur_PK">
<meta property="og:locale:alternate" content="hi_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@hammadtariq">
<meta name="twitter:title" content="{t} · HamariHawa">
<meta name="twitter:description" content="{dsc}">
<meta name="twitter:image" content="{SITE}{og_image}">
<meta name="twitter:image:alt" content="{html.escape(og_alt)}">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="alternate" type="application/atom+xml" title="HamariHawa updates" href="/updates/feed.xml">
{extra_head}<script type="application/ld+json">
{jsonld if isinstance(jsonld, str) else json.dumps(jsonld, ensure_ascii=False, indent=1)}
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
    <a class="gh" href="https://github.com/hammadtq/hamarihawa" aria-label="Source code on GitHub" title="Source code on GitHub"><svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg></a>
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


# Written out in full: Google's Dataset check rejects a bare {"@id"} reference as the creator.
ORG = {"@type": "Organization", "@id": f"{SITE}/#org", "name": "HamariHawa", "url": f"{SITE}/"}


def updates():
    entries = json.load(open(os.path.join(PUB, "updates", "updates.json"), encoding="utf-8"))
    entries.sort(key=lambda e: e["date"], reverse=True)
    head = {
        "en": ("What's new", "Everything we add or fix on HamariHawa, newest first. Follow along with the <a href=\"/updates/feed.xml\">feed</a>."),
        "ur": ("نیا کیا ہے", "ہماری ہوا میں جو کچھ بھی شامل یا درست کیا جاتا ہے، وہ یہاں درج ہے، اور تازہ ترین سب سے اوپر ہے۔ <a href=\"/updates/feed.xml\">فیڈ</a> کے ذریعے باخبر رہیں۔"),
        "hi": ("नया क्या है", "हमारी हवा में जो कुछ भी जोड़ा या ठीक किया जाता है, वह यहाँ दर्ज है, सबसे नया सबसे ऊपर। ताज़ा जानकारी के लिए <a href=\"/updates/feed.xml\">फ़ीड</a> से जुड़ें।"),
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
                            "author": ORG, "publisher": ORG, "image": f"{SITE}/og/map-v3.png"} for e in entries]}
    out = page("/updates/", "What's new", "Updates to HamariHawa, the live satellite fire and air map of Pakistan and India: new layers, data and fixes, newest first.",
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
              "about": ["Google Earth KML feed of fires and air pollution in Pakistan and India", "Open air-quality data APIs"]}
    out = page("/data/", "Use the data", "Open HamariHawa's live fires, city air, NO₂, haze and pollution sites in Google Earth, QGIS or ArcGIS, or use the JSON feeds.",
               arts, jsonld)
    open(os.path.join(PUB, "data", "index.html"), "w", encoding="utf-8").write(out)
    print("data page written")


def trends_page():
    arts = {l: open(os.path.join(ROOT, "scripts", "pages", f"trends-{l}.html"), encoding="utf-8").read().strip() for l in LANGS}
    js_v = int(os.path.getmtime(os.path.join(PUB, "trends", "trends.js")))
    jsonld = {"@context": "https://schema.org", "@type": "WebPage", "@id": f"{SITE}/trends/#page",
              "name": "Crop fire trends in Pakistan and India since 2019", "url": f"{SITE}/trends/",
              "inLanguage": ["en", "ur", "hi"], "publisher": ORG, "isPartOf": {"@id": f"{SITE}/#website"},
              "about": ["Crop residue burning in Punjab and Haryana", "Satellite fire counts by season, district, day and night"],
              "mainEntity": {"@type": "Dataset", "name": "HamariHawa daily fire archive",
                             "description": "Daily counts of satellite fire spots over Pakistan and India (and the northern plains, 25-35.5 N, 66-88.5 E, on their own) from NASA FIRMS, "
                                            "October-November 2019 onwards and every day since 1 October 2026, split by country, day/night pass and district.",
                             "url": f"{SITE}/trends/", "license": "https://creativecommons.org/licenses/by/4.0/",
                             "creator": ORG, "temporalCoverage": "2019-10-01/..",
                             "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{SITE}/api/days"},
                                              {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{SITE}/api/districts"}]}}
    head = ('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">\n'
            f'<link rel="stylesheet" href="/trends/trends.css?v={js_v}">\n')
    scripts = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>\n'
               f'<script src="/trends/trends.js?v={js_v}"></script>\n')
    out = page("/trends/", "Fire trends", "Crop burning in Pakistan and India since 2019: every October–November season compared, this year against last, "
               "district by district, from NASA satellite data.",
               arts, jsonld, extra_head=head, scripts=scripts, wide=True)
    open(os.path.join(PUB, "trends", "index.html"), "w", encoding="utf-8").write(out)
    print("trends page written")


REPORTS = [  # newest first: (path, date, title, summary per language)
    ("/report/two-punjabs/", "2026-10-20", "Two Punjabs: seven seasons of crop fires", {
        "en": "Satellite-seen crop fires fell 95% in Indian Punjab since 2021 but not in Pakistani Punjab, which has had more since 2024. Checked against India's official counts, with district tables and why fire counts undercount.",
        "ur": "2021 کے بعد ہندوستانی پنجاب میں سیٹلائٹ کو نظر آنے والی آگ 95% کم ہو گئی، مگر پاکستانی پنجاب میں کم نہیں ہوئی، جہاں 2024 سے ہندوستانی پنجاب سے زیادہ آگ دیکھی جا رہی ہے۔ رپورٹ میں ہندوستان کے سرکاری اعداد سے جانچ، اضلاع کی فہرست، اور یہ وضاحت بھی ہے کہ آگ کی گنتی اصل سے کم کیوں ہوتی ہے۔",
        "hi": "2021 के बाद भारतीय पंजाब में उपग्रह को दिखने वाली आग 95% घट गई, लेकिन पाकिस्तानी पंजाब में नहीं घटी, जहाँ 2024 से ज़्यादा आग दिख रही है। साथ में भारत के सरकारी आँकड़ों से जाँच, ज़िलों की तालिकाएँ, और यह कि आग की गिनती असल से कम क्यों रहती है।"}),
    ("/report/", "2026-09-15", "Lahore & Islamabad Air Ledger", {
        "en": "24 months of PM2.5 and AQI in Lahore and Islamabad side by side: monthly IQAir data, sources, health impact and projections. In English, with a PDF.",
        "ur": "لاہور اور اسلام آباد میں 24 مہینوں کا PM2.5 اور AQI، ایک ساتھ: IQAir کا ماہانہ ڈیٹا، آلودگی کے ذرائع، صحت پر اثر اور آئندہ کے اندازے۔ انگریزی میں، PDF کے ساتھ۔",
        "hi": "लाहौर और इस्लामाबाद के 24 महीनों के PM2.5 और AQI की आमने-सामने तुलना: IQAir का मासिक डेटा, प्रदूषण के स्रोत, सेहत पर असर और आगे के अनुमान। अंग्रेज़ी में, PDF के साथ।"}),
]


def reports_page():
    head = {"en": ("Reports", "Longer pieces built from HamariHawa's data, newest first."),
            "ur": ("رپورٹس", "ہماری ہوا کے ڈیٹا سے تیار کی گئی تفصیلی رپورٹس، تازہ ترین سب سے اوپر۔"),
            "hi": ("रिपोर्ट", "हमारी हवा के डेटा पर आधारित विस्तृत रिपोर्टें, सबसे नई सबसे ऊपर।")}
    arts = {l: f'  <h1>{head[l][0]}</h1>\n  <p class="lede">{head[l][1]}</p>\n' + "\n".join(
        f'  <section class="entry"><time datetime="{d}">{fmt_date(d, l)}</time><h2><a href="{p}">{html.escape(t)}</a></h2><p>{s[l]}</p></section>'
        for p, d, t, s in REPORTS) for l in LANGS}
    jsonld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": f"{SITE}/reports/#page", "name": "HamariHawa reports",
              "url": f"{SITE}/reports/", "inLanguage": ["en", "ur", "hi"], "publisher": ORG,
              "hasPart": [{"@type": "Report", "name": t, "url": f"{SITE}{p}", "datePublished": d} for p, d, t, _ in REPORTS]}
    out = page("/reports/", "Reports", "HamariHawa's reports on air pollution and crop fires in Pakistan and India: Two Punjabs (crop fires 2019-2025) and the Lahore & Islamabad Air Ledger.",
               arts, jsonld)
    os.makedirs(os.path.join(PUB, "reports"), exist_ok=True)
    open(os.path.join(PUB, "reports", "index.html"), "w", encoding="utf-8").write(out)
    print("reports page written")


# The cities with air cards. data/cities.json is the list to edit; this writes the browser's copy
# (site/public/cities.js) and the Worker's (site/src/cities.json, used by the /air/ pages and the KML), adding
# what each city page says about the ground around it: pollution sources within 50 km and the nearest cities.
NEAR_KM = 50


def _km(a, b):
    import math
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def cities():
    cs = json.load(open(os.path.join(ROOT, "data", "cities.json"), encoding="utf-8"))
    src = lambda f: json.load(open(os.path.join(PUB, "sources", f), encoding="utf-8"))["items"]
    kinds = {"kilns": src("kilns.json"), "plants": src("plants.json"), "industry": src("osm-industrial.json"), "landfills": src("osm-landfill.json")}
    worker = []
    for c in cs:
        here = (c["lat"], c["lon"])
        near = {}
        for k, items in kinds.items():
            # A cheap box test first: 50 km is under half a degree everywhere in the region.
            hits = [it for it in items if abs(it[0] - here[0]) < 0.5 and abs(it[1] - here[1]) < 0.6 and _km(here, it) <= NEAR_KM]
            near[k] = len(hits)
            if k == "plants":
                near["plantNames"] = [it[3] for it in sorted(hits, key=lambda it: -float(re.sub(r"[^0-9.]", "", it[4] or "0") or 0)) if it[3]][:3]
        others = sorted((x for x in cs if x["id"] != c["id"]), key=lambda x: _km(here, (x["lat"], x["lon"])))[:4]
        worker.append({**{k: c[k] for k in ("id", "cc", "lat", "lon", "pop", "name")}, "near": near,
                       "nearby": [[x["id"], round(_km(here, (x["lat"], x["lon"])))] for x in others]})
    open(os.path.join(ROOT, "site", "src", "cities.json"), "w", encoding="utf-8").write(
        "[\n" + ",\n".join(json.dumps(w, ensure_ascii=False, separators=(",", ":")) for w in worker) + "\n]\n")
    js = ["// Cities shown in the health section. Generated by scripts/build-pages.py from data/cities.json; edit that file.",
          "// pop: approximate urban population (Pakistan 2023 census city/district figures, Sukkur and Abbottabad estimated;",
          "// India 2026 urban-agglomeration estimates).",
          "// cdr: crude death rate per 1,000 per year (Pakistan ~6.5, World Bank 2023; India 6.8, SRS 2022).",
          "window.HH_CITIES = ["]
    for c in cs:
        n = c["name"]
        js.append(f'  {{ id: "{c["id"]}", cc: "{c["cc"]}", lat: {c["lat"]}, lon: {c["lon"]}, pop: {c["pop"]}, cdr: {c["cdr"]}, '
                  f'name: {{ en: "{n["en"]}", ur: "{n["ur"]}", hi: "{n["hi"]}" }} }},')
    js.append("];")
    open(os.path.join(PUB, "cities.js"), "w", encoding="utf-8").write("\n".join(js) + "\n")
    print(f"cities: {len(cs)}")


def worker_shell():
    """The page shell for pages the Worker renders from KV (daily fires, districts), with @@MARKERS@@
    for it to fill. Written to site/src/shell.html, which the Worker imports as text."""
    out = page("@@PATH@@", "@@TITLE@@", "@@DESC@@", {l: f"@@BODY_{l}@@" for l in LANGS}, "@@JSONLD@@",
               extra_head="@@HEAD@@", scripts="@@SCRIPTS@@", wide=True, current="trends")
    open(os.path.join(ROOT, "site", "src", "shell.html"), "w", encoding="utf-8").write(out)
    print("worker shell written")


# Sitemap: one entry per page, with the date its source last changed in git. The trilingual
# pages carry all three languages in one URL (the toggle is client-side), so there are no
# hreflang alternates: ?lang= URLs would only canonicalise back to the bare URL.
SITEMAP = [  # (path, source files whose last commit dates the page, changefreq, priority, trilingual)
    ("/", ["site/public/index.html", "site/public/app.js", "site/public/i18n.js"], "hourly", "1.0", True),
    ("/sites/", ["site/public/sites/index.html", "site/public/sites/sites.js", "site/public/sources/sites.json"], "daily", "0.9", True),
    ("/trends/", ["scripts/pages/trends-en.html", "site/public/trends/trends.js"], "daily", "0.8", True),
    ("/report/two-punjabs/", ["scripts/build-report-punjabs.py", "site/public/report/two-punjabs/seasons.json"], "monthly", "0.8", True),
    ("/data/", ["scripts/pages/data-en.html"], "monthly", "0.7", True),
    ("/updates/", ["site/public/updates/updates.json"], "weekly", "0.7", True),
    ("/reports/", ["scripts/build-pages.py"], "monthly", "0.6", True),
    ("/about/", ["site/public/about/index.html"], "monthly", "0.6", True),
    ("/report/", ["site/public/report/index.html"], "yearly", "0.5", False),
]


def last_changed(files):
    """Newest commit date (YYYY-MM-DD) among files; today for anything changed but not yet committed."""
    import subprocess
    dates = []
    for f in files:
        dirty = subprocess.run(["git", "status", "--porcelain", "--", f], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if dirty:
            dates.append(date.today().isoformat())
            continue
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", f], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if out:
            dates.append(out)
    return max(dates) if dates else date.today().isoformat()


# The pollution sites directory draws its cards in the browser from sources/sites.json. Without
# them in the HTML, search engines see an almost empty page, so the top cards of each section are
# written in here in English; sites.js replaces them once the data has loaded.
SITES_SECTIONS = [
    ("landfills", "Landfills leaking methane or burning",
     "Rotting rubbish releases methane, a strong greenhouse gas, and dumps often smoulder, adding smoke and toxic fumes for the people living around them.",
     "Methane plumes: Carbon Mapper (satellite and aircraft, 2022–2026). Fires: NASA FIRMS 2025. Names: OpenStreetMap."),
    ("plants", "Power and industrial plants",
     "Coal and gas plants and heavy industry, ranked by the carbon dioxide plume satellites measured. The same chimneys release NO₂ and sulphur dioxide.",
     "CO₂ plumes: Carbon Mapper. Names: OpenStreetMap power plants and industrial estates."),
    ("hot", "Always-hot industrial sites",
     "Places NASA's fire satellites saw hot on many days through the year: gas flares, furnaces, cement and steel works, refineries. Not crop fires, which move with the seasons.",
     "NASA FIRMS VIIRS 2025 archive: spots hot on 20+ days, or flagged by NASA as static land sources."),
    ("kilns", "Brick-kiln belts",
     "Districts with the most brick kilns. Old fixed-chimney kilns burn coal, rubber and waste and are among the dirtiest sources near cities; zigzag kilns cut smoke sharply. The kiln survey covers the Indo-Gangetic plain, from Pakistani Punjab to Bangladesh, so kilns elsewhere in Pakistan and India aren't counted.",
     "Kiln locations: SentinelKilnDB (IIT Gandhinagar) and the Pakistan IGP kiln dataset, from Sentinel-2 images. PM2.5 estimates: Pakistan dataset, firing season."),
]
SITES_SHOW = 12
FUEL = {"coal": "Coal power plant", "gas": "Gas power plant", "oil": "Oil-fired power plant", "power": "Power plant", "industry": "Industrial plant"}


def sites_page():
    from html import escape as esc
    data = json.load(open(os.path.join(PUB, "sources", "sites.json"), encoding="utf-8"))
    nf = lambda n: f"{n:,}" if isinstance(n, int) else f"{n:,.3f}".rstrip("0").rstrip(".")
    country = {"PK": "Pakistan", "IN": "India"}

    def loc(x):
        out = []
        for v in (x.get("district"), x.get("state"), country.get(x["cc"], "")):
            if v and v not in out:
                out.append(v)
        return ", ".join(out)

    def link(x, layer, src, z):
        return f"/#at={x['lat']},{x['lon']},{z}" + (f"&amp;layer={layer}" if layer else "") + (f"&amp;src={src}" if src else "")

    def seen(x):
        return (f"seen in {nf(x['plumes'])} plumes, {nf(x['persistence'])}% of passes "
                f"({x['first'][:4]}–{x['last'][:4]})")

    def card(i, title, where, ev, href, cc):
        return (f'<article class="site sketch" data-cc="{cc}"><span class="rank">#{i + 1}</span><h3>{esc(title)}</h3>\n'
                f'      <span class="loc">{esc(where)}</span><div class="ev">{ev}</div><a class="btn go" href="{href}">See on map →</a></article>')

    cards = {"landfills": [], "plants": [], "hot": [], "kilns": []}
    for i, x in enumerate(data["landfills"][:SITES_SHOW]):
        ev = ""
        if x["rate"]:
            ev += f"<b>{nf(x['rate'])}</b> kg/h CH₄<small>≈ {nf(x['rate'])} kg of methane an hour · {esc(seen(x))}</small>"
        if x["heatDays"]:
            ev += f"<small>🔥 burning on {nf(x['heatDays'])} days in 2025</small>"
        title = f"Landfill near {x['near']}" if x["unnamed"] else x["name"]
        cards["landfills"].append(card(i, title, loc(x), ev, link(x, "", "plumes", 14), x["cc"]))
    for i, x in enumerate(data["plants"][:SITES_SHOW]):
        title = f"Plant near {x['near']}" if x["unnamed"] else x["name"]
        ev = f"<b>{nf(x['co2_t_h'])}</b> t/h CO₂<small>≈ {nf(x['co2_t_h'])} tonnes of CO₂ an hour · {esc(seen(x))}</small>"
        cards["plants"].append(card(i, title, f"{FUEL.get(x['kind'], 'Power plant')} · {loc(x)}", ev, link(x, "traffic", "plants", 13), x["cc"]))
    for i, x in enumerate(data["hot"][:SITES_SHOW]):
        title = f"Industrial site near {x['near']}" if x["unnamed"] else x["name"]
        ev = f"<b>{nf(x['days'])}</b> days hot, across {nf(x['months'])} months of 2025"
        cards["hot"].append(card(i, title, loc(x), ev, link(x, "", "hotspots", 14), x["cc"]))
    for i, x in enumerate(data["kilnbelts"][:SITES_SHOW]):
        where = ", ".join(v for v in (x.get("state"), country.get(x["cc"], "")) if v)
        pm = f" · ≈ {nf(x['pm25_t_day'])} tonnes of PM2.5 a day in firing season (estimate)" if x.get("pm25_t_day") else ""
        ev = f"<b>{nf(x['kilns'])}</b> kilns<small>{nf(x['zigzagPct'])}% zigzag (cleaner design){pm}</small>"
        cards["kilns"].append(card(i, x["name"], where, ev, link(x, "", "kilns", 10), x["cc"]))

    total = {"landfills": len(data["landfills"]), "plants": len(data["plants"]), "hot": len(data["hot"]), "kilns": len(data["kilnbelts"])}
    html = []
    for sid, title, why, how in SITES_SECTIONS:
        more = f'\n      <a class="btn more" href="/sources/sites.json">All {nf(total[sid])} in the data file</a>' if total[sid] > SITES_SHOW else ""
        html.append(f'<section class="cat" id="{sid}"><h2>{esc(title)}</h2>\n      <p class="why">{esc(why)}</p><p class="src-note">{esc(how)}</p>\n'
                    f'      <div class="grid">{"".join(cards[sid])}</div>{more}</section>')
    path = os.path.join(PUB, "sites", "index.html")
    page_html = open(path, encoding="utf-8").read()
    a, b = "<!-- sites:start (scripts/build-pages.py) -->", "<!-- sites:end -->"
    i, j = page_html.index(a) + len(a), page_html.index(b)
    open(path, "w", encoding="utf-8").write(page_html[:i] + "\n" + "\n".join(html) + "\n" + page_html[j:])
    print("sites: prerendered", sum(len(v) for v in cards.values()), "cards")


def sitemap():
    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, files, freq, prio, tri in SITEMAP:
        url = f"{SITE}{path}"
        rows.append(f"  <url><loc>{url}</loc><lastmod>{last_changed(files)}</lastmod><changefreq>{freq}</changefreq><priority>{prio}</priority></url>")
    rows.append("</urlset>")
    open(os.path.join(PUB, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print(f"sitemap: {len(SITEMAP)} pages")


if __name__ == "__main__":
    data_page()
    trends_page()
    reports_page()
    updates()
    cities()
    worker_shell()
    sites_page()
    sitemap()
