#!/usr/bin/env python3
"""Build the "Two Punjabs" report (site/public/report/two-punjabs/index.html) from seasons.json.

The numbers come from scripts/season-stats.py; this only lays them out. Charts are static SVG so
the page works without JavaScript and prints cleanly. In English, Urdu and Hindi; district
names in the text and tables are translated where we have a spelling, otherwise left as GeoNames gives them.

Usage: python3 -I scripts/build-report-punjabs.py
"""
import importlib.util, json, math, os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("build_pages", os.path.join(HERE, "build-pages.py"))
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)

DIR = os.path.join(bp.PUB, "report", "two-punjabs")
D = json.load(open(os.path.join(DIR, "seasons.json"), encoding="utf-8"))
S = D["seasons"]
YEARS = sorted(int(y) for y in S)
OFFICIAL = {int(k): v for k, v in D["official_in_punjab"]["counts"].items()}
PK, IN, HR = "PK|Punjab", "IN|Punjab", "IN|Haryana"
COL = {PK: "#1f7a4d", IN: "#d9822b", HR: "#8a857b"}
UNNAMED = "Punjab"  # spots GeoNames couldn't place in a district carry the province name

tot = lambda k, y: S[str(y)][k]["total"]
night = lambda k, y: S[str(y)][k]["night"] / max(1, tot(k, y))
f = lambda n: f"{n:,.0f}"


def pct(a, b):
    return round((a - b) / b * 100)


# ---------- Charts ----------
def axis_max(v):
    raw = v / 4
    p = 10 ** math.floor(math.log10(raw))
    step = next(s * p for s in (1, 2, 5, 10) if s * p >= raw)
    return step * math.ceil(v / step - 1e-9), step


def line_chart(series, fmt, label, end_fmt, names, rtl=False, W=640, H=300):
    """series: {key: [values per YEARS]}. Returns an inline SVG."""
    m = {"l": 58, "r": 130, "t": 12, "b": 34}
    top, step = axis_max(max(v for vals in series.values() for v in vals))
    x = lambda i: m["l"] + i * (W - m["l"] - m["r"]) / (len(YEARS) - 1)
    y = lambda v: H - m["b"] - v / top * (H - m["t"] - m["b"])
    out = [f'<figure class="rfig"><figcaption>{escape(label)}</figcaption><svg viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}" class="rchart" style="direction:ltr">']
    v = 0
    while v <= top + step / 2:
        out.append(f'<line x1="{m["l"]}" x2="{W - m["r"]}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/>'
                   f'<text x="{m["l"] - 8}" y="{y(v) + 4:.1f}" class="tick" text-anchor="end">{fmt(v)}</text>')
        v += step
    for i, yr in enumerate(YEARS):
        out.append(f'<text x="{x(i):.1f}" y="{H - 10}" class="tick" text-anchor="middle">{yr}</text>')
    ends = []
    for k, vals in series.items():
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))
        dash = ' stroke-dasharray="5 4"' if k == HR else ""
        out.append(f'<polyline points="{pts}" fill="none" stroke="{COL[k]}" stroke-width="{2 if k == HR else 3}"{dash} stroke-linejoin="round"/>')
        out += [f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3.5" fill="{COL[k]}"><title>{names[k]} {yr}: {fmt(v)}</title></circle>'
                for i, (yr, v) in enumerate(zip(YEARS, vals))]
        ends.append([y(vals[-1]) + 5, k, vals[-1]])
    # Each label is two lines (~30 px). Stack them upwards from the lowest so none reach the year axis.
    ends.sort(reverse=True)
    ends[0][0] = min(ends[0][0], H - m["b"] - 22)
    for i in range(1, len(ends)):
        ends[i][0] = min(ends[i][0], ends[i - 1][0] - 32)
    for ly, k, v in ends:
        bidi = ' direction="rtl" text-anchor="end"' if rtl else ""
        out.append(f'<text x="{W - m["r"] + 12}" y="{ly:.1f}" class="lab" fill="{COL[k]}"{bidi}>{names[k]}</text>'
                   f'<text x="{W - m["r"] + 12}" y="{ly + 15:.1f}" class="tick"{bidi}>{end_fmt(v)}</text>')
    out.append("</svg></figure>")
    return "".join(out)


def pair_bars(a, b, la, lb, label, W=640, H=270):  # noqa: E302
    """Two bars per season: a (ours) and b (official)."""
    m = {"l": 58, "r": 10, "t": 12, "b": 34}
    top, step = axis_max(max(max(a), max(b)))
    band = (W - m["l"] - m["r"]) / len(YEARS)
    bw = band * 0.32
    y = lambda v: H - m["b"] - v / top * (H - m["t"] - m["b"])
    out = [f'<figure class="rfig"><figcaption>{escape(label)}</figcaption><svg viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}" class="rchart" style="direction:ltr">']
    v = 0
    while v <= top + step / 2:
        out.append(f'<line x1="{m["l"]}" x2="{W - m["r"]}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/>'
                   f'<text x="{m["l"] - 8}" y="{y(v) + 4:.1f}" class="tick" text-anchor="end">{v / 1000:g}k</text>')
        v += step
    for i, yr in enumerate(YEARS):
        cx = m["l"] + band * i + band / 2
        for dx, val, cls, who in ((-bw / 2 - 1, a[i], "b-ours", la), (bw / 2 + 1, b[i], "b-off", lb)):
            out.append(f'<rect x="{cx + dx - bw / 2:.1f}" y="{y(val):.1f}" width="{bw:.1f}" height="{y(0) - y(val):.1f}" class="{cls}">'
                       f'<title>{yr}, {who}: {f(val)}</title></rect>')
        out.append(f'<text x="{cx:.1f}" y="{H - 10}" class="tick" text-anchor="middle">{yr}</text>')
    out.append("</svg></figure>")
    return "".join(out)


# ---------- Numbers used in the text ----------
peak_in = max(YEARS, key=lambda y: tot(IN, y))
last = YEARS[-1]
in_fall = -pct(tot(IN, last), tot(IN, peak_in))
pk_vs_2019 = pct(tot(PK, last), tot(PK, YEARS[0]))
cross = next(y for y in YEARS if tot(PK, y) > tot(IN, y))
ratio_last = tot(PK, last) / tot(IN, last)
ours = [tot(IN, y) for y in YEARS]
off = [OFFICIAL[y] for y in YEARS]
mx, my = sum(ours) / len(ours), sum(off) / len(off)
r = sum((a - mx) * (b - my) for a, b in zip(ours, off)) / math.sqrt(sum((a - mx) ** 2 for a in ours) * sum((b - my) ** 2 for b in off))
ratios = [a / b for a, b in zip(ours, off)]
pk_d = {}
for y in YEARS:
    for d, n in S[str(y)][PK]["districts"].items():
        if d != UNNAMED:
            pk_d.setdefault(d, {})[y] = n
top_pk = sorted(pk_d, key=lambda d: -sum(pk_d[d].values()))[:10]
top3 = sorted(pk_d, key=lambda d: -pk_d[d].get(last, 0))[:3]
top3_sum = sum(pk_d[d].get(last, 0) for d in top3)


# ---------- Article, in three languages ----------
in_top = {y: [d for d in S[str(y)][IN]["districts"] if d != UNNAMED][:3] for y in YEARS}
unnamed_total = sum(S[str(y)][PK]["districts"].get(UNNAMED, 0) for y in YEARS)
fall_2022 = -pct(tot(IN, last), tot(IN, 2022))

