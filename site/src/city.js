// The city pages' longer snapshot (/air/<city>/) and the live rankings (/rankings/): fires around the city
// day by day and season by season ("city-fires", scripts/build-feed.py city_fires), NO2 from the satellite
// ("no2-cities", scripts/build-no2.py), and the measured and mapped sources within 50 km (cities.json "src",
// scripts/build-pages.py city_sources). Every number is precomputed by those builders; this only formats.
// Wording rule: these are measurements around a city, never shares of what is in its air.
import CITIES from "./cities.json";
import { SITE, LANGS, MONTHS, COUNTRY, ORG, esc, nf } from "./pages.js";

const BY_ID = new Map(CITIES.map((c) => [c.id, c]));
const date = (iso, l, year) => {
  const [y, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[l][m - 1]}${year ? " " + y : ""}`;
};
const SEP = (l) => (l === "ur" ? "، " : ", "); // Hindi lists use the Latin comma; Urdu its own

const KIND = {
  en: { traffic: "a city's traffic", plant: "a power or industrial plant", industry: "an industrial estate", kilns: "brick kilns", corridor: "a road or rail corridor" },
  ur: { traffic: "شہر کی ٹریفک", plant: "بجلی گھر یا صنعتی پلانٹ", industry: "صنعتی علاقہ", kilns: "اینٹوں کے بھٹے", corridor: "سڑک یا ریل کی پٹی" },
  hi: { traffic: "शहर का ट्रैफ़िक", plant: "बिजलीघर या औद्योगिक प्लांट", industry: "औद्योगिक इलाक़ा", kilns: "ईंट भट्ठे", corridor: "सड़क या रेल गलियारा" },
};
const FUEL = { en: { coal: "coal", gas: "gas", oil: "oil" }, ur: { coal: "کوئلہ", gas: "گیس", oil: "تیل" }, hi: { coal: "कोयला", gas: "गैस", oil: "तेल" } };
const PLANT = {
  en: { coal: "coal plant", gas: "gas plant", oil: "oil plant", power: "power plant", industry: "industrial plant" },
  ur: { coal: "کوئلے کا پلانٹ", gas: "گیس پلانٹ", oil: "تیل کا پلانٹ", power: "بجلی گھر", industry: "صنعتی پلانٹ" },
  hi: { coal: "कोयला प्लांट", gas: "गैस प्लांट", oil: "तेल प्लांट", power: "बिजलीघर", industry: "औद्योगिक प्लांट" },
};

const T = {
  en: {
    hFires: (N) => `Fires around ${N} in the last 30 days`,
    firesLede: (N, n30, n50, last, days) => `NASA's satellites saw <b>${n30}</b> fire spots within 250 km of ${N} in the ${days} days to ${last}, <b>${n50}</b> of them within 50 km.`,
    firesNone: (N, last, days) => `NASA's satellites saw no fires within 250 km of ${N} in the ${days} days to ${last}.`,
    key250: "within 250 km", key50: "within 50 km", noDay: "no data",
    chartFires: (N) => `Fire spots around ${N} per day`,
    firesNote: "A fire spot is one fire seen on a day, however many satellites saw it (Pakistan-time days). The archive runs every day from 1 October 2026; before that it holds only the October-November seasons.",
    hSeason: (N) => `Fires around ${N} this season compared with past years`,
    seasonLede: (N, to) => `Fire spots within 250 km of ${N} from 1 October to ${to}, each year. These count Suomi NPP alone, so every year is measured by the same instrument and the years compare fairly (the 30-day chart above counts all five satellites, three VIIRS and two MODIS, so its numbers are higher).`,
    seasonLedeDone: (N) => `Fire spots within 250 km of ${N} over each whole season, 1 October to 30 November, counted from Suomi NPP alone, so every year is measured by the same instrument.`,
    thYear: "Season", thSpots: "Fire spots", thVsNow: "This season",
    soFar: "so far", gapNote: (n, one) => `${n} day${one ? "" : "s"} without Suomi NPP data: a floor`, noData: "no data",
    seasonUp: (N, p, y) => `So far this season there have been ${p}% more fire spots around ${N} than at the same point in ${y}.`,
    seasonDown: (N, p, y) => `So far this season there have been ${p}% fewer fire spots around ${N} than at the same point in ${y}.`,
    hNo2: (N) => `NO₂ pollution in ${N}: traffic, industry and power plants`,
    no2Lede: (N, r, m, rank, n, from, to) => `Over the 14 days ${from} to ${to}, nitrogen dioxide in the air over ${N} (within 15 km) was about <b>${r} times</b> the usual level of the surrounding region, roughly ${m} ×10¹⁵ molecules/cm². Of the ${n} cities with enough clear days, it ranks <b>${rank}</b>.`,
    no2Trend: (p, dir) => dir === 0 ? ` About the same as the two weeks before.` : ` That is ${p}% ${dir > 0 ? "higher" : "lower"} than in the two weeks before.`,
    no2None: (N) => `Clouds or missing passes left too little satellite data over ${N} in the last 14 days for a reading.`,
    no2Peak: (r, km, what, site) => `The strongest NO₂ peak within 35 km was ${r} times the usual level, ${km} km from the city centre, near ${what} (${esc(site)}).`,
    no2PeakHere: (r, what) => `The strongest NO₂ peak within 35 km was ${r} times the usual level, in the city itself, the pattern of ${what}.`,
    no2PeakTown: (r, km, site) => `The strongest NO₂ peak within 35 km was ${r} times the usual level, ${km} km from the city centre in the built-up area of ${esc(site)}, the pattern of traffic.`,
    chartNo2: (N) => `NO₂ over ${N}, each 14-day window`,
    no2Note: "From Sentinel-5P's TROPOMI instrument via NASA's GIBS tiles, which publish NO₂ as colour bands: a level here is good to about one band. NO₂ in big cities comes mostly from vehicle engines; peaks are named after what is nearby, which suggests a source but doesn't measure one.",
    hCh4: (N) => `Landfills and methane near ${N}`,
    ch4Lede: (N, n, kg, one) => `Carbon Mapper's satellites and aircraft have measured methane rising from <b>${n}</b> landfill site${one ? "" : "s"} within 50 km of ${N}, together about <b>${kg} kg an hour</b>.`,
    ch4None: (N) => `Carbon Mapper hasn't measured a methane plume from a landfill within 50 km of ${N}. Its overpasses are occasional, so that isn't proof there are none.`,
    thSite: "Site", thRate: "Methane", thPlumes: "Plumes seen", thLast: "Last seen", thRankAll: "Rank",
    rateCell: (v) => `${v} kg/h`, rankOf: (r, n) => `${r} of ${n}`,
    ch4Note: (n) => `Rank among the ${n} landfill records with a measured rate in Carbon Mapper's data for Pakistan and India (this extract covers only these two countries). Rates are Carbon Mapper's automatic per-plume estimates; landfill methane also carries the smell and smoke of burning rubbish.`,
    hPlants: (N) => `Power plants, factories and brick kilns near ${N}`,
    co2Line: (n, t, one) => `<b>${n}</b> plant${one ? "" : "s"} with CO₂ plumes measured by Carbon Mapper, about <b>${t} tonnes of CO₂ an hour</b>${one ? "" : " together"}`,
    fossilLine: (n, parts, one) => `<b>${n}</b> fossil-fuel power plant${one ? "" : "s"} mapped in OpenStreetMap (${parts})`,
    industryLine: (n) => `<b>${n}</b> industrial areas mapped in OpenStreetMap`,
    hotLine: (n, top, one) => `<b>${n}</b> always-hot site${one ? "" : "s"} that NASA's satellites saw burning on 20 or more days in 2025${top}`,
    kilnLine: (n, pk, inn, z, one) => one ? `<b>1</b> brick kiln in the satellite surveys` : `<b>${n}</b> brick kilns in the satellite surveys (${pk} in Pakistan, ${inn} in India), ${z}% of them the cleaner zigzag kind`,
    kilnPm: (t, e, n) => `; their survey estimates ${t} tonnes of PM2.5 a day in the firing season from the ${e} of the ${n} kilns it has figures for`,
    kilnNone: "No brick kilns in the survey within 50 km",
    kilnOutside: "Outside the area the brick-kiln surveys cover, so kilns here aren't counted",
    shown: (k) => ` (largest ${k} shown)`,
    plantsNote: "Within 50 km of the city centre, on either side of the border. These are lists of what is there, not measures of how much each adds to the air.",
    hCompare: (N) => `${N}'s pollution sources compared with other cities`,
    compareLede: (N, n) => `Where ${N} stands among the ${n} cities with pages here, on each measure. They are different measures, so a high rank on one isn't a larger share of the air than a high rank on another.`,
    thMeasure: "Measure", thValue: (N) => N, thRank: "Rank",
    mFires: "Fire spots within 250 km, last 30 days", mNo2: "NO₂, times the usual level (14 days)", mCh4: "Landfill methane within 50 km",
    mCo2: "Measured plant CO₂ within 50 km", mKilns: "Brick kilns within 50 km", mInd: "Industrial areas within 50 km", mHot: "Always-hot sites within 50 km",
    kgh: (v) => `${v} kg/h`, th: (v) => `${v} t/h`, km: (v) => `${v} km`, x: (v) => `${v}×`, none: "none", noneMeasured: "none measured", noReading: "no reading", notRanked: "–", calmRank: "calm wind, no upwind direction",
    hRanks: (N) => `Where ${N} ranks right now`,
    ranksLede: (N) => `${N}'s place among the cities, on the numbers that change with each satellite pass.`,
    rUp: "Fire spots upwind, last 24 hours", rAll: "Fire spots within 250 km, last 24 hours", rWeek: "Fire spots within 250 km, last 7 days",
    seeAll: `All the rankings: <a href="/rankings/">city rankings</a>`,
    hQa: (N) => `Questions about ${N}'s air`,
    qFrom: (N) => `Where is ${N}'s smoke coming from today?`,
    qFires: (N) => `Are crop fires burning near ${N}?`,
    aFires: (N, n24, n30) => `In the last 24 hours NASA's satellites saw ${n24} fire spots within 250 km of ${N}, and ${n30} in the last 30 days. Satellites only see what is burning as they pass, and not under cloud.`,
    qNo2: (N) => `How bad is traffic pollution in ${N}?`,
    qKilns: (N) => `How many brick kilns are there near ${N}?`,
    aKilns: (N, n) => `The satellite surveys count ${n} brick kilns within 50 km of ${N}.`,
    qCh4: (N) => `Which landfills near ${N} release methane?`,
    aCh4: (list) => `Carbon Mapper has measured methane plumes from ${list}.`,
    dataLine: (u) => `Every number on this page is also in <a href="${u}">machine-readable form (JSON)</a>.`,
    asOf: (d) => `Fires up to ${d}.`, sourcesAsOf: (d) => `Site lists built ${d}.`, no2AsOf: (a, b) => `NO₂ window ${a} to ${b}.`,
    // /rankings/
    rkTitle: "City rankings: smoke, fires and pollution right now in Pakistan and India",
    rkDesc: "58 cities in Pakistan and India ranked by the smoke the wind is bringing, fires within 250 km, satellite NO₂ and the methane, plants and brick kilns around them. Updated with each satellite pass.",
    rkH1: "City rankings: smoke, fires and pollution right now",
    rkLede: (n) => `How the ${n} cities with pages here compare, on what the satellites see around them. The fire tables change with each satellite pass; NO₂ is a 14-day average updated daily; the site counts change only when the source lists are rebuilt. These rank what is around each city, not how much of it is in the air.`,
    rkFresh: (d) => `Fires up to ${d}.`, rkNo2Fresh: (a, b) => `14 days, ${a} to ${b}.`, rkSrcFresh: (d) => `Lists built ${d}.`,
    thCity: "City", thCountry: "Country",
    rkAir: "Air quality now", rkAirBtn: "Load live air quality for all cities",
    rkAirNote: "Readings come straight to your browser from Copernicus CAMS model estimates via Open-Meteo, so they load only when you ask. The model reads low in winter.",
    rkAqi: "US AQI", rkPm: "PM2.5 (µg/m³)", rkAirFail: "The air-quality service didn't answer. Try again in a minute.",
    rkMore: (n) => `Show all ${n}`,
  },
  ur: {
    hFires: (N) => `پچھلے 30 دن میں ${N} کے آس پاس آگ`,
    firesLede: (N, n30, n50, last, days) => `${last} تک کے ${days} دنوں میں ناسا کے سیٹلائٹس نے ${N} سے 250 کلومیٹر کے اندر <b>${n30}</b> جگہ آگ دیکھی، جن میں سے <b>${n50}</b> 50 کلومیٹر کے اندر تھیں۔`,
    firesNone: (N, last, days) => `${last} تک کے ${days} دنوں میں ناسا کے سیٹلائٹس نے ${N} سے 250 کلومیٹر کے اندر کوئی آگ نہیں دیکھی۔`,
    key250: "250 کلومیٹر کے اندر", key50: "50 کلومیٹر کے اندر", noDay: "معلومات نہیں",
    chartFires: (N) => `${N} کے آس پاس روزانہ آگ`,
    firesNote: "ایک دن میں ایک جگہ کی آگ ایک بار گنی جاتی ہے، چاہے اسے کتنے ہی سیٹلائٹس نے دیکھا ہو (پاکستانی وقت کے دن)۔ ریکارڈ یکم اکتوبر 2026 سے ہر دن کا ہے؛ اس سے پہلے صرف اکتوبر-نومبر کے موسم۔",
    hSeason: (N) => `اس موسم میں ${N} کے آس پاس آگ پچھلے برسوں کے مقابلے میں`,
    seasonLede: (N, to) => `ہر سال یکم اکتوبر سے ${to} تک ${N} سے 250 کلومیٹر کے اندر آگ۔ یہ صرف سومی این پی پی سیٹلائٹ کی گنتی ہے، اس لیے ہر سال ایک ہی آلے سے ناپا گیا اور برسوں کا موازنہ منصفانہ ہے (اوپر والا 30 دن کا چارٹ پانچوں سیٹلائٹس گنتا ہے، تین VIIRS اور دو MODIS، اس لیے اس کے اعداد زیادہ ہیں)۔`,
    seasonLedeDone: (N) => `ہر پورے موسم میں، یکم اکتوبر سے 30 نومبر تک، ${N} سے 250 کلومیٹر کے اندر آگ، صرف سومی این پی پی کی گنتی سے، تاکہ ہر سال ایک ہی آلے سے ناپا جائے۔`,
    thYear: "موسم", thSpots: "آگ", thVsNow: "یہ موسم",
    soFar: "اب تک", gapNote: (n) => `${n} دن سومی این پی پی کی معلومات کے بغیر: کم از کم`, noData: "معلومات نہیں",
    seasonUp: (N, p, y) => `اس موسم میں اب تک ${N} کے آس پاس ${y} کے اسی وقت کے مقابلے میں ${p}% زیادہ آگ دیکھی گئی۔`,
    seasonDown: (N, p, y) => `اس موسم میں اب تک ${N} کے آس پاس ${y} کے اسی وقت کے مقابلے میں ${p}% کم آگ دیکھی گئی۔`,
    hNo2: (N) => `${N} میں NO₂ آلودگی: ٹریفک، صنعت اور بجلی گھر`,
    no2Lede: (N, r, m, rank, n, from, to) => `${from} سے ${to} تک کے 14 دنوں میں ${N} کی فضا میں (15 کلومیٹر کے اندر) نائٹروجن ڈائی آکسائیڈ ارد گرد کے علاقے کی عام سطح سے تقریباً <b>${r} گنا</b> تھی، تقریباً ${m} ×10¹⁵ مالیکیول فی مربع سینٹی میٹر۔ کافی صاف دنوں والے ${n} شہروں میں یہ نمبر <b>${rank}</b> ہے۔`,
    no2Trend: (p, dir) => dir === 0 ? ` پچھلے دو ہفتوں جیسی ہی۔` : ` یہ پچھلے دو ہفتوں سے ${p}% ${dir > 0 ? "زیادہ" : "کم"} ہے۔`,
    no2None: (N) => `پچھلے 14 دنوں میں بادلوں یا سیٹلائٹ کے نہ گزرنے کی وجہ سے ${N} پر پیمائش کے لیے کافی معلومات نہیں۔`,
    no2Peak: (r, km, what, site) => `35 کلومیٹر کے اندر NO₂ کی سب سے اونچی جگہ عام سطح سے ${r} گنا تھی، شہر کے مرکز سے ${km} کلومیٹر دور، ${what} کے قریب (${esc(site)})۔`,
    no2PeakHere: (r, what) => `35 کلومیٹر کے اندر NO₂ کی سب سے اونچی جگہ عام سطح سے ${r} گنا تھی، خود شہر میں، جو ${what} کا انداز ہے۔`,
    no2PeakTown: (r, km, site) => `35 کلومیٹر کے اندر NO₂ کی سب سے اونچی جگہ عام سطح سے ${r} گنا تھی، شہر کے مرکز سے ${km} کلومیٹر دور ${esc(site)} کی آبادی میں، جو ٹریفک کا انداز ہے۔`,
    chartNo2: (N) => `${N} پر NO₂، ہر 14 دن کا دور`,
    no2Note: "سینٹینل-5P کے ٹروپومی آلے سے، ناسا کی GIBS تصاویر کے ذریعے، جو NO₂ کو رنگوں کی پٹیوں میں دکھاتی ہیں: یہاں کی سطح تقریباً ایک پٹی تک درست ہے۔ بڑے شہروں میں NO₂ زیادہ تر گاڑیوں کے انجنوں سے آتی ہے؛ اونچی جگہوں کے نام قریب کی چیز پر رکھے گئے ہیں، جو ممکنہ ذریعہ بتاتا ہے، ناپتا نہیں۔",
    hCh4: (N) => `${N} کے قریب کچرا کنڈیاں اور میتھین`,
    ch4Lede: (N, n, kg) => `کاربن میپر کے سیٹلائٹس اور جہازوں نے ${N} سے 50 کلومیٹر کے اندر <b>${n}</b> کچرا کنڈیوں سے اٹھتی میتھین ناپی ہے، مل کر تقریباً <b>${kg} کلوگرام فی گھنٹہ</b>۔`,
    ch4None: (N) => `کاربن میپر نے ${N} سے 50 کلومیٹر کے اندر کسی کچرا کنڈی سے میتھین نہیں ناپی۔ اس کے گزر کبھی کبھار ہوتے ہیں، اس لیے یہ اس بات کا ثبوت نہیں کہ کوئی نہیں۔`,
    thSite: "جگہ", thRate: "میتھین", thPlumes: "دیکھے گئے دھوئیں", thLast: "آخری بار", thRankAll: "درجہ",
    rateCell: (v) => `${v} کلوگرام فی گھنٹہ`, rankOf: (r, n) => `${n} میں ${r}`,
    ch4Note: (n) => `پاکستان اور ہندوستان کے لیے کاربن میپر کے ڈیٹا میں ناپی گئی شرح والے ${n} کچرا کنڈی ریکارڈز میں درجہ (یہ ڈیٹا صرف ان دو ملکوں کا ہے)۔ شرحیں کاربن میپر کے خودکار اندازے ہیں؛ کچرا کنڈی کی میتھین کے ساتھ کچرا جلنے کی بو اور دھواں بھی آتا ہے۔`,
    hPlants: (N) => `${N} کے قریب بجلی گھر، کارخانے اور اینٹوں کے بھٹے`,
    co2Line: (n, t, one) => one ? `<b>1</b> پلانٹ جس کا CO₂ کاربن میپر نے ناپا، تقریباً <b>${t} ٹن CO₂ فی گھنٹہ</b>` : `<b>${n}</b> پلانٹ جن کا CO₂ کاربن میپر نے ناپا، مل کر تقریباً <b>${t} ٹن CO₂ فی گھنٹہ</b>`,
    fossilLine: (n, parts) => `اوپن اسٹریٹ میپ میں <b>${n}</b> ایندھن سے چلنے والے بجلی گھر (${parts})`,
    industryLine: (n) => `اوپن اسٹریٹ میپ میں <b>${n}</b> صنعتی علاقے`,
    hotLine: (n, top) => `<b>${n}</b> ہمیشہ گرم جگہیں جنہیں ناسا کے سیٹلائٹس نے 2025 میں 20 یا زیادہ دن جلتے دیکھا${top}`,
    kilnLine: (n, pk, inn, z) => `سیٹلائٹ سروے میں <b>${n}</b> اینٹوں کے بھٹے (${pk} پاکستان میں، ${inn} ہندوستان میں)، جن میں سے ${z}% صاف تر زگ زیگ قسم کے`,
    kilnPm: (t, e, n) => `؛ سروے کا اندازہ ہے کہ جن ${e} بھٹوں کے اعداد ہیں (کل ${n}) وہ بھٹوں کے موسم میں روزانہ ${t} ٹن PM2.5 چھوڑتے ہیں`,
    kilnNone: "50 کلومیٹر کے اندر سروے میں اینٹوں کا کوئی بھٹہ نہیں",
    kilnOutside: "یہ جگہ بھٹوں کے سروے کے علاقے سے باہر ہے، اس لیے یہاں کے بھٹے نہیں گنے گئے",
    shown: (k) => ` (سب سے بڑے ${k} دکھائے گئے)`,
    plantsNote: "شہر کے مرکز سے 50 کلومیٹر کے اندر، سرحد کے دونوں طرف۔ یہ وہاں موجود چیزوں کی فہرستیں ہیں، یہ نہیں کہ ہر ایک ہوا میں کتنا حصہ ڈالتی ہے۔",
    hCompare: (N) => `${N} کے آلودگی کے ذرائع دوسرے شہروں کے مقابلے میں`,
    compareLede: (N, n) => `یہاں موجود ${n} شہروں میں ہر پیمانے پر ${N} کہاں ہے۔ یہ الگ الگ پیمانے ہیں، اس لیے ایک پر اونچا درجہ دوسرے پر اونچے درجے سے ہوا میں زیادہ حصہ نہیں۔`,
    thMeasure: "پیمانہ", thValue: (N) => N, thRank: "درجہ",
    mFires: "250 کلومیٹر کے اندر آگ، پچھلے 30 دن", mNo2: "NO₂، عام سطح سے گنا (14 دن)", mCh4: "50 کلومیٹر کے اندر کچرا کنڈی میتھین",
    mCo2: "50 کلومیٹر کے اندر ناپا گیا پلانٹ CO₂", mKilns: "50 کلومیٹر کے اندر اینٹوں کے بھٹے", mInd: "50 کلومیٹر کے اندر صنعتی علاقے", mHot: "50 کلومیٹر کے اندر ہمیشہ گرم جگہیں",
    kgh: (v) => `${v} کلوگرام/گھنٹہ`, th: (v) => `${v} ٹن/گھنٹہ`, km: (v) => `${v} کلومیٹر`, x: (v) => `${v} گنا`, none: "کوئی نہیں", noneMeasured: "کوئی ناپا نہیں گیا", noReading: "پیمائش نہیں", notRanked: "–", calmRank: "ہوا رکی ہوئی، رخ نہیں",
    hRanks: (N) => `${N} اس وقت کس نمبر پر ہے`,
    ranksLede: (N) => `ہر سیٹلائٹ گزر کے ساتھ بدلنے والے اعداد پر شہروں میں ${N} کا مقام۔`,
    rUp: "ہوا کے رخ پر آگ، پچھلے 24 گھنٹے", rAll: "250 کلومیٹر کے اندر آگ، پچھلے 24 گھنٹے", rWeek: "250 کلومیٹر کے اندر آگ، پچھلے 7 دن",
    seeAll: `تمام درجہ بندیاں: <a href="/rankings/">شہروں کی درجہ بندی</a>`,
    hQa: (N) => `${N} کی ہوا کے بارے میں سوالات`,
    qFrom: (N) => `آج ${N} کا دھواں کہاں سے آ رہا ہے؟`,
    qFires: (N) => `کیا ${N} کے قریب فصلوں کی آگ جل رہی ہے؟`,
    aFires: (N, n24, n30) => `پچھلے 24 گھنٹوں میں ناسا کے سیٹلائٹس نے ${N} سے 250 کلومیٹر کے اندر ${n24} جگہ آگ دیکھی، اور پچھلے 30 دنوں میں ${n30}۔ سیٹلائٹ صرف وہی دیکھتے ہیں جو ان کے گزرتے وقت جل رہا ہو، اور بادلوں کے نیچے نہیں۔`,
    qNo2: (N) => `${N} میں ٹریفک کی آلودگی کتنی ہے؟`,
    qKilns: (N) => `${N} کے قریب اینٹوں کے کتنے بھٹے ہیں؟`,
    aKilns: (N, n) => `سیٹلائٹ سروے ${N} سے 50 کلومیٹر کے اندر ${n} اینٹوں کے بھٹے گنتے ہیں۔`,
    qCh4: (N) => `${N} کے قریب کون سی کچرا کنڈیاں میتھین چھوڑتی ہیں؟`,
    aCh4: (list) => `کاربن میپر نے ${list} سے میتھین کے دھوئیں ناپے ہیں۔`,
    dataLine: (u) => `اس صفحے کا ہر عدد <a href="${u}">مشین کے پڑھنے کے قابل شکل (JSON)</a> میں بھی ہے۔`,
    asOf: (d) => `آگ ${d} تک۔`, sourcesAsOf: (d) => `فہرستیں ${d} کو بنیں۔`, no2AsOf: (a, b) => `NO₂ کا دور ${a} سے ${b}۔`,
    rkTitle: "شہروں کی درجہ بندی: پاکستان اور ہندوستان میں اس وقت دھواں، آگ اور آلودگی",
    rkDesc: "",
    rkH1: "شہروں کی درجہ بندی: اس وقت دھواں، آگ اور آلودگی",
    rkLede: (n) => `یہاں موجود ${n} شہروں کا موازنہ، اس پر جو سیٹلائٹ ان کے آس پاس دیکھتے ہیں۔ آگ کی جدولیں ہر سیٹلائٹ گزر کے ساتھ بدلتی ہیں؛ NO₂ روزانہ تازہ ہونے والی 14 دن کی اوسط ہے؛ جگہوں کی گنتی تب بدلتی ہے جب فہرستیں دوبارہ بنتی ہیں۔ یہ ہر شہر کے آس پاس کی چیزوں کی درجہ بندی ہے، یہ نہیں کہ ہوا میں ان کا کتنا حصہ ہے۔`,
    rkFresh: (d) => `آگ ${d} تک۔`, rkNo2Fresh: (a, b) => `14 دن، ${a} سے ${b}۔`, rkSrcFresh: (d) => `فہرستیں ${d} کو بنیں۔`,
    thCity: "شہر", thCountry: "ملک",
    rkAir: "اس وقت ہوا کا معیار", rkAirBtn: "تمام شہروں کی تازہ ہوا لوڈ کریں",
    rkAirNote: "یہ پیمائشیں Open-Meteo کے ذریعے Copernicus CAMS کے ماڈل اندازوں سے سیدھی آپ کے براؤزر میں آتی ہیں، اس لیے صرف آپ کے کہنے پر لوڈ ہوتی ہیں۔ ماڈل سردیوں میں کم بتاتا ہے۔",
    rkAqi: "US AQI", rkPm: "PM2.5 (µg/m³)", rkAirFail: "ہوا کے معیار کی سروس نے جواب نہیں دیا۔ ایک منٹ بعد دوبارہ کوشش کریں۔",
    rkMore: (n) => `تمام ${n} دکھائیں`,
  },
  hi: {
    hFires: (N) => `पिछले 30 दिनों में ${N} के आसपास आग`,
    firesLede: (N, n30, n50, last, days) => `${last} तक के ${days} दिनों में नासा के उपग्रहों ने ${N} से 250 किमी के भीतर <b>${n30}</b> जगह आग देखी, जिनमें से <b>${n50}</b> 50 किमी के भीतर थीं।`,
    firesNone: (N, last, days) => `${last} तक के ${days} दिनों में नासा के उपग्रहों ने ${N} से 250 किमी के भीतर कोई आग नहीं देखी।`,
    key250: "250 किमी के भीतर", key50: "50 किमी के भीतर", noDay: "डेटा नहीं",
    chartFires: (N) => `${N} के आसपास रोज़ की आग`,
    firesNote: "एक दिन में एक जगह की आग एक बार गिनी जाती है, चाहे उसे कितने भी उपग्रहों ने देखा हो (पाकिस्तानी समय के दिन)। रिकॉर्ड 1 अक्टूबर 2026 से हर दिन का है; उससे पहले सिर्फ़ अक्टूबर-नवंबर के मौसम।",
    hSeason: (N) => `इस मौसम में ${N} के आसपास आग पिछले सालों की तुलना में`,
    seasonLede: (N, to) => `हर साल 1 अक्टूबर से ${to} तक ${N} से 250 किमी के भीतर आग। यह सिर्फ़ सुओमी एनपीपी उपग्रह की गिनती है, इसलिए हर साल एक ही उपकरण से मापा गया और सालों की तुलना निष्पक्ष है (ऊपर का 30 दिन का चार्ट पाँचों उपग्रह गिनता है, तीन VIIRS और दो MODIS, इसलिए उसके आँकड़े ज़्यादा हैं)।`,
    seasonLedeDone: (N) => `हर पूरे मौसम में, 1 अक्टूबर से 30 नवंबर तक, ${N} से 250 किमी के भीतर आग, सिर्फ़ सुओमी एनपीपी की गिनती से, ताकि हर साल एक ही उपकरण से मापा जाए।`,
    thYear: "मौसम", thSpots: "आग", thVsNow: "यह मौसम",
    soFar: "अब तक", gapNote: (n) => `${n} दिन सुओमी एनपीपी के डेटा के बिना: कम से कम`, noData: "डेटा नहीं",
    seasonUp: (N, p, y) => `इस मौसम में अब तक ${N} के आसपास ${y} के इसी समय की तुलना में ${p}% ज़्यादा आग दिखी।`,
    seasonDown: (N, p, y) => `इस मौसम में अब तक ${N} के आसपास ${y} के इसी समय की तुलना में ${p}% कम आग दिखी।`,
    hNo2: (N) => `${N} में NO₂ प्रदूषण: ट्रैफ़िक, उद्योग और बिजलीघर`,
    no2Lede: (N, r, m, rank, n, from, to) => `${from} से ${to} तक के 14 दिनों में ${N} की हवा में (15 किमी के भीतर) नाइट्रोजन डाइऑक्साइड आसपास के इलाक़े के सामान्य स्तर से लगभग <b>${r} गुना</b> थी, लगभग ${m} ×10¹⁵ अणु प्रति वर्ग सेमी। पर्याप्त साफ़ दिनों वाले ${n} शहरों में यह <b>${rank}</b> नंबर पर है।`,
    no2Trend: (p, dir) => dir === 0 ? ` पिछले दो हफ़्तों जैसी ही।` : ` यह पिछले दो हफ़्तों से ${p}% ${dir > 0 ? "ज़्यादा" : "कम"} है।`,
    no2None: (N) => `पिछले 14 दिनों में बादलों या उपग्रह के न गुज़रने से ${N} पर माप के लिए पर्याप्त डेटा नहीं।`,
    no2Peak: (r, km, what, site) => `35 किमी के भीतर NO₂ का सबसे ऊँचा बिंदु सामान्य स्तर से ${r} गुना था, शहर के केंद्र से ${km} किमी दूर, ${what} के पास (${esc(site)})।`,
    no2PeakHere: (r, what) => `35 किमी के भीतर NO₂ का सबसे ऊँचा बिंदु सामान्य स्तर से ${r} गुना था, ख़ुद शहर में, जो ${what} का पैटर्न है।`,
    no2PeakTown: (r, km, site) => `35 किमी के भीतर NO₂ का सबसे ऊँचा बिंदु सामान्य स्तर से ${r} गुना था, शहर के केंद्र से ${km} किमी दूर ${esc(site)} की आबादी में, जो ट्रैफ़िक का पैटर्न है।`,
    chartNo2: (N) => `${N} पर NO₂, हर 14 दिन की अवधि`,
    no2Note: "सेंटिनल-5P के ट्रोपोमी उपकरण से, नासा की GIBS तस्वीरों के ज़रिए, जो NO₂ को रंग की पट्टियों में दिखाती हैं: यहाँ का स्तर लगभग एक पट्टी तक सही है। बड़े शहरों में NO₂ ज़्यादातर गाड़ियों के इंजनों से आती है; ऊँचे बिंदुओं के नाम पास की चीज़ पर रखे गए हैं, जो संभावित स्रोत बताता है, मापता नहीं।",
    hCh4: (N) => `${N} के पास कचरा डंप और मीथेन`,
    ch4Lede: (N, n, kg) => `कार्बन मैपर के उपग्रहों और विमानों ने ${N} से 50 किमी के भीतर <b>${n}</b> कचरा डंपों से उठती मीथेन मापी है, मिलाकर लगभग <b>${kg} किलो प्रति घंटा</b>।`,
    ch4None: (N) => `कार्बन मैपर ने ${N} से 50 किमी के भीतर किसी कचरा डंप से मीथेन नहीं मापी। उसके गुज़रने कभी-कभार होते हैं, इसलिए यह इस बात का सबूत नहीं कि कोई नहीं।`,
    thSite: "जगह", thRate: "मीथेन", thPlumes: "देखे गए धुएँ", thLast: "आख़िरी बार", thRankAll: "रैंक",
    rateCell: (v) => `${v} किलो/घंटा`, rankOf: (r, n) => `${n} में ${r}`,
    ch4Note: (n) => `पाकिस्तान और भारत के लिए कार्बन मैपर के डेटा में मापी गई दर वाले ${n} कचरा डंप रिकॉर्ड में रैंक (यह डेटा सिर्फ़ इन दो देशों का है)। दरें कार्बन मैपर के स्वचालित अनुमान हैं; कचरा डंप की मीथेन के साथ कचरा जलने की गंध और धुआँ भी आता है।`,
    hPlants: (N) => `${N} के पास बिजलीघर, कारख़ाने और ईंट भट्ठे`,
    co2Line: (n, t, one) => one ? `<b>1</b> प्लांट जिसका CO₂ कार्बन मैपर ने मापा, लगभग <b>${t} टन CO₂ प्रति घंटा</b>` : `<b>${n}</b> प्लांट जिनका CO₂ कार्बन मैपर ने मापा, मिलाकर लगभग <b>${t} टन CO₂ प्रति घंटा</b>`,
    fossilLine: (n, parts) => `ओपनस्ट्रीटमैप में <b>${n}</b> जीवाश्म ईंधन वाले बिजलीघर (${parts})`,
    industryLine: (n) => `ओपनस्ट्रीटमैप में <b>${n}</b> औद्योगिक इलाक़े`,
    hotLine: (n, top) => `<b>${n}</b> हमेशा गर्म जगहें जिन्हें नासा के उपग्रहों ने 2025 में 20 या ज़्यादा दिन जलते देखा${top}`,
    kilnLine: (n, pk, inn, z) => `उपग्रह सर्वे में <b>${n}</b> ईंट भट्ठे (${pk} पाकिस्तान में, ${inn} भारत में), जिनमें से ${z}% साफ़ ज़िगज़ैग क़िस्म के`,
    kilnPm: (t, e, n) => `; सर्वे का अनुमान है कि जिन ${e} भट्ठों के आँकड़े हैं (कुल ${n}) वे भट्ठों के मौसम में रोज़ ${t} टन PM2.5 छोड़ते हैं`,
    kilnNone: "50 किमी के भीतर सर्वे में कोई ईंट भट्ठा नहीं",
    kilnOutside: "यह जगह भट्ठों के सर्वे के इलाक़े से बाहर है, इसलिए यहाँ के भट्ठे नहीं गिने गए",
    shown: (k) => ` (सबसे बड़े ${k} दिखाए गए)`,
    plantsNote: "शहर के केंद्र से 50 किमी के भीतर, सीमा के दोनों ओर। ये वहाँ मौजूद चीज़ों की सूचियाँ हैं, यह नहीं कि हर एक हवा में कितना जोड़ती है।",
    hCompare: (N) => `${N} के प्रदूषण स्रोत दूसरे शहरों की तुलना में`,
    compareLede: (N, n) => `यहाँ मौजूद ${n} शहरों में हर पैमाने पर ${N} कहाँ है। ये अलग-अलग पैमाने हैं, इसलिए एक पर ऊँची रैंक दूसरे पर ऊँची रैंक से हवा में ज़्यादा हिस्सा नहीं।`,
    thMeasure: "पैमाना", thValue: (N) => N, thRank: "रैंक",
    mFires: "250 किमी के भीतर आग, पिछले 30 दिन", mNo2: "NO₂, सामान्य स्तर से गुना (14 दिन)", mCh4: "50 किमी के भीतर कचरा डंप मीथेन",
    mCo2: "50 किमी के भीतर मापा गया प्लांट CO₂", mKilns: "50 किमी के भीतर ईंट भट्ठे", mInd: "50 किमी के भीतर औद्योगिक इलाक़े", mHot: "50 किमी के भीतर हमेशा गर्म जगहें",
    kgh: (v) => `${v} किलो/घंटा`, th: (v) => `${v} टन/घंटा`, km: (v) => `${v} किमी`, x: (v) => `${v} गुना`, none: "कोई नहीं", noneMeasured: "कोई नहीं मापा गया", noReading: "माप नहीं", notRanked: "–", calmRank: "हवा थमी हुई, रुख़ नहीं",
    hRanks: (N) => `${N} इस समय किस नंबर पर है`,
    ranksLede: (N) => `हर उपग्रह गुज़रने के साथ बदलने वाले आँकड़ों पर शहरों में ${N} की जगह।`,
    rUp: "हवा के रुख़ पर आग, पिछले 24 घंटे", rAll: "250 किमी के भीतर आग, पिछले 24 घंटे", rWeek: "250 किमी के भीतर आग, पिछले 7 दिन",
    seeAll: `सारी रैंकिंग: <a href="/rankings/">शहरों की रैंकिंग</a>`,
    hQa: (N) => `${N} की हवा के बारे में सवाल`,
    qFrom: (N) => `आज ${N} का धुआँ कहाँ से आ रहा है?`,
    qFires: (N) => `क्या ${N} के पास पराली की आग जल रही है?`,
    aFires: (N, n24, n30) => `पिछले 24 घंटों में नासा के उपग्रहों ने ${N} से 250 किमी के भीतर ${n24} जगह आग देखी, और पिछले 30 दिनों में ${n30}। उपग्रह सिर्फ़ वही देखते हैं जो उनके गुज़रते समय जल रहा हो, और बादलों के नीचे नहीं।`,
    qNo2: (N) => `${N} में ट्रैफ़िक का प्रदूषण कितना है?`,
    qKilns: (N) => `${N} के पास कितने ईंट भट्ठे हैं?`,
    aKilns: (N, n) => `उपग्रह सर्वे ${N} से 50 किमी के भीतर ${n} ईंट भट्ठे गिनते हैं।`,
    qCh4: (N) => `${N} के पास कौन से कचरा डंप मीथेन छोड़ते हैं?`,
    aCh4: (list) => `कार्बन मैपर ने ${list} से मीथेन के धुएँ मापे हैं।`,
    dataLine: (u) => `इस पन्ने का हर आँकड़ा <a href="${u}">मशीन के पढ़ने लायक़ रूप (JSON)</a> में भी है।`,
    asOf: (d) => `आग ${d} तक।`, sourcesAsOf: (d) => `सूचियाँ ${d} को बनीं।`, no2AsOf: (a, b) => `NO₂ की अवधि ${a} से ${b}।`,
    rkTitle: "शहरों की रैंकिंग: पाकिस्तान और भारत में इस समय धुआँ, आग और प्रदूषण",
    rkDesc: "",
    rkH1: "शहरों की रैंकिंग: इस समय धुआँ, आग और प्रदूषण",
    rkLede: (n) => `यहाँ मौजूद ${n} शहरों की तुलना, उस पर जो उपग्रह उनके आसपास देखते हैं। आग की तालिकाएँ हर उपग्रह गुज़रने के साथ बदलती हैं; NO₂ रोज़ ताज़ा होने वाला 14 दिन का औसत है; जगहों की गिनती तब बदलती है जब सूचियाँ दोबारा बनती हैं। यह हर शहर के आसपास की चीज़ों की रैंकिंग है, यह नहीं कि हवा में उनका कितना हिस्सा है।`,
    rkFresh: (d) => `आग ${d} तक।`, rkNo2Fresh: (a, b) => `14 दिन, ${a} से ${b}।`, rkSrcFresh: (d) => `सूचियाँ ${d} को बनीं।`,
    thCity: "शहर", thCountry: "देश",
    rkAir: "इस समय हवा की गुणवत्ता", rkAirBtn: "सभी शहरों की ताज़ा हवा लोड करें",
    rkAirNote: "ये माप Open-Meteo के ज़रिए Copernicus CAMS के मॉडल अनुमानों से सीधे आपके ब्राउज़र में आते हैं, इसलिए सिर्फ़ आपके कहने पर लोड होते हैं। मॉडल सर्दियों में कम आँकता है।",
    rkAqi: "US AQI", rkPm: "PM2.5 (µg/m³)", rkAirFail: "हवा की गुणवत्ता सेवा ने जवाब नहीं दिया। एक मिनट बाद फिर कोशिश करें।",
    rkMore: (n) => `सभी ${n} दिखाएँ`,
  },
};
const SRC_BUILT = "2026-10-26"; // sources/sites.json "built"; scripts/build-pages.py could stamp it

