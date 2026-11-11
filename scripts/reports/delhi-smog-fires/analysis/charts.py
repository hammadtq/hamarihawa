# Charts for the Delhi report, drawn from site/public/report/delhi-smog-fires/data.json . python3 charts.py [en|ur|hi]
import json, os
from i18n import T, FONT, save, OUT, LANG
def J(s): return ('\u2067' + s.replace('\u2067', '').replace('\u2069', '') + '\u2069') if LANG == 'ur' else s   # a label built from several pieces: one right-to-left run in Urdu
E = {e['id']: e['value'] for e in json.load(open(os.path.join(OUT, 'data.json')))['evidence']}
INK, MUT, RED, PALE, BLUE, GREY = '#1d1d1b', '#7c7c80', '#d62d20', '#e8a29b', '#8aa6c1', '#c9c9c4'
def head(W, H, title, sub, aria):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" aria-label="{aria}">', '<rect width="100%" height="100%" fill="#fff"/>',
            f'<text x="46" y="18" font-size="14" font-weight="700" fill="{INK}">{title}</text>', f'<text x="46" y="33" font-size="10.5" fill="{MUT}">{sub}</text>']
MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# 1 monthly PM2.5 (with days of data) and the mixing-height climatology
W, H = 720, 462; L, R = 46, 14; t1, h1, t2, h2 = 62, 190, 334, 76
mon = E['pm_monthly_12']; keys = list(mon); cl = E['weather_climatology']
o = head(W, H, T("Delhi's fine particles (PM2.5) month by month, µg/m³"), T('Mean of the daily city values (median across government monitors), November 2025 to October 2026. Under each bar: days with a value'), T('Delhi monthly PM2.5 and mixing-height climatology'))
bw = (W - L - R) / 12; y = lambda v: t1 + h1 - v / 250 * h1
for g in (50, 100, 150, 200, 250):
    o.append(f'<line x1="{L}" x2="{W-R}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="#eee"/><text x="{L-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{MUT}">{g}</text>')
for i, k in enumerate(keys):
    v = mon[k]['mean']; m = int(k[5:]); x = L + i * bw + 4; cx = x + (bw - 8) / 2
    o.append(f'<rect x="{x:.1f}" y="{y(v):.1f}" width="{bw-8:.1f}" height="{t1+h1-y(v):.1f}" fill="{RED if m in (10, 11, 12, 1) else PALE}" rx="2"/>')
    o.append(f'<text x="{cx:.1f}" y="{(y(40)-5 if 30 <= v <= 44 else y(v)-4):.1f}" font-size="9.5" text-anchor="middle" fill="#3a3935">{v}</text><text x="{cx:.1f}" y="{t1+h1+14}" font-size="10" text-anchor="middle" fill="#3a3935">{T(MN[m-1])}</text>')
    o.append(f'<text x="{cx:.1f}" y="{t1+h1+26}" font-size="8.5" text-anchor="middle" fill="{MUT}">{mon[k]["days"]}/{mon[k]["days_in_month"]}</text>')
STD_LABEL = T("India's annual standard (40), shown as a benchmark")
o.append(f'<line x1="{L}" x2="{W-R}" y1="{y(40):.1f}" y2="{y(40):.1f}" stroke="{INK}" stroke-dasharray="5 3"/><line x1="{L}" x2="{L+22}" y1="48" y2="48" stroke="{INK}" stroke-dasharray="5 3"/><text x="{L+28}" y="51" font-size="9.5" fill="{INK}">{STD_LABEL}</text>')
o.append(f'<text x="{L}" y="{t1+h1+40}" font-size="9.5" fill="{MUT}">2025</text><text x="{L+bw*2+4}" y="{t1+h1+40}" font-size="9.5" fill="{MUT}">2026</text>')
o.append(f'<text x="{L}" y="{t2-14}" font-size="12" font-weight="700" fill="{INK}">{T("How deep the air is that pollution mixes into (mixing height), metres: 2016–2025 average for each month")}</text>')
yb = lambda v: t2 + h2 - v / 900 * h2
for i, k in enumerate(keys):
    v = cl[str(int(k[5:]))]['blh']; x = L + i * bw + 4
    o.append(f'<rect x="{x:.1f}" y="{yb(v):.1f}" width="{bw-8:.1f}" height="{t2+h2-yb(v):.1f}" fill="{BLUE}" rx="2"/><text x="{x+(bw-8)/2:.1f}" y="{yb(v)-4:.1f}" font-size="9.5" text-anchor="middle" fill="#3a3935">{v}</text>')
    o.append(f'<text x="{x+(bw-8)/2:.1f}" y="{t2+h2+14}" font-size="10" text-anchor="middle" fill="#3a3935">{T(MN[int(k[5:])-1])}</text>')
