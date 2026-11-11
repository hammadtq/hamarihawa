# Daily MAIAC aerosol optical depth (GIBS PNG decoded through the layer colour map) averaged over three boxes:
# Punjab fire belt (29.8-31.3N, 74.5-76.5E), Haryana corridor (28.9-29.8N, 75.5-76.9E), Delhi (28.3-28.9N, 76.9-77.5E).
# Output out/aod_daily.csv: date, mean AOD and share of pixels retrieved for each box. Cloud and very thick smoke leave gaps.
import os, re, sys, glob, csv, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pngdecode
H = sys.argv[1]; SAT = os.path.join(H, 'raw', 'sat')
cm = {}
for e in re.finditer(r'<ColorMapEntry rgb="(\d+),(\d+),(\d+)"([^>]*)/>', open(glob.glob(os.path.join(SAT, 'cmap_*.xml'))[0]).read()):
    a = e.group(4)
    if 'nodata="true"' in a: continue
    v = re.search(r' value="[\[(]([^,\])]+)(?:,([^)\]]+))?[)\]]"', a)
    if not v: continue
    lo = float(v.group(1).replace('-INF', '0')); hi = v.group(2); hi = lo if hi is None or 'INF' in hi else float(hi)
    cm[(int(e.group(1)), int(e.group(2)), int(e.group(3)))] = (lo + hi) / 2
print('colour bins', len(cm), 'max', max(cm.values()))
W, Hh = 150, 130; X0, Y1, RES = 72.0, 33.0, 0.05
BOX = {'punjab': (29.8, 31.3, 74.5, 76.5), 'haryana': (28.9, 29.8, 75.5, 76.9), 'delhi': (28.3, 28.9, 76.9, 77.5)}
rows = []; unknown = 0
for fn in sorted(glob.glob(os.path.join(SAT, 'aod', '*.png'))):
    w, h, px = pngdecode.decode(open(fn, 'rb').read()); assert (w, h) == (W, Hh)
    r = dict(date=os.path.basename(fn)[:10])
    for name, (la0, la1, lo0, lo1) in BOX.items():
        vals = []; n = 0
        for j in range(int((Y1 - la1) / RES), int((Y1 - la0) / RES)):
            for i in range(int((lo0 - X0) / RES), int((lo1 - X0) / RES)):
                n += 1; p = px[j * W + i]
                if p[3] == 0: continue
                if p[:3] in cm: vals.append(cm[p[:3]])
                else: unknown += 1
        r[name] = round(st.mean(vals), 3) if vals else ''; r[name + '_cover'] = round(len(vals) / n, 2)
    rows.append(r)
with open(os.path.join(H, 'out', 'aod_daily.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('days', len(rows), 'unknown colours', unknown)
for r in rows[-12:]: print(r)