DNAME = {
    "ur": {"Jhang": "جھنگ", "Hafizabad": "حافظ آباد", "Okara": "اوکاڑہ", "Gujranwala": "گوجرانوالہ", "Nankana Sahib": "ننکانہ صاحب",
           "Shekhupura": "شیخوپورہ", "Pakpattan": "پاکپتن", "Kasur": "قصور", "Khanewal": "خانیوال", "Dera Ghazi Khan": "ڈیرہ غازی خان",
           "Bahawalnagar": "بہاولنگر", "Tarn Taran": "ترن تارن", "Moga": "موگا", "Firozpur": "فیروزپور", "Bathinda": "بٹھنڈا",
           "Sangrur": "سنگرور", "Amritsar": "امرتسر", "Muktsar": "مکتسر", "Patiala": "پٹیالہ", "Ludhiana": "لدھیانہ", "Barnala": "برنالہ"},
    "hi": {"Jhang": "झंग", "Hafizabad": "हाफ़िज़ाबाद", "Okara": "ओकाड़ा", "Gujranwala": "गुजरांवाला", "Nankana Sahib": "ननकाना साहिब",
           "Shekhupura": "शेख़ूपुरा", "Pakpattan": "पाकपट्टन", "Kasur": "क़सूर", "Khanewal": "ख़ानेवाल", "Dera Ghazi Khan": "डेरा ग़ाज़ी ख़ान",
           "Bahawalnagar": "बहावलनगर", "Tarn Taran": "तरनतारन", "Moga": "मोगा", "Firozpur": "फ़िरोज़पुर", "Bathinda": "बठिंडा",
           "Sangrur": "संगरूर", "Amritsar": "अमृतसर", "Muktsar": "मुक्तसर", "Patiala": "पटियाला", "Ludhiana": "लुधियाना", "Barnala": "बरनाला"},
}
dn = lambda d, L: escape(DNAME.get(L, {}).get(d, d))

L10N = {
    "en": {"names": {PK: "Pakistani Punjab", IN: "Indian Punjab", HR: "Haryana"}, "in_year": "{v} in {y}", "and": " and ",
           "c_tot": "Fire spots seen by Suomi NPP, 1 Oct–30 Nov", "c_night": "Share of fires seen on the 1:30 am pass",
           "c_valid": "Indian Punjab: our count (dark) vs India's official count (light)", "ours": "our count", "official": "official count",
           "th_tot": ["Season", "Pakistani Punjab", "Indian Punjab", "Haryana", "Pakistan ÷ India"],
           "th_valid": ["Season", "Our count (Suomi NPP, 1 Oct–30 Nov)", "India's official count (15 Sep–30 Nov)", "Ours as share"],
           "th_night": ["Season", "Pakistani Punjab", "Indian Punjab", "Haryana"], "th_d": "District",
           "th_peak": ["Season", "Pakistani Punjab: busiest week starts", "Indian Punjab: busiest week starts"]},
    "ur": {"names": {PK: "پاکستانی پنجاب", IN: "ہندوستانی پنجاب", HR: "ہریانہ"}, "in_year": "{y} میں {v}", "and": " اور ",
           "c_tot": "Suomi NPP کو نظر آنے والے آگ کے مقامات، 1 اکتوبر تا 30 نومبر", "c_night": "رات ڈیڑھ بجے کے چکر میں نظر آنے والی آگ کا حصہ",
           "c_valid": "ہندوستانی پنجاب: ہماری گنتی (گہرا رنگ) اور سرکاری گنتی (ہلکا رنگ)", "ours": "ہماری گنتی", "official": "سرکاری گنتی",
           "th_tot": ["موسم", "پاکستانی پنجاب", "ہندوستانی پنجاب", "ہریانہ", "پاکستان ÷ ہندوستان"],
           "th_valid": ["موسم", "ہماری گنتی (Suomi NPP، 1 اکتوبر تا 30 نومبر)", "ہندوستان کی سرکاری گنتی (15 ستمبر تا 30 نومبر)", "سرکاری گنتی کا کتنا حصہ"],
           "th_night": ["موسم", "پاکستانی پنجاب", "ہندوستانی پنجاب", "ہریانہ"], "th_d": "ضلع",
           "th_peak": ["موسم", "پاکستانی پنجاب: سب سے زیادہ آگ والا ہفتہ شروع ہوا", "ہندوستانی پنجاب: سب سے زیادہ آگ والا ہفتہ شروع ہوا"]},
    "hi": {"names": {PK: "पाकिस्तानी पंजाब", IN: "भारतीय पंजाब", HR: "हरियाणा"}, "in_year": "{y} में {v}", "and": " और ",
           "c_tot": "Suomi NPP को दिखी आग की जगहें, 1 अक्टूबर से 30 नवंबर", "c_night": "रात डेढ़ बजे के चक्कर में दिखी आग का हिस्सा",
           "c_valid": "भारतीय पंजाब: हमारी गिनती (गहरा रंग) और सरकारी गिनती (हल्का रंग)", "ours": "हमारी गिनती", "official": "सरकारी गिनती",
           "th_tot": ["मौसम", "पाकिस्तानी पंजाब", "भारतीय पंजाब", "हरियाणा", "पाकिस्तान ÷ भारत"],
           "th_valid": ["मौसम", "हमारी गिनती (Suomi NPP, 1 अक्टूबर से 30 नवंबर)", "भारत की सरकारी गिनती (15 सितंबर से 30 नवंबर)", "सरकारी गिनती का कितना हिस्सा"],
           "th_night": ["मौसम", "पाकिस्तानी पंजाब", "भारतीय पंजाब", "हरियाणा"], "th_d": "ज़िला",
           "th_peak": ["मौसम", "पाकिस्तानी पंजाब: सबसे ज़्यादा आग वाला हफ़्ता शुरू हुआ", "भारतीय पंजाब: सबसे ज़्यादा आग वाला हफ़्ता शुरू हुआ"]},
}

