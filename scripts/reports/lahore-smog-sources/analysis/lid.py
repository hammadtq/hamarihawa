from i18n import T, FONT, save
import random
W,H=760,560
G=440          # ground y
PX=0.3         # px per metre
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" aria-label="{T("Diagram: the same smoke mixes through about 860 m of air in May and June but only about 260 m in November")}">',
'<defs>',
'<linearGradient id="skyS" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7fb6e6"/><stop offset="1" stop-color="#d7ecfb"/></linearGradient>',
'<linearGradient id="skyW" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9fb3c6"/><stop offset="1" stop-color="#dfe5ea"/></linearGradient>',
'<linearGradient id="lid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f3b26b" stop-opacity="0"/><stop offset="1" stop-color="#f3b26b" stop-opacity=".55"/></linearGradient>',
'<marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#33414f"/></marker>',
'<marker id="aw" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#fff"/></marker>',
'<style>@keyframes up{to{transform:translateY(var(--p))}}@keyframes dn{to{transform:translateY(var(--p))}}@keyframes wind{to{transform:translateX(var(--w))}}@keyframes jig{0%,100%{transform:translateY(-2px)}50%{transform:translateY(2px)}}@keyframes flow{to{stroke-dashoffset:-28}}@keyframes plume{0%{transform:translate(0,0) scale(.6);opacity:0}10%{opacity:.75}55%{transform:translate(-4px,var(--r)) scale(1.6);opacity:.7}100%{transform:translate(-90px,var(--r)) scale(2);opacity:0}}.puff{transform-box:fill-box;transform-origin:center}@keyframes lid{0%,100%{opacity:.75}50%{opacity:1}}.a{animation-timing-function:linear;animation-iteration-count:infinite}.flow{stroke-dasharray:9 5;animation:flow 1.6s linear infinite}.lidp{animation:lid 4s ease-in-out infinite}@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>',
'</defs>','<rect width="100%" height="100%" fill="#fff"/>',
f'<text x="20" y="24" font-size="17" font-weight="700" fill="#1d1d1b">{T("Why the same smoke gets worse in November")}</text>',
f'<text x="20" y="42" font-size="11.5" fill="#55534e">{T("Lahore's smoke mixes into a layer of air near the ground. In autumn and winter that layer gets much shallower.")}</text>']
def lab(x,y,t,anchor='middle'):
    wd=len(t)*5.4+10
    o.append(f'<rect x="{x-wd/2:.1f}" y="{y-11}" width="{wd:.1f}" height="15" rx="7" fill="#fff" fill-opacity=".88"/><text x="{x}" y="{y}" font-size="10.5" text-anchor="middle" fill="#33414f">{t}</text>')
