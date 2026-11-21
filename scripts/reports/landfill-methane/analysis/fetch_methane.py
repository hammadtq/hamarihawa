#!/usr/bin/env python3
"""Download Carbon Mapper's public methane plume records for the Lahore area.

Usage: python3 fetch_methane.py <H>     (H = ~/.cache/hamarihawa/landfill-report)
Writes inputs/methane/<city>_plumes.json (plume list, signed image links removed), inputs/methane/<city>_sources.json
(Carbon Mapper's grouping of plumes into sources, with the scenes that observed each source), and the plume images
to <H>/raw/methane/<plume_id>_{plume,rgb}.png. No account or key is needed for these endpoints. Parses on Python 3.9.
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.carbonmapper.org/api/v1/catalog"
BOX = {"lahore": (73.9, 31.2, 74.7, 31.8)}  # W, S, E, N
UA = {"User-Agent": "research-script/1.0"}


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            time.sleep(10 * (attempt + 1))
    raise SystemExit("Carbon Mapper kept failing: " + url[:90])


def main():
    H = os.path.expanduser(sys.argv[1])
    img = os.path.join(H, "raw", "methane")
    out = os.path.join(HERE, "inputs", "methane")
    os.makedirs(img, exist_ok=True); os.makedirs(out, exist_ok=True)
    for city, b in BOX.items():
        q = "&".join("bbox=%s" % v for v in b)
        d = json.loads(get(f"{API}/plumes/annotated?{q}&limit=1000&plume_gas=CH4"))
        assert d["bbox_count"] == len(d["items"]), "more plumes than one page"
        for p in d["items"]:
            for k, tag in (("plume_png", "plume"), ("plume_rgb_png", "rgb")):
                path = os.path.join(img, f"{p['plume_id']}_{tag}.png")
                if p.get(k) and not os.path.exists(path):
                    open(path, "wb").write(get(p[k]))
            for k in ("plume_png", "plume_rgb_png", "plume_tif", "con_tif", "rgb_png"):
                p.pop(k, None)  # signed links that expire
        items = sorted(d["items"], key=lambda p: (p["scene_timestamp"], p["plume_id"]))
        json.dump({"retrieved": time.strftime("%Y-%m-%d"), "bbox_w_s_e_n": b, "items": items}, open(os.path.join(out, f"{city}_plumes.json"), "w"), indent=1)
        src = json.loads(get(f"{API}/sources.geojson?{q}"))
        json.dump(src, open(os.path.join(out, f"{city}_sources.json"), "w"), indent=1)
        print(city, len(items), "plumes,", len(src["features"]), "sources")


if __name__ == "__main__":
    main()