TEXT = {
"en": """  <p class="kicker">Report · {date}</p>
  <h1>Two Punjabs: seven seasons of crop fires</h1>
  <p class="lede">Between {peak_in} and {last}, the crop fires NASA's satellites saw in Indian Punjab fell by {in_fall}%. Across the border, Pakistani Punjab ended higher than it started: {pk0} fire spots in {y0}, {pk1} in {last}. Since {cross}, the satellite has seen more crop fires in Pakistani Punjab than in Indian Punjab, and in {last} it saw {ratio} times as many.</p>
  <p class="muted">Parali ki aag: {peak_in} se {last} tak Indian Punjab mein satellite ko dikhne wali aag {in_fall}% kam hui, magar Pakistani Punjab mein nahi. {last} mein Pakistani Punjab mein {ratio} guna zyada aag dikhi.</p>
  <div class="facts">
    <div class="fact sketch"><b dir="ltr">−{in_fall}%</b><span>Indian Punjab, {peak_in} to {last}</span></div>
    <div class="fact sketch"><b dir="ltr">{pk_pct}%</b><span>Pakistani Punjab, {y0} to {last}</span></div>
    <div class="fact sketch"><b dir="ltr">{ratio}×</b><span>Pakistani vs Indian Punjab, {last}</span></div>
    <div class="fact sketch"><b dir="ltr">{r2}</b><span>match with India's official counts</span></div>
  </div>
  <div class="callout sketch"><p><b>Check this report.</b> Every number here is in <a href="/report/two-punjabs/seasons.json"><code>seasons.json</code></a>, which two scripts in our <a href="https://github.com/hammadtq/hamarihawa">open-source code</a> rebuild from NASA's archive: <code>scripts/backfill-days.py</code>, then <code>scripts/season-stats.py</code> (you need a free NASA FIRMS key). As a cross-check, our Indian Punjab counts and India's official ones have a correlation of {r3}.</p></div>
  <p>This is the first season-by-season comparison of both Punjabs counted the same way that we know of. India publishes daily fire counts for its states, and its press reports them every day of the season. We could find no equivalent public series for Pakistani Punjab. To compare the two fairly we counted every fire spot NASA's Suomi NPP satellite saw on either side of the border in each October and November since {y0}, using one method throughout.</p>

  <h2 id="crossed">The lines crossed in {cross}</h2>
  {chart_tot}
  <p>Indian Punjab's count rose to a peak of {in_peak} in {peak_in}, then fell every year to {in_last} in {last}. Haryana followed the same path at a smaller scale. Pakistani Punjab stayed between {pk_min} and {pk_max} every season except 2021, when it reached {pk_2021}, and ended {last} {pk_vs}% above where it started.</p>
  <p>In {last}, three Pakistani districts alone, {top3}, had {top3_sum} fire spots between them, more than all of Indian Punjab ({in_last}).</p>
  {table_tot}

  <h2 id="check">Can these counts be trusted?</h2>
  <p>We checked our method against India's official figures, which come from the same kind of satellite data, processed by India's Commission for Air Quality Management and the Punjab Remote Sensing Centre. Across seven seasons the two series move together almost perfectly (correlation {r3}). Ours run at {rmin}–{rmax} of the official numbers, which is expected: we count only one satellite and only from 1 October, while India's season starts on 15 September. The one year they disagree on direction is 2021, which we count as slightly up on 2020 and India counts as slightly down. In {last} our busiest Indian district is {in_top1}, which the Indian press also reported as the worst that season.</p>
  <p>Because the same code counts both sides of the border, the Pakistani numbers are as reliable as the Indian ones. Pakistan doesn't publish a comparable count, so there's no official figure to check them against directly.</p>
  {chart_valid}
  {table_valid}

  <h2 id="missed">Fewer fires, or fires the satellite missed?</h2>
  <p>Fire counts are a floor, not a total. A polar-orbiting satellite like Suomi NPP passes over around 1:30 pm and 1:30 am, and only sees a fire that is burning at that moment. Over the past two seasons, Indian researchers and NASA scientist Hiren Jethva have shown that many farmers in Indian Punjab now burn in the late afternoon, after the daytime pass. The think tank iFOREST, using a European geostationary satellite that looks every 15 minutes, found that over 90% of large farm fires in Punjab in 2024 and 2025 started after 3 pm, against 3% in 2021. Burnt-area maps tell the same story: iFOREST puts Punjab's burnt area at about 20,000 km² in 2025, down from 31,447 km² in 2022, a fall of about a third rather than the {fall22}% fall in fire counts.</p>
  <p>Our own data shows a trace of this shift. The night pass catches very few crop fires anywhere, but in Indian Punjab and Haryana the night count held steady or rose while daytime fires collapsed, so the share caught at night went up sharply. In Pakistani Punjab it stayed flat, at around 3–6% every season.</p>
  {chart_night}
  {table_night}
  <p>So two things are true at once. Burning in Indian Punjab has really fallen, but by much less than the fire counts say, because more of it now happens out of the satellite's sight. In Pakistani Punjab we see no sign of the same shift: the counts haven't fallen and the night share hasn't moved. That makes the gap between the two Punjabs in recent seasons partly an artefact of timing, and the true gap is probably smaller than {ratio} times. It does not make it disappear: on the counts that both sides are measured by, Pakistani Punjab went from a quarter of India's number to well over it. Settling the real size of the gap needs geostationary or burnt-area data for the Pakistani side, which nobody has published.</p>

  <h2 id="where">Where in Pakistani Punjab</h2>
  <p>The burning is concentrated in the rice belt between Lahore, Gujranwala and Jhang. The same handful of districts lead every season. Spots the place-name data couldn't put in a district ({unnamed} over seven seasons) are left out of this table.</p>
  {table_d}
  <p>Watch any season move district by district on the <a href="/trends/#districts">fire trends map</a>.</p>

  <h2 id="when">When the burning peaks</h2>
  <p>The busiest week usually starts in the last days of October or the first days of November on both sides. In 2023 and 2024 Pakistani Punjab peaked about two weeks later than Indian Punjab, in mid-November.</p>
  {table_peak}

  <h2 id="method">How this was counted</h2>
  <ul>
    <li><b>Data</b>: NASA FIRMS active fires from the VIIRS instrument on Suomi NPP (375 m pixels), final processing, 1 October–30 November of each year, downloaded through the FIRMS area API.</li>
    <li><b>One satellite</b>: newer satellites (NOAA-20 from 2018, NOAA-21 from 2023) see more fires. Counting only Suomi NPP keeps every season on the same footing.</li>
    <li><b>Fire spots</b>: low-confidence detections are dropped; the same spot seen more than once in a day counts once. Days run on Pakistan time.</li>
    <li><b>Where</b>: each spot is placed in a district and province using GeoNames place data, the same way the <a href="/">live map</a> names fires.</li>
    <li><b>India's official counts</b>: as published by CAQM and the Punjab Remote Sensing Centre and reported in the press. Some years have more than one published figure (2019 is also given as 55,210 and 2020 as 83,002); we use the more commonly cited one.</li>
    <li><b>Limits</b>: counts miss fires lit and put out between satellite passes, and fires under cloud or thick smoke. They count places that were burning, not area burnt or smoke produced.</li>
    <li><b>Download</b>: every number on this page is in <a href="/report/two-punjabs/seasons.json"><code>seasons.json</code></a> (CC BY 4.0). Daily totals for both countries are at <a href="/api/days"><code>/api/days</code></a>.</li>
  </ul>
  <p class="muted">Sources for others' findings: iFOREST's geostationary analysis and Hiren Jethva's observations as reported by {src_tribune} and {src_hpw}; CEEW's {src_ceew}; India's official counts as reported by {src_off1} and {src_off2}.</p>
  <p>Please cite as: HamariHawa, "Two Punjabs: seven seasons of crop fires", hamarihawa.org/report/two-punjabs/, October 2026.</p>""",

"ur": """  <p class="kicker">رپورٹ · {date}</p>
  <h1>دو پنجاب: فصلوں کی آگ کے سات موسم</h1>
  <p class="lede">{peak_in} سے {last} کے دوران ہندوستانی پنجاب میں ناسا کے سیٹلائٹس نے فصلوں کی جو آگ دیکھی، وہ {in_fall}% کم ہو گئی۔ سرحد کے اُس پار پاکستانی پنجاب میں یہ تعداد کم نہیں ہوئی بلکہ بڑھی: {y0} میں {pk0} مقامات پر آگ دیکھی گئی تھی اور {last} میں {pk1} مقامات پر۔ {cross} سے سیٹلائٹ کو ہندوستانی پنجاب کے مقابلے میں پاکستانی پنجاب میں زیادہ آگ نظر آ رہی ہے، اور {last} میں یہ تعداد {ratio} گنا تھی۔</p>
  <div class="facts">
    <div class="fact sketch"><b dir="ltr">−{in_fall}%</b><span>ہندوستانی پنجاب، {peak_in} سے {last} تک</span></div>
    <div class="fact sketch"><b dir="ltr">{pk_pct}%</b><span>پاکستانی پنجاب، {y0} سے {last} تک</span></div>
    <div class="fact sketch"><b dir="ltr">{ratio}×</b><span>ہندوستانی پنجاب کے مقابلے میں پاکستانی پنجاب ({last})</span></div>
    <div class="fact sketch"><b dir="ltr">{r2}</b><span>ہندوستان کے سرکاری اعداد سے مطابقت</span></div>
  </div>
  <div class="callout sketch"><p><b>اس رپورٹ کو خود جانچیں۔</b> یہاں کا ہر عدد <a href="/report/two-punjabs/seasons.json"><code>seasons.json</code></a> میں موجود ہے، جسے ہمارے <a href="https://github.com/hammadtq/hamarihawa">اوپن سورس کوڈ</a> کے دو اسکرپٹس ناسا کے ریکارڈ سے دوبارہ بناتے ہیں: پہلے <code>scripts/backfill-days.py</code> اور پھر <code>scripts/season-stats.py</code> (اس کے لیے ناسا FIRMS کی مفت key درکار ہے)۔ مزید جانچ کے طور پر، ہندوستانی پنجاب کے ہمارے اعداد اور ہندوستان کے سرکاری اعداد کا باہمی تعلق {r3} ہے۔</p></div>
  <p>جہاں تک ہمیں معلوم ہے، یہ پہلا موقع ہے کہ دونوں پنجابوں کی آگ کو ایک ہی طریقے سے، موسم بہ موسم گنا اور پرکھا گیا ہے۔ ہندوستان اپنی ریاستوں میں آگ کے روزانہ اعداد و شمار جاری کرتا ہے، اور وہاں کے اخبارات پورے موسم میں ہر روز ان کی خبر دیتے ہیں۔ پاکستانی پنجاب کے لیے ہمیں ایسے کوئی عوامی اعداد و شمار نہیں ملے۔ دونوں کا منصفانہ موازنہ کرنے کے لیے ہم نے {y0} سے اب تک ہر سال اکتوبر اور نومبر میں سرحد کے دونوں جانب وہ تمام مقامات گنے جہاں ناسا کے Suomi NPP سیٹلائٹ نے آگ دیکھی، اور شروع سے آخر تک ایک ہی طریقہ استعمال کیا۔</p>

  <h2 id="crossed">{cross} میں دونوں لکیریں ایک دوسرے کو کاٹ گئیں</h2>
  {chart_tot}
  <p>ہندوستانی پنجاب میں یہ تعداد {peak_in} میں {in_peak} کی بلند ترین سطح پر پہنچی، پھر ہر سال کم ہوتے ہوتے {last} میں {in_last} رہ گئی۔ ہریانہ میں بھی چھوٹے پیمانے پر یہی ہوا۔ پاکستانی پنجاب میں 2021 کے سوا ہر موسم یہ تعداد {pk_min} اور {pk_max} کے درمیان رہی؛ 2021 میں یہ {pk_2021} تک پہنچی، اور {last} میں {y0} کے مقابلے میں {pk_vs}% زیادہ تھی۔</p>
  <p>{last} میں صرف تین پاکستانی اضلاع، {top3}، میں مجموعی طور پر {top3_sum} مقامات پر آگ دیکھی گئی، جو پورے ہندوستانی پنجاب ({in_last}) سے زیادہ ہے۔</p>
  {table_tot}

  <h2 id="check">کیا ان اعداد و شمار پر بھروسا کیا جا سکتا ہے؟</h2>
  <p>اپنے طریقے کو پرکھنے کے لیے ہم نے اپنے نتائج کا موازنہ ہندوستان کے سرکاری اعداد و شمار سے کیا، جو ہندوستان کا کمیشن برائے فضائی معیار (CAQM) اور پنجاب ریموٹ سینسنگ سینٹر اسی قسم کے سیٹلائٹ ڈیٹا سے تیار کرتے ہیں۔ سات موسموں میں دونوں سلسلے تقریباً ایک ساتھ اوپر نیچے ہوتے ہیں (باہمی تعلق {r3})۔ ہمارے اعداد سرکاری اعداد کے {rmin} سے {rmax} کے برابر ہیں، اور یہ فرق متوقع ہے، کیونکہ ہم صرف ایک سیٹلائٹ کی دیکھی آگ گنتے ہیں اور وہ بھی 1 اکتوبر سے، جبکہ ہندوستان کا موسم 15 ستمبر سے شروع ہوتا ہے۔ دونوں صرف 2021 میں مختلف سمت دکھاتے ہیں: ہمارے حساب سے اُس سال آگ 2020 سے کچھ بڑھی، جبکہ سرکاری حساب سے کچھ کم ہوئی۔ {last} میں ہماری فہرست میں سب سے اوپر {in_top1} ہے، جسے ہندوستانی اخبارات نے بھی اُس موسم کا سب سے زیادہ آگ والا ضلع بتایا تھا۔</p>
  <p>چونکہ سرحد کے دونوں جانب گنتی ایک ہی کوڈ سے ہوتی ہے، اس لیے پاکستانی اعداد بھی اتنے ہی قابلِ اعتماد ہیں جتنے ہندوستانی۔ پاکستان ایسے اعداد جاری نہیں کرتا، اس لیے ان کا براہِ راست کسی سرکاری عدد سے موازنہ ممکن نہیں۔</p>
  {chart_valid}
  {table_valid}

  <h2 id="missed">کیا آگ واقعی کم ہوئی، یا سیٹلائٹ کی نظر سے بچ گئی؟</h2>
  <p>آگ کی گنتی اصل تعداد نہیں بلکہ کم از کم تعداد بتاتی ہے۔ Suomi NPP جیسا قطبی مدار میں گھومنے والا سیٹلائٹ اس علاقے کے اوپر سے دوپہر اور رات کو تقریباً ڈیڑھ بجے گزرتا ہے، اور صرف وہی آگ دیکھ پاتا ہے جو اُس وقت جل رہی ہو۔ پچھلے دو موسموں میں ہندوستانی محققین اور ناسا کے سائنس دان ہیرن جیٹھوا نے دکھایا ہے کہ ہندوستانی پنجاب میں بہت سے کسان اب سیٹلائٹ کے دوپہر والے چکر کے بعد، سہ پہر یا شام کو پرالی جلاتے ہیں۔ تحقیقی ادارے iFOREST نے ایک یورپی جیوسٹیشنری سیٹلائٹ کی مدد سے، جو ہر 15 منٹ بعد تصویر لیتا ہے، یہ معلوم کیا کہ 2024 اور 2025 میں پنجاب میں فصلوں کی 90 فیصد سے زیادہ بڑی آگ سہ پہر 3 بجے کے بعد لگائی گئی، جبکہ 2021 میں یہ شرح صرف 3 فیصد تھی۔ جلے ہوئے رقبے کے نقشے بھی یہی کہانی سناتے ہیں: iFOREST کے مطابق 2025 میں پنجاب میں تقریباً 20,000 مربع کلومیٹر رقبہ جلا، جو 2022 کے 31,447 مربع کلومیٹر سے تقریباً ایک تہائی کم ہے، جبکہ اسی عرصے میں آگ کی گنتی {fall22} فیصد گری۔</p>
  <p>ہمارے اپنے ڈیٹا میں بھی اس تبدیلی کی جھلک ملتی ہے۔ رات کے چکر میں کہیں بھی فصلوں کی بہت کم آگ نظر آتی ہے، لیکن ہندوستانی پنجاب اور ہریانہ میں رات کو دکھنے والی آگ یا تو اتنی ہی رہی یا بڑھ گئی، جبکہ دن کی آگ بہت کم ہو گئی۔ اسی لیے وہاں رات کو دکھنے والی آگ کا حصہ تیزی سے بڑھا۔ پاکستانی پنجاب میں یہ حصہ ہر موسم تقریباً 3 سے 6 فیصد کے درمیان ہی رہا۔</p>
  {chart_night}
  {table_night}
  <p>یعنی دو باتیں بیک وقت درست ہیں۔ ہندوستانی پنجاب میں پرالی جلانا واقعی کم ہوا ہے، مگر اتنا نہیں جتنا آگ کی گنتی بتاتی ہے، کیونکہ اب اس کا بڑا حصہ سیٹلائٹ کی نظر سے اوجھل رہتا ہے۔ پاکستانی پنجاب میں ہمیں ایسی کسی تبدیلی کا نشان نہیں ملتا: نہ آگ کی گنتی کم ہوئی، نہ رات کا حصہ بدلا۔ لہٰذا حالیہ موسموں میں دونوں پنجابوں کے فرق کی ایک وجہ آگ لگانے کا وقت بھی ہے، اور اصل فرق غالباً {ratio} گنا سے کم ہے۔ لیکن اس سے یہ فرق ختم نہیں ہو جاتا: جس پیمانے سے دونوں کو ناپا جاتا ہے، اُس پر پاکستانی پنجاب ہندوستان کے ایک چوتھائی سے بڑھ کر اُس سے کہیں آگے نکل گیا ہے۔ اصل فرق جاننے کے لیے پاکستانی پنجاب کا جیوسٹیشنری سیٹلائٹ یا جلے ہوئے رقبے کا ڈیٹا درکار ہے، جو اب تک کسی نے شائع نہیں کیا۔</p>

  <h2 id="where">پاکستانی پنجاب میں آگ کہاں لگتی ہے</h2>
  <p>زیادہ تر آگ لاہور، گوجرانوالہ اور جھنگ کے درمیان پھیلی چاول کی پٹی میں لگتی ہے، اور ہر موسم وہی چند اضلاع سرِفہرست رہتے ہیں۔ جن مقامات کو ہم کسی ضلع میں شامل نہیں کر سکے (سات موسموں میں {unnamed}) وہ اس جدول میں شامل نہیں۔</p>
  {table_d}
  <p>کسی بھی موسم میں آگ کو ضلع بہ ضلع پھیلتے دیکھنے کے لیے <a href="/trends/#districts">آگ کے رجحان کا نقشہ</a> دیکھیں۔</p>

  <h2 id="when">آگ عروج پر کب ہوتی ہے</h2>
  <p>دونوں جانب سب سے زیادہ آگ والا ہفتہ عموماً اکتوبر کے آخری یا نومبر کے ابتدائی دنوں میں شروع ہوتا ہے۔ 2023 اور 2024 میں پاکستانی پنجاب میں یہ عروج ہندوستانی پنجاب سے تقریباً دو ہفتے بعد، وسط نومبر میں آیا۔</p>
  {table_peak}

  <h2 id="method">یہ اعداد کیسے گنے گئے</h2>
  <ul>
    <li><b>ڈیٹا</b>: ناسا FIRMS کے فعال آگ کے ریکارڈ، جو Suomi NPP سیٹلائٹ پر نصب VIIRS آلے سے حاصل ہوتے ہیں (375 میٹر پکسل)۔ ہم نے حتمی پروسیسنگ والا ڈیٹا استعمال کیا، ہر سال 1 اکتوبر سے 30 نومبر تک، جو FIRMS area API سے ڈاؤن لوڈ کیا گیا۔</li>
    <li><b>ایک ہی سیٹلائٹ</b>: نئے سیٹلائٹ (2018 سے NOAA-20 اور 2023 سے NOAA-21) زیادہ آگ دیکھتے ہیں۔ صرف Suomi NPP کو گننے سے ہر موسم کا موازنہ ایک ہی بنیاد پر ہوتا ہے۔</li>
    <li><b>آگ کے مقامات</b>: کم یقینی والی نشاندہیاں نکال دی گئی ہیں، اور اگر ایک ہی مقام دن میں ایک سے زیادہ بار نظر آئے تو اسے ایک ہی بار گنا گیا ہے۔ دن کا حساب پاکستانی وقت کے مطابق ہے۔</li>
    <li><b>مقام کی نشاندہی</b>: ہر مقام کو GeoNames کے ڈیٹا کی مدد سے کسی ضلع اور صوبے میں رکھا گیا ہے، بالکل اسی طرح جیسے <a href="/">تازہ نقشہ</a> ہر آگ کو اس کے قریبی مقام کا نام دیتا ہے۔</li>
    <li><b>ہندوستان کے سرکاری اعداد</b>: CAQM اور پنجاب ریموٹ سینسنگ سینٹر کے جاری کردہ، جیسا کہ اخبارات میں شائع ہوئے۔ بعض سالوں کے ایک سے زیادہ اعداد سامنے آئے (2019 کے لیے 55,210 اور 2020 کے لیے 83,002 بھی)؛ ہم نے وہ عدد لیا ہے جو زیادہ تر حوالوں میں آتا ہے۔</li>
    <li><b>حدود</b>: یہ گنتی اُس آگ کو شامل نہیں کرتی جو سیٹلائٹ کے دو چکروں کے درمیان لگ کر بجھ جائے، یا جو بادل یا گہرے دھوئیں کے نیچے ہو۔ یہ جلتے ہوئے مقامات گنتی ہے، جلا ہوا رقبہ یا پیدا ہونے والا دھواں نہیں۔</li>
    <li><b>ڈاؤن لوڈ</b>: اس صفحے کے تمام اعداد <a href="/report/two-punjabs/seasons.json"><code>seasons.json</code></a> میں موجود ہیں (CC BY 4.0)۔ دونوں ملکوں کے روزانہ اعداد <a href="/api/days"><code>/api/days</code></a> پر دستیاب ہیں۔</li>
  </ul>
  <p class="muted">دوسروں کی تحقیق کے حوالے: iFOREST کا جیوسٹیشنری تجزیہ اور ہیرن جیٹھوا کے مشاہدات، {src_tribune} اور {src_hpw} کی رپورٹوں کے مطابق؛ سیٹلائٹ سے آگ کی نشاندہی پر CEEW کی {src_ceew}؛ اور ہندوستان کے سرکاری اعداد، {src_off1} اور {src_off2} کے مطابق۔</p>
  <p>حوالہ دینے کے لیے: HamariHawa، "Two Punjabs: seven seasons of crop fires"، hamarihawa.org/report/two-punjabs/، اکتوبر 2026۔</p>""",

"hi": """  <p class="kicker">रिपोर्ट · {date}</p>
  <h1>दो पंजाब: फ़सल की आग के सात मौसम</h1>
  <p class="lede">{peak_in} से {last} के बीच भारतीय पंजाब में नासा के उपग्रहों ने फ़सल की जितनी आग देखी, वह {in_fall}% घट गई। सरहद के उस पार पाकिस्तानी पंजाब में यह संख्या घटी नहीं, बल्कि बढ़ी: {y0} में {pk0} जगहों पर आग दिखी थी और {last} में {pk1} जगहों पर। {cross} से उपग्रह को भारतीय पंजाब की तुलना में पाकिस्तानी पंजाब में ज़्यादा आग दिख रही है, और {last} में यह संख्या {ratio} गुना थी।</p>
  <div class="facts">
    <div class="fact sketch"><b dir="ltr">−{in_fall}%</b><span>भारतीय पंजाब, {peak_in} से {last} तक</span></div>
    <div class="fact sketch"><b dir="ltr">{pk_pct}%</b><span>पाकिस्तानी पंजाब, {y0} से {last} तक</span></div>
    <div class="fact sketch"><b dir="ltr">{ratio}×</b><span>भारतीय पंजाब की तुलना में पाकिस्तानी पंजाब ({last})</span></div>
    <div class="fact sketch"><b dir="ltr">{r2}</b><span>भारत के सरकारी आँकड़ों से मेल</span></div>
  </div>
  <div class="callout sketch"><p><b>इस रिपोर्ट को ख़ुद जाँचें।</b> यहाँ का हर आँकड़ा <a href="/report/two-punjabs/seasons.json"><code>seasons.json</code></a> में मौजूद है, जिसे हमारे <a href="https://github.com/hammadtq/hamarihawa">ओपन सोर्स कोड</a> की दो स्क्रिप्ट नासा के रिकॉर्ड से दोबारा बनाती हैं: पहले <code>scripts/backfill-days.py</code> और फिर <code>scripts/season-stats.py</code> (इसके लिए नासा FIRMS की मुफ़्त key चाहिए)। अतिरिक्त जाँच के तौर पर, भारतीय पंजाब के हमारे आँकड़ों और भारत के सरकारी आँकड़ों का सहसंबंध {r3} है।</p></div>
  <p>जहाँ तक हमें पता है, यह पहली बार है जब दोनों पंजाबों की आग को एक ही तरीक़े से, मौसम-दर-मौसम गिना और परखा गया है। भारत अपने राज्यों में आग के रोज़ाना आँकड़े जारी करता है, और वहाँ के अख़बार पूरे मौसम में हर दिन इनकी ख़बर छापते हैं। पाकिस्तानी पंजाब के लिए हमें ऐसे कोई सार्वजनिक आँकड़े नहीं मिले। दोनों की निष्पक्ष तुलना के लिए हमने {y0} से अब तक हर साल अक्टूबर और नवंबर में सरहद के दोनों तरफ़ वे सभी जगहें गिनीं जहाँ नासा के Suomi NPP उपग्रह ने आग देखी, और शुरू से आख़िर तक एक ही तरीक़ा अपनाया।</p>

  <h2 id="crossed">{cross} में दोनों रेखाएँ एक-दूसरे को काट गईं</h2>
  {chart_tot}
  <p>भारतीय पंजाब में यह संख्या {peak_in} में {in_peak} के सबसे ऊँचे स्तर पर पहुँची, फिर हर साल घटते-घटते {last} में {in_last} रह गई। हरियाणा में भी छोटे पैमाने पर यही हुआ। पाकिस्तानी पंजाब में 2021 को छोड़कर हर मौसम यह संख्या {pk_min} और {pk_max} के बीच रही; 2021 में यह {pk_2021} तक पहुँची, और {last} में {y0} की तुलना में {pk_vs}% ज़्यादा थी।</p>
  <p>{last} में सिर्फ़ तीन पाकिस्तानी ज़िलों, {top3}, में कुल मिलाकर {top3_sum} जगहों पर आग दिखी, जो पूरे भारतीय पंजाब ({in_last}) से ज़्यादा है।</p>
  {table_tot}

  <h2 id="check">क्या इन आँकड़ों पर भरोसा किया जा सकता है?</h2>
  <p>अपने तरीक़े को परखने के लिए हमने अपने नतीजों की तुलना भारत के सरकारी आँकड़ों से की, जिन्हें वायु गुणवत्ता प्रबंधन आयोग (CAQM) और पंजाब रिमोट सेंसिंग सेंटर इसी तरह के उपग्रह डेटा से तैयार करते हैं। सात मौसमों में दोनों आँकड़े लगभग एक साथ घटते-बढ़ते हैं (सहसंबंध {r3})। हमारे आँकड़े सरकारी आँकड़ों के {rmin} से {rmax} के बराबर हैं, और यह अंतर अपेक्षित है, क्योंकि हम सिर्फ़ एक उपग्रह की देखी आग गिनते हैं और वह भी 1 अक्टूबर से, जबकि भारत का मौसम 15 सितंबर से शुरू होता है। दोनों सिर्फ़ 2021 में अलग दिशा दिखाते हैं: हमारे हिसाब से उस साल आग 2020 से थोड़ी बढ़ी, जबकि सरकारी हिसाब से थोड़ी घटी। {last} में हमारी सूची में सबसे ऊपर {in_top1} है, जिसे भारतीय अख़बारों ने भी उस मौसम का सबसे ज़्यादा आग वाला ज़िला बताया था।</p>
  <p>चूँकि सरहद के दोनों तरफ़ गिनती एक ही कोड से होती है, इसलिए पाकिस्तानी आँकड़े भी उतने ही भरोसेमंद हैं जितने भारतीय। पाकिस्तान ऐसे आँकड़े जारी नहीं करता, इसलिए इनकी सीधे किसी सरकारी आँकड़े से तुलना नहीं की जा सकती।</p>
  {chart_valid}
  {table_valid}

  <h2 id="missed">क्या आग सचमुच घटी, या उपग्रह की नज़र से बच गई?</h2>
  <p>आग की गिनती असल संख्या नहीं, बल्कि कम से कम संख्या बताती है। Suomi NPP जैसा ध्रुवीय कक्षा वाला उपग्रह इस इलाक़े के ऊपर से दोपहर और रात को लगभग डेढ़ बजे गुज़रता है, और सिर्फ़ वही आग देख पाता है जो उस समय जल रही हो। पिछले दो मौसमों में भारतीय शोधकर्ताओं और नासा के वैज्ञानिक हिरेन जेठवा ने दिखाया है कि भारतीय पंजाब में बहुत से किसान अब उपग्रह के दोपहर वाले चक्कर के बाद, शाम को पराली जलाते हैं। शोध संस्था iFOREST ने एक यूरोपीय भूस्थिर उपग्रह की मदद से, जो हर 15 मिनट में तस्वीर लेता है, पाया कि 2024 और 2025 में पंजाब में फ़सल की 90 प्रतिशत से ज़्यादा बड़ी आग दोपहर 3 बजे के बाद लगाई गई, जबकि 2021 में यह दर सिर्फ़ 3 प्रतिशत थी। जले हुए रकबे के नक्शे भी यही बताते हैं: iFOREST के अनुसार 2025 में पंजाब में लगभग 20,000 वर्ग किलोमीटर रकबा जला, जो 2022 के 31,447 वर्ग किलोमीटर से लगभग एक-तिहाई कम है, जबकि इसी दौरान आग की गिनती {fall22} प्रतिशत गिरी।</p>
  <p>हमारे अपने डेटा में भी इस बदलाव की झलक मिलती है। रात के चक्कर में कहीं भी फ़सल की बहुत कम आग दिखती है, लेकिन भारतीय पंजाब और हरियाणा में रात को दिखने वाली आग या तो उतनी ही रही या बढ़ गई, जबकि दिन की आग बहुत घट गई। इसीलिए वहाँ रात को दिखने वाली आग का हिस्सा तेज़ी से बढ़ा। पाकिस्तानी पंजाब में यह हिस्सा हर मौसम लगभग 3 से 6 प्रतिशत के बीच ही रहा।</p>
  {chart_night}
  {table_night}
  <p>यानी दो बातें एक साथ सच हैं। भारतीय पंजाब में पराली जलाना सचमुच घटा है, पर उतना नहीं जितना आग की गिनती बताती है, क्योंकि अब इसका बड़ा हिस्सा उपग्रह की नज़र से ओझल रहता है। पाकिस्तानी पंजाब में हमें ऐसे किसी बदलाव का निशान नहीं मिलता: न आग की गिनती घटी, न रात का हिस्सा बदला। इसलिए हाल के मौसमों में दोनों पंजाबों के फ़र्क़ की एक वजह आग लगाने का समय भी है, और असली फ़र्क़ शायद {ratio} गुना से कम है। लेकिन इससे यह फ़र्क़ मिट नहीं जाता: जिस पैमाने पर दोनों को नापा जाता है, उस पर पाकिस्तानी पंजाब भारत के एक-चौथाई से बढ़कर उससे कहीं आगे निकल गया है। असली फ़र्क़ जानने के लिए पाकिस्तानी पंजाब का भूस्थिर उपग्रह या जले रकबे का डेटा चाहिए, जो अब तक किसी ने प्रकाशित नहीं किया।</p>

  <h2 id="where">पाकिस्तानी पंजाब में आग कहाँ लगती है</h2>
  <p>ज़्यादातर आग लाहौर, गुजरांवाला और झंग के बीच फैली धान की पट्टी में लगती है, और हर मौसम वही कुछ ज़िले सबसे आगे रहते हैं। जिन जगहों को हम किसी ज़िले में नहीं रख सके (सात मौसमों में {unnamed}) उन्हें इस तालिका में शामिल नहीं किया गया।</p>
  {table_d}
  <p>किसी भी मौसम में आग को ज़िला-दर-ज़िला फैलते देखने के लिए <a href="/trends/#districts">आग के रुझान का नक्शा</a> देखें।</p>

  <h2 id="when">आग का चरम कब आता है</h2>
  <p>दोनों तरफ़ सबसे ज़्यादा आग वाला हफ़्ता आमतौर पर अक्टूबर के आख़िरी या नवंबर के शुरुआती दिनों में शुरू होता है। 2023 और 2024 में पाकिस्तानी पंजाब में यह चरम भारतीय पंजाब से लगभग दो हफ़्ते बाद, नवंबर के बीच में आया।</p>
  {table_peak}

  <h2 id="method">ये आँकड़े कैसे गिने गए</h2>
  <ul>
    <li><b>डेटा</b>: नासा FIRMS के सक्रिय आग के रिकॉर्ड, जो Suomi NPP उपग्रह पर लगे VIIRS उपकरण से मिलते हैं (375 मीटर पिक्सल)। हमने अंतिम प्रोसेसिंग वाला डेटा इस्तेमाल किया, हर साल 1 अक्टूबर से 30 नवंबर तक का, जो FIRMS area API से डाउनलोड किया गया।</li>
    <li><b>एक ही उपग्रह</b>: नए उपग्रह (2018 से NOAA-20 और 2023 से NOAA-21) ज़्यादा आग देखते हैं। सिर्फ़ Suomi NPP को गिनने से हर मौसम की तुलना एक ही आधार पर होती है।</li>
    <li><b>आग की जगहें</b>: कम भरोसे वाली पहचानें हटा दी गई हैं, और अगर एक ही जगह दिन में एक से ज़्यादा बार दिखे तो उसे एक ही बार गिना गया है। दिन का हिसाब पाकिस्तानी समय से है।</li>
    <li><b>जगह की पहचान</b>: हर जगह को GeoNames के डेटा की मदद से किसी ज़िले और प्रांत में रखा गया है, ठीक उसी तरह जैसे <a href="/">लाइव नक्शा</a> हर आग को उसकी नज़दीकी जगह का नाम देता है।</li>
    <li><b>भारत के सरकारी आँकड़े</b>: CAQM और पंजाब रिमोट सेंसिंग सेंटर के जारी किए हुए, जैसा अख़बारों में छपा। कुछ सालों के एक से ज़्यादा आँकड़े सामने आए (2019 के लिए 55,210 और 2020 के लिए 83,002 भी); हमने वह आँकड़ा लिया है जो ज़्यादातर जगह मिलता है।</li>
    <li><b>सीमाएँ</b>: यह गिनती उस आग को शामिल नहीं करती जो उपग्रह के दो चक्करों के बीच लगकर बुझ जाए, या जो बादल या घने धुएँ के नीचे हो। यह जलती हुई जगहें गिनती है, जला हुआ रकबा या पैदा हुआ धुआँ नहीं।</li>
    <li><b>डाउनलोड</b>: इस पेज के सभी आँकड़े <a href="/report/two-punjabs/seasons.json"><code>seasons.json</code></a> में मौजूद हैं (CC BY 4.0)। दोनों देशों के रोज़ के आँकड़े <a href="/api/days"><code>/api/days</code></a> पर उपलब्ध हैं।</li>
  </ul>
  <p class="muted">दूसरों के शोध के स्रोत: iFOREST का भूस्थिर उपग्रह विश्लेषण और हिरेन जेठवा के अवलोकन, {src_tribune} और {src_hpw} की रिपोर्टों के अनुसार; उपग्रह से आग की पहचान पर CEEW की {src_ceew}; और भारत के सरकारी आँकड़े, {src_off1} और {src_off2} के अनुसार।</p>
  <p>हवाला देने के लिए: HamariHawa, "Two Punjabs: seven seasons of crop fires", hamarihawa.org/report/two-punjabs/, अक्टूबर 2026।</p>""",
}

