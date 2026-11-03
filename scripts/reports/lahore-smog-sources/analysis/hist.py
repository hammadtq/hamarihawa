from i18n import T, FONT, save
import csv, os
H=os.path.dirname(os.path.abspath(__file__))+'/'
rows=[r for r in csv.DictReader(open(H+'firms_season_counts.csv')) if 2002<=int(r['year'])<=2025]
yrs=[int(r['year']) for r in rows]; IN=[int(r['IN_share_Nov_pct']) for r in rows]; PK=[int(r['PK_share_Nov_pct']) for r in rows]
dec=[('1970s',0.8),('1980s',4.4),('1990s',10.3),('2000s',13.9),('2010s',20.0),('2020–24',41.1)]
W,Ht=760,380
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Ht}" font-family="{FONT}" role="img" aria-label="{T("Charts: very low-visibility winter days at Amritsar by decade, and the share of MODIS active-fire detections in Punjab recorded in November, 2002 to 2025")}">','<rect width="100%" height="100%" fill="#fff"/>']
# left panel
x0,y0,w,h=40,70,300,230
o.append(f'<text x="20" y="22" font-size="14" font-weight="700" fill="#1d1d1b">{T("Very low-visibility winter days")}</text>')
o.append(f'<text x="20" y="38" font-size="10.5" fill="#55534e">{T("Share of December–January days with visibility under 1 km,")}</text><text x="20" y="52" font-size="10.5" fill="#55534e">{T("Amritsar airport, about 47 km from Lahore; unadjusted")}</text>')
for g in (0,10,20,30,40):
    y=y0+h-g/45*h; o.append(f'<line x1="{x0}" x2="{x0+w}" y1="{y:.1f}" y2="{y:.1f}" stroke="#eee"/><text x="{x0-5}" y="{y+3:.1f}" font-size="9.5" text-anchor="end" fill="#7c7c80">{g}%</text>')
bw=w/len(dec)
for i,(lab,v) in enumerate(dec):
    x=x0+i*bw+6; y=y0+h-v/45*h
    o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw-12:.1f}" height="{y0+h-y:.1f}" fill="#7d8ea0" rx="2"/>')
    o.append(f'<text x="{x+(bw-12)/2:.1f}" y="{y-4:.1f}" font-size="10" text-anchor="middle" fill="#1d1d1b">{v:g}%</text><text x="{x+(bw-12)/2:.1f}" y="{y0+h+14}" font-size="10" text-anchor="middle" fill="#3a3935">{T(lab)}</text>')
# right panel
X0,Y0,WW,HH=430,70,310,230
o.append(f'<text x="410" y="22" font-size="14" font-weight="700" fill="#1d1d1b">{T("When satellites detect fire activity")}</text>')
o.append(f'<text x="410" y="38" font-size="10.5" fill="#55534e">{T("Share of October–November MODIS active-fire detections")}</text><text x="410" y="52" font-size="10.5" fill="#55534e">{T("recorded in November; not classified by source or deduplicated")}</text>')
for g in (0,25,50,75,100):
    y=Y0+HH-g/100*HH; o.append(f'<line x1="{X0}" x2="{X0+WW}" y1="{y:.1f}" y2="{y:.1f}" stroke="#eee"/><text x="{X0-5}" y="{y+3:.1f}" font-size="9.5" text-anchor="end" fill="#7c7c80">{g}%</text>')
X=lambda yr: X0+(yr-2002)/(2025-2002)*WW
def line(vals,col,dash=''):
    pts=' '.join(f'{X(y):.1f},{Y0+HH-v/100*HH:.1f}' for y,v in zip(yrs,vals))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.4" {dash}/>')
line(IN,'#d62d20'); line(PK,'#1f6f8b')
for yr in (2002,2009,2015,2020,2025):
    o.append(f'<text x="{X(yr):.1f}" y="{Y0+HH+14}" font-size="10" text-anchor="middle" fill="#3a3935">{yr}</text>')
x9=X(2009); o.append(f'<line x1="{x9:.1f}" x2="{x9:.1f}" y1="{Y0}" y2="{Y0+HH}" stroke="#999" stroke-dasharray="3 3"/><text x="{x9+4:.1f}" y="{Y0+HH-8}" font-size="9" fill="#55534e">{T("2009: India's rice-planting")}</text><text x="{x9+4:.1f}" y="{Y0+HH+2-0}" font-size="9" fill="#55534e" dy="-0">{T("dates pushed later")}</text>')
o.append(f'<text x="{X(2018.6):.1f}" y="{Y0+HH-0.93*HH:.1f}" font-size="10.5" font-weight="700" fill="#d62d20">{T("Indian Punjab")}</text>')
o.append(f'<text x="{X(2002):.1f}" y="{Y0+HH-95/100*HH:.1f}" font-size="10.5" font-weight="700" fill="#1f6f8b">{T("Pakistani Punjab (north-east)")}</text>')
o.append(f'<text x="20" y="{Ht-40}" font-size="9" fill="#7c7c80">{T("Visibility: NOAA GSOD, Amritsar (VIAR), daily-mean visibility, not adjusted; 5–7 readings a day before 1990, 22–24 since 2010. Fog and smoke can't be told apart.")}</text>')
o.append(f'<text x="20" y="{Ht-27}" font-size="9" fill="#7c7c80">{T("Winter = December plus the next January, grouped by December's year. Fires: FIRMS MODIS (Terra, Aqua), type 0, confidence ≥30, 1 Oct–30 Nov,")}</text>')
o.append(f'<text x="20" y="{Ht-14}" font-size="9" fill="#7c7c80">{T("Punjab on each side within 29.5–32.6 N, 72–76.9 E; fires lit after the afternoon overpass are missed. HamariHawa (hamarihawa.org)")}</text>')
o.append('</svg>')
save('history', '\n'.join(o))
print(list(zip(yrs,IN,PK)))
