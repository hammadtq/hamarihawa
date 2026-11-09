# Delhi station-feed statistics by IQAir attribution, from data/iqair-delhi-stations-recapture.json.
# Value i is the hour starting 2026-11-07 22:30 IST + i h. Writes data/delhi-stations-stats.json.
import json, datetime as D, collections
R = json.load(open("data/iqair-delhi-stations-recapture.json"))
t0 = D.datetime(2026, 11, 7, 22, 30)
I = lambda s: int((D.datetime.fromisoformat(s) - t0).total_seconds() // 3600)
rows = {r[0]: (r[1], [int(x) if x else None for x in r[5].split(",")]) for r in R["rows"]}
group = lambda a: "CPCB" if a.startswith("Central") else "DPCC" if a.startswith("Delhi Pollution") else "private"
night = range(I("2026-11-08 18:30"), I("2026-11-09 06:30") + 1)
satn = range(I("2026-11-07 22:30"), I("2026-11-08 06:30") + 1)
noon = I("2026-11-08 12:30")
out = {"by_station": {}, "groups": {}}
for k, (a, v) in rows.items():
    nm = [x for x in (v[i] for i in night) if x]
    sm = [x for x in (v[i] for i in satn) if x]
    mx = max(nm) if nm else None
    at = (t0 + D.timedelta(hours=max((i for i in night if v[i]), key=lambda i: v[i]))).strftime("%a %H:%M") if nm else None
    out["by_station"][k] = {"group": group(a), "attribution": a, "sun_night_max": mx, "sun_night_max_at_IST": at, "night_hours_with_data": len(nm),
                            "sun_12_30": v[noon], "sat_night_max": max(sm) if sm else None}
for g in ("CPCB", "DPCC", "private"):
    S = {k: s for k, s in out["by_station"].items() if s["group"] == g}
    out["groups"][g] = {"n": len(S), "passed_1000_sun_night": sorted(k for k, s in S.items() if (s["sun_night_max"] or 0) > 1000),
                        "passed_1000_sat_night": sorted(k for k, s in S.items() if (s["sat_night_max"] or 0) > 1000),
                        "sun_night_max_range": [min(s["sun_night_max"] for s in S.values() if s["sun_night_max"]), max(s["sun_night_max"] for s in S.values() if s["sun_night_max"])],
                        "sun_12_30_range": [min(s["sun_12_30"] for s in S.values() if s["sun_12_30"]), max(s["sun_12_30"] for s in S.values() if s["sun_12_30"])]}
# How alike are the CPCB-attributed feeds? Hours in which a feed's value equals another feed's value exactly.
C = {k: rows[k][1] for k in rows if group(rows[k][0]) == "CPCB"}
sig = collections.Counter(tuple(v) for v in C.values())
pairs_ident = []
ks = sorted(C)
for i, a in enumerate(ks):
    for b in ks[i + 1:]:
        both = [(x, y) for x, y in zip(C[a], C[b]) if x is not None and y is not None]
        pairs_ident.append((a, b, sum(x == y for x, y in both), len(both)))
out["cpcb_similarity"] = {"feeds": len(C), "distinct_full_series": len(sig),
    "pairs_identical_in_at_least_90pct_of_hours": sum(1 for a, b, s, n in pairs_ident if n and s / n >= 0.9), "pairs_total": len(pairs_ident),
    "largest_cluster_identical_90pct": None}
# cluster by 90% identity
adj = collections.defaultdict(set)
for a, b, s, n in pairs_ident:
    if n and s / n >= 0.9: adj[a].add(b); adj[b].add(a)
seen, clusters = set(), []
for k in ks:
    if k in seen: continue
    stack, comp = [k], set()
    while stack:
        x = stack.pop()
        if x in comp: continue
        comp.add(x); stack += list(adj[x])
    seen |= comp; clusters.append(sorted(comp))
out["cpcb_similarity"]["clusters_90pct"] = sorted(clusters, key=len, reverse=True)
ev = range(I("2026-11-08 19:30"), I("2026-11-08 23:30") + 1)
out["cpcb_sun_19_30_to_23_30_range"] = [min(C[k][i] for k in C for i in ev if C[k][i]), max(C[k][i] for k in C for i in ev if C[k][i])]
json.dump(out, open("data/delhi-stations-stats.json", "w"), indent=1)
print(json.dumps(out["groups"], indent=0)); print(json.dumps(out["cpcb_similarity"])); print(out["cpcb_sun_19_30_to_23_30_range"])
for k, s in out["by_station"].items():
    if s["group"] != "CPCB": print(k, s)

# Direct, simultaneous agreement within each group (not pairwise graph membership): readings where every feed in the
# group shows the same value. Overnight window = the 13 readings labelled 18:30 IST Sun to 06:30 IST Mon; also the whole capture.
def simultaneous(group, idxs):
    ok = tot = 0
    for i in idxs:
        vals = [C[k][i] for k in group]
        if any(v is None for v in vals): continue
        tot += 1; ok += len(set(vals)) == 1
    return ok, tot
ovn = list(range(I("2026-11-08 18:30"), I("2026-11-09 06:30") + 1))
full = list(range(min(len(v) for v in C.values())))
out["cpcb_groups_direct"] = {"window_overnight_IST": "2026-11-08 18:30 to 2026-11-09 06:30 (13 hourly readings)",
    "groups": [{"feeds": g, "n": len(g), "overnight_same_value": "%d/%d" % simultaneous(g, ovn), "full_capture_same_value": "%d/%d" % simultaneous(g, full)}
               for g in out["cpcb_similarity"]["clusters_90pct"]],
    "note": "groups are the connected components of a >=90% pairwise-agreement graph; the counts here are direct simultaneous agreement"}
json.dump(out, open("data/delhi-stations-stats.json", "w"), indent=1)
print(json.dumps(out["cpcb_groups_direct"], indent=0))
