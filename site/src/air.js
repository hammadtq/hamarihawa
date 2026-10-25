// City pages (/air/ and /air/<city>/): for each city-card city, which way the wind is blowing and the fires
// satellites saw in that direction. Built from two small KV keys: "cities" (the fires within 250 km of each
// city by district and 5-degree direction, written by scripts/build-feed.py with the 24 h feed) and "wind"
// (the hourly 2-degree grid from scripts/build-wind.py). The air reading itself loads in the visitor's
// browser (/city-air.js), as the city cards do, so the Worker never calls Open-Meteo.
import CITIES from "./cities.json";
import { SITE, LANGS, MONTHS, COUNTRY, ORG, STYLE, esc, nf, pct, dname, render, page, kvJson, notFound } from "./pages.js";

const BY_ID = new Map(CITIES.map((c) => [c.id, c]));
const CALM = 3; // km/h; below this the cards say there is no upwind, and so do these pages
const UPWIND = 45; // degrees either side of where the wind comes from
const DIRS = {
  en: ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"],
  ur: ["شمال", "شمال مشرق", "مشرق", "جنوب مشرق", "جنوب", "جنوب مغرب", "مغرب", "شمال مغرب"],
  hi: ["उत्तर", "उत्तर-पूर्व", "पूर्व", "दक्षिण-पूर्व", "दक्षिण", "दक्षिण-पश्चिम", "पश्चिम", "उत्तर-पश्चिम"],
};
const ZONE = { PK: [300, { en: "PKT", ur: "پاکستانی وقت", hi: "पाकिस्तानी समय" }], IN: [330, { en: "IST", ur: "بھارتی وقت", hi: "भारतीय समय" }] };
const BANDS = {
  en: ["Good", "Moderate", "Unhealthy for sensitive people", "Unhealthy", "Very unhealthy", "Hazardous"],
  ur: ["اچھی", "درمیانی", "حساس افراد کے لیے مضر", "مضر صحت", "بہت مضر", "خطرناک"],
  hi: ["अच्छी", "मध्यम", "संवेदनशील लोगों के लिए हानिकारक", "हानिकारक", "बहुत हानिकारक", "ख़तरनाक"],
};

