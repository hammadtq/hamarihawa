#!/usr/bin/env python3
"""Download the footprints of every Carbon Mapper methane scene (satellite pass) over the Lahore box.

Usage: python3 fetch_scenes.py
Writes inputs/methane/<city>_scenes.json: id, time, platform and footprint polygon of each scene, from the public
STAC endpoint, with the scene-wide cloud, haze and sensitivity-mode fields Carbon Mapper publishes. A scene that covers a site and\nhas no plume there is a pass that reported nothing; the scene-wide fields do not say what the view of one site was.
Parses on Python 3.9.
"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STAC = "https://api.carbonmapper.org/api/v1/stac/collections/l2b-ch4/items"
BOX = {"lahore": (73.9, 31.2, 74.7, 31.8)}


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-script/1.0"}), timeout=90) as r:
                return json.loads(r.read())
        except Exception:  # noqa: BLE001
            time.sleep(10 * (attempt + 1))
    raise SystemExit("Carbon Mapper kept failing: " + url[:90])


for city, b in BOX.items():
    out, off = [], 0
    while True:
        d = get(f"{STAC}?bbox={','.join(map(str, b))}&limit=100&offset={off}")
        for f in d["features"]:
            p = f["properties"]
            out.append({"id": f["id"], "datetime": p["datetime"], "platform": p.get("platform"), "version": p.get("version"), "geometry": f["geometry"],
                        "cloud_cover_pct": p.get("cm:scene:cloud_cover_pct"), "cloud_cover_pct_assessed": p.get("cm:scene:cloud_cover_pct_assessed"),
                        "light_haze_pct": p.get("cm:light_haze_pct"), "sensitivity_mode": p.get("cm:sensitivity_mode"), "sun_elevation": p.get("view:sun_elevation")})
        off += len(d["features"])
        if not d["features"] or off >= d["numberMatched"]:
            break
    ids = {}
    for s in out:
        ids[s["id"]] = s
    out = sorted(ids.values(), key=lambda s: s["datetime"])
    json.dump({"retrieved": time.strftime("%Y-%m-%d"), "bbox_w_s_e_n": b, "scenes": out}, open(os.path.join(HERE, "inputs", "methane", f"{city}_scenes.json"), "w"))
    print(city, len(out), "scenes", out[0]["datetime"][:10], out[-1]["datetime"][:10])
