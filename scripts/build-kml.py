#!/usr/bin/env python3
"""Write the pollution-sites layer for Google Earth (site/public/kml/sources.kml).

Reads site/public/sources/sites.json (from build-sites.py) and plants.json (OpenStreetMap power
plants). The live layers (fires, city air, traffic NO2, satellite images) are served by the Worker;
site/public/hamarihawa.kml links them all together.

Usage: python3 -I scripts/build-kml.py
"""
import json, os
from xml.sax.saxutils import escape as x

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "site", "public", "sources")
OUT = os.path.join(ROOT, "site", "public", "kml", "sources.kml")
ICON = "https://maps.google.com/mapfiles/kml/shapes/"
COUNTRY = {"PK": "Pakistan", "IN": "India"}

# id: (folder name, KML colour aabbggrr, icon)
STYLES = {
    "landfills": ("Landfills leaking methane or burning", "ff3c6e60", "triangle.png"),
    "plants": ("Power and industrial plants with CO₂ plumes", "ff2b2b2b", "square.png"),
    "osmplants": ("Fossil-fuel power plants (OpenStreetMap)", "ff555555", "square.png"),
    "hot": ("Always-hot industrial sites", "ff1e26b3", "target.png"),
    "kilnbelts": ("Brick-kiln belts (districts with the most kilns)", "ff2a4a7a", "donut.png"),
}


def where(e):
    return ", ".join(v for v in (e.get("near") if e.get("near") != e.get("name") else "", e.get("district"),
                                 e.get("state"), COUNTRY.get(e.get("cc"), e.get("cc"))) if v)


def link(lat, lon, src):
    return f'<a href="https://hamarihawa.org/#at={lat},{lon},12&src={src}">Open on HamariHawa</a>'


def placemark(style, name, lat, lon, lines):
    desc = "<br>".join(l for l in lines if l)
    return (f"<Placemark><name>{x(name)}</name><styleUrl>#{style}</styleUrl>"
            f"<description><![CDATA[{desc}]]></description>"
            f"<Point><coordinates>{lon},{lat}</coordinates></Point></Placemark>")


def seen(e):
    return f"Plumes seen {e['first'][:7]} to {e['last'][:7]}" if e.get("first") and e.get("last") else ""


def main():
    sites = json.load(open(os.path.join(SRC, "sites.json"), encoding="utf-8"))
    plants = json.load(open(os.path.join(SRC, "plants.json"), encoding="utf-8"))
    folders = {k: [] for k in STYLES}
    for e in sites["landfills"]:
        rate = f"Methane leak about {e['rate']:,.0f} kg an hour ({e['plumes']} plumes seen, Carbon Mapper)" if e.get("rate") else ""
        heat = f"Seen burning on {e['heatDays']} days in NASA's 2025 fire archive" if e.get("heatDays") else ""
        folders["landfills"].append(placemark("landfills", e["name"] or "Landfill", e["lat"], e["lon"],
                                              [where(e), rate, seen(e), heat, link(e["lat"], e["lon"], "landfill")]))
    for e in sites["plants"]:
        folders["plants"].append(placemark("plants", e["name"] or f"Unnamed {e['kind']} plant", e["lat"], e["lon"],
                                           [where(e), f"CO₂ plume about {e['co2_t_h']:,} tonnes an hour (Carbon Mapper)",
                                            seen(e), link(e["lat"], e["lon"], "plumes")]))
    for lat, lon, fuel, name, mw in plants["items"]:
        folders["osmplants"].append(placemark("osmplants", name, lat, lon,
                                              [f"{fuel.capitalize()} power plant" + (f", {mw}" if mw else ""),
                                               "© OpenStreetMap contributors", link(lat, lon, "plants")]))
    for e in sites["hot"]:
        folders["hot"].append(placemark("hot", e["name"] or e.get("label") or "Always-hot site", e["lat"], e["lon"],
                                        [where(e), f"Hot on {e['days']} days across {e['months']} months of 2025 (NASA FIRMS)",
                                         link(e["lat"], e["lon"], "hotspots")]))
    for e in sites["kilnbelts"]:
        pm = f"About {e['pm25_t_day']} tonnes of PM2.5 a day (research estimate)" if e.get("pm25_t_day") else ""
        folders["kilnbelts"].append(placemark("kilnbelts", f"{e['name']}: {e['kilns']:,} brick kilns", e["lat"], e["lon"],
                                              [where(e), f"{e['zigzagPct']}% are cleaner zigzag kilns", pm,
                                               "Kilns mapped from Sentinel-2 (SentinelKilnDB, CC BY-NC 4.0; Pakistan IGP kiln dataset, CC BY 4.0)",
                                               link(e["lat"], e["lon"], "kilns")]))

    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
           "<name>Pollution sites</name>",
           f"<description>Places that show up again and again in satellite data. Built {sites['built']}. "
           "Full list: https://hamarihawa.org/sites/</description>"]
    for k, (_, colour, icon) in STYLES.items():
        out.append(f'<Style id="{k}"><IconStyle><color>{colour}</color><scale>0.9</scale><Icon><href>{ICON}{icon}</href></Icon>'
                   "</IconStyle><LabelStyle><scale>0.7</scale></LabelStyle></Style>")
    for k, (title, _, _) in STYLES.items():
        out.append(f"<Folder><name>{x(title)} ({len(folders[k])})</name>" + "".join(folders[k]) + "</Folder>")
    out.append("</Document></kml>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(out))
    print({k: len(v) for k, v in folders.items()}, "->", OUT)


if __name__ == "__main__":
    main()