// ---------- Charts (string-only SVG) ----------
function fireChart(cf, id, l, N) {
  const rows = cf.cities[id]?.r || [];
  if (!rows.some(Boolean)) return "";
  const W = 720, H = 180, pad = 24, n = cf.dates.length, bw = (W - 8) / n;
  const max = Math.max(1, ...rows.map((r) => (r ? r[1] : 0)));
  const y = (v) => ((H - pad - 8) * v) / max;
  let g = "", line = [];
  cf.dates.forEach((d, i) => {
    const r = rows[i], x = 4 + i * bw, w = Math.max(1, bw - 3);
    if (r) {
      g += `<g><title>${esc(`${date(d, l)}: ${nf(r[1], l)} · ${nf(r[0], l)}`)}</title><rect x="${x.toFixed(1)}" y="${(H - pad - y(r[1])).toFixed(1)}" width="${w.toFixed(1)}" height="${Math.max(0.5, y(r[1])).toFixed(1)}" fill="#f0a35a"/></g>`;
      line.push(`${(x + w / 2).toFixed(1)},${(H - pad - y(r[0])).toFixed(1)}`);
    } else {
      g += `<rect x="${x.toFixed(1)}" y="${H - pad - 3}" width="${w.toFixed(1)}" height="3" fill="#ddd"><title>${esc(`${date(d, l)}: ${T[l].noDay}`)}</title></rect>`;
      if (line.length) { g += `<polyline points="${line.join(" ")}" fill="none" stroke="#d62d20" stroke-width="2"/>`; line = []; }
    }
    if (i === 0 || i === n - 1 || i === Math.floor(n / 2))
      g += `<text x="${(i === 0 ? x : i === n - 1 ? x + w : x + w / 2).toFixed(1)}" y="${H - 7}" text-anchor="${i === 0 ? "start" : i === n - 1 ? "end" : "middle"}" font-size="12" fill="#7c7c80">${esc(date(d, l))}</text>`;
  });
  if (line.length) g += `<polyline points="${line.join(" ")}" fill="none" stroke="#d62d20" stroke-width="2"/>`;
  g += `<line x1="0" x2="${W}" y1="${(H - pad - y(max)).toFixed(1)}" y2="${(H - pad - y(max)).toFixed(1)}" stroke="#e6e3dc"/><text x="4" y="${(H - pad - y(max) - 4).toFixed(1)}" font-size="12" fill="#7c7c80">${nf(max, l)}</text>`;
  return `<svg class="ff-bars" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(T[l].chartFires(N))}" direction="ltr">${g}</svg>` +
    `<p class="ff-key"><i style="background:#f0a35a"></i>${T[l].key250} &nbsp; <i style="background:#d62d20"></i>${T[l].key50}</p>`;
}