const T = {
  en: {
    h1: (N) => `${N}'s air today: where the smoke is coming from`,
    title: (N) => `${N} air today: where the smoke is coming from`,
    wind: (N, dir, v, at) => `Right now the wind over ${N} blows from the <b>${dir}</b> at ${v} km/h (weather model, ${at}).`,
    calm: (N, at) => `The air over ${N} is almost still right now (under 3 km/h, ${at}), so smoke from the city's own sources and from nearby fires builds up instead of blowing away.`,
    noWind: (N) => `We don't have a wind reading for ${N} right now.`,
    up: (N, n, all) => ` In the last 24 hours NASA's satellites saw <b>${n}</b> fires within 250 km upwind of ${N}, in the direction the wind is coming from, out of ${all} within 250 km in every direction.`,
    upTop: (list) => ` Most were in ${list}.`, upMost: (list) => ` The largest numbers were in ${list}.`,
    crop: (p) => ` About ${p}% were on farmland, the pattern of crop-residue burning.`,
    noneUp: (all) => ` None of the ${all} fires seen within 250 km in the last 24 hours lie upwind, so the wind is not carrying their smoke here right now.`,
    noneAll: (N) => ` Satellites saw no fires within 250 km of ${N} in the last 24 hours, so today's haze is most likely the city's own: traffic, industry, brick kilns, burning rubbish and dust.`,
    around: (all) => ` ${all} fires were seen within 250 km in the last 24 hours.`,
    and: " and ",
    hAir: "The air right now",
    airLine: "US AQI {aqi} ({band}). PM2.5 has averaged {pm} µg/m³ over 24 hours, {who} times the WHO limit, like smoking {cigs} cigarettes a day.",
    airWait: (map) => `Loading the latest reading (Copernicus CAMS model estimates via Open-Meteo)… It is also on the <a href="${map}">live map</a>.`,
    hUp: "Upwind districts, last 24 hours", hDir: "Fires within 250 km by direction, last 24 hours", hWeek: "Fires within 250 km in the last 7 days",
    thDistrict: "District", thState: "Province or state", thCountry: "Country", thDir: "Direction", thKm: "Distance", thFires: "Fires", thCrop: "On farmland",
    thFrom: "From the", windHere: "the wind is coming from here",
    weekNone: "No fires within 250 km in the last 7 days.",
    hLocal: "Pollution sources within 50 km",
    kilns: (n) => `${n} brick kilns`, kilnsNone: "No brick kilns in the survey within 50 km (the kiln surveys cover only the Indus-Gangetic plain)",
    plants: (n) => `${n} fossil-fuel power plants`, incl: (names) => `, including ${names}`,
    industry: (n) => `${n} industrial areas mapped in OpenStreetMap`, landfills: (n) => `${n} landfills and dump sites`,
    localNote: 'From OpenStreetMap and the brick-kiln surveys. Every site is in the <a href="/sites/">pollution sites directory</a>.',
    hMore: (N) => `More about ${N}`, mapLink: (N) => `${N} on the live map`, distLink: (d) => `Fires in ${d} district, every season since 2019`,
    daily: "Daily fire pages", trends: "Fire trends", nearby: "Nearby cities:", allCities: "All cities",
    caveat: "Upwind is a guide, not proof: smoke can travel further than 250 km, the wind turns during the day, and satellites can't see fires under cloud. A fire here is one satellite detection, about 375 m across. Fires: NASA FIRMS (VIIRS and MODIS). Wind: Open-Meteo's weather model. Air: Copernicus CAMS model estimates, which read low in winter.",
    updated: (at) => `Fires up to ${at}. This page updates every 15 minutes.`,
    km: (n) => `${n} km`,
    desc: (N, txt) => `${N} air quality today, and where the smoke is coming from: ${txt} Live from NASA fire satellites and the wind.`,
    descUp: (n, dir) => `wind from the ${dir}, ${n} fires within 250 km upwind in the last 24 hours.`,
    descCalm: (all) => `almost no wind, ${all} fires within 250 km in the last 24 hours.`,
    idxH1: "City air: where the smoke is coming from",
    idxTitle: "City air today: where the smoke is coming from",
    idxDesc: "For 58 cities in Pakistan and India: which way the wind is blowing right now and how many fires satellites saw upwind in the last 24 hours.",
    idxLede: (n) => `For each of ${n} cities: which way the wind is blowing right now, and how many fires NASA's satellites saw in that direction within 250 km in the last 24 hours. Open a city for the districts the smoke is coming from and its air right now.`,
    thCity: "City", thWind: "Wind from", thUp: "Fires upwind (24 h)", thWeek: "Fires within 250 km (7 days)", calmCell: "almost still",
  },
  ur: {
    h1: (N) => `${N} کی ہوا آج: دھواں کہاں سے آ رہا ہے`,
    title: (N) => `${N} کی ہوا آج: دھواں کہاں سے آ رہا ہے`,
    wind: (N, dir, v, at) => `اس وقت ${N} پر ہوا <b>${dir}</b> سے ${v} کلومیٹر فی گھنٹہ کی رفتار سے چل رہی ہے (موسمی ماڈل، ${at})۔`,
    calm: (N, at) => `اس وقت ${N} پر ہوا تقریباً رکی ہوئی ہے (3 کلومیٹر فی گھنٹہ سے کم، ${at})، اس لیے شہر کے اپنے ذرائع اور قریب کی آگ کا دھواں اڑنے کے بجائے یہیں جمع ہوتا ہے۔`,
    noWind: (N) => `اس وقت ہمارے پاس ${N} کی ہوا کی معلومات نہیں ہیں۔`,
    up: (N, n, all) => ` پچھلے 24 گھنٹوں میں ناسا کے سیٹلائٹس نے ${N} سے 250 کلومیٹر کے اندر ہوا کے رخ پر، یعنی جدھر سے ہوا آ رہی ہے، <b>${n}</b> جگہ آگ دیکھی، جبکہ ہر سمت میں 250 کلومیٹر کے اندر کل ${all} جگہ۔`,
    upTop: (list) => ` ان میں سے زیادہ تر ${list} میں تھیں۔`, upMost: (list) => ` سب سے زیادہ ${list} میں تھیں۔`,
    crop: (p) => ` تقریباً ${p}% کھیتوں میں تھیں، جو فصلوں کی باقیات جلانے کا انداز ہے۔`,
    noneUp: (all) => ` پچھلے 24 گھنٹوں میں 250 کلومیٹر کے اندر دیکھی گئی ${all} آگ میں سے کوئی بھی ہوا کے رخ پر نہیں، اس لیے ہوا اس وقت ان کا دھواں یہاں نہیں لا رہی۔`,
    noneAll: (N) => ` پچھلے 24 گھنٹوں میں سیٹلائٹس نے ${N} سے 250 کلومیٹر کے اندر کوئی آگ نہیں دیکھی، اس لیے آج کی دھند غالباً شہر کی اپنی ہے: ٹریفک، صنعت، اینٹوں کے بھٹے، کچرا جلانا اور گرد۔`,
    around: (all) => ` پچھلے 24 گھنٹوں میں 250 کلومیٹر کے اندر ${all} جگہ آگ دیکھی گئی۔`,
    and: " اور ",
    hAir: "اس وقت کی ہوا",
    airLine: "امریکی AQI {aqi} ({band})۔ PM2.5 کا 24 گھنٹے کا اوسط {pm} µg/m³ رہا، عالمی ادارۂ صحت کی حد کا {who} گنا، یعنی روزانہ {cigs} سگریٹ پینے جتنا۔",
    airWait: (map) => `تازہ ترین ریڈنگ آ رہی ہے (Copernicus CAMS کے ماڈل اندازے، بذریعہ Open-Meteo)… یہ <a href="${map}">تازہ نقشے</a> پر بھی ہے۔`,
    hUp: "ہوا کے رخ پر اضلاع، پچھلے 24 گھنٹے", hDir: "250 کلومیٹر کے اندر آگ، سمت کے لحاظ سے، پچھلے 24 گھنٹے", hWeek: "پچھلے 7 دنوں میں 250 کلومیٹر کے اندر آگ",
    thDistrict: "ضلع", thState: "صوبہ یا ریاست", thCountry: "ملک", thDir: "سمت", thKm: "فاصلہ", thFires: "آگ", thCrop: "کھیتوں میں",
    thFrom: "سمت", windHere: "ہوا اسی طرف سے آ رہی ہے",
    weekNone: "پچھلے 7 دنوں میں 250 کلومیٹر کے اندر کوئی آگ نہیں دیکھی گئی۔",
    hLocal: "50 کلومیٹر کے اندر آلودگی کے ذرائع",
    kilns: (n) => `${n} اینٹوں کے بھٹے`, kilnsNone: "سروے میں 50 کلومیٹر کے اندر کوئی بھٹہ نہیں (بھٹوں کے سروے صرف سندھ و گنگا کے میدان کے ہیں)",
    plants: (n) => `فوسل ایندھن کے ${n} بجلی گھر`, incl: (names) => `، جن میں ${names} شامل ہیں`,
    industry: (n) => `OpenStreetMap میں درج ${n} صنعتی علاقے`, landfills: (n) => `${n} کچرا کنڈیاں اور ڈمپ`,
    localNote: 'OpenStreetMap اور اینٹوں کے بھٹوں کے سروے سے۔ ہر جگہ <a href="/sites/">آلودگی کے مقامات</a> کی فہرست میں ہے۔',
    hMore: (N) => `${N} کے بارے میں مزید`, mapLink: (N) => `${N} تازہ نقشے پر`, distLink: (d) => `ضلع ${d} میں آگ، 2019 سے ہر موسم`,
    daily: "روزانہ آگ کے صفحات", trends: "آگ کا رجحان", nearby: "قریبی شہر:", allCities: "تمام شہر",
    caveat: "ہوا کا رخ رہنمائی ہے، ثبوت نہیں: دھواں 250 کلومیٹر سے زیادہ دور تک جا سکتا ہے، دن میں ہوا کا رخ بدلتا رہتا ہے، اور بادلوں کے نیچے کی آگ سیٹلائٹ کو نظر نہیں آتی۔ یہاں ایک آگ سے مراد سیٹلائٹ کی ایک نشاندہی ہے، تقریباً 375 میٹر کا رقبہ۔ آگ: ناسا FIRMS (VIIRS اور MODIS)۔ ہوا: Open-Meteo کا موسمی ماڈل۔ ہوا کا معیار: Copernicus CAMS کے ماڈل اندازے، جو سردیوں میں کم بتاتے ہیں۔",
    updated: (at) => `آگ ${at} تک۔ یہ صفحہ ہر 15 منٹ بعد تازہ ہوتا ہے۔`,
    km: (n) => `${n} کلومیٹر`,
    idxH1: "شہروں کی ہوا: دھواں کہاں سے آ رہا ہے",
    idxLede: (n) => `${n} شہروں میں سے ہر ایک کے لیے: اس وقت ہوا کس طرف سے آ رہی ہے، اور پچھلے 24 گھنٹوں میں اس طرف 250 کلومیٹر کے اندر ناسا کے سیٹلائٹس نے کتنی آگ دیکھی۔ کسی شہر کو کھولیں تو وہ اضلاع نظر آئیں گے جہاں سے دھواں آ رہا ہے، اور اس وقت کی ہوا بھی۔`,
    thCity: "شہر", thWind: "ہوا کس طرف سے", thUp: "ہوا کے رخ پر آگ (24 گھنٹے)", thWeek: "250 کلومیٹر کے اندر آگ (7 دن)", calmCell: "تقریباً رکی ہوئی",
  },
  hi: {
    h1: (N) => `${N} की हवा आज: धुआँ कहाँ से आ रहा है`,
    title: (N) => `${N} की हवा आज: धुआँ कहाँ से आ रहा है`,
    wind: (N, dir, v, at) => `इस समय ${N} पर हवा <b>${dir}</b> से ${v} किमी/घंटा की रफ़्तार से चल रही है (मौसम मॉडल, ${at})।`,
    calm: (N, at) => `इस समय ${N} पर हवा लगभग थमी हुई है (3 किमी/घंटा से कम, ${at}), इसलिए शहर के अपने स्रोतों और पास की आग का धुआँ उड़ने के बजाय यहीं जमा होता है।`,
    noWind: (N) => `इस समय हमारे पास ${N} की हवा की जानकारी नहीं है।`,
    up: (N, n, all) => ` पिछले 24 घंटों में नासा के उपग्रहों ने ${N} से 250 किमी के भीतर हवा के रुख़ पर, यानी जिधर से हवा आ रही है, <b>${n}</b> जगह आग देखी, जबकि हर दिशा में 250 किमी के भीतर कुल ${all} जगह।`,
    upTop: (list) => ` इनमें से ज़्यादातर ${list} में थीं।`, upMost: (list) => ` सबसे ज़्यादा ${list} में थीं।`,
    crop: (p) => ` लगभग ${p}% खेतों में थीं, जो पराली जलाने का पैटर्न है।`,
    noneUp: (all) => ` पिछले 24 घंटों में 250 किमी के भीतर दिखी ${all} आग में से कोई भी हवा के रुख़ पर नहीं है, इसलिए हवा इस समय उनका धुआँ यहाँ नहीं ला रही।`,
    noneAll: (N) => ` पिछले 24 घंटों में उपग्रहों ने ${N} से 250 किमी के भीतर कोई आग नहीं देखी, इसलिए आज की धुंध शायद शहर की अपनी है: ट्रैफ़िक, उद्योग, ईंट भट्ठे, कूड़ा जलाना और धूल।`,
    around: (all) => ` पिछले 24 घंटों में 250 किमी के भीतर ${all} जगह आग दिखी।`,
    and: " और ",
    hAir: "इस समय की हवा",
    airLine: "अमेरिकी AQI {aqi} ({band})। PM2.5 का 24 घंटे का औसत {pm} µg/m³ रहा, WHO सीमा का {who} गुना, यानी रोज़ {cigs} सिगरेट पीने जितना।",
    airWait: (map) => `ताज़ा रीडिंग आ रही है (Copernicus CAMS के मॉडल अनुमान, Open-Meteo के ज़रिए)… यह <a href="${map}">लाइव नक्शे</a> पर भी है।`,
    hUp: "हवा के रुख़ पर ज़िले, पिछले 24 घंटे", hDir: "250 किमी के भीतर आग, दिशा के हिसाब से, पिछले 24 घंटे", hWeek: "पिछले 7 दिनों में 250 किमी के भीतर आग",
    thDistrict: "ज़िला", thState: "प्रांत या राज्य", thCountry: "देश", thDir: "दिशा", thKm: "दूरी", thFires: "आग", thCrop: "खेतों में",
    thFrom: "दिशा", windHere: "हवा इसी तरफ़ से आ रही है",
    weekNone: "पिछले 7 दिनों में 250 किमी के भीतर कोई आग नहीं दिखी।",
    hLocal: "50 किमी के भीतर प्रदूषण के स्रोत",
    kilns: (n) => `${n} ईंट भट्ठे`, kilnsNone: "सर्वे में 50 किमी के भीतर कोई भट्ठा नहीं (भट्ठों के सर्वे सिर्फ़ सिंधु-गंगा के मैदान के हैं)",
    plants: (n) => `जीवाश्म ईंधन के ${n} बिजलीघर`, incl: (names) => `, जिनमें ${names} शामिल हैं`,
    industry: (n) => `OpenStreetMap में दर्ज ${n} औद्योगिक क्षेत्र`, landfills: (n) => `${n} कचरा डंप`,
    localNote: 'OpenStreetMap और ईंट भट्ठों के सर्वे से। हर ठिकाना <a href="/sites/">प्रदूषण के ठिकानों</a> की सूची में है।',
    hMore: (N) => `${N} के बारे में और`, mapLink: (N) => `${N} लाइव नक्शे पर`, distLink: (d) => `${d} ज़िले में आग, 2019 से हर मौसम`,
    daily: "रोज़ की आग के पन्ने", trends: "आग का रुझान", nearby: "पास के शहर:", allCities: "सभी शहर",
    caveat: "हवा का रुख़ संकेत है, सबूत नहीं: धुआँ 250 किमी से ज़्यादा दूर तक जा सकता है, दिन में हवा का रुख़ बदलता रहता है, और बादलों के नीचे की आग उपग्रह को नहीं दिखती। यहाँ एक आग का मतलब उपग्रह की एक पहचान है, लगभग 375 मीटर का इलाक़ा। आग: नासा FIRMS (VIIRS और MODIS)। हवा: Open-Meteo का मौसम मॉडल। हवा की गुणवत्ता: Copernicus CAMS के मॉडल अनुमान, जो सर्दियों में कम आँकते हैं।",
    updated: (at) => `आग ${at} तक। यह पन्ना हर 15 मिनट में ताज़ा होता है।`,
    km: (n) => `${n} किमी`,
    idxH1: "शहरों की हवा: धुआँ कहाँ से आ रहा है",
    idxLede: (n) => `${n} शहरों में से हर एक के लिए: इस समय हवा किस तरफ़ से आ रही है, और पिछले 24 घंटों में उस तरफ़ 250 किमी के भीतर नासा के उपग्रहों ने कितनी आग देखी। किसी शहर को खोलें तो वे ज़िले दिखेंगे जहाँ से धुआँ आ रहा है, और इस समय की हवा भी।`,
    thCity: "शहर", thWind: "हवा किधर से", thUp: "हवा के रुख़ पर आग (24 घंटे)", thWeek: "250 किमी के भीतर आग (7 दिन)", calmCell: "लगभग थमी हुई",
  },
};

