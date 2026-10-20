#!/usr/bin/env python3
"""Build the "Two Punjabs" report (site/public/report/two-punjabs/index.html) from seasons.json.

The numbers come from scripts/season-stats.py; this only lays them out. Charts are static SVG so
the page works without JavaScript and prints cleanly. English for now; the Urdu and Hindi tabs
say so and link to the trilingual trends page.

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
NAME = {PK: "Pakistani Punjab", IN: "Indian Punjab", HR: "Haryana"}
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


def line_chart(series, fmt, label, end_fmt, W=640, H=300):
    """series: {key: [values per YEARS]}. Returns an inline SVG."""
    m = {"l": 58, "r": 130, "t": 28, "b": 34}
    top, step = axis_max(max(v for vals in series.values() for v in vals))
    x = lambda i: m["l"] + i * (W - m["l"] - m["r"]) / (len(YEARS) - 1)
    y = lambda v: H - m["b"] - v / top * (H - m["t"] - m["b"])
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}" class="rchart">',
           f'<text x="{m["l"]}" y="14" class="axis">{escape(label)}</text>']
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
        out += [f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3.5" fill="{COL[k]}"><title>{NAME[k]} {yr}: {fmt(v)}</title></circle>'
                for i, (yr, v) in enumerate(zip(YEARS, vals))]
        ends.append([y(vals[-1]) + 5, k, vals[-1]])
    # Each label is two lines (~30 px). Stack them upwards from the lowest so none reach the year axis.
    ends.sort(reverse=True)
    ends[0][0] = min(ends[0][0], H - m["b"] - 22)
    for i in range(1, len(ends)):
        ends[i][0] = min(ends[i][0], ends[i - 1][0] - 32)
    for ly, k, v in ends:
        out.append(f'<text x="{W - m["r"] + 12}" y="{ly:.1f}" class="lab" fill="{COL[k]}">{NAME[k]}</text>'
                   f'<text x="{W - m["r"] + 12}" y="{ly + 15:.1f}" class="tick">{end_fmt(v)} in {YEARS[-1]}</text>')
    out.append("</svg>")
    return "".join(out)


def pair_bars(a, b, la, lb, label, W=640, H=270):
    """Two bars per season: a (ours) and b (official)."""
    m = {"l": 58, "r": 10, "t": 28, "b": 34}
    top, step = axis_max(max(max(a), max(b)))
    band = (W - m["l"] - m["r"]) / len(YEARS)
    bw = band * 0.32
    y = lambda v: H - m["b"] - v / top * (H - m["t"] - m["b"])
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}" class="rchart">',
           f'<text x="{m["l"]}" y="14" class="axis">{escape(label)}</text>']
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
    out.append("</svg>")
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


def peak_week(k, y):
    daily = S[str(y)][k]["daily"]
    days = sorted(daily)
    best = max(range(len(days)), key=lambda i: sum(daily[d] for d in days[i:i + 7]))
    from datetime import date
    d0 = date.fromisoformat(days[best])
    return f"{d0.day} {d0:%b}"


# ---------- Article ----------
rows_valid = "".join(f"<tr><td>{y}</td><td>{f(a)}</td><td>{f(b)}</td><td>{a / b:.0%}</td></tr>" for y, a, b in zip(YEARS, ours, off))
rows_tot = "".join(f"<tr><td>{y}</td><td>{f(tot(PK, y))}</td><td>{f(tot(IN, y))}</td><td>{f(tot(HR, y))}</td><td>{tot(PK, y) / tot(IN, y):.2f}</td></tr>" for y in YEARS)
rows_night = "".join(f"<tr><td>{y}</td>" + "".join(f"<td>{S[str(y)][k]['night']:,} <span class=\"muted\">({night(k, y):.1%})</span></td>" for k in (PK, IN, HR)) + "</tr>" for y in YEARS)
rows_d = "".join(f"<tr><td>{escape(d)}</td>" + "".join(f"<td>{f(pk_d[d].get(y, 0))}</td>" for y in YEARS) + "</tr>" for d in top_pk)
rows_peak = "".join(f"<tr><td>{y}</td><td>{peak_week(PK, y)}</td><td>{peak_week(IN, y)}</td></tr>" for y in YEARS)
in_top = {y: [d for d in S[str(y)][IN]["districts"] if d != UNNAMED][:3] for y in YEARS}

chart_tot = line_chart({k: [tot(k, y) for y in YEARS] for k in (IN, PK, HR)}, lambda v: f"{v / 1000:g}k",
                       "Fire spots seen by Suomi NPP, 1 Oct–30 Nov", f)
chart_night = line_chart({k: [night(k, y) * 100 for y in YEARS] for k in (PK, IN, HR)}, lambda v: f"{v:g}%",
                         "Share of fires seen on the 1:30 am pass", lambda v: f"{v:.1f}%")
chart_valid = pair_bars(ours, off, "our count", "official count", "Indian Punjab: our count (dark) vs India's official count (light)")

EN = f"""  <p class="kicker">Report · {bp.fmt_date("2026-10-20", "en")}</p>
  <h1>Two Punjabs: seven seasons of crop fires</h1>
  <p class="lede">Between {peak_in} and {last}, the crop fires NASA's satellites saw in Indian Punjab fell by {in_fall}%. Across the border, Pakistani Punjab ended higher than it started: {f(tot(PK, YEARS[0]))} fire spots in {YEARS[0]}, {f(tot(PK, last))} in {last}. Since {cross}, the satellite has seen more crop fires in Pakistani Punjab than in Indian Punjab, and in {last} it saw {ratio_last:.1f} times as many.</p>

  <div class="facts">
    <div class="fact sketch"><b>−{in_fall}%</b><span>Indian Punjab, {peak_in} to {last}</span></div>
    <div class="fact sketch"><b>{"+" if pk_vs_2019 >= 0 else ""}{pk_vs_2019}%</b><span>Pakistani Punjab, {YEARS[0]} to {last}</span></div>
    <div class="fact sketch"><b>{ratio_last:.1f}×</b><span>Pakistani vs Indian Punjab, {last}</span></div>
    <div class="fact sketch"><b>{r:.2f}</b><span>match with India's official counts</span></div>
  </div>

  <p>This is the first season-by-season comparison of both Punjabs counted the same way that we know of. India publishes daily fire counts for its states, and its press reports them every day of the season. We could find no equivalent public series for Pakistani Punjab. To compare the two fairly we counted every fire spot NASA's Suomi NPP satellite saw on either side of the border in each October and November since 2019, using one method throughout.</p>

  <h2 id="crossed">The lines crossed in {cross}</h2>
  {chart_tot}
  <p>Indian Punjab's count rose to a peak of {f(tot(IN, peak_in))} in {peak_in}, then fell every year to {f(tot(IN, last))} in {last}. Haryana followed the same path at a smaller scale. Pakistani Punjab stayed between {f(min(tot(PK, y) for y in YEARS if y != 2021))} and {f(max(tot(PK, y) for y in YEARS if y != 2021))} every season except 2021, when it reached {f(tot(PK, 2021))}, and ended {last} {pk_vs_2019}% above where it started.</p>
  <p>In {last}, three Pakistani districts alone, {escape(top3[0])}, {escape(top3[1])} and {escape(top3[2])}, had {f(top3_sum)} fire spots between them, more than all of Indian Punjab ({f(tot(IN, last))}).</p>
  <div class="table-wrap"><table>
    <tr><th>Season</th><th>Pakistani Punjab</th><th>Indian Punjab</th><th>Haryana</th><th>Pakistan ÷ India</th></tr>
    {rows_tot}
  </table></div>

  <h2 id="check">Can these counts be trusted?</h2>
  <p>We checked our method against India's official figures, which come from the same kind of satellite data, processed by India's Commission for Air Quality Management and the Punjab Remote Sensing Centre. Across seven seasons the two series move together almost perfectly (correlation {r:.3f}). Ours run at {min(ratios):.0%}–{max(ratios):.0%} of the official numbers, which is expected: we count only one satellite and only from 1 October, while India's season starts on 15 September. The one year they disagree on direction is 2021, which we count as slightly up on 2020 and India counts as slightly down. Our busiest Indian districts each year (in {last}: {", ".join(escape(d) for d in in_top[last])}) are also the ones the Indian press named.</p>
  <p>Because the same code counts both sides of the border, the Pakistani numbers are as reliable as the Indian ones. Pakistan doesn't publish a comparable count, so there's no official figure to check them against directly.</p>
  {chart_valid}
  <div class="table-wrap"><table>
    <tr><th>Season</th><th>Our count (Suomi NPP, 1 Oct–30 Nov)</th><th>India's official count (15 Sep–30 Nov)</th><th>Ours as share</th></tr>
    {rows_valid}
  </table></div>

  <h2 id="missed">Fewer fires, or fires the satellite missed?</h2>
  <p>Fire counts are a floor, not a total. A polar-orbiting satellite like Suomi NPP passes over around 1:30 pm and 1:30 am, and only sees a fire that is burning at that moment. Over the past two seasons, Indian researchers and NASA scientist Hiren Jethva have shown that many farmers in Indian Punjab now burn in the late afternoon, after the daytime pass. The think tank iFOREST, using a European geostationary satellite that looks every 15 minutes, found that over 90% of large farm fires in Punjab in 2024 and 2025 started after 3 pm, against 3% in 2021. Burnt-area maps tell the same story: iFOREST puts Punjab's burnt area at about 20,000 km² in 2025, down from 31,447 km² in 2022, a fall of about a third rather than the {-pct(tot(IN, last), tot(IN, 2022))}% fall in fire counts.</p>
  <p>Our own data shows a trace of this shift. The night pass catches very few crop fires anywhere, but in Indian Punjab and Haryana the night count held steady or rose while daytime fires collapsed, so the share caught at night went up sharply. In Pakistani Punjab it stayed flat, at around 3–6% every season.</p>
  {chart_night}
  <div class="table-wrap"><table>
    <tr><th>Season</th><th>Pakistani Punjab</th><th>Indian Punjab</th><th>Haryana</th></tr>
    {rows_night}
  </table></div>
  <p>So two things are true at once. Burning in Indian Punjab has really fallen, but by much less than the fire counts say, because more of it now happens out of the satellite's sight. In Pakistani Punjab we see no sign of the same shift: the counts haven't fallen and the night share hasn't moved. That makes the gap between the two Punjabs in recent seasons partly an artefact of timing, and the true gap is probably smaller than {ratio_last:.1f} times. It does not make it disappear: on the counts that both sides are measured by, Pakistani Punjab went from a quarter of India's number to well over it. Settling the real size of the gap needs geostationary or burnt-area data for the Pakistani side, which nobody has published.</p>

  <h2 id="where">Where in Pakistani Punjab</h2>
  <p>The burning is concentrated in the rice belt between Lahore, Gujranwala and Jhang. The same handful of districts lead every season. Spots the place-name data couldn't put in a district ({f(sum(S[str(y)][PK]["districts"].get(UNNAMED, 0) for y in YEARS))} over seven seasons) are left out of this table.</p>
  <div class="table-wrap"><table>
    <tr><th>District</th>{"".join(f"<th>{y}</th>" for y in YEARS)}</tr>
    {rows_d}
  </table></div>
  <p>Watch any season move district by district on the <a href="/trends/#districts">fire trends map</a>.</p>

  <h2 id="when">When the burning peaks</h2>
  <p>The busiest week usually starts in the last days of October or the first days of November on both sides. In 2023 and 2024 Pakistani Punjab peaked about two weeks later than Indian Punjab, in mid-November.</p>
  <div class="table-wrap"><table>
    <tr><th>Season</th><th>Pakistani Punjab: busiest week starts</th><th>Indian Punjab: busiest week starts</th></tr>
    {rows_peak}
  </table></div>

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
  <p class="muted">Sources for others' findings: iFOREST's geostationary analysis and Hiren Jethva's observations as reported by <a href="https://www.tribuneindia.com/news/delhi/satellites-miss-majority-of-stubble-fires-delhi-air-pollution-underestimated-report">The Tribune</a> and <a href="https://healthpolicy-watch.news/delhi-air-pollution-are-government-satellites-missing-the-stubble-fires/">Health Policy Watch</a>; CEEW's <a href="https://www.ceew.in/blogs/how-does-satellite-technology-detect-punjab-stubble-burning-fires">explainer on satellite detection</a>; India's official counts as reported by <a href="https://www.tribuneindia.com/news/punjab/farm-fires-down-by-27-in-punjab-37-in-haryana-compared-to-last-year-environment-ministry-567656">The Tribune</a> and <a href="https://www.tribuneindia.com/news/india/punjab-haryana-record-90-per-cent-fewer-farm-fire-incidents-in-2025-govt-in-lok-sabha/amp">The Tribune (2025)</a>.</p>
  <p>Please cite as: HamariHawa, "Two Punjabs: seven seasons of crop fires", hamarihawa.org/report/two-punjabs/, October 2026.</p>"""

NOTE = {
    "ur": '<p class="callout sketch">یہ رپورٹ فی الحال صرف انگریزی میں ہے۔ اس کے چارٹ اردو میں <a href="/trends/">آگ کا رجحان</a> صفحے پر دیکھیں۔</p>',
    "hi": '<p class="callout sketch">यह रिपोर्ट अभी सिर्फ़ अंग्रेज़ी में है। इसके चार्ट हिंदी में <a href="/trends/">आग का रुझान</a> पेज पर देखें।</p>',
}

CSS = """<style>
  .doc .kicker { font-family: var(--hand); color: var(--fire); font-size: 16px; margin-bottom: 4px; }
  .facts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 22px 0 26px; }
  .fact { padding: 14px 14px 12px; }
  .fact b { display: block; font-family: var(--hand); font-size: 34px; line-height: 1.1; color: var(--fire); }
  .fact span { display: block; font-size: 13.5px; color: var(--ink-2); line-height: 1.35; margin-top: 4px; }
  @media (max-width: 760px) { .facts { grid-template-columns: repeat(2, 1fr); } }
  .rchart { display: block; width: 100%; height: auto; margin: 16px 0 8px; overflow: visible; }
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
    arts = {"en": EN, "ur": NOTE["ur"] + "\n" + EN, "hi": NOTE["hi"] + "\n" + EN}
    jsonld = {"@context": "https://schema.org", "@type": "Report", "@id": f"{bp.SITE}/report/two-punjabs/#report",
              "name": "Two Punjabs: seven seasons of crop fires", "headline": "Two Punjabs: seven seasons of crop fires",
              "url": f"{bp.SITE}/report/two-punjabs/", "datePublished": "2026-10-20", "inLanguage": "en",
              "author": bp.ORG, "publisher": bp.ORG, "isPartOf": {"@id": f"{bp.SITE}/#website"},
              "about": ["Crop residue burning in Pakistani Punjab", "Crop residue burning in Indian Punjab and Haryana", "Satellite fire detection"],
              "abstract": f"Satellite-detected crop fires in Indian Punjab fell {in_fall}% between {peak_in} and {last}; in Pakistani Punjab they did not fall. "
                          f"Since {cross} NASA's Suomi NPP has seen more crop fires in Pakistani Punjab, {ratio_last:.1f} times as many in {last}. "
                          "Part of India's fall reflects burning moved out of the satellite's view.",
              "isBasedOn": {"@type": "Dataset", "name": "Two Punjabs season statistics", "url": f"{bp.SITE}/report/two-punjabs/seasons.json",
                            "license": "https://creativecommons.org/licenses/by/4.0/"}}
    out = bp.page("/report/two-punjabs/", "Two Punjabs: seven seasons of crop fires",
                  f"Crop fires seen by NASA's satellites fell {in_fall}% in Indian Punjab from {peak_in} to {last} but not in Pakistani Punjab, "
                  f"which has had more since {cross}. District counts, peak weeks, a check against India's official numbers, and why fire counts undercount.",
                  arts, jsonld, extra_head=CSS, wide=True)
    open(os.path.join(DIR, "index.html"), "w", encoding="utf-8").write(out)
    print(f"report written: India -{in_fall}% since {peak_in}, Pakistan {pk_vs_2019:+}% since {YEARS[0]}, crossed {cross}, r={r:.3f}")


if __name__ == "__main__":
    main()