SRC = {
    "tribune": ("https://www.tribuneindia.com/news/delhi/satellites-miss-majority-of-stubble-fires-delhi-air-pollution-underestimated-report", "The Tribune"),
    "hpw": ("https://healthpolicy-watch.news/delhi-air-pollution-are-government-satellites-missing-the-stubble-fires/", "Health Policy Watch"),
    "ceew": ("https://www.ceew.in/blogs/how-does-satellite-technology-detect-punjab-stubble-burning-fires",
             {"en": "explainer on satellite detection", "ur": "وضاحت", "hi": "व्याख्या"}),
    "off1": ("https://www.tribuneindia.com/news/punjab/farm-fires-down-by-27-in-punjab-37-in-haryana-compared-to-last-year-environment-ministry-567656", "The Tribune"),
    "off2": ("https://www.tribuneindia.com/news/india/punjab-haryana-record-90-per-cent-fewer-farm-fire-incidents-in-2025-govt-in-lok-sabha/amp", "The Tribune (2025)"),
}


def table(head, rows):
    return ('<div class="table-wrap"><table>\n    <tr>' + "".join(f"<th>{escape(h)}</th>" for h in head) + "</tr>\n    "
            + "\n    ".join(rows) + "\n  </table></div>")


def peak_week(k, y, L):
    from datetime import date
    daily = S[str(y)][k]["daily"]
    days = sorted(daily)
    best = max(range(len(days)), key=lambda i: sum(daily[d] for d in days[i:i + 7]))
    d0 = date.fromisoformat(days[best])
    return f"{d0.day} {d0:%b}" if L == "en" else f"{d0.day} {bp.MONTHS[L][d0.month - 1]}"