const AIR_STYLE = `<style>
  .air-now { font-size: 17px; margin: 6px 0 4px; }
  .air-now b { font-variant-numeric: tabular-nums; }
  .doc tr.wind-here td { font-weight: 600; }
  .doc ul.links li { margin-top: 4px; }
</style>\n`;

// Local time of a UTC instant (ms) for a city's country: "25 October, 18:40 PKT".
function at(ms, cc, l) {
  const [mins, names] = ZONE[cc] || ZONE.PK;
  const d = new Date(ms + mins * 60000);
  const hh = String(d.getUTCHours()).padStart(2, "0"), mm = String(d.getUTCMinutes()).padStart(2, "0");
  return `${d.getUTCDate()} ${MONTHS[l][d.getUTCMonth()]}${l === "ur" ? "،" : ","} <bdi dir="ltr">${hh}:${mm}</bdi> ${names[l]}`;
}
const compass = (deg, l) => DIRS[l][Math.round(deg / 45) % 8];
const angle = (a, b) => { const d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d; };

// Wind at a point from the 2-degree grid, interpolated as wind.js does: [speed km/h, direction it comes from].
function windAt(g, lat, lon) {
  if (!g || !g.speed) return null;
  const x = (lon - g.lon0) / g.step, y = (lat - g.lat0) / g.step;
  if (x < 0 || y < 0 || x > g.nx - 1 || y > g.ny - 1) return null;
  const x0 = Math.min(g.nx - 2, Math.floor(x)), y0 = Math.min(g.ny - 2, Math.floor(y)), fx = x - x0, fy = y - y0;
  let u = 0, v = 0;
  for (const [yy, xx, w] of [[y0, x0, (1 - fx) * (1 - fy)], [y0, x0 + 1, fx * (1 - fy)], [y0 + 1, x0, (1 - fx) * fy], [y0 + 1, x0 + 1, fx * fy]]) {
    const i = yy * g.nx + xx, s = g.speed[i], r = (g.dir[i] * Math.PI) / 180;
    u -= w * s * Math.sin(r); v -= w * s * Math.cos(r);
  }
  return [Math.hypot(u, v), ((Math.atan2(-u, -v) * 180) / Math.PI + 360) % 360];
}

