from i18n import T, FONT, save
# Baseline chart: IQAir monthly PM2.5 (Oct 2025-Sep 2026) + Oct 2026 (PAQI), and ERA5 mixing height climatology
months=[T(m) for m in ['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct']]
pm=[123.5,183.4,177.5,124,125.3,67.1,48.4,45.5,40,53,55.9,58.6,100.3]
mn=[10,11,12,1,2,3,4,5,6,7,8,9,10]
blh={1:224,2:298,3:408,4:688,5:858,6:825,7:529,8:477,9:451,10:399,11:262,12:191}
W,H=720,430; L,R=46,14; top1,h1=40,200; top2,h2=300,80
n=len(pm); bw=(W-L-R)/n
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" aria-label="{T("Lahore monthly PM2.5 and mixing height")}">',
 '<rect width="100%" height="100%" fill="#fff"/>',
 f'<text x="{L}" y="18" font-size="14" font-weight="700" fill="#1d1d1b">{T("Lahore's fine particles (PM2.5) month by month, µg/m³")}</text>',
 f'<text x="{L}" y="33" font-size="10.5" fill="#7c7c80">{T("Monthly averages, IQAir city history (read 14 Sep and 3 Nov 2026)")}</text>']
ymax=200; y=lambda v: top1+h1-v/ymax*h1
for g in [50,100,150,200]:
    o.append(f'<line x1="{L}" x2="{W-R}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="#eee"/><text x="{L-6}" y="{y(g)+3:.1f}" font-size="9.5" text-anchor="end" fill="#7c7c80">{g}</text>')
for i,v in enumerate(pm):
    x=L+i*bw+4; base=(v if v<35 else 35)
    col='#d62d20' if mn[i] in (10,11,12,1,2) else '#e8a29b'
    hatch=''
    o.append(f'<rect x="{x:.1f}" y="{y(v):.1f}" width="{bw-8:.1f}" height="{top1+h1-y(v):.1f}" fill="{col}"{hatch} rx="2"/>')
    o.append(f'<text x="{x+(bw-8)/2:.1f}" y="{y(v)-4:.1f}" font-size="9.5" text-anchor="middle" fill="#3a3935">{round(v)}</text>')
    o.append(f'<text x="{x+(bw-8)/2:.1f}" y="{top1+h1+14:.1f}" font-size="10" text-anchor="middle" fill="#3a3935">{months[i]}</text>')
o.append(f'<line x1="{L}" x2="{W-R}" y1="{y(35):.1f}" y2="{y(35):.1f}" stroke="#1d1d1b" stroke-dasharray="5 3"/>')
o.append(f'<line x1="{W-R-232}" x2="{W-R-210}" y1="22" y2="22" stroke="#1d1d1b" stroke-dasharray="5 3"/><text x="{W-R}" y="25" font-size="9.5" text-anchor="end" fill="#1d1d1b">{T("Pakistan's 24-hour standard (35), for context")}</text>')
o.append(f'<text x="{L+bw*0}" y="{top1+h1+28}" font-size="9.5" fill="#7c7c80">2025</text><text x="{L+bw*3+4}" y="{top1+h1+28}" font-size="9.5" fill="#7c7c80">2026</text>')
o.append(f'<text x="{L}" y="{top2-12}" font-size="12" font-weight="700" fill="#1d1d1b">{T("How deep the air is that smoke can mix into (mixing height), metres")}</text>')
bmax=900; yb=lambda v: top2+h2-v/bmax*h2
for i,m in enumerate(mn):
    v=blh[m]; x=L+i*bw+4
    o.append(f'<rect x="{x:.1f}" y="{yb(v):.1f}" width="{bw-8:.1f}" height="{top2+h2-yb(v):.1f}" fill="#8aa6c1" rx="2"/>')
    o.append(f'<text x="{x+(bw-8)/2:.1f}" y="{yb(v)-4:.1f}" font-size="9.5" text-anchor="middle" fill="#3a3935">{v}</text>')
    o.append(f'<text x="{x+(bw-8)/2:.1f}" y="{top2+h2+14:.1f}" font-size="10" text-anchor="middle" fill="#3a3935">{months[i]}</text>')
o.append(f'<text x="{L}" y="{H-6}" font-size="9" fill="#7c7c80">{T("The 35 line is a 24-hour standard; these bars are monthly means. Mixing height: ERA5, all-hour average for each month, 2019–2025, central Lahore. HamariHawa")}</text>')
o.append('</svg>')
save('baseline', '\n'.join(o))