function no2Chart(n2, id, l, N) {
  const pts = Object.entries(n2.hist || {}).map(([d, v]) => [d, v[id]?.[1]]).filter((p) => p[1] != null);
  if (pts.length < 5) return "";
  const W = 720, H = 150, pad = 22, lo = Math.min(1, ...pts.map((p) => p[1])), hi = Math.max(...pts.map((p) => p[1])) * 1.08;
  const t0 = Date.parse(pts[0][0]), span = Math.max(1, Date.parse(pts[pts.length - 1][0]) - t0);
  const x = (i) => 6 + ((Date.parse(pts[i][0]) - t0) * (W - 12)) / span, y = (v) => H - pad - ((H - pad - 10) * (v - lo)) / Math.max(0.1, hi - lo);
  const one = y(1);
  let g = `<line x1="0" x2="${W}" y1="${one.toFixed(1)}" y2="${one.toFixed(1)}" stroke="#ccc" stroke-dasharray="4 4"/>` +
    `<text x="4" y="${(one - 4).toFixed(1)}" font-size="11" fill="#999">1×</text>`;
  g += `<polyline points="${pts.map((p, i) => `${x(i).toFixed(1)},${y(p[1]).toFixed(1)}`).join(" ")}" fill="none" stroke="#7a3fa0" stroke-width="2.2"/>`;
  pts.forEach((p, i) => { g += `<circle cx="${x(i).toFixed(1)}" cy="${y(p[1]).toFixed(1)}" r="3" fill="#7a3fa0"><title>${esc(`${date(p[0], l)}: ${nf(p[1], l)}×`)}</title></circle>`; });
  [0, pts.length - 1].forEach((i) => {
    g += `<text x="${x(i).toFixed(1)}" y="${H - 6}" text-anchor="${i ? "end" : "start"}" font-size="12" fill="#7c7c80">${esc(date(pts[i][0], l))}</text>`;
  });
  return `<svg class="ff-bars" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(T[l].chartNo2(N))}" direction="ltr">${g}</svg>`;
}