// What the page says about one city: wind, upwind fires by district, fires by direction, the week's districts.
function smoke(data, wind, c) {
  const e = data?.cities?.[c.id];
  const w = windAt(wind, c.lat, c.lon);
  const calm = w && w[0] < CALM;
  const rows = e?.a || [];
  const bin = data?.bin || 5;
  const sectors = Array(8).fill(0);
  const up = new Map();
  let all = 0, upN = 0, upCrop = 0;
  for (const [di, b, n, crop, km] of rows) {
    const deg = b * bin + bin / 2;
    all += n;
    sectors[Math.round(deg / 45) % 8] += n;
    if (w && !calm && angle(deg, w[1]) <= UPWIND) {
      upN += n; upCrop += crop;
      const r = up.get(di) || { di, n: 0, crop: 0, km: 0, x: 0, y: 0 };
      r.n += n; r.crop += crop; r.km += km * n;
      r.x += n * Math.sin((deg * Math.PI) / 180); r.y += n * Math.cos((deg * Math.PI) / 180);
      up.set(di, r);
    }
  }
  const upRows = [...up.values()].sort((a, b) => b.n - a.n)
    .map((r) => ({ ...r, km: Math.round(r.km / r.n), deg: ((Math.atan2(r.x, r.y) * 180) / Math.PI + 360) % 360 }));
  return { e, w, calm, all, upN, upCrop, upRows, sectors, week: e?.w || [], n7: e?.n7 ?? (e?.w || []).reduce((x, r) => x + r[1], 0) };
}