def article(L):
    t = L10N[L]
    nm = t["names"]
    in_yr = lambda fmt: (lambda v: t["in_year"].format(v=fmt(v), y=last))
    link = lambda key: (lambda u, txt: f'<a href="{u}">{escape(txt[L] if isinstance(txt, dict) else txt)}</a>')(*SRC[key])
    tops = [dn(d, L) for d in top3]
    V = dict(
        date=bp.fmt_date("2026-10-20", L), peak_in=peak_in, last=last, in_fall=in_fall, y0=YEARS[0], cross=cross,
        pk0=f(tot(PK, YEARS[0])), pk1=f(tot(PK, last)), ratio=f"{ratio_last:.1f}", pk_pct=f"{pk_vs_2019:+}", pk_vs=pk_vs_2019,
        r2=f"{r:.2f}", r3=f"{r:.3f}", rmin=f"{min(ratios):.0%}", rmax=f"{max(ratios):.0%}",
        in_peak=f(tot(IN, peak_in)), in_last=f(tot(IN, last)),
        pk_min=f(min(tot(PK, y) for y in YEARS if y != 2021)), pk_max=f(max(tot(PK, y) for y in YEARS if y != 2021)), pk_2021=f(tot(PK, 2021)),
        top3=("، " if L == "ur" else ", ").join(tops[:2]) + t["and"] + tops[2], top3_sum=f(top3_sum),
        in_top1=dn(in_top[last][0], L), fall22=fall_2022, unnamed=f(unnamed_total),
        src_tribune=link("tribune"), src_hpw=link("hpw"), src_ceew=link("ceew"), src_off1=link("off1"), src_off2=link("off2"),
        chart_tot=line_chart({k: [tot(k, y) for y in YEARS] for k in (IN, PK, HR)}, lambda v: f"{v / 1000:g}k", t["c_tot"], in_yr(f), nm, L == "ur"),
        chart_night=line_chart({k: [night(k, y) * 100 for y in YEARS] for k in (PK, IN, HR)}, lambda v: f"{v:g}%", t["c_night"],
                               in_yr(lambda v: f"{v:.1f}%"), nm, L == "ur"),
        chart_valid=pair_bars(ours, off, t["ours"], t["official"], t["c_valid"]),
        table_tot=table(t["th_tot"], [f"<tr><td>{y}</td><td>{f(tot(PK, y))}</td><td>{f(tot(IN, y))}</td><td>{f(tot(HR, y))}</td><td>{tot(PK, y) / tot(IN, y):.2f}</td></tr>" for y in YEARS]),
        table_valid=table(t["th_valid"], [f"<tr><td>{y}</td><td>{f(a)}</td><td>{f(b)}</td><td>{a / b:.0%}</td></tr>" for y, a, b in zip(YEARS, ours, off)]),
        table_night=table(t["th_night"], [f"<tr><td>{y}</td>" + "".join(f"<td>{S[str(y)][k]['night']:,} <span class=\"muted\">({night(k, y):.1%})</span></td>" for k in (PK, IN, HR)) + "</tr>" for y in YEARS]),
        table_d=table([t["th_d"]] + [str(y) for y in YEARS], [f"<tr><td>{dn(d, L)}</td>" + "".join(f"<td>{f(pk_d[d].get(y, 0))}</td>" for y in YEARS) + "</tr>" for d in top_pk]),
        table_peak=table(t["th_peak"], [f"<tr><td>{y}</td><td>{peak_week(PK, y, L)}</td><td>{peak_week(IN, y, L)}</td></tr>" for y in YEARS]),
    )
    return TEXT[L].format(**V)