// A rank of n as a row of 58 ticks with this city's marked: 1 is the most.
const rankBar = (r, n) => {
  if (!r) return "";
  const W = 120, x = 2 + ((W - 4) * (r - 1)) / Math.max(1, n - 1);
  return ` <svg width="${W}" height="10" viewBox="0 0 ${W} 10" aria-hidden="true" style="vertical-align:middle" direction="ltr"><rect x="0" y="4" width="${W}" height="2" fill="#ddd"/><circle cx="${x.toFixed(1)}" cy="5" r="4" fill="#d62d20"/></svg>`;
};

// ---------- Numbers shared by the sections, /api/city and /rankings/ ----------
function fires30(cf, id) {
  const r = cf?.cities?.[id]?.r || [];
  return { n250: r.reduce((s, x) => s + (x ? x[1] : 0), 0), n50: r.reduce((s, x) => s + (x ? x[0] : 0), 0), days: r.filter(Boolean).length };
}
function no2Of(n2, id) {
  const v = n2?.cities?.[id];
  if (!v) return null;
  const end = n2.window?.[1];
  const prevEnd = end && new Date(Date.parse(end + "T00:00:00Z") - 14 * 86400000).toISOString().slice(0, 10);
  const prev = prevEnd && n2.hist?.[prevEnd]?.[id];
  return { ...v, prev: prev ? prev[1] : null, prevEnd };
}
// Ranks of every city on the live fire numbers; smoke() is air.js's per-city summary.
export function liveRanks(rows) {
  const rank = (f) => {
    const m = new Map();
    for (const { c, s } of rows) {
      const v = f(s);
      if (v == null || v <= 0) continue;
      m.set(c.id, 1 + rows.filter((o) => (f(o.s) ?? 0) > v).length);
    }
    return m;
  };
  return { up: rank((s) => (s.w && !s.calm ? s.upN : null)), all: rank((s) => s.all), week: rank((s) => s.n7) };
}