function districtName(data, di) {
  const d = data.districts[di] || ["?", "", "", ""];
  return { name: dname(d[0]), state: d[1], cc: d[2], slug: d[3] };
}
const districtLink = (d) => (d.slug ? `<a href="/district/${d.slug}/">${esc(d.name)}</a>` : esc(d.name));

function lede(t, l, N, c, s, data, windTime) {
  let out = !s.w ? t.noWind(N) : s.calm ? t.calm(N, windTime) : t.wind(N, compass(s.w[1], l), nf(Math.round(s.w[0]), l), windTime);
  if (!s.all) return out + t.noneAll(N);
  if (!s.w || s.calm) return out + t.around(nf(s.all, l));
  if (!s.upN) return out + t.noneUp(nf(s.all, l));
  out += t.up(N, nf(s.upN, l), nf(s.all, l));
  // "Most" only when the two biggest districts really hold most of them; otherwise just name the biggest.
  const top2 = s.upRows.slice(0, 2), share = top2.reduce((x, r) => x + r.n, 0) / s.upN;
  const top = top2.map((r) => esc(districtName(data, r.di).name)).join(t.and);
  if (top2.length) out += share > 0.5 ? t.upTop(top) : t.upMost(top);
  if (s.upCrop / s.upN >= 0.5) out += t.crop(pct(s.upCrop, s.upN));
  return out;
}