o.append(f'<text x="{L}" y="{H-18}" font-size="9" fill="{MUT}">{T("The city value is a median of monitors within 25 km of central Delhi, not a regulatory average. Missing days are not filled.")}</text>')
o.append(f'<text x="{L}" y="{H-6}" font-size="9" fill="{MUT}">{T("Mixing height: ERA5, all hours, a ten-year average and not the weather of these twelve months. HamariHawa.")}</text></svg>')
save('baseline', '\n'.join(o))
# 2 fire detections by year and Delhi's November mean
W, H = 720, 412; L, R = 46, 46; t, h = 50, 262
fv = E['fires_by_year']; ys = list(fv); bw = (W - L - R) / len(ys)
o = head(W, H, T('Satellite fire detections by year, and Delhi’s November average'), T('Bars: MODIS detections in Indian Punjab and Haryana, 1 Oct–30 Nov. Dots: Delhi mean PM2.5 in November, µg/m³'), T('Fire detections by year against Delhi November PM2.5'))
top = 20000; yf = lambda v: t + h - v / top * h; yp = lambda v: t + h - v / 300 * h
for g in (5000, 10000, 15000, 20000):
    o.append(f'<line x1="{L}" x2="{W-R}" y1="{yf(g):.1f}" y2="{yf(g):.1f}" stroke="#eee"/><text x="{L-6}" y="{yf(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{MUT}">{g:,}</text><text x="{W-R+6}" y="{yf(g)+3:.1f}" font-size="9.5" fill="{RED}">{g*300//top}</text>')
for i, k in enumerate(ys):
    r = fv[k]; x = L + i * bw + 6; v = r['punjab_haryana']; cx = x + (bw - 12) / 2
    o.append(f'<rect x="{x:.1f}" y="{yf(v):.1f}" width="{bw-12:.1f}" height="{t+h-yf(v):.1f}" fill="{GREY if not r["partial"] else "#e4e4df"}" rx="2"/><text x="{cx:.1f}" y="{t+h-5}" font-size="9" text-anchor="middle" fill="#3a3935">{v:,}</text>')
    o.append(f'<text x="{cx:.1f}" y="{t+h+14}" font-size="10" text-anchor="middle" fill="#3a3935">{k}{"*" if r["partial"] else ""}</text>')
    if r['delhi_nov_mean'] and not r['partial']:
        o.append(f'<circle cx="{cx:.1f}" cy="{yp(r["delhi_nov_mean"]):.1f}" r="5" fill="{RED}"/><text x="{cx:.1f}" y="{yp(r["delhi_nov_mean"])-9:.1f}" font-size="10" font-weight="700" text-anchor="middle" fill="{RED}">{r["delhi_nov_mean"]}</text>')
        o.append(f'<text x="{cx:.1f}" y="{t+h+26}" font-size="8.5" text-anchor="middle" fill="{MUT}">{J(str(r["delhi_nov_days"]) + " " + T("days"))}</text>')
    elif not r['partial']:
        o.append(f'<text x="{cx:.1f}" y="{t+h+26}" font-size="8.5" text-anchor="middle" fill="{MUT}">{J(str(r["delhi_nov_days"]) + " " + (T("day") if r["delhi_nov_days"] == 1 else T("days"))) if r["delhi_nov_days"] else T("no data")}</text>')
o.append(f'<text x="{L}" y="{H-32}" font-size="9" fill="{MUT}">{T("Detections are not fires, burnt area or emissions. The satellites sample fires at particular times of day; burning has moved later")}</text>')
o.append(f'<text x="{L}" y="{H-20}" font-size="9" fill="{MUT}">{T("and orbits have drifted, so the years are not sampled alike. A fall in detections does not imply an equal fall in burnt area or emissions.")}</text>')
o.append(f'<text x="{L}" y="{H-8}" font-size="9" fill="{MUT}">{T("*2026: to 10 November. Under each year: November days with a Delhi value; an average is shown only with 15 or more. HamariHawa.")}</text></svg>')
save('fires-by-year', '\n'.join(o))
# 3 median PM2.5 by upstream fire-detection category within each part of the season
W, H = 720, 388; L, R = 46, 14; t, h = 50, 240
P = E['path_index_days']; tab = E['pm_by_path_index']['pooled_thirds']; parts = list(tab); gw = (W - L - R) / 3
o = head(W, H, T('Delhi’s PM2.5 by fire detections near the path of the arriving air, µg/m³'), J(T('Median of daily city values, ') + str(P['days']) + T(' days in 15 Oct–30 Nov of 2016–2021, 2025 and 2026, within each part of the season')), T('Delhi PM2.5 by upstream fire-detection category within each part of the season'))
y = lambda v: t + h - v / 400 * h
for g in (100, 200, 300, 400):
    o.append(f'<line x1="{L}" x2="{W-R}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="#eee"/><text x="{L-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{MUT}">{g}</text>')