// ---------- The city page's new sections ----------
export function citySections(c, l, { N, s, cf, n2, ranks, ledeText }) {
  const t = T[l], n = (v) => nf(v, l), src = c.src || {};
  let h = "";
  const f30 = fires30(cf, c.id);
  // Fires: 30 days, then the seasons.
  if (cf) {
    const last = date(cf.last, l);
    h += `  <h2>${t.hFires(N)}</h2>\n  <p>${f30.n250 ? t.firesLede(N, n(f30.n250), n(f30.n50), last, n(f30.days)) : f30.days ? t.firesNone(N, last, n(f30.days)) : ""}</p>\n`;
    h += `  ${fireChart(cf, c.id, l, N)}\n  <p class="muted">${t.firesNote}</p>\n`;
    const S = cf.season, sv = cf.cities[c.id]?.s || [];
    if (S && sv.some((v) => v != null)) {
      const toLabel = date(`2000-${S.to}`, l);
      h += `  <h2>${t.hSeason(N)}</h2>\n  <p>${S.to === "11-30" ? t.seasonLedeDone(N) : t.seasonLede(N, toLabel)}</p>\n`;
      const cur = sv[S.years.length - 1], prevI = S.years.length - 2, prevV = sv[prevI];
      const clean = (y) => !(S.gaps?.[y] || []).length && !(S.missing?.[y] || []).length;
      if (S.to !== "11-30" && cur != null && prevV && clean(S.years[S.years.length - 1]) && clean(S.years[prevI])) {
        const p = Math.round(((cur - prevV) / prevV) * 100);
        h += `  <p>${p >= 0 ? t.seasonUp(N, n(p), S.years[prevI]) : t.seasonDown(N, n(-p), S.years[prevI])}</p>\n`;
      }
      h += `  <div class="table-wrap"><table><thead><tr><th>${t.thYear}</th><th class="n">${t.thSpots}</th></tr></thead><tbody>\n` +
        S.years.map((y, i) => {
          const v = sv[i], gaps = new Set([...(S.gaps?.[y] || []), ...(S.missing?.[y] || [])]).size, cur = i === S.years.length - 1 && S.to !== "11-30";
          const cell = v == null ? t.noData : n(v) + (gaps ? ` <span class="muted">(${t.gapNote(n(gaps), gaps === 1)})</span>` : "");
          return `   <tr${cur ? ' class="wind-here"' : ""}><td>${y}${cur ? ` <span class="muted">(${t.soFar})</span>` : ""}</td><td class="n">${cell}</td></tr>`;
        }).join("\n") + "\n  </tbody></table></div>\n";
    }
  }
  // NO2.
  const no2 = no2Of(n2, c.id);
  if (n2) {
    h += `  <h2>${t.hNo2(N)}</h2>\n`;
    if (no2 && no2.r != null) {
      let p = t.no2Lede(N, n(no2.r), n(no2.m), n(no2.rank), n(n2.ranked), date(n2.window[0], l), date(n2.window[1], l, true));
      if (no2.prev) {
        const d = Math.round(((no2.r - no2.prev) / no2.prev) * 100);
        p += t.no2Trend(n(Math.abs(d)), Math.abs(d) < 5 ? 0 : Math.sign(d));
      }
      h += `  <p>${p}</p>\n`;
    } else h += `  <p>${t.no2None(N)}</p>\n`;
    if (no2?.peak && no2.peak[0] >= 1.5) {
      const [r, kind, site, km] = no2.peak;
      h += `  <p>${kind === "traffic" ? (km <= 5 ? t.no2PeakHere(n(r), KIND[l][kind]) : t.no2PeakTown(n(r), n(km), site)) : t.no2Peak(n(r), n(km), KIND[l][kind] || kind, site)}</p>\n`;
    }
    h += `  ${no2Chart(n2, c.id, l, N)}\n  <p class="muted">${t.no2Note} ${t.no2AsOf(date(n2.window[0], l), date(n2.window[1], l, true))}</p>\n`;
  }
  // Methane.
  const ch4 = src.ch4;
  if (ch4) {
    h += `  <h2>${t.hCh4(N)}</h2>\n  <p>${ch4.n ? t.ch4Lede(N, n(ch4.n), n(ch4.kg_h), ch4.n === 1) + (ch4.n > ch4.top.length ? t.shown(n(ch4.top.length)) : "") : t.ch4None(N)}</p>\n`;
    if (ch4.n) {
      h += `  <div class="table-wrap"><table><thead><tr><th>${t.thSite}</th><th class="n">${t.thRate}</th><th class="n">${t.thPlumes}</th><th>${t.thLast}</th><th class="n">${t.thRankAll}</th></tr></thead><tbody>\n` +
        ch4.top.map(([name, rate, plumes, , last, cc, km, district, rk]) =>
          `   <tr><td>${esc(name)} <span class="muted">(${esc(district)}${SEP(l)}${COUNTRY[l][cc]}${SEP(l)}${t.km(n(km))})</span></td><td class="n">${t.rateCell(n(rate))}</td><td class="n">${n(plumes)}</td><td>${date(last, l, true)}</td><td class="n">${t.rankOf(n(rk), n(ch4.of))}</td></tr>`).join("\n") +
        "\n  </tbody></table></div>\n";
      h += `  <p class="muted">${t.ch4Note(n(ch4.of))}</p>\n`;
    }
  }
  // Plants, industry, kilns.
  if (src.kilns) {
    const items = [];
    if (src.co2.n) items.push(t.co2Line(n(src.co2.n), n(src.co2.t_h), src.co2.n === 1) + ": " +
      src.co2.top.map(([name, kind, th]) => `${esc(name)} (${PLANT[l][kind] || kind}${SEP(l)}${t.th(n(th))})`).join(SEP(l)));
    if (src.fossil.n) {
      const parts = ["coal", "gas", "oil"].filter((f) => src.fossil[f]).map((f) => `${n(src.fossil[f])} ${FUEL[l][f]}`).join(SEP(l));
      items.push(t.fossilLine(n(src.fossil.n), parts, src.fossil.n === 1) + (src.fossil.top.length ? ": " + src.fossil.top.map(([name, , mw]) => esc(name) + (mw ? ` (${n(Math.round(mw))} MW)` : "")).join(SEP(l)) + (src.fossil.n > src.fossil.top.length ? t.shown(n(src.fossil.top.length)) : "") : ""));
    }
    if (src.industry.n) items.push(t.industryLine(n(src.industry.n)));
    if (src.hot.n) items.push(t.hotLine(n(src.hot.n), src.hot.top.length ? ": " + src.hot.top.map(([name, days]) => `${esc(name)} (${n(days)})`).join(SEP(l)) : "", src.hot.n === 1));
    const k = src.kilns;
    items.push(!k.survey ? t.kilnOutside : k.n ? t.kilnLine(n(k.n), n(k.pk), n(k.in), n(k.zigzag ?? 0), k.n === 1) + (k.pm25_t_day != null && k.est * 2 >= k.n ? t.kilnPm(n(k.pm25_t_day), n(k.est), n(k.n)) : "") : t.kilnNone);
    h += `  <h2>${t.hPlants(N)}</h2>\n  <ul>${items.map((x) => `<li>${x}</li>`).join("")}</ul>\n  <p class="muted">${t.plantsNote} <a href="/sites/">/sites/</a> · ${t.sourcesAsOf(date(SRC_BUILT, l, true))}</p>\n`;
  }
  // Comparison of the measures.
  const R = src.rank || {}, RN = src.ranked || {};
  const fRank = (() => { // fire spots in 30 days, among cities with any
    if (!cf) return null;
    const v = f30.n250;
    if (!v) return null;
    let r = 1, tot = 0;
    for (const id in cf.cities) { const o = fires30(cf, id).n250; if (o > 0) tot++; if (o > v) r++; }
    return [r, tot];
  })();
  const rows = [
    [t.mFires, n(f30.n250), fRank],
    [t.mNo2, no2?.r != null ? t.x(n(no2.r)) : t.noReading, no2?.rank ? [no2.rank, n2.ranked] : null],
    [t.mCh4, src.ch4?.kg_h ? t.kgh(n(src.ch4.kg_h)) : t.noneMeasured, R.ch4 ? [R.ch4, RN.ch4] : null],
    [t.mCo2, src.co2?.t_h ? t.th(n(src.co2.t_h)) : t.noneMeasured, R.co2 ? [R.co2, RN.co2] : null],
    [t.mKilns, src.kilns?.survey ? n(src.kilns.n) : "–", R.kilns ? [R.kilns, RN.kilns] : null],
    [t.mInd, src.industry ? n(src.industry.n) : "0", R.industry ? [R.industry, RN.industry] : null],
    [t.mHot, n(src.hot?.n || 0), R.hot ? [R.hot, RN.hot] : null],
  ];
  h += `  <h2>${t.hCompare(N)}</h2>\n  <p>${t.compareLede(N, n(CITIES.length))}</p>\n` +
    `  <div class="table-wrap"><table><thead><tr><th>${t.thMeasure}</th><th class="n">${t.thValue(N)}</th><th>${t.thRank}</th></tr></thead><tbody>\n` +
    rows.map(([m, v, rk]) => `   <tr><td>${m}</td><td class="n">${v}</td><td>${rk ? t.rankOf(n(rk[0]), n(rk[1])) + rankBar(rk[0], rk[1]) : t.notRanked}</td></tr>`).join("\n") +
    "\n  </tbody></table></div>\n";
  // Live ranks.
  if (ranks) {
    const live = [[t.rUp, ranks.up, true], [t.rAll, ranks.all], [t.rWeek, ranks.week]].map(([label, m, isUp]) => {
      const r = m.get(c.id);
      return `<li>${label}: ${r ? `<b>${t.rankOf(n(r), n(m.size))}</b>` : isUp && (!s.w || s.calm) ? t.calmRank : "0"}</li>`;
    });
    h += `  <h2>${t.hRanks(N)}</h2>\n  <p>${t.ranksLede(N)}</p>\n  <ul>${live.join("")}</ul>\n  <p>${t.seeAll}</p>\n`;
  }
  // Questions, answered from the numbers above (no claims about shares of the air).
  const qa = [[t.qFrom(N), ledeText]];
  if (cf) qa.push([t.qFires(N), t.aFires(N, n(s.all), n(f30.n250))]);
  if (no2?.r != null) qa.push([t.qNo2(N), t.no2Lede(N, n(no2.r), n(no2.m), n(no2.rank), n(n2.ranked), date(n2.window[0], l), date(n2.window[1], l, true))]);
  if (src.kilns?.survey) qa.push([t.qKilns(N), src.kilns.n ? t.aKilns(N, n(src.kilns.n)) : t.kilnNone + "."]);
  if (src.ch4) qa.push([t.qCh4(N), src.ch4.n ? t.aCh4(src.ch4.top.map(([name, rate]) => `${esc(name)} (${t.rateCell(n(rate))})`).join(SEP(l))) : t.ch4None(N)]);
  h += `  <h2>${t.hQa(N)}</h2>\n` + qa.map(([q, a]) => `  <h3>${q}</h3>\n  <p>${a}</p>`).join("\n") + "\n";
  h += `  <p class="muted">${t.dataLine(`/api/city?id=${c.id}`)}</p>\n`;
  return h;
}