function cityPage(c, data, wind) {
  const s = smoke(data, wind, c);
  const latest = data?.latest, windMs = wind?.time ? Date.parse(wind.time + "Z") : null;
  const mapUrl = `/#at=${c.lat},${c.lon},9`;
  const home = s.e && s.e.home >= 0 ? districtName(data, s.e.home) : null;
  const body = {};
  for (const l of LANGS) {
    const t = T[l], N = esc(c.name[l]), n = (v) => nf(v, l);
    const windTime = windMs ? at(windMs, c.cc, l) : "";
    const th = (cells) => `<thead><tr>${cells.map(([x, num]) => `<th${num ? ' class="n"' : ""}>${x}</th>`).join("")}</tr></thead>`;
    let h = `  <h1>${t.h1(N)}</h1>\n  <p class="lede">${lede(t, l, N, c, s, data, windTime)}</p>\n`;
    h += `  <h2>${t.hAir}</h2>\n  <p class="air-now" data-air data-lat="${c.lat}" data-lon="${c.lon}" data-lang="${l}" data-line="${esc(t.airLine)}" data-bands="${esc(BANDS[l].join("|"))}">${t.airWait(mapUrl)}</p>\n`;
    if (s.upRows.length) {
      h += `  <h2>${t.hUp}</h2>\n  <div class="table-wrap"><table>${th([[t.thDistrict], [t.thState], [t.thCountry], [t.thDir], [t.thKm, 1], [t.thFires, 1]])}<tbody>\n` +
        s.upRows.slice(0, 12).map((r) => { const d = districtName(data, r.di);
          return `   <tr><td>${districtLink(d)}</td><td>${esc(d.state)}</td><td>${COUNTRY[l][d.cc] || ""}</td><td>${compass(r.deg, l)}</td><td class="n">${t.km(n(r.km))}</td><td class="n">${n(r.n)}</td></tr>`; }).join("\n") +
        "\n  </tbody></table></div>\n";
    }
    if (s.all) {
      const here = s.w && !s.calm ? Math.round(s.w[1] / 45) % 8 : -1;
      h += `  <h2>${t.hDir}</h2>\n  <div class="table-wrap"><table>${th([[t.thFrom], [t.thFires, 1]])}<tbody>\n` +
        s.sectors.map((v, i) => `   <tr${i === here ? ' class="wind-here"' : ""}><td>${DIRS[l][i]}${i === here ? ` <span class="muted">(${t.windHere})</span>` : ""}</td><td class="n">${n(v)}</td></tr>`).join("\n") +
        "\n  </tbody></table></div>\n";
    }
    h += `  <h2>${t.hWeek}</h2>\n`;
    h += s.week.length ? `  <div class="table-wrap"><table>${th([[t.thDistrict], [t.thState], [t.thCountry], [t.thKm, 1], [t.thFires, 1], [t.thCrop, 1]])}<tbody>\n` +
      s.week.slice(0, 10).map(([di, wn, crop, km]) => { const d = districtName(data, di);
        return `   <tr><td>${districtLink(d)}</td><td>${esc(d.state)}</td><td>${COUNTRY[l][d.cc] || ""}</td><td class="n">${t.km(n(km))}</td><td class="n">${n(wn)}</td><td class="n">${pct(crop, wn)}%</td></tr>`; }).join("\n") +
      "\n  </tbody></table></div>\n" : `  <p>${t.weekNone}</p>\n`;
    const near = c.near || {};
    const local = [near.kilns ? t.kilns(n(near.kilns)) : t.kilnsNone];
    if (near.plants) local.push(t.plants(n(near.plants)) + (near.plantNames?.length ? t.incl(near.plantNames.map(esc).join(l === "en" ? ", " : "، ")) : ""));
    if (near.industry) local.push(t.industry(n(near.industry)));
    if (near.landfills) local.push(t.landfills(n(near.landfills)));
    h += `  <h2>${t.hLocal}</h2>\n  <ul>${local.map((x) => `<li>${x}</li>`).join("")}</ul>\n  <p class="muted">${t.localNote}</p>\n`;
    const links = [`<a href="${mapUrl}">${t.mapLink(N)}</a>`];
    if (home?.slug) links.push(`<a href="/district/${home.slug}/">${t.distLink(esc(home.name))}</a>`);
    links.push(`<a href="/fires/">${t.daily}</a>`, `<a href="/trends/">${t.trends}</a>`, `<a href="/air/">${t.allCities}</a>`);
    const nearby = (c.nearby || []).map(([id, km]) => BY_ID.get(id) && `<a href="/air/${id}/">${esc(BY_ID.get(id).name[l])}</a> (${t.km(n(km))})`).filter(Boolean);
    h += `  <h2>${t.hMore(N)}</h2>\n  <ul class="links">${links.map((x) => `<li>${x}</li>`).join("")}</ul>\n`;
    if (nearby.length) h += `  <p>${t.nearby} ${nearby.join(l === "en" ? ", " : "، ")}</p>\n`;
    h += `  <p class="muted" style="margin-top:18px">${latest ? t.updated(at(latest, c.cc, l)) + " " : ""}${t.caveat}</p>`;
    body[l] = h;
  }
  const N = c.name.en;
  const country = COUNTRY.en[c.cc];
  const descTxt = !s.w ? "" : s.calm ? T.en.descCalm(nf(s.all, "en")) : T.en.descUp(nf(s.upN, "en"), compass(s.w[1], "en"));
  const jsonld = { "@context": "https://schema.org", "@type": "WebPage", "@id": `${SITE}/air/${c.id}/#page`, name: T.en.title(N), url: `${SITE}/air/${c.id}/`,
    inLanguage: LANGS, publisher: ORG, isPartOf: { "@id": `${SITE}/#website` },
    about: { "@type": "City", name: N, geo: { "@type": "GeoCoordinates", latitude: c.lat, longitude: c.lon }, containedInPlace: { "@type": "Country", name: country } } };
  return render({ path: `/air/${c.id}/`, title: T.en.title(N), desc: T.en.desc(N, descTxt), body, jsonld,
    head: STYLE + AIR_STYLE, scripts: '<script src="/city-air.js?v=1" defer></script>\n' });
}

