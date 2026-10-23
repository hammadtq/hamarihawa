// Live KML layers for Google Earth, linked together by public/hamarihawa.kml.
// Fires come prebuilt from the GitHub Action (KV "kml-24" etc.); these are cheap enough to build per request.

const SITE = "https://hamarihawa.org";
const BOX = { s: 6, n: 37.5, w: 60.5, e: 97.5 }; // scripts/geo.py REGION

// Same cities as public/cities.js (name, lat, lon, country).
const CITIES = [["Lahore",31.5497,74.3436,"PK"],["Karachi",24.8607,67.0011,"PK"],["Faisalabad",31.418,73.079,"PK"],["Rawalpindi",33.5973,73.0479,"PK"],["Islamabad",33.6938,73.0652,"PK"],["Gujranwala",32.1617,74.1883,"PK"],["Multan",30.1978,71.4711,"PK"],["Peshawar",34.008,71.5785,"PK"],["Quetta",30.1798,66.975,"PK"],["Hyderabad (Sindh)",25.396,68.3578,"PK"],["Delhi",28.6139,77.209,"IN"],["Gurugram",28.4595,77.0266,"IN"],["Amritsar",31.634,74.8723,"IN"],["Ludhiana",30.901,75.8573,"IN"],["Chandigarh",30.7333,76.7794,"IN"],["Lucknow",26.8467,80.9462,"IN"],["Kanpur",26.4499,80.3319,"IN"],["Varanasi",25.3176,82.9739,"IN"],["Patna",25.5941,85.1376,"IN"],["Mumbai",19.076,72.8777,"IN"],["Kolkata",22.5726,88.3639,"IN"],["Bengaluru",12.9716,77.5946,"IN"],["Chennai",13.0827,80.2707,"IN"],["Hyderabad",17.385,78.4867,"IN"],["Ahmedabad",23.0225,72.5714,"IN"],["Surat",21.1702,72.8311,"IN"],["Pune",18.5204,73.8567,"IN"],["Jaipur",26.9124,75.7873,"IN"],["Indore",22.7196,75.8577,"IN"],["Nagpur",21.1458,79.0882,"IN"],["Bhopal",23.2599,77.4126,"IN"],["Kochi",9.9312,76.2673,"IN"],["Visakhapatnam",17.6868,83.2185,"IN"],["Raipur",21.2514,81.6296,"IN"],["Ranchi",23.3441,85.3096,"IN"],["Guwahati",26.1445,91.7362,"IN"],["Bhubaneswar",20.2961,85.8245,"IN"]];

// US AQI bands, as on the site; KML colours are aabbggrr.
const BANDS = [
  [50, "Good", "ff4ce400"], [100, "Moderate", "ff00ffff"], [150, "Unhealthy for sensitive groups", "ff007eff"],
  [200, "Unhealthy", "ff0000ff"], [300, "Very unhealthy", "ff4c0099"], [Infinity, "Hazardous", "ff23007e"],
];
const HOT_KIND = { traffic: "City traffic hotspot", plant: "Power or industrial plant", industry: "Industrial estate", kilns: "Brick-kiln belt", corridor: "Highway / mixed sources" };

const esc = (s) => String(s).replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" })[c]);
const doc = (name, desc, body) =>
  `<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>${esc(name)}</name><description>${esc(desc)}</description>${body}</Document></kml>`;
const point = (name, style, lat, lon, html) =>
  `<Placemark><name>${esc(name)}</name><styleUrl>#${style}</styleUrl><description><![CDATA[${html}]]></description><Point><coordinates>${lon},${lat}</coordinates></Point></Placemark>`;
const day = (back) => new Date(Date.now() - back * 864e5).toISOString().slice(0, 10);

export function kmlResponse(body, maxAge) {
  return new Response(body, { headers: {
    "content-type": "application/vnd.google-earth.kml+xml; charset=utf-8",
    "cache-control": `public, max-age=${maxAge}`, "access-control-allow-origin": "*" } });
}

// City air now: one Open-Meteo call for all cities (CAMS model, not ground sensors).
export async function airKml() {
  const q = `latitude=${CITIES.map((c) => c[1]).join(",")}&longitude=${CITIES.map((c) => c[2]).join(",")}`;
  const r = await fetch(`https://air-quality-api.open-meteo.com/v1/air-quality?${q}&current=us_aqi,pm2_5&timezone=GMT`,
    { cf: { cacheTtl: 1800, cacheEverything: true } });
  if (!r.ok) return null;
  const data = [].concat(await r.json());
  const styles = BANDS.map(([, , c], i) => `<Style id="b${i}"><IconStyle><color>${c}</color><scale>1.3</scale><Icon><href>https://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle><LabelStyle><scale>1</scale></LabelStyle></Style>`).join("");
  const marks = CITIES.map(([name, lat, lon], i) => {
    const cur = data[i]?.current;
    if (!cur || cur.us_aqi == null) return "";
    const b = BANDS.findIndex(([max]) => cur.us_aqi <= max);
    const pm = cur.pm2_5;
    return point(`${name} ${Math.round(cur.us_aqi)}`, `b${b}`, lat, lon,
      `<b>US AQI ${Math.round(cur.us_aqi)}</b>: ${BANDS[b][1]}<br>PM2.5 ${pm.toFixed(0)} µg/m³, ${(pm / 15).toFixed(1)}× the WHO 24-hour limit` +
      `<br>Like smoking ${(pm / 22).toFixed(1)} cigarettes a day<br>Model hour ${esc(cur.time)} UTC (Copernicus CAMS via Open-Meteo). ` +
      `Model estimates read low in winter.<br><a href="${SITE}/#at=${lat},${lon},10">Open on HamariHawa</a>`);
  }).join("");
  return doc("City air now (US AQI)", "Copernicus CAMS model estimates for 17 cities, refreshed every 30 minutes.", styles + marks);
}

