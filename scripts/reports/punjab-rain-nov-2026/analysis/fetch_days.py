# Daily fire summaries from HamariHawa's archive for the days around the rain spell.
# python3 fetch_days.py   -> data/day-summaries/YYYY-MM-DD.json (summary and districts only; retrieval time in data/day-summaries/RETRIEVED.txt)
import json, os, urllib.request, datetime as D
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "data", "day-summaries"); os.makedirs(OUT, exist_ok=True)
d = D.date(2026, 11, 1)
while d <= D.date(2026, 11, 15):
    req = urllib.request.Request(f"https://hamarihawa.org/api/day?d={d}", headers={"User-Agent": "curl/8"})
    j = json.loads(urllib.request.urlopen(req, timeout=60).read())
    json.dump({"summary": j["summary"], "districts": j.get("districts")}, open(os.path.join(OUT, f"{d}.json"), "w"))
    d += D.timedelta(1)
open(os.path.join(OUT, "RETRIEVED.txt"), "w").write(D.datetime.now(D.timezone.utc).isoformat() + "\n")
