# Decode GIBS PNGs back to AOD values via the layer's GIBS colormap, then summarise per season.
import os, re, sys, glob, statistics as st, collections, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pngdecode
H = sys.argv[1]
def cmap(fn):
    m = {}
    for e in re.finditer(r'<ColorMapEntry rgb="(\d+),(\d+),(\d+)"([^>]*)/>', open(fn).read()):
        attrs = e.group(4)
        if 'nodata="true"' in attrs: continue
        v = re.search(r' value="\[([^,\]]+)(?:,([^)\]]+))?[)\]]"', attrs)
        if not v: continue
        lo = float(v.group(1).replace('-INF', '-1')); hi = v.group(2)
        hi = lo if hi is None or 'INF' in hi else float(hi)
        m[(int(e.group(1)), int(e.group(2)), int(e.group(3)))] = (lo, hi)
    return m
def values(png, cm):
    w, h, px = pngdecode.decode(open(png, 'rb').read()); vals = []; bad = 0
    for r, g, b, a in px:
        if a == 0: continue
        k = (r, g, b)
        if k in cm: lo, hi = cm[k]; vals.append(((lo + hi) / 2, lo, hi))
        else: bad += 1
    return vals, bad, w * h
out = []
# MERRA-2 monthly (20x20 px over 2x2 deg around Lahore; take the centre 4x4 px ~ 0.4 deg)
cm = cmap(os.path.join(H, 'raw', 'aod', 'cmap_MERRA2_Total_Aerosol_Optical_Thickness_550nm_Extinction_Monthly.xml'))
print('MERRA-2 total AOD 550nm, monthly, ~0.4 deg box centred on Lahore (colour bins of 0.005; top bin is >=0.9)')
print('year | Oct | Nov | Dec')
mrows = []
for y in range(1980, 2026):
    row = [y]
    for m in (10, 11, 12):
        fn = os.path.join(H, 'raw', 'aod', 'merra2', f'{y}-{m:02d}.png')
        w, h, px = pngdecode.decode(open(fn, 'rb').read())
        sub = [px[j * w + i] for j in range(8, 12) for i in range(8, 12)]
        v = []; sat = 0
        for r, g, b, a in sub:
            if a and (r, g, b) in cm:
                lo, hi = cm[(r, g, b)]; v.append((lo + hi) / 2 if hi > lo else lo); sat += hi == lo and lo >= 0.9
        row.append((round(st.mean(v), 3) if v else None, sat))
    mrows.append(row)
    print(y, '|', ' | '.join(f"{x[0]}{'(sat)' if x[1] else ''}" for x in row[1:]))
with open(os.path.join(H, 'out', 'merra2_aod_monthly.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['year', 'oct', 'oct_sat_px', 'nov', 'nov_sat_px', 'dec', 'dec_sat_px'])
    for r in mrows: w.writerow([r[0]] + [z for x in r[1:] for z in x])
# MODIS Deep Blue combined, daily, 15 Oct-30 Nov, ~25 km box
cm = cmap(os.path.join(H, 'raw', 'aod', 'cmap_MODIS_VIIRS_AOD.xml'))
for sensor in ('terra_db', 'aqua_db'):
    print(f'\nMODIS {sensor} AOD 550nm, 15 Oct-30 Nov, pixels within 31.33-31.77N 74.08-74.60E')
    print('year | days with any retrieval | pixel-days | median AOD | mean AOD (bin midpoints) | % pixels >=0.7 | % >=1.13')
    rows = []
    for y in range(2000, 2027):
        files = sorted(glob.glob(os.path.join(H, 'raw', 'aod', sensor, f'{y}-*.png')))
        if not files: continue
        allv = []; ndays = 0; unk = 0
        for fn in files:
            v, bad, n = values(fn, cm); unk += bad
            if v: ndays += 1; allv += [x[0] for x in v]
        if not allv: print(y, '| 0'); continue
        r = dict(year=y, days=ndays, nfiles=len(files), pixels=len(allv), median=round(st.median(allv), 2), mean=round(st.mean(allv), 2),
                 ge07=round(100 * sum(1 for x in allv if x >= 0.7) / len(allv)), ge113=round(100 * sum(1 for x in allv if x >= 1.13) / len(allv)), unmatched=unk)
        rows.append(r)
        print(f"{y}{'*' if len(files) < 47 else ''} | {ndays}/{len(files)} | {r['pixels']} | {r['median']} | {r['mean']} | {r['ge07']} | {r['ge113']} | unmatched px {unk}")
    with open(os.path.join(H, 'out', f'modis_{sensor}_aod_season.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