function indexPage(data, wind) {
  const rows = CITIES.map((c) => ({ c, s: smoke(data, wind, c) }))
    .sort((a, b) => b.s.upN - a.s.upN || b.s.n7 - a.s.n7);
  const body = {};
  for (const l of LANGS) {
    const t = T[l], n = (v) => nf(v, l);
    body[l] = `  <h1>${t.idxH1}</h1>\n  <p class="lede">${t.idxLede(n(CITIES.length))}</p>\n` +
      `  <div class="table-wrap"><table><thead><tr><th>${t.thCity}</th><th>${t.thCountry}</th><th>${t.thWind}</th><th class="n">${t.thUp}</th><th class="n">${t.thWeek}</th></tr></thead><tbody>\n` +
      rows.map(({ c, s }) => `   <tr><td><a href="/air/${c.id}/">${esc(c.name[l])}</a></td><td>${COUNTRY[l][c.cc]}</td>` +
        `<td>${!s.w ? "" : s.calm ? t.calmCell : compass(s.w[1], l)}</td><td class="n">${s.w && !s.calm ? n(s.upN) : "–"}</td><td class="n">${n(s.n7)}</td></tr>`).join("\n") +
      `\n  </tbody></table></div>\n  <p class="muted" style="margin-top:18px">${t.caveat}</p>`;
  }
  const jsonld = { "@context": "https://schema.org", "@type": "CollectionPage", "@id": `${SITE}/air/#page`, name: T.en.idxTitle, url: `${SITE}/air/`,
    inLanguage: LANGS, publisher: ORG, isPartOf: { "@id": `${SITE}/#website` } };
  return render({ path: "/air/", title: T.en.idxTitle, desc: T.en.idxDesc, body, jsonld, head: STYLE + AIR_STYLE });
}

