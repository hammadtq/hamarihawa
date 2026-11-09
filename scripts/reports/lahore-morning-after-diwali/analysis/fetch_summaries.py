# Fetch the summary (with per-state counts) of every archived day, 1 Oct-30 Nov 2019-2026, from HamariHawa's /api/day.
# python3 fetch_summaries.py -> data/day-summaries/YYYY-MM-DD.json (summary only) and data/day-summaries/_fetched.txt
import json, os, urllib.request, datetime as D, concurrent.futures as C
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "day-summaries")
def one(d):
    p = os.path.join(OUT, d + ".json")
    if os.path.exists(p): return d, "cached"
    r = urllib.request.urlopen(urllib.request.Request(f"https://hamarihawa.org/api/day?d={d}", headers={"User-Agent": "hamarihawa-report"}), timeout=60)
    j = json.load(r)
    json.dump({"date": j.get("date"), "v": j.get("v"), "source": j.get("source"), "summary": j.get("summary")}, open(p, "w"))
    return d, "ok"
days = []
for y in range(2019, 2027):
    d = D.date(y, 10, 1)
    while d <= min(D.date(y, 11, 30), D.date(2026, 11, 9)):
        days.append(d.isoformat()); d += D.timedelta(1)
with C.ThreadPoolExecutor(4) as ex:
    res = list(ex.map(lambda d: (lambda: one(d))() if True else None, days))
open(os.path.join(OUT, "_fetched.txt"), "w").write(f"fetched {D.datetime.utcnow().isoformat()}Z from https://hamarihawa.org/api/day?d=\n" + "\n".join(f"{a} {b}" for a, b in res))
print(len(res), sum(b == "ok" for a, b in res))