CSS = """<style>
  .doc .kicker { font-family: var(--hand); color: var(--fire); font-size: 16px; margin-bottom: 4px; }
  .facts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 22px 0 26px; }
  .fact { padding: 14px 14px 12px; }
  .fact b { display: block; font-family: var(--hand); font-size: 34px; line-height: 1.1; color: var(--fire); }
  .fact span { display: block; font-size: 13.5px; color: var(--ink-2); line-height: 1.35; margin-top: 4px; }
  @media (max-width: 760px) { .facts { grid-template-columns: repeat(2, 1fr); } }
  .rfig { margin: 18px 0 8px; }
  .rfig figcaption { font-size: 14px; color: var(--ink-2); margin-bottom: 4px; }
  .rchart { display: block; width: 100%; height: auto; overflow: visible; }
  .fact b[dir="ltr"] { unicode-bidi: isolate; }
  .rchart .grid { stroke: var(--hair); }
  .rchart .tick { font: 13px var(--sans); fill: var(--ink-3); }
  .rchart .axis { font: 13.5px var(--sans); fill: var(--ink-2); }
  .rchart .lab { font: 700 15px var(--hand); }
  .rchart .b-ours { fill: #d9822b; } .rchart .b-off { fill: #efd3b4; }
  .doc td .muted { font-size: 13px; }
  .doc td, .doc th { white-space: nowrap; }
  .doc td:first-child, .doc th:first-child { white-space: normal; }
</style>
"""


