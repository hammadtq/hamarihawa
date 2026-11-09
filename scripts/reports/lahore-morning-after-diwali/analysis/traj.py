# Approximate 24-hour back-trajectories from gridded GFS winds (Open-Meteo, 0.5 degree, 10 m and 925 hPa),
# and the NASA FIRMS fire detections within 20 km of each path in the 24 hours before the air passed.
# Horizontal only: no vertical motion, no turbulence. Run from this folder: python3 traj.py

import json,math,datetime as D,sys
G=json.load(open("data/wind-grid.json")); LA,LO=G["lats"],G["lons"]; NX=len(LO)
T0=D.datetime(2026,11,6)
def field(var,h):
    return [d[var][h] for d in G["data"]]
def uv(lat,lon,t,lev):
    # t: hours since T0 (UTC), bilinear space, linear time
    h0=int(math.floor(t)); f=t-h0
    i=(lat-LA[0])/0.5; j=(lon-LO[0])/0.5
    if not(0<=i<len(LA)-1 and 0<=j<NX-1): return None
    i0,j0=int(i),int(j); di,dj=i-i0,j-j0
    U=V=0
    for hh,wt in ((h0,1-f),(h0+1,f)):
        for (a,b,w) in ((i0,j0,(1-di)*(1-dj)),(i0+1,j0,di*(1-dj)),(i0,j0+1,(1-di)*dj),(i0+1,j0+1,di*dj)):
            d=G["data"][a*NX+b]; s=d[f"wind_speed_{lev}"][hh]; dr=d[f"wind_direction_{lev}"][hh]
            if s is None: return None
            # direction is where wind comes FROM
            U+=wt*w*(-s*math.sin(math.radians(dr))); V+=wt*w*(-s*math.cos(math.radians(dr)))
    return U,V  # km/h
def back(lat,lon,arr_utc,hours,lev):
    t=(arr_utc-T0).total_seconds()/3600; path=[(lat,lon,t)]; dt=0.25
    for _ in range(int(hours/dt)):
        w=uv(lat,lon,t,lev)
        if not w: break
        U,V=w; lat-=V*dt/111.0; lon-=U*dt/(111.0*math.cos(math.radians(lat))); t-=dt
        path.append((lat,lon,t))
    return path
def km(a,b,c,d):
    p=math.pi/180; x=math.sin((c-a)*p/2)**2+math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2; return 12742*math.asin(math.sqrt(x))
fires=[]
for day in ["2026-11-06","2026-11-07","2026-11-08","2026-11-09"]:
    d=json.load(open(f"data/day-{day}.json")); dist=d["dict"]["district"]
    for s in d["spots"]: fires.append((s[0],s[1],s[2]/1000,dist[s[5]][2],dist[s[5]][0],s[6]))
def along(path,R=20):
    # fires within R km of the path, detected in the 24 h before the air passed that point
    hit={}
    for (fl,fo,ft,cc,dn,kind) in fires:
        for (la,lo,t) in path[::2]:
            tu=(T0+D.timedelta(hours=t)).replace(tzinfo=D.timezone.utc).timestamp()
            # cheap bounding box derived from R (1 deg lat = 111 km; lon scaled at this latitude, conservative), then the true distance test
            if abs(fl-la)<=R/111.0+0.01 and abs(fo-lo)<=R/(111.0*math.cos(math.radians(abs(la)+1)))+0.01 and 0<=tu-ft<=24*3600 and km(fl,fo,la,lo)<=R:
                hit[(fl,fo,ft)]=(cc,dn); break
    return hit
PKT=D.timedelta(hours=5)
C={"Lahore":(31.5497,74.3436),"Faisalabad":(31.418,73.079),"Multan":(30.1978,71.4711),"Gujranwala":(32.1617,74.1883),"Amritsar":(31.634,74.8723),"Ludhiana":(30.901,75.8573),"Delhi":(28.6139,77.209)}
cases=[(c,D.datetime(2026,11,9,9)) for c in C]+[(c,D.datetime(2026,11,8,9)) for c in C]
res={}
for c,arr in cases:
    for lev in ("10m","925hPa"):
        p=back(*C[c],arr-PKT,24,lev)
        h=along(p); cc=[v[0] for v in h.values()]
        from collections import Counter
        dd=Counter(v[1]+"("+v[0]+")" for v in h.values()).most_common(4)
        end=p[-1]; dkm=km(C[c][0],C[c][1],end[0],end[1])
        print(f"{c:10s} arr {arr:%a %H:%M} PKT {lev:6s} 24h back -> {end[0]:.2f}N {end[1]:.2f}E ({dkm:.0f} km, {len(p)/4:.0f}h)  fires on path: PK {cc.count('PK')} IN {cc.count('IN')}  {dd}")
        res[f"{c}|{arr:%Y-%m-%dT%H}|{lev}"]={"path":[(round(a,3),round(b,3),(T0+D.timedelta(hours=t)+PKT).strftime("%Y-%m-%d %H:%M PKT")) for a,b,t in p[::4]],"pk":cc.count('PK'),"in":cc.count('IN'),"top":dd}
json.dump(res,open("data/traj.json","w"))