// ---------- JSON-LD: the page's numbers as one derived dataset ----------
export function cityDataset(c, cf, n2) {
  const N = c.name.en, url = `${SITE}/air/${c.id}/`;
  const pv = (name, unitText, description) => ({ "@type": "PropertyValue", name, unitText, description });
  return {
    "@type": "Dataset", "@id": `${url}#data`, name: `HamariHawa city summary: ${N}`,
    description: `Fires around ${N} day by day and season by season, NO₂ over the city, and the measured and mapped pollution sources within 50 km, derived by HamariHawa from NASA FIRMS, Sentinel-5P TROPOMI (via NASA GIBS), Carbon Mapper, OpenStreetMap and brick-kiln surveys. Upstream sources keep their own terms: OpenStreetMap ODbL, the kiln surveys CC BY-NC, Carbon Mapper its own; see ${SITE}/data/.`,
    url, isAccessibleForFree: true, creator: ORG, publisher: ORG, usageInfo: `${SITE}/data/`,
    temporalCoverage: cf ? `2019-10-01/${cf.last}` : undefined,
    spatialCoverage: { "@type": "Place", name: `${N} and 250 km around it`, geo: { "@type": "GeoCircle", geoMidpoint: { "@type": "GeoCoordinates", latitude: c.lat, longitude: c.lon }, geoRadius: "250 km" } },
    variableMeasured: [
      pv("Fire spots within 50 and 250 km per day", "count", `Distinct fire spots per Pakistan-time day, all satellites, the last 30 days${cf ? ` to ${cf.last}` : ""}`),
      pv("Season fire spots within 250 km", "count", "Suomi NPP fire spots from 1 October to the same date, each season since 2019; days Suomi NPP missed are left out and listed"),
      pv("Tropospheric NO₂ within 15 km", "1e15 molecules/cm2 and ratio to the surrounding level", n2?.window ? `Approximate 14-day mean, ${n2.window[0]} to ${n2.window[1]}` : "Approximate 14-day mean"),
      pv("Landfill methane within 50 km", "kg/h", "Carbon Mapper plume-based emission estimates"),
      pv("Plant CO₂ within 50 km", "t/h", "Carbon Mapper"),
      pv("Brick kilns, industrial areas, fossil power plants and always-hot sites within 50 km", "count", `Satellite kiln surveys, OpenStreetMap, NASA FIRMS 2025; lists built ${SRC_BUILT}`),
    ],
    isBasedOn: ["https://firms.modaps.eosdis.nasa.gov/", "https://gibs.earthdata.nasa.gov/", "https://carbonmapper.org/", "https://www.openstreetmap.org/"],
    distribution: [{ "@type": "DataDownload", encodingFormat: "application/json", contentUrl: `${SITE}/api/city?id=${c.id}` }],
  };
}