// Traffic and industry NO2: our 14-day average image plus the labelled hotspots.
export function trafficKml(meta) {
  const [[s, w], [n, e]] = meta.bounds;
  const days = `${meta.days[0]} to ${meta.days[meta.days.length - 1]}`;
  const style = `<Style id="hot"><IconStyle><color>ff202dd6</color><scale>0.9</scale><Icon><href>https://maps.google.com/mapfiles/kml/shapes/caution.png</href></Icon></IconStyle><LabelStyle><scale>0.7</scale></LabelStyle></Style>`;
  const overlay = `<GroundOverlay><name>NO₂, 2-week average (${days})</name><color>c8ffffff</color>` +
    `<Icon><href>${SITE}/api/no2-geo.png?b=${encodeURIComponent(meta.built)}</href></Icon>` +
    `<LatLonBox><north>${n}</north><south>${s}</south><east>${e}</east><west>${w}</west></LatLonBox></GroundOverlay>`;
  const marks = meta.hotspots.map(([lat, lon, ratio, kind, site, km, town, cc]) =>
    point(`${town || site || "Hotspot"}: ${HOT_KIND[kind] || kind}`, "hot", lat, lon,
      `${HOT_KIND[kind] || kind}${site && site !== town ? ` (${esc(site)})` : ""}<br>NO₂ ${ratio.toFixed(1)}× the usual level on the plains, averaged ${days}` +
      `<br>Sentinel-5P TROPOMI via NASA GIBS<br><a href="${SITE}/#at=${lat},${lon},10&layer=traffic">Open on HamariHawa</a>`)).join("");
  return doc("Traffic and industry NO₂", `Where exhaust gas collects: Sentinel-5P NO₂ averaged ${days}, with the strongest peaks labelled.`,
    style + overlay + `<Folder><name>Hotspots (${meta.hotspots.length})</name>${marks}</Folder>`);
}

// Daily satellite images straight from NASA GIBS (WMS), a day behind so they've finished processing.
// Haze stacks two days so orbit gaps show the day before.
export function satelliteKml() {
  const wms = (layer, d, fmt) => `https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&amp;REQUEST=GetMap&amp;VERSION=1.1.1&amp;STYLES=&amp;SRS=EPSG:4326` +
    `&amp;BBOX=${BOX.w},${BOX.s},${BOX.e},${BOX.n}&amp;WIDTH=2048&amp;HEIGHT=1744&amp;TRANSPARENT=TRUE&amp;FORMAT=${fmt}&amp;LAYERS=${layer}&amp;TIME=${d}`;
  const box = `<LatLonBox><north>${BOX.n}</north><south>${BOX.s}</south><east>${BOX.e}</east><west>${BOX.w}</west></LatLonBox>`;
  const ov = (name, layer, d, fmt, order, colour, vis) =>
    `<GroundOverlay><name>${esc(name)}</name><visibility>${vis}</visibility><drawOrder>${order}</drawOrder><color>${colour}</color>` +
    `<TimeStamp><when>${d}</when></TimeStamp><Icon><href>${wms(layer, d, fmt)}</href></Icon>${box}</GroundOverlay>`;
  const body =
    `<Folder><name>Haze and smoke (MODIS aerosol), ${day(1)}</name><visibility>1</visibility>` +
      ov(`Haze, ${day(2)} (fills gaps)`, "MODIS_Combined_Value_Added_AOD", day(2), "image/png", 1, "b4ffffff", 1) +
      ov(`Haze, ${day(1)}`, "MODIS_Combined_Value_Added_AOD", day(1), "image/png", 2, "b4ffffff", 1) + `</Folder>` +
    ov(`Satellite photo (VIIRS true colour), ${day(1)}`, "VIIRS_SNPP_CorrectedReflectance_TrueColor", day(1), "image/jpeg", 0, "ffffffff", 0);
  return doc("Satellite images", "NASA GIBS: MODIS haze and smoke, and the VIIRS true-colour photo where smoke plumes are visible. Refreshed every 6 hours.", body);
}