def main():
    arts = {L: article(L) for L in bp.LANGS}
    jsonld = {"@context": "https://schema.org", "@type": "Report", "@id": f"{bp.SITE}/report/two-punjabs/#report",
              "name": "Two Punjabs: seven seasons of crop fires", "headline": "Two Punjabs: seven seasons of crop fires",
              "url": f"{bp.SITE}/report/two-punjabs/", "datePublished": "2026-10-20", "inLanguage": ["en", "ur", "hi"],
              "author": bp.ORG, "publisher": bp.ORG, "isPartOf": {"@id": f"{bp.SITE}/#website"},
              "about": ["Crop residue burning in Pakistani Punjab", "Crop residue burning in Indian Punjab and Haryana", "Satellite fire detection"],
              "abstract": f"Satellite-detected crop fires in Indian Punjab fell {in_fall}% between {peak_in} and {last}; in Pakistani Punjab they did not fall. "
                          f"Since {cross} NASA's Suomi NPP has seen more crop fires in Pakistani Punjab, {ratio_last:.1f} times as many in {last}. "
                          "Part of India's fall reflects burning moved out of the satellite's view.",
              "image": f"{bp.SITE}/og/two-punjabs.png",
              "isBasedOn": {"@type": "Dataset", "name": "Two Punjabs season statistics", "url": f"{bp.SITE}/report/two-punjabs/seasons.json",
                            "license": "https://creativecommons.org/licenses/by/4.0/"}}
    out = bp.page("/report/two-punjabs/", "Two Punjabs: seven seasons of crop fires",
                  f"NASA saw crop fires fall {in_fall}% in Indian Punjab from {peak_in} to {last}, but not in Pakistani Punjab, which has had more since {cross}.",
                  arts, jsonld, extra_head=CSS, wide=True, og_image="/og/two-punjabs.png",
                  og_alt=f"Two Punjabs: crop fires fell {in_fall}% in Indian Punjab but not in Pakistani Punjab, which had {ratio_last:.1f} times as many in {last}")
    open(os.path.join(DIR, "index.html"), "w", encoding="utf-8").write(out)
    print(f"report written: India -{in_fall}% since {peak_in}, Pakistan {pk_vs_2019:+}% since {YEARS[0]}, crossed {cross}, r={r:.3f}")


if __name__ == "__main__":
    main()