COL = {'few': GREY, 'some': PALE, 'many': RED}; LAB = {'few': 'Few detections near the path', 'some': 'Some', 'many': 'Many detections near the path'}
for i, p in enumerate(parts):
    for j, k in enumerate(('few', 'some', 'many')):
        c = tab[p][k]; x = L + i * gw + 20 + j * (gw - 40) / 3; w = (gw - 40) / 3 - 6
        if c['median'] is not None:
            o.append(f'<rect x="{x:.1f}" y="{y(c["median"]):.1f}" width="{w:.1f}" height="{t+h-y(c["median"]):.1f}" fill="{COL[k]}" rx="2"/><text x="{x+w/2:.1f}" y="{y(c["median"])-4:.1f}" font-size="10" font-weight="700" text-anchor="middle" fill="#3a3935">{c["median"]}</text>')
        o.append(f'<text x="{x+w/2:.1f}" y="{t+h+13}" font-size="9" text-anchor="middle" fill="{MUT}">{J(str(c["days"]) + " " + T("days"))}</text>')
    o.append(f'<text x="{L+i*gw+gw/2:.1f}" y="{t+h+30}" font-size="11.5" font-weight="700" text-anchor="middle" fill="{INK}">{T(p)}</text>')
for j, k in enumerate(('few', 'some', 'many')):
    o.append(f'<rect x="{L+j*200}" y="{H-50}" width="10" height="10" fill="{COL[k]}" rx="2"/><text x="{L+j*200+15}" y="{H-41}" font-size="10" fill="#3a3935">{T(LAB[k])}</text>')
o.append(f'<text x="{L}" y="{H-20}" font-size="9" fill="{MUT}">{T("Categories are thirds of all days by the number of MODIS detections within 25 km of the 48-hour back-path, around the time the air passed.")}</text>')
o.append(f'<text x="{L}" y="{H-8}" font-size="9" fill="{MUT}">{T("An association between groups of days. It does not measure how much of the pollution came from fires. HamariHawa.")}</text></svg>')
save('path-fires', '\n'.join(o))
# 4 peak fire-week days beside their ventilation-matched December-January days (two measured averages side by side, not components)
W, H = 720, 392; L, R = 46, 14; t, h = 62, 228
G = E['matched_comparison']; gw = (W - L - R) / 3
o = head(W, H, T('Fire-week days and winter days with similar ventilation: Delhi’s PM2.5, µg/m³'), J(T('Average of ') + str(G['days']) + T(' days in 25 Oct–20 Nov and of their paired December–January days, by category of the index')), T('Delhi PM2.5 on peak fire-week days and on ventilation-matched winter days, by upstream fire-detection category'))
y = lambda v: t + h - v / 320 * h
for g in (100, 200, 300):
    o.append(f'<line x1="{L}" x2="{W-R}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="#eee"/><text x="{L-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="{MUT}">{g}</text>')
for i, k in enumerate(('few', 'some', 'many')):
    c = G[k]; x0 = L + i * gw + 34; w = (gw - 68) / 2 - 4
    for j, (v, col) in enumerate(((c['mean_pm'], RED), (c['matched_winter'], GREY))):
        x = x0 + j * (w + 8)
        o.append(f'<rect x="{x:.1f}" y="{y(v):.1f}" width="{w:.1f}" height="{t+h-y(v):.1f}" fill="{col}" rx="2"/><text x="{x+w/2:.1f}" y="{y(v)-5:.1f}" font-size="11" font-weight="700" text-anchor="middle" fill="#3a3935">{v}</text>')
    o.append(f'<text x="{L+i*gw+gw/2:.1f}" y="{t+h+15}" font-size="11.5" font-weight="700" text-anchor="middle" fill="{INK}">{T(LAB[k])}</text><text x="{L+i*gw+gw/2:.1f}" y="{t+h+29}" font-size="9.5" text-anchor="middle" fill="{MUT}">{J(str(c["days"]) + " " + T("days"))}</text>')
o.append(f'<rect x="{L}" y="{H-52}" width="10" height="10" fill="{RED}"/><text x="{L+15}" y="{H-43}" font-size="10" fill="#3a3935">{T("Days of 25 Oct–20 Nov")}</text>')
o.append(f'<rect x="{L+170}" y="{H-52}" width="10" height="10" fill="{GREY}"/><text x="{L+185}" y="{H-43}" font-size="10" fill="#3a3935">{T("December–January days of the same season with similar ventilation")}</text>')
o.append(f'<text x="{L}" y="{H-20}" font-size="9" fill="{MUT}">{T("Matched on one measure only (mixing height × wind speed). The gap between the bars is not the amount caused by fires:")}</text>')
o.append(f'<text x="{L}" y="{H-8}" font-size="9" fill="{MUT}">{T("temperature, humidity, fireworks and the mix of sources also differ between these weeks and midwinter. HamariHawa.")}</text></svg>')
save('fire-weeks', '\n'.join(o))