// ---------- /api/city ----------
export function cityJson(c, { s, cf, n2, ranks, districtName }) {
  const f = cf?.cities?.[c.id];
  return {
    city: { id: c.id, name: c.name, country: c.cc, lat: c.lat, lon: c.lon, page: `${SITE}/air/${c.id}/` },
    note: "Measurements around the city, not shares of what is in its air. Live air quality is not included: the pages fetch it in the browser from Open-Meteo (Copernicus CAMS model).",
    fires_now: { wind_from_deg: s.w && !s.calm ? Math.round(s.w[1]) : null, wind_kmh: s.w ? Math.round(s.w[0]) : null,
      upwind_24h: s.w && !s.calm ? s.upN : null, within_250km_24h: s.all, within_250km_7d: s.n7,
      upwind_districts: s.upRows.slice(0, 12).map((r) => ({ ...districtName(r.di), spots: r.n, km: r.km })),
      unit: "distinct fire spots (one per fire, however many satellites saw it)" },
    fires_daily: cf ? { dates: cf.dates, within_50km: f?.r.map((x) => (x ? x[0] : null)), within_250km: f?.r.map((x) => (x ? x[1] : null)), unit: "fire spots per Pakistan-time day, all satellites" } : null,
    seasons: cf ? { from: "10-01", to: cf.season.to, years: cf.season.years, suomi_npp_within_250km: f?.s, gaps: cf.season.gaps, missing: cf.season.missing } : null,
    no2: n2 ? { ...no2Of(n2, c.id), window: n2.window, unit: n2.unit, ranked_cities: n2.ranked, fields: n2.fields } : null,
    sources_within_50km: c.src, sources_built: SRC_BUILT,
    live_ranks: ranks ? { upwind_24h: ranks.up.get(c.id) ?? null, within_250km_24h: ranks.all.get(c.id) ?? null, within_250km_7d: ranks.week.get(c.id) ?? null } : null,
    sources: { fires: "NASA FIRMS (VIIRS, MODIS)", no2: "Sentinel-5P TROPOMI via NASA GIBS", methane_co2: "Carbon Mapper", maps: "OpenStreetMap (ODbL)", kilns: "SentinelKilnDB and Pakistan kiln surveys (CC BY-NC)" },
  };
}