// The shared shell marks the daily pages' section ("Fire trends") as current; these pages are "City air".
const navAir = (html) => html.replace(/ aria-current="page"/g, "").replace('data-nav="air"', 'data-nav="air" aria-current="page"');

// Returns a Response for /air/ and /air/<city>/, or null for any other path.
export async function airPages(url, env, ctx, edgeCached) {
  const p = url.pathname;
  if (p === "/air") return Response.redirect(`${url.origin}/air/${url.search}`, 301);
  const m = p.match(/^\/air\/([a-z0-9-]+)\/?$/);
  if (p !== "/air/" && !m) return p.startsWith("/air/") ? notFound() : null;
  if (m && !p.endsWith("/")) return Response.redirect(`${url.origin}${p}/${url.search}`, 301);
  const c = m && BY_ID.get(m[1]);
  if (m && !c) return notFound();
  // The fires change every 20 minutes at most and the wind hourly.
  return edgeCached(ctx, p, 900, async () => {
    const [data, wind] = await Promise.all([kvJson(env, "cities"), kvJson(env, "wind")]);
    if (!data) return new Response("City pages aren't built yet. Try again in a few minutes.", { status: 503 });
    return page(navAir(c ? cityPage(c, data, wind) : indexPage(data, wind)), 200, 600);
  });
}

export const AIR_PATHS = ["/air/", ...CITIES.map((c) => `/air/${c.id}/`)];