def panel(x0,w,h_m,sky,title,sub,warm,seed,fires):
    top=G-1000*PX
    o.append(f'<rect x="{x0}" y="{top-10}" width="{w}" height="{G-top+10}" fill="url(#{sky})" rx="6"/>')
    o.append(f'<text x="{x0+2}" y="{top-32}" font-size="14" font-weight="700" fill="#1d1d1b">{title}</text>')
    o.append(f'<text x="{x0+2}" y="{top-17}" font-size="10.5" fill="#33414f">{sub}</text>')
    hy=G-h_m*PX
    if warm:  # warm lid above the layer
        o.append(f'<rect class="lidp" x="{x0}" y="{hy-46}" width="{w}" height="46" fill="url(#lid)"/>')
        o.append(f'<text x="{x0+w-10}" y="{hy-28}" font-size="10.5" text-anchor="end" fill="#8a4b0f" font-weight="700">{T("warmer air on top acts as a lid")}</text>')
        o.append(f'<text x="{x0+w-10}" y="{hy-15}" font-size="9.5" text-anchor="end" fill="#8a4b0f">{T("(a temperature inversion)")}</text>')
    o.append(f'<rect x="{x0}" y="{hy}" width="{w}" height="{G-hy}" fill="#8c8a80" fill-opacity=".22"/>')
    o.append(f'<line x1="{x0}" x2="{x0+w}" y1="{hy}" y2="{hy}" stroke="#33414f" stroke-width="1.5" stroke-dasharray="6 4"/>')
    o.append(f'<text x="{x0+12}" y="{hy-7}" font-size="12" font-weight="700" fill="#1d1d1b">{T("mixing height ≈ {} m").format(h_m)}</text>')
    r=random.Random(seed)
    P=G-hy
    o.append(f'<clipPath id="c{seed}{int(warm)}"><rect x="{x0}" y="{hy}" width="{w}" height="{P}"/></clipPath><g clip-path="url(#c{seed}{int(warm)})">')
    pts=[(x0+3+r.random()*(w-6), hy+r.random()*P, '#4a4a46', '.75') for i in range(330)]
    if fires: pts+=[(x0+3+r.random()*(w-6), hy+r.random()*P, '#c0561d', '.8') for i in range(140)]
    def dots(ps,dx=0,dy=0): return ''.join(f'<circle cx="{x+dx:.1f}" cy="{y+dy:.1f}" r="1.9" fill="{c}" fill-opacity="{a}"/>' for x,y,c,a in ps)
    if not warm:  # deep stirred layer: half the smoke rising, half sinking, wrapping round
        for k in range(6):
            grp=pts[k::6]; upw=k%2==0; dur=(13,17,21)[k//2]
            sh=P if upw else -P
            o.append(f'<g class="a" style="--p:{-sh}px;animation-name:{"up" if upw else "dn"};animation-duration:{dur}s">{dots(grp)}{dots(grp,0,sh)}</g>')
    else:  # shallow capped layer: smoke drifts with the light wind and jiggles, but can't rise
        for k in range(4):
            grp=pts[k::4]
            o.append(f'<g class="a" style="--w:{-w}px;animation-name:wind;animation-duration:{(46,52,58,64)[k]}s"><g style="animation:jig {(2.6,3.1,3.7,4.3)[k]}s ease-in-out infinite">{dots(grp)}{dots(grp,w,0)}</g></g>')
    o.append('</g>')
    if fires:  # crop smoke rising from the fires, stopped by the lid and spreading under it
        fx=x0+w-88
        for k in range(4):
            for j in range(6):
                X=fx+k*20+4; d=-(k*0.7+j*1.1)
                o.append(f'<circle cx="{X}" cy="{G-6}" r="4" fill="#b8673a" opacity="0" class="a puff" style="--r:{-(P-20)}px;animation-name:plume;animation-duration:6.5s;animation-delay:{d:.1f}s;animation-timing-function:ease-out"/>')
    # air movement
    if not warm:
        for cx in (x0+70,x0+w-80):
            o.append(f'<path class="flow" d="M{cx} {G-40} C {cx-40} {G-120}, {cx-30} {hy+60}, {cx} {hy+30}" fill="none" stroke="#33414f" stroke-width="1.6" marker-end="url(#ar)"/>')
            o.append(f'<path class="flow" d="M{cx+30} {hy+40} C {cx+60} {hy+90}, {cx+55} {G-120}, {cx+30} {G-45}" fill="none" stroke="#33414f" stroke-width="1.6" marker-end="url(#ar)"/>')
        lab(x0+w/2,hy+80,T("sun-heated ground stirs")); lab(x0+w/2,hy+96,T("the air up and down"))
    # light wind arrow, same in both
    wy=hy+14 if warm else hy+150
    o.append(f'<line x1="{x0+w/2+10}" x2="{x0+w/2-60}" y1="{wy}" y2="{wy}" stroke="#33414f" stroke-width="2.2" marker-end="url(#ar)"/>')
    lab(x0+w/2+62,wy+4,T("light wind, ~2 m/s"))
    # ground: city, chimney, fields
    o.append(f'<rect x="{x0}" y="{G}" width="{w}" height="14" fill="#7b6a4f"/>')
    bx=x0+18
    for bw_,bh in [(16,26),(12,40),(20,18),(14,33),(18,22),(10,46),(16,28)]:
        o.append(f'<rect x="{bx}" y="{G-bh}" width="{bw_}" height="{bh}" fill="#5d6670"/>'); bx+=bw_+3
    o.append(f'<rect x="{bx+10}" y="{G-58}" width="7" height="58" fill="#6d5a4a"/>')  # kiln chimney
    for k in range(2):
        o.append(f'<rect x="{bx+36+k*24}" y="{G-9}" width="18" height="7" rx="2" fill="#4b5560"/><circle cx="{bx+40+k*24}" cy="{G-1}" r="2.2" fill="#222"/><circle cx="{bx+50+k*24}" cy="{G-1}" r="2.2" fill="#222"/>')
    if fires:
        fx=x0+w-88
        for k in range(4):
            X=fx+k*20
            o.append(f'<path d="M{X} {G} q4 -14 8 -4 q2 -10 6 -2 q3 6 0 6z" fill="#e8642c"/>')
        o.append(f'<text x="{x0+w-4}" y="{G+28}" font-size="9.5" text-anchor="end" fill="#8a4b0f">{T("crop fires on the city's edge")}</text>')
    o.append(f'<text x="{x0+12}" y="{G+28}" font-size="9.5" fill="#55534e">{T("traffic, kilns, industry: all year")}</text>')
# height axis
ax=40
for m in (0,250,500,750,1000):
    y=G-m*PX
    o.append(f'<line x1="{ax-4}" x2="{ax}" y1="{y}" y2="{y}" stroke="#7c7c80"/><text x="{ax-7}" y="{y+3}" font-size="9.5" text-anchor="end" fill="#7c7c80">{m} m</text>')
o.append(f'<line x1="{ax}" x2="{ax}" y1="{G-1000*PX}" y2="{G}" stroke="#7c7c80"/>')
panel(48,340,850,'skyS',T('May and June'),T('smoke spreads through deep, stirred-up air'),False,7,False)
panel(404,340,260,'skyW',T('November'),T('the same smoke is squeezed into a shallow layer'),True,7,True)
o.append(f'<text x="218" y="{G+50}" font-size="12" text-anchor="middle" fill="#1d1d1b"><tspan font-weight="700">{T("Same everyday smoke")}</tspan>{T(", spread through ~850 m")}</text>')
o.append(f'<text x="574" y="{G+50}" font-size="12" text-anchor="middle" fill="#1d1d1b"><tspan font-weight="700">{T("About 3× as concentrated*")}</tspan>{T(", plus crop smoke")}</text>')
o.append(f'<circle cx="60" cy="{G+76}" r="3" fill="#4a4a46"/><text x="68" y="{G+80}" font-size="10" fill="#55534e">{T("everyday smoke (same amount in both)")}</text>')
o.append(f'<circle cx="290" cy="{G+76}" r="3" fill="#c0561d"/><text x="298" y="{G+80}" font-size="10" fill="#55534e">{T("added smoke from crop burning")}</text>')
o.append(f'<text x="20" y="{H-22}" font-size="9" fill="#7c7c80">{T("*Idealized: the same emissions in a shallower layer, other factors held constant. Mixing heights: ERA5, monthly averages over all hours of the day,")}</text>')
o.append(f'<text x="20" y="{H-10}" font-size="9" fill="#7c7c80">{T("central Lahore, 2019–2025 (May 858 m, June 825 m, November 262 m); nights are much shallower, afternoons deeper. HamariHawa (hamarihawa.org)")}</text>')
o.append('</svg>')
save('mixing-layer', '\n'.join(o))