// ---------- /rankings/ ----------
export function rankingsBody(rows, { n2, latest, at }) {
  const body = {}, lists = [];
  const tables = [
    ["up", (l) => T[l].rUp, (r) => (r.s.w && !r.s.calm ? r.s.upN : null), "fire"],
    ["all", (l) => T[l].rAll, (r) => r.s.all, "fire"],
    ["week", (l) => T[l].rWeek, (r) => r.s.n7, "fire"],
    ["no2", (l) => T[l].mNo2, (r) => n2?.cities?.[r.c.id]?.r ?? null, "no2"],
    ["ch4", (l) => T[l].mCh4, (r) => r.c.src?.ch4?.kg_h || null, "src"],
    ["kilns", (l) => T[l].mKilns, (r) => (r.c.src?.kilns?.survey ? r.c.src.kilns.n || null : null), "src"],
  ];
  const fmt = (k, v, l) => (k === "no2" ? T[l].x(nf(v, l)) : k === "ch4" ? T[l].kgh(nf(v, l)) : nf(v, l));
  for (const [k, label, f] of tables) {
    const list = rows.filter((r) => f(r) != null && f(r) > 0).sort((a, b) => f(b) - f(a));
    lists.push({ "@type": "ItemList", name: label("en"), numberOfItems: list.length,
      itemListElement: list.map((r, i) => ({ "@type": "ListItem", position: i + 1, name: r.c.name.en, url: `${SITE}/air/${r.c.id}/` })) });
    for (const l of LANGS) {
      const t = T[l];
      const fresh = k === "no2" && n2?.window ? t.rkNo2Fresh(date(n2.window[0], l), date(n2.window[1], l, true)) : k === "ch4" || k === "kilns" ? t.rkSrcFresh(date(SRC_BUILT, l, true)) : latest ? t.rkFresh(at(latest, l)) : "";
      body[l] = (body[l] || "") + `  <h2 id="${k}">${label(l)}</h2>\n  <p class="muted">${fresh}</p>\n` +
        `  <div class="table-wrap"><table class="rk"><thead><tr><th class="n">#</th><th>${t.thCity}</th><th>${t.thCountry}</th><th class="n">${label(l)}</th></tr></thead><tbody>\n` +
        list.map((r, i) => `   <tr${i >= 15 ? ' class="more" hidden' : ""}><td class="n">${nf(1 + list.findIndex((o) => f(o) === f(r)), l)}</td><td><a href="/air/${r.c.id}/">${esc(r.c.name[l])}</a></td><td>${COUNTRY[l][r.c.cc]}</td><td class="n">${fmt(k, f(r), l)}</td></tr>`).join("\n") +
        `\n  </tbody></table></div>\n` + (list.length > 15 ? `  <p><button type="button" class="btn" data-more>${t.rkMore(nf(list.length, l))}</button></p>\n` : "");
    }
  }
  return { body, lists };
}
export const RANK_T = T;
