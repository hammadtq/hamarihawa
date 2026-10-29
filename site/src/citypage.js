// The city page's layout (/air/<city>/): a report card on top (the air now, the wind in words, the city's
// strongest ranks, share buttons), today's smoke map with a wind rose, one tile and one short story per kind of
// pollution the satellites and surveys see around the city, a map of the mapped sources, the seasons, the
// city against the others, and every table folded under "All the numbers" at the end.
// The numbers are city.js's and air.js's; this arranges them. Same wording rule: measurements around a city,
// never shares of what is in its air.
import CITIES from "./cities.json";
import { ogUrl } from "./og.js";
import { SITE, COUNTRY, esc, nf, pct } from "./pages.js";
import { RANK_T as CT, fireChart, no2Chart, fires30, no2Of, cityRows, liveRows, qaRows, ch4Table, seasonTable, KIND, FUEL, SEP, date } from "./city.js";

const T = {
  en: {
    kicker: (N) => `${N}'s smoke report`,
    aqiUnit: "US AQI", aqiWait: "Loading today's air reading…",
    aqiSub: "PM2.5 has averaged {pm} µg/m³ over 24 hours, {who} times the WHO limit: like smoking {cigs} cigarettes a day.",
    aqiSrc: "Copernicus CAMS model estimate via Open-Meteo, which reads low in winter.",
    rankNote: () => `Ranks among the cities with pages here that have any of each: #1 has the most.`,
    rk: (r) => `#${r}`, of: (n) => `of ${n}`,
    b: { fires24: "fire spots within 250 km, last 24 hours", fires30: "fire spots within 250 km, last 30 days", no2: "NO₂ over the city (traffic, industry, power plants), last 14 days",
      kilns: "brick kilns within 50 km", fossil: "fossil-fuel power plants within 50 km", ch4: "landfill methane measured within 50 km", industry: "industrial areas within 50 km" },
    wa: "Share on WhatsApp", x: "Post on X", copy: "Copy link", copied: "Link copied",
    shareText: (N) => `${N}'s air today: where the smoke is coming from`,
    jump: { today: "Today's smoke", causes: "Around the city", map: "Sources map", season: "This season", compare: "Against other cities", details: "All the numbers" },
    jumpLabel: "On this page",
    roseLabel: "Fires within 250 km in the last 24 hours, by the direction they lie in",
    roseUp: (d) => `Fires within 250 km in the last 24 hours, by direction. Red: the side the wind is coming from (the ${d}). Tap a direction to pick out its fires on the map.`,
    roseCalm: "Fires within 250 km in the last 24 hours, by direction. The wind is calm, so no side is upwind. Tap a direction to pick out its fires on the map.",
    roseNone: "No fires within 250 km in the last 24 hours.",
    calm: "calm",
    hCauses: (N) => `What satellites see around ${N}`,
    causesLede: "What satellites and surveys see around the city. Each is a different measure, so they can't be added up into shares of the air.",
    cFires: "Fires", cNo2: "NO₂: traffic and industry", cKilns: "Brick kilns", cLandfill: "Landfills", cPower: "Power plants and industry",
    tFires: (d) => `fire spots within 250 km in the last ${d} days`, tNo2: "times the region's usual NO₂, last 14 days", tNo2None: "not enough clear days for a reading",
    tKilns: "brick kilns within 50 km", tKilnsPm: (t) => `brick kilns within 50 km; the survey puts their smoke at ${t} t of PM2.5 a day in season`,
    tCh4: (name) => `kg of methane an hour measured from ${name}`, tCh4Many: (n) => `kg of methane an hour measured from ${n} landfills`,
    tDumps: "landfills and dump sites mapped within 50 km",
    tFossil: (ind, one) => `fossil-fuel power plant${one ? "" : "s"} within 50 km, and ${ind} industrial areas`, tInd: "industrial areas within 50 km",
    tRank: (r, n) => `#${r} of ${n} cities`, tRankLf: (r, n) => `#${r} of ${n} measured landfills`,
    hlPeakLast: (N, d, v, v50) => `Fires around ${N} were at their highest on the latest day, <em>${d}, with ${v} fire spots</em> within 250 km${v50 ? `, ${v50} of them within 50 km` : ""}.`,
    hlPeak: (days, d, v, v50) => `The busiest of the last ${days} days was <em>${d}, with ${v} fire spots</em> within 250 km${v50 ? `, ${v50} of them within 50 km` : ""}.`,
    s30: (d) => `fire spots within 250 km in the last ${d} days`, s50: "of them within 50 km",
    sCrop: "of the last 7 days' fires within 250 km were on farmland, the pattern of crop-residue burning",
    hlNo2: (N, r, rank, n) => `Over the last 14 days the air over ${N} held <em>${r} times</em> the region's usual level of nitrogen dioxide (NO₂), <em>#${rank} of ${n} cities</em>.`,
    hlKilns: (N, n) => n === "1" ? `<em>1 brick kiln</em> stands within 50 km of ${N}.` : `<em>${n} brick kilns</em> stand within 50 km of ${N}.`,
    hlKilnsSplit: (pk, inn) => ` ${pk} are in Pakistan and ${inn} in India.`,
    hlKilnsPm: (t, e) => ` Their survey puts the smoke from the ${e} it has figures for at about <em>${t} tonnes of PM2.5 a day</em> in the firing season.`,
    satKilns: (n, where) => `${n} brick kilns in one patch, ${where}. Each oval is a kiln.`,
    whereTown: (town, km, dir) => `near ${town}, ${km} km ${dir} of the centre`, whereKm: (km, dir) => `${km} km ${dir} of the centre`,
    sZig: "are the cleaner zigzag kind", sKilnRank: "by brick kilns within 50 km, among the cities the kiln surveys cover", mFossil: "Fossil-fuel power plants within 50 km",
    gapFoot: (txt) => `* ${txt}`,
    hlCh4: (name, km, plumes, kg) => `Satellites and aircraft have measured methane rising from <em>${name}</em>, ${km} km from the centre, ${plumes} times, about <em>${kg} kg an hour</em>.`,
    hlCh4Rank: (rk, of) => ` That puts it <em>#${rk} of the ${of}</em> measured landfills in Pakistan and India.`,
    hlCh4None: (N, n) => `Carbon Mapper hasn't measured a methane plume from a landfill within 50 km of ${N}, but ${n} landfills and dump sites are mapped there.`,
    satSite: (name, km, dir) => `${name} from above, ${km} km ${dir} of the centre`,
    sPlumes: "methane plumes measured", sLast: "last measured", sDumps: "landfills and dump sites mapped within 50 km",
    hlPower: (N, n, ind) => `<em>${n} fossil-fuel power plant${n === "1" ? "" : "s"}</em> and <em>${ind} industrial area${ind === "1" ? "" : "s"}</em> lie within 50 km of ${N}.`,
    hlPowerNone: (N, ind) => `No fossil-fuel power plant is mapped within 50 km of ${N}, but <em>${ind} industrial areas</em> are.`,
    hlCo2: (k, t) => ` Carbon Mapper has measured CO₂ plumes from ${k} plant${k === "1" ? "" : "s"} here, about <em>${t} tonnes an hour</em>.`,
    hlBig: (name, mw) => ` The largest, ${name}, can generate ${mw} MW.`,
    satFoot: "Satellite view: Esri, Maxar, Earthstar Geographics",
    hSrc: (N) => `Every mapped source within 50 km of ${N}`,
    srcLede: "Tap a layer to hide it, or a site for its name.",
    srcNote: "Brick-kiln surveys, OpenStreetMap, Carbon Mapper and NASA FIRMS, on either side of the border. These map what is there, not how much each adds to the air.",
    srcFail: "The map didn't load. Every site is also in the pollution sites directory.",
    hSeason: (N) => `Fires around ${N} this season compared with past years`,
    seasonFewest: (N, y, live) => `${live ? "So far this season has" : "This season had"} the fewest fire spots around ${N} of any season since ${y}.`,
    seasonMost: (N, y, live) => `${live ? "So far this season has" : "This season had"} the most fire spots around ${N} of any season since ${y}.`,
    seasonChart: (N) => `Fire spots within 250 km of ${N}, each season`, soFar: "so far",
    hCompare: (N) => `${N} against the other cities`,
    compareLede: (N) => `Each strip holds the cities with pages here that have any of it, the most on the left; the red mark is ${N}. They are different measures, so a high rank on one isn't a larger share of the air than a high rank on another.`,
    rankCell: (r, n) => `#${r} of ${n}`,
    hShare: (N) => `Send this to someone in ${N}`,
    shareLede: "Pasted into WhatsApp or X, the link shows this map of the fires and the wind, redrawn every few hours.",
    ogAlt: (N) => `${N}: the last 24 hours of fires within 250 km and the wind`,
    hDetails: "All the numbers",
    detailsLede: "Every table behind this page.",
    dCh4: "Landfill methane records", dCompare: "Every measure and rank", dLive: "Ranks on today's fires", dQa: (N) => `Questions about ${N}'s air`,
  },
  ur: {
    kicker: (N) => `${N} کے دھوئیں کی رپورٹ`,
    aqiUnit: "امریکی AQI", aqiWait: "آج کی ہوا کی پیمائش لوڈ ہو رہی ہے…",
    aqiSub: "PM2.5 کا 24 گھنٹے کا اوسط {pm} µg/m³ رہا، عالمی ادارۂ صحت کی حد کا {who} گنا: روزانہ {cigs} سگریٹ پینے جتنا۔",
    aqiSrc: "Open-Meteo کے ذریعے Copernicus CAMS کا ماڈل اندازہ، جو سردیوں میں کم بتاتا ہے۔",
    rankNote: () => `یہاں موجود ان شہروں میں درجہ جن کے پاس یہ چیز ہے: نمبر 1 پر سب سے زیادہ۔`,
    rk: (r) => `نمبر ${r}`, of: (n) => `${n} میں سے`,
    b: { fires24: "250 کلومیٹر کے اندر آگ، پچھلے 24 گھنٹے", fires30: "250 کلومیٹر کے اندر آگ، پچھلے 30 دن", no2: "شہر پر NO₂ (ٹریفک، صنعت، بجلی گھر)، پچھلے 14 دن",
      kilns: "50 کلومیٹر کے اندر اینٹوں کے بھٹے", fossil: "50 کلومیٹر کے اندر ایندھن سے چلنے والے بجلی گھر", ch4: "50 کلومیٹر کے اندر ناپی گئی کچرا کنڈی میتھین", industry: "50 کلومیٹر کے اندر صنعتی علاقے" },
    wa: "واٹس ایپ پر بھیجیں", x: "X پر پوسٹ کریں", copy: "لنک کاپی کریں", copied: "لنک کاپی ہو گیا",
    shareText: (N) => `${N} کی ہوا آج: دھواں کہاں سے آ رہا ہے`,
    jump: { today: "آج کا دھواں", causes: "شہر کے آس پاس", map: "ذرائع کا نقشہ", season: "یہ موسم", compare: "دوسرے شہروں سے موازنہ", details: "تمام اعداد" },
    jumpLabel: "اس صفحے پر",
    roseLabel: "پچھلے 24 گھنٹوں میں 250 کلومیٹر کے اندر آگ، سمت کے لحاظ سے",
    roseUp: (d) => `پچھلے 24 گھنٹوں میں 250 کلومیٹر کے اندر آگ، سمت کے لحاظ سے۔ سرخ: وہ طرف جدھر سے ہوا آ رہی ہے (${d})۔ نقشے پر کسی سمت کی آگ دیکھنے کے لیے اس پر ٹیپ کریں۔`,
    roseCalm: "پچھلے 24 گھنٹوں میں 250 کلومیٹر کے اندر آگ، سمت کے لحاظ سے۔ ہوا رکی ہوئی ہے، اس لیے کوئی طرف ہوا کے رخ پر نہیں۔ نقشے پر کسی سمت کی آگ دیکھنے کے لیے اس پر ٹیپ کریں۔",
    roseNone: "پچھلے 24 گھنٹوں میں 250 کلومیٹر کے اندر کوئی آگ نہیں دیکھی گئی۔",
    calm: "رکی ہوا",
    hCauses: (N) => `سیٹلائٹ ${N} کے آس پاس کیا دیکھتے ہیں`,
    causesLede: "سیٹلائٹ اور سروے شہر کے آس پاس کیا دیکھتے ہیں۔ ہر ایک الگ پیمانہ ہے، اس لیے انہیں جوڑ کر ہوا میں حصے نہیں بنائے جا سکتے۔",
    cFires: "آگ", cNo2: "NO₂: ٹریفک اور صنعت", cKilns: "اینٹوں کے بھٹے", cLandfill: "کچرا کنڈیاں", cPower: "بجلی گھر اور صنعت",
    tFires: (d) => `پچھلے ${d} دنوں میں 250 کلومیٹر کے اندر آگ`, tNo2: "علاقے کی عام NO₂ سے گنا، پچھلے 14 دن", tNo2None: "پیمائش کے لیے کافی صاف دن نہیں",
    tKilns: "50 کلومیٹر کے اندر اینٹوں کے بھٹے", tKilnsPm: (t) => `50 کلومیٹر کے اندر اینٹوں کے بھٹے؛ سروے کے مطابق موسم میں روزانہ ${t} ٹن PM2.5`,
    tCh4: (name) => `کلوگرام میتھین فی گھنٹہ، ${name} سے ناپی گئی`, tCh4Many: (n) => `کلوگرام میتھین فی گھنٹہ، ${n} کچرا کنڈیوں سے ناپی گئی`,
    tDumps: "50 کلومیٹر کے اندر نقشے پر کچرا کنڈیاں اور کوڑے کے ڈھیر",
    tFossil: (ind) => `50 کلومیٹر کے اندر ایندھن سے چلنے والے بجلی گھر، اور ${ind} صنعتی علاقے`, tInd: "50 کلومیٹر کے اندر صنعتی علاقے",
    tRank: (r, n) => `${n} شہروں میں نمبر ${r}`, tRankLf: (r, n) => `ناپی گئی ${n} کچرا کنڈیوں میں نمبر ${r}`,
    hlPeakLast: (N, d, v, v50) => `${N} کے آس پاس آگ تازہ ترین دن سب سے زیادہ تھی: <em>${d} کو ${v} جگہ آگ</em> 250 کلومیٹر کے اندر${v50 ? `، جن میں سے ${v50} 50 کلومیٹر کے اندر` : ""}۔`,
    hlPeak: (days, d, v, v50) => `پچھلے ${days} دنوں میں سب سے مصروف دن <em>${d} تھا، ${v} جگہ آگ</em> 250 کلومیٹر کے اندر${v50 ? `، جن میں سے ${v50} 50 کلومیٹر کے اندر` : ""}۔`,
    s30: (d) => `پچھلے ${d} دنوں میں 250 کلومیٹر کے اندر آگ`, s50: "ان میں سے 50 کلومیٹر کے اندر",
    sCrop: "پچھلے 7 دنوں میں 250 کلومیٹر کے اندر کی آگ کھیتوں میں تھی، جو فصل کی باقیات جلانے کا انداز ہے",
    hlNo2: (N, r, rank, n) => `پچھلے 14 دنوں میں ${N} کی فضا میں نائٹروجن ڈائی آکسائیڈ (NO₂) علاقے کی عام سطح سے <em>${r} گنا</em> تھی، <em>${n} شہروں میں نمبر ${rank}</em>۔`,
    hlKilns: (N, n) => `${N} سے 50 کلومیٹر کے اندر <em>${n} اینٹوں کے بھٹے</em> ہیں۔`,
    hlKilnsSplit: (pk, inn) => ` ${pk} پاکستان میں اور ${inn} ہندوستان میں۔`,
    hlKilnsPm: (t, e) => ` سروے کا اندازہ ہے کہ جن ${e} بھٹوں کے اعداد ہیں وہ بھٹوں کے موسم میں روزانہ تقریباً <em>${t} ٹن PM2.5</em> چھوڑتے ہیں۔`,
    satKilns: (n, where) => `ایک ہی جگہ ${n} اینٹوں کے بھٹے، ${where}۔ ہر بیضوی شکل ایک بھٹہ ہے۔`,
    whereTown: (town, km, dir) => `${town} کے قریب، مرکز سے ${km} کلومیٹر ${dir} میں`, whereKm: (km, dir) => `مرکز سے ${km} کلومیٹر ${dir} میں`,
    sZig: "صاف تر زگ زیگ قسم کے", sKilnRank: "50 کلومیٹر کے اندر بھٹوں میں، ان شہروں میں جنہیں بھٹوں کے سروے میں شامل کیا گیا", mFossil: "50 کلومیٹر کے اندر ایندھن سے چلنے والے بجلی گھر",
    gapFoot: (txt) => `* ${txt}`,
    hlCh4: (name, km, plumes, kg) => `سیٹلائٹس اور جہازوں نے مرکز سے ${km} کلومیٹر دور <em>${name}</em> سے ${plumes} بار میتھین اٹھتی ناپی ہے، تقریباً <em>${kg} کلوگرام فی گھنٹہ</em>۔`,
    hlCh4Rank: (rk, of) => ` یوں یہ پاکستان اور ہندوستان کی ناپی گئی ${of} کچرا کنڈیوں میں <em>نمبر ${rk}</em> ہے۔`,
    hlCh4None: (N, n) => `کاربن میپر نے ${N} سے 50 کلومیٹر کے اندر کسی کچرا کنڈی سے میتھین نہیں ناپی، لیکن وہاں ${n} کچرا کنڈیاں اور کوڑے کے ڈھیر نقشے پر ہیں۔`,
    satSite: (name, km, dir) => `${name} اوپر سے، مرکز سے ${km} کلومیٹر ${dir} میں`,
    sPlumes: "بار میتھین کا اخراج ناپا گیا", sLast: "آخری پیمائش", sDumps: "50 کلومیٹر کے اندر نقشے پر کچرا کنڈیاں اور ڈھیر",
    hlPower: (N, n, ind) => `${N} سے 50 کلومیٹر کے اندر <em>${n} ایندھن سے چلنے والے بجلی گھر</em> اور <em>${ind} صنعتی علاقے</em> ہیں۔`,
    hlPowerNone: (N, ind) => `${N} سے 50 کلومیٹر کے اندر ایندھن سے چلنے والا کوئی بجلی گھر نقشے پر نہیں، لیکن <em>${ind} صنعتی علاقے</em> ہیں۔`,
    hlCo2: (k, t) => ` کاربن میپر نے یہاں ${k} پلانٹس سے CO₂ کا اخراج ناپا ہے، تقریباً <em>${t} ٹن فی گھنٹہ</em>۔`,
    hlBig: (name, mw) => ` سب سے بڑا، ${name}، ${mw} میگاواٹ بجلی بنا سکتا ہے۔`,
    satFoot: "سیٹلائٹ منظر: Esri، Maxar، Earthstar Geographics",
    hSrc: (N) => `${N} سے 50 کلومیٹر کے اندر نقشے پر ہر ذریعہ`,
    srcLede: "کسی تہہ کو چھپانے کے لیے اس پر ٹیپ کریں، یا نام دیکھنے کے لیے کسی جگہ پر۔",
    srcNote: "اینٹوں کے بھٹوں کے سروے، اوپن اسٹریٹ میپ، کاربن میپر اور ناسا FIRMS، سرحد کے دونوں طرف۔ یہ بتاتے ہیں کہ وہاں کیا ہے، یہ نہیں کہ ہر ایک ہوا میں کتنا حصہ ڈالتا ہے۔",
    srcFail: "نقشہ لوڈ نہیں ہوا۔ ہر جگہ آلودگی کی جگہوں کی فہرست میں بھی ہے۔",
    hSeason: (N) => `اس موسم میں ${N} کے آس پاس آگ پچھلے برسوں کے مقابلے میں`,
    seasonFewest: (N, y, live) => live ? `اب تک یہ موسم ${y} کے بعد سے ${N} کے آس پاس سب سے کم آگ والا ہے۔` : `یہ موسم ${y} کے بعد سے ${N} کے آس پاس سب سے کم آگ والا رہا۔`,
    seasonMost: (N, y, live) => live ? `اب تک یہ موسم ${y} کے بعد سے ${N} کے آس پاس سب سے زیادہ آگ والا ہے۔` : `یہ موسم ${y} کے بعد سے ${N} کے آس پاس سب سے زیادہ آگ والا رہا۔`,
    seasonChart: (N) => `${N} سے 250 کلومیٹر کے اندر آگ، ہر موسم`, soFar: "اب تک",
    hCompare: (N) => `${N} دوسرے شہروں کے مقابلے میں`,
    compareLede: (N) => `ہر پٹی میں یہاں موجود وہ شہر ہیں جن کے پاس یہ چیز ہے، سب سے زیادہ والا بائیں طرف؛ سرخ نشان ${N} ہے۔ یہ الگ الگ پیمانے ہیں، اس لیے ایک پر اونچا درجہ دوسرے پر اونچے درجے سے ہوا میں زیادہ حصہ نہیں۔`,
    rankCell: (r, n) => `${n} میں ${r}`,
    hShare: (N) => `یہ ${N} میں کسی کو بھیجیں`,
    shareLede: "واٹس ایپ یا X میں لنک ڈالیں تو آگ اور ہوا کا یہ نقشہ دکھاتا ہے، جو ہر چند گھنٹے بعد نیا بنتا ہے۔",
    ogAlt: (N) => `${N}: پچھلے 24 گھنٹوں میں 250 کلومیٹر کے اندر آگ اور ہوا`,
    hDetails: "تمام اعداد",
    detailsLede: "اس صفحے کے پیچھے ہر جدول۔",
    dCh4: "کچرا کنڈی میتھین کے ریکارڈ", dCompare: "ہر پیمانہ اور درجہ", dLive: "آج کی آگ پر درجے", dQa: (N) => `${N} کی ہوا کے بارے میں سوالات`,
  },
  hi: {
    kicker: (N) => `${N} के धुएँ की रिपोर्ट`,
    aqiUnit: "अमेरिकी AQI", aqiWait: "आज की हवा की माप लोड हो रही है…",
    aqiSub: "PM2.5 का 24 घंटे का औसत {pm} µg/m³ रहा, विश्व स्वास्थ्य संगठन की सीमा का {who} गुना: रोज़ {cigs} सिगरेट पीने जितना।",
    aqiSrc: "Open-Meteo के ज़रिए Copernicus CAMS का मॉडल अनुमान, जो सर्दियों में कम बताता है।",
    rankNote: () => `यहाँ के उन शहरों में रैंक जिनके पास यह चीज़ है: नंबर 1 पर सबसे ज़्यादा।`,
    rk: (r) => `नंबर ${r}`, of: (n) => `${n} में से`,
    b: { fires24: "250 किमी के भीतर आग, पिछले 24 घंटे", fires30: "250 किमी के भीतर आग, पिछले 30 दिन", no2: "शहर पर NO₂ (ट्रैफ़िक, उद्योग, बिजलीघर), पिछले 14 दिन",
      kilns: "50 किमी के भीतर ईंट भट्ठे", fossil: "50 किमी के भीतर जीवाश्म ईंधन वाले बिजलीघर", ch4: "50 किमी के भीतर मापी गई लैंडफ़िल मीथेन", industry: "50 किमी के भीतर औद्योगिक इलाक़े" },
    wa: "व्हाट्सऐप पर भेजें", x: "X पर पोस्ट करें", copy: "लिंक कॉपी करें", copied: "लिंक कॉपी हो गया",
    shareText: (N) => `${N} की हवा आज: धुआँ कहाँ से आ रहा है`,
    jump: { today: "आज का धुआँ", causes: "शहर के आसपास", map: "स्रोतों का नक़्शा", season: "यह मौसम", compare: "दूसरे शहरों से तुलना", details: "सारे आँकड़े" },
    jumpLabel: "इस पन्ने पर",
    roseLabel: "पिछले 24 घंटों में 250 किमी के भीतर आग, दिशा के हिसाब से",
    roseUp: (d) => `पिछले 24 घंटों में 250 किमी के भीतर आग, दिशा के हिसाब से। लाल: वह तरफ़ जिधर से हवा आ रही है (${d})। नक़्शे पर किसी दिशा की आग देखने के लिए उस पर टैप करें।`,
    roseCalm: "पिछले 24 घंटों में 250 किमी के भीतर आग, दिशा के हिसाब से। हवा थमी हुई है, इसलिए कोई तरफ़ हवा के रुख़ पर नहीं। नक़्शे पर किसी दिशा की आग देखने के लिए उस पर टैप करें।",
    roseNone: "पिछले 24 घंटों में 250 किमी के भीतर कोई आग नहीं दिखी।",
    calm: "थमी हवा",
    hCauses: (N) => `उपग्रह ${N} के आसपास क्या देखते हैं`,
    causesLede: "उपग्रह और सर्वे शहर के आसपास क्या देखते हैं। हर एक अलग पैमाना है, इसलिए इन्हें जोड़कर हवा में हिस्से नहीं बनाए जा सकते।",
    cFires: "आग", cNo2: "NO₂: ट्रैफ़िक और उद्योग", cKilns: "ईंट भट्ठे", cLandfill: "लैंडफ़िल", cPower: "बिजलीघर और उद्योग",
    tFires: (d) => `पिछले ${d} दिनों में 250 किमी के भीतर आग`, tNo2: "इलाक़े के सामान्य NO₂ का गुना, पिछले 14 दिन", tNo2None: "माप के लिए पर्याप्त साफ़ दिन नहीं",
    tKilns: "50 किमी के भीतर ईंट भट्ठे", tKilnsPm: (t) => `50 किमी के भीतर ईंट भट्ठे; सर्वे के मुताबिक़ मौसम में रोज़ ${t} टन PM2.5`,
    tCh4: (name) => `किलो मीथेन प्रति घंटा, ${name} से मापी गई`, tCh4Many: (n) => `किलो मीथेन प्रति घंटा, ${n} लैंडफ़िल से मापी गई`,
    tDumps: "50 किमी के भीतर नक़्शे पर लैंडफ़िल और कूड़े के ढेर",
    tFossil: (ind) => `50 किमी के भीतर जीवाश्म ईंधन वाले बिजलीघर, और ${ind} औद्योगिक इलाक़े`, tInd: "50 किमी के भीतर औद्योगिक इलाक़े",
    tRank: (r, n) => `${n} शहरों में नंबर ${r}`, tRankLf: (r, n) => `मापे गए ${n} लैंडफ़िल में नंबर ${r}`,
    hlPeakLast: (N, d, v, v50) => `${N} के आसपास आग सबसे ताज़ा दिन सबसे ज़्यादा थी: <em>${d} को ${v} जगह आग</em> 250 किमी के भीतर${v50 ? `, जिनमें से ${v50} 50 किमी के भीतर` : ""}।`,
    hlPeak: (days, d, v, v50) => `पिछले ${days} दिनों में सबसे ज़्यादा आग <em>${d} को थी, ${v} जगह</em> 250 किमी के भीतर${v50 ? `, जिनमें से ${v50} 50 किमी के भीतर` : ""}।`,
    s30: (d) => `पिछले ${d} दिनों में 250 किमी के भीतर आग`, s50: "इनमें से 50 किमी के भीतर",
    sCrop: "पिछले 7 दिनों में 250 किमी के भीतर की आग खेतों में थी, जो पराली जलाने का पैटर्न है",
    hlNo2: (N, r, rank, n) => `पिछले 14 दिनों में ${N} की हवा में नाइट्रोजन डाइऑक्साइड (NO₂) इलाक़े के सामान्य स्तर से <em>${r} गुना</em> थी, <em>${n} शहरों में नंबर ${rank}</em>।`,
    hlKilns: (N, n) => `${N} से 50 किमी के भीतर <em>${n} ईंट भट्ठे</em> हैं।`,
    hlKilnsSplit: (pk, inn) => ` ${pk} पाकिस्तान में और ${inn} भारत में।`,
    hlKilnsPm: (t, e) => ` सर्वे का अनुमान है कि जिन ${e} भट्ठों के आँकड़े हैं वे भट्ठों के मौसम में रोज़ लगभग <em>${t} टन PM2.5</em> छोड़ते हैं।`,
    satKilns: (n, where) => `एक ही जगह ${n} ईंट भट्ठे, ${where}। हर अंडाकार आकृति एक भट्ठा है।`,
    whereTown: (town, km, dir) => `${town} के पास, केंद्र से ${km} किमी ${dir} में`, whereKm: (km, dir) => `केंद्र से ${km} किमी ${dir} में`,
    sZig: "साफ़ ज़िगज़ैग क़िस्म के हैं", sKilnRank: "50 किमी के भीतर भट्ठों में, उन शहरों में जिन्हें भट्ठा सर्वे में शामिल किया गया", mFossil: "50 किमी के भीतर जीवाश्म ईंधन वाले बिजलीघर",
    gapFoot: (txt) => `* ${txt}`,
    hlCh4: (name, km, plumes, kg) => `उपग्रहों और विमानों ने केंद्र से ${km} किमी दूर <em>${name}</em> से ${plumes} बार मीथेन उठती मापी है, लगभग <em>${kg} किलो प्रति घंटा</em>।`,
    hlCh4Rank: (rk, of) => ` इससे यह पाकिस्तान और भारत के मापे गए ${of} लैंडफ़िल में <em>नंबर ${rk}</em> है।`,
    hlCh4None: (N, n) => `कार्बन मैपर ने ${N} से 50 किमी के भीतर किसी लैंडफ़िल से मीथेन नहीं मापी, लेकिन वहाँ ${n} लैंडफ़िल और कूड़े के ढेर नक़्शे पर हैं।`,
    satSite: (name, km, dir) => `${name} ऊपर से, केंद्र से ${km} किमी ${dir} में`,
    sPlumes: "मीथेन के गुबार मापे गए", sLast: "आख़िरी माप", sDumps: "50 किमी के भीतर नक़्शे पर लैंडफ़िल और ढेर",
    hlPower: (N, n, ind) => `${N} से 50 किमी के भीतर <em>${n} जीवाश्म ईंधन वाले बिजलीघर</em> और <em>${ind} औद्योगिक इलाक़े</em> हैं।`,
    hlPowerNone: (N, ind) => `${N} से 50 किमी के भीतर जीवाश्म ईंधन वाला कोई बिजलीघर नक़्शे पर नहीं, लेकिन <em>${ind} औद्योगिक इलाक़े</em> हैं।`,
    hlCo2: (k, t) => ` कार्बन मैपर ने यहाँ ${k} प्लांट से CO₂ के गुबार मापे हैं, लगभग <em>${t} टन प्रति घंटा</em>।`,
    hlBig: (name, mw) => ` सबसे बड़ा, ${name}, ${mw} मेगावाट बिजली बना सकता है।`,
    satFoot: "उपग्रह दृश्य: Esri, Maxar, Earthstar Geographics",
    hSrc: (N) => `${N} से 50 किमी के भीतर नक़्शे पर हर स्रोत`,
    srcLede: "किसी परत को छिपाने के लिए उस पर टैप करें, या नाम देखने के लिए किसी जगह पर।",
    srcNote: "ईंट भट्ठा सर्वे, ओपनस्ट्रीटमैप, कार्बन मैपर और नासा FIRMS, सरहद के दोनों तरफ़। ये बताते हैं कि वहाँ क्या है, यह नहीं कि हर एक हवा में कितना जोड़ता है।",
    srcFail: "नक़्शा लोड नहीं हुआ। हर जगह प्रदूषण स्थलों की सूची में भी है।",
    hSeason: (N) => `इस मौसम में ${N} के आसपास आग पिछले सालों की तुलना में`,
    seasonFewest: (N, y, live) => live ? `अब तक यह मौसम ${y} के बाद से ${N} के आसपास सबसे कम आग वाला है।` : `यह मौसम ${y} के बाद से ${N} के आसपास सबसे कम आग वाला रहा।`,
    seasonMost: (N, y, live) => live ? `अब तक यह मौसम ${y} के बाद से ${N} के आसपास सबसे ज़्यादा आग वाला है।` : `यह मौसम ${y} के बाद से ${N} के आसपास सबसे ज़्यादा आग वाला रहा।`,
    seasonChart: (N) => `${N} से 250 किमी के भीतर आग, हर मौसम`, soFar: "अब तक",
    hCompare: (N) => `${N} दूसरे शहरों की तुलना में`,
    compareLede: (N) => `हर पट्टी में यहाँ के वे शहर हैं जिनके पास यह चीज़ है, सबसे ज़्यादा वाला बाईं तरफ़; लाल निशान ${N} है। ये अलग-अलग पैमाने हैं, इसलिए एक पर ऊँची रैंक दूसरे पर ऊँची रैंक से हवा में बड़ा हिस्सा नहीं।`,
    rankCell: (r, n) => `${n} में ${r}`,
    hShare: (N) => `इसे ${N} में किसी को भेजें`,
    shareLede: "व्हाट्सऐप या X में लिंक डालें तो आग और हवा का यह नक़्शा दिखता है, जो हर कुछ घंटों में नया बनता है।",
    ogAlt: (N) => `${N}: पिछले 24 घंटों में 250 किमी के भीतर आग और हवा`,
    hDetails: "सारे आँकड़े",
    detailsLede: "इस पन्ने के पीछे हर तालिका।",
    dCh4: "लैंडफ़िल मीथेन के रिकॉर्ड", dCompare: "हर पैमाना और रैंक", dLive: "आज की आग पर रैंक", dQa: (N) => `${N} की हवा के बारे में सवाल`,
  },
};

export const CITY_STYLE = `<style>
  .cp { --cp-fire: #d62d20; --cp-fire-soft: #fbe3dc; --cp-no2: #7a3fa0; --cp-no2-soft: #efe5f5; --cp-kiln: #a0522d; --cp-kiln-soft: #f5e6dc;
    --cp-lf: #5e7d2e; --cp-lf-soft: #e9f0dc; --cp-gas: #2f6f9f; --cp-gas-soft: #e2edf5; }
  .doc .cp-card { border: 1.5px solid var(--line); border-radius: 14px; padding: 18px 18px 16px; margin: 14px 0 6px; background: var(--paper); box-shadow: 3px 4px 0 var(--hair); display: flex; flex-direction: column; gap: 14px; }
  .cp-kicker { font-size: 13px; letter-spacing: .05em; text-transform: uppercase; color: var(--ink-3); }
  html[lang="ur"] .cp-kicker { text-transform: none; letter-spacing: 0; }
  .cp-aqi { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; min-height: 74px; }
  .cp-aqi-num { background: #999; color: #fff; border-radius: 12px; padding: 8px 16px; text-align: center; min-width: 112px; }
  .cp-aqi-num b { display: block; font: 700 46px/1 var(--sans); font-variant-numeric: tabular-nums; }
  .cp-aqi-num span { font-size: 12px; letter-spacing: .04em; }
  .cp-aqi-num.dark { color: var(--ink); }
  .cp-aqi-txt { flex: 1 1 240px; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
  .cp-aqi-band { font: 700 25px/1.15 var(--hand); }
  html[lang="ur"] .cp-aqi-band { font-family: var(--urdu); font-size: 22px; line-height: 1.8; }
  .cp-cigs { display: inline-flex; gap: 3px; vertical-align: -1px; margin-inline-start: 6px; flex-wrap: wrap; }
  .cp-cig { width: 20px; height: 7px; border-radius: 2px; background: linear-gradient(90deg, #fff 0 72%, #e9a15c 72% 100%); border: 1px solid #9a9a9a; }
  .doc .cp-card .lede { margin: 0; border-top: 1px dashed var(--hair); padding-top: 12px; }
  .cp-badges { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
  .doc a.cp-badge { display: flex; flex-direction: column; gap: 1px; border: 1px solid var(--hair); border-radius: 10px; padding: 8px 11px; background: var(--bg); text-decoration: none; }
  .doc a.cp-badge:hover { border-color: var(--ink-3); }
  .cp-badge b { font: 700 22px/1.15 var(--sans); font-variant-numeric: tabular-nums; }
  .cp-badge b small { font-size: 13px; font-weight: 500; color: var(--ink-3); }
  .cp-badge span { font-size: 13px; color: var(--ink-2); line-height: 1.3; }
  .doc .cp-note { font-size: 12.5px; color: var(--ink-3); margin: -6px 0 0; }
  .cp-share { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .cp-share a, .cp-share button { border: 1.5px solid var(--line); background: var(--bg); border-radius: 99px; padding: 5px 14px; font-size: 14px; font-weight: 600; text-decoration: none; cursor: pointer; color: var(--ink); }
  .cp-share a.wa { background: #1f9d55; border-color: #1f9d55; color: #fff; }
  .cp-jump { position: sticky; top: 0; z-index: 500; background: rgba(255,255,255,.96); display: flex; gap: 6px; overflow-x: auto; padding: 8px 0; margin: 18px 0 0; border-bottom: 1px solid var(--hair); }
  .doc .cp-jump a { flex: none; font-size: 13.5px; text-decoration: none; border: 1px solid var(--hair); border-radius: 99px; padding: 3px 12px; background: var(--bg); white-space: nowrap; }
  .doc .cp-jump a.on { background: var(--ink); color: #fff; border-color: var(--ink); }
  .doc .cp h2, .doc h2.cp-h { scroll-margin-top: 60px; }
  .cp-smoke { display: grid; grid-template-columns: minmax(0, 1fr) 200px; gap: 14px; align-items: start; }
  .cp-smoke .ff-map { margin-top: 0; }
  .cp-rose svg { width: 100%; height: auto; display: block; }
  .cp-rose path { cursor: pointer; }
  .cp-rose path:focus { outline: none; }
  .cp-rose path:focus-visible { outline: none; stroke: var(--ink); stroke-width: 2; }
  .doc .cp-rose p { font-size: 13px; color: var(--ink-3); margin-top: 4px; }
  @media (max-width: 700px) { .cp-smoke { grid-template-columns: minmax(0, 1fr); } .cp-rose { max-width: 280px; margin: 0 auto; } }
  .cp-causes { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin: 10px 0 6px; }
  .doc a.cp-cause { display: flex; flex-direction: column; gap: 5px; border: 1.5px solid var(--line); border-radius: 12px; padding: 11px 12px 10px; background: var(--c-soft); text-decoration: none; min-width: 0; transition: transform .15s; }
  .doc a.cp-cause:hover { transform: translateY(-2px); }
  @media (max-width: 600px) { .doc a.cp-cause:last-child:nth-child(odd) { grid-column: 1 / -1; } }
  .cp-cause svg { width: 42px; height: 42px; color: var(--c); }
  .cp-cause .t { font: 700 18px/1.15 var(--hand); }
  html[lang="ur"] .cp-cause .t { font-family: var(--urdu); font-size: 16px; line-height: 1.8; }
  .cp-cause .v { font: 700 23px/1.1 var(--sans); color: var(--c); font-variant-numeric: tabular-nums; }
  .cp-cause .s { font-size: 13px; color: var(--ink-2); line-height: 1.35; }
  .cp-cause .r { font-size: 12px; font-weight: 600; border-top: 1px dashed rgba(0,0,0,.18); padding-top: 5px; margin-top: auto; }
  .cp-story { display: grid; grid-template-columns: 42px minmax(0, 1fr); gap: 2px 14px; border-top: 1.5px solid var(--line); padding-top: 16px; margin-top: 26px; scroll-margin-top: 60px; }
  .cp-story > .ic { grid-row: span 2; color: var(--c); } .cp-story > .ic svg { width: 42px; height: 42px; }
  .doc .cp-story h3 { margin: 0; font-size: 24px; }
  .cp-story .body { grid-column: 2; display: flex; flex-direction: column; gap: 10px; min-width: 0; }
  @media (max-width: 560px) { .cp-story { grid-template-columns: minmax(0, 1fr); } .cp-story > .ic { grid-row: auto; } .cp-story .body { grid-column: 1; } }
  .doc .cp-hl { font-size: 17.5px; line-height: 1.5; font-weight: 500; margin: 0; }
  .cp-hl em { font-style: normal; font-weight: 700; color: var(--c); }
  .cp-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; }
  .cp-stat { background: var(--c-soft); border-radius: 10px; padding: 9px 12px; }
  .cp-stat b { display: block; font: 700 21px/1.2 var(--sans); color: var(--c); font-variant-numeric: tabular-nums; }
  .cp-stat span { font-size: 13px; color: var(--ink-2); line-height: 1.35; display: block; }
  .doc figure.cp-sat { margin: 0; }
  .cp-sat { position: relative; aspect-ratio: 16 / 9; max-width: 100%; border-radius: 10px; overflow: hidden; background: #c9c3b4; }
  .cp-sat .leaflet-container { position: absolute; inset: 0; background: #c9c3b4; }
  .cp-sat-ring { position: absolute; left: 50%; top: 50%; width: 70px; height: 70px; margin: -35px 0 0 -35px; border: 2.5px dashed #fff; border-radius: 50%; box-shadow: 0 0 0 1px rgba(0,0,0,.35); z-index: 450; pointer-events: none; }
  .cp-sat figcaption { position: absolute; inset-inline-start: 8px; bottom: 18px; z-index: 450; background: rgba(0,0,0,.66); color: #fff; font-size: 13px; line-height: 1.4; padding: 3px 9px; border-radius: 6px; max-width: calc(100% - 16px); }
  .cp-sat .att { position: absolute; inset-inline-end: 6px; bottom: 2px; z-index: 450; color: rgba(255,255,255,.9); font-size: 10px; text-shadow: 0 0 2px #000; }
  .cp-mw { display: flex; flex-direction: column; gap: 5px; }
  .cp-mw div { display: grid; grid-template-columns: minmax(0, 200px) minmax(0, 1fr) 76px; gap: 10px; align-items: center; font-size: 14px; }
  .cp-mw div span:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  @media (max-width: 560px) { .cp-mw div { grid-template-columns: minmax(0, 1fr) 70px; } .cp-mw div span:first-child { grid-column: 1 / -1; } }
  .cp-mw i { display: block; height: 11px; border-radius: 3px; background: var(--c); }
  .cp-mw div span:last-child { text-align: end; font-variant-numeric: tabular-nums; color: var(--ink-2); }
  .cp-layers { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
  .cp-layers button { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--hair); border-radius: 99px; padding: 3px 11px; font-size: 13px; background: var(--bg); cursor: pointer; }
  .cp-layers button i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .cp-layers button[aria-pressed="false"] { opacity: .45; text-decoration: line-through; }
  .ff-map.cp-src { height: 460px; }
  @media (max-width: 600px) { .ff-map.cp-src { height: 360px; } }
  .cp-ranks { display: flex; flex-direction: column; gap: 9px; margin: 10px 0; }
  .cp-rank { display: grid; grid-template-columns: minmax(0, 230px) minmax(0, 1fr) 84px; gap: 12px; align-items: center; font-size: 14px; }
  .cp-rank svg { width: 100%; height: 16px; display: block; }
  .cp-rank b { text-align: end; font-variant-numeric: tabular-nums; }
  @media (max-width: 560px) { .cp-rank { grid-template-columns: minmax(0, 1fr) 80px; } .cp-rank svg { grid-column: 1 / -1; grid-row: 2; } }
  .doc figure.cp-og { margin: 10px 0; }
  .cp-og { max-width: 480px; border: 1px solid var(--hair); border-radius: 10px; overflow: hidden; margin: 10px 0; }
  .cp-og img { display: block; width: 100%; height: auto; aspect-ratio: 1200 / 630; background: var(--paper); }
  .cp-og p { font-size: 13px; padding: 6px 10px; margin: 0; border-top: 1px solid var(--hair); }
  .doc details.cp-d { border: 1px solid var(--hair); border-radius: 10px; margin: 8px 0; }
  .doc details.cp-d > summary { cursor: pointer; padding: 10px 14px; font-weight: 600; }
  .doc details.cp-d > div { padding: 0 14px 12px; }
  .doc details.cp-d h3 { font-size: 17px; margin-top: 12px; }
  @media (prefers-reduced-motion: reduce) { .doc a.cp-cause { transition: none; } }
</style>\n`;

// Hand-drawn icons for the five kinds of pollution.
const ICON = {
  fire: '<path d="M24 5c3 7 11 10 11 20a11 11 0 0 1-22 0c0-6 4-8 5-13 2 4 4 6 6 6-1-4-1-9 0-13z"/><path d="M24 40a5 5 0 0 1-5-5c0-3 3-4 4-7 2 3 6 4 6 7a5 5 0 0 1-5 5z"/><path d="M6 43h36"/>',
  car: '<path d="M7 30l3-9c1-3 3-4 6-4h14c3 0 5 1 6 4l3 9"/><rect x="5" y="30" width="34" height="8" rx="3"/><circle cx="13" cy="39" r="3"/><circle cx="31" cy="39" r="3"/><path d="M40 33c3 0 4-2 6-2M40 36c3 0 5 1 6 3"/>',
  kiln: '<path d="M18 44V12h8v32"/><path d="M6 44h36"/><path d="M9 44V30c0-3 5-5 15-5s15 2 15 5v14"/><path d="M21 9c-1-3 2-4 1-7M25 9c2-2 0-4 3-6"/>',
  landfill: '<path d="M4 42c4-10 9-16 16-16 5 0 7 4 11 4 5 0 8 5 13 12z"/><path d="M14 34l3-2M24 33l2 2M33 36l2-3"/><path d="M22 22c-2-4 2-6 0-10M28 21c2-3-1-6 2-9"/>',
  factory: '<path d="M5 44V24l10 6v-6l10 6v-6l10 6V10h7v34z"/><path d="M5 44h37"/><path d="M36 7c0-3 3-3 3-6"/><path d="M12 38h4M21 38h4M30 38h4"/>',
};
const icon = (k) => `<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[k]}</svg>`;
const COLOR = { fires: "fire", no2: "no2", kilns: "kiln", landfill: "lf", power: "gas" };
const cvars = (k) => `--c: var(--cp-${COLOR[k]}); --c-soft: var(--cp-${COLOR[k]}-soft)`;
const ID = (k, l) => `${k}-${l}`; // anchors are per language: all three articles are in the page

// The wind rose: fires within 250 km in the last 24 hours by 45-degree sector, the upwind sectors red.
function rose(s, l, t, dirs) {
  const max = Math.max(1, ...s.sectors), up = (i) => s.w && !s.calm && Math.min(Math.abs(i * 45 - s.w[1]) % 360, 360 - (Math.abs(i * 45 - s.w[1]) % 360)) <= 45;
  const p = (a, r) => `${(r * Math.sin(a)).toFixed(1)},${(-r * Math.cos(a)).toFixed(1)}`;
  let g = `<circle r="100" fill="none" stroke="#e6e3dc"/><circle r="50" fill="none" stroke="#e6e3dc"/>`;
  s.sectors.forEach((v, i) => {
    const r = 16 + 84 * Math.sqrt(v / max), a0 = ((i * 45 - 20) * Math.PI) / 180, a1 = ((i * 45 + 20) * Math.PI) / 180, mid = (i * 45 * Math.PI) / 180;
    const fill = up(i) ? "#d62d20" : s.w && !s.calm ? "#c9c9cc" : "#f0a35a";
    g += `<path d="M${p(a0, 12)} L${p(a0, r)} A${r.toFixed(1)},${r.toFixed(1)} 0 0 1 ${p(a1, r)} L${p(a1, 12)} A12,12 0 0 0 ${p(a0, 12)}Z" fill="${fill}" data-sector="${i}" tabindex="0" role="button" aria-pressed="false" aria-label="${esc(`${dirs[i]}: ${nf(v, l)}`)}"><title>${esc(`${dirs[i]}: ${nf(v, l)}`)}</title></path>`;
    g += `<text x="${((r + 13) * Math.sin(mid)).toFixed(1)}" y="${(-(r + 13) * Math.cos(mid) + 4).toFixed(1)}" text-anchor="middle" font-size="11.5" font-weight="600" fill="#1d1d1f">${nf(v, l)}</text>`;
  });
  // Compass letters stay N/E/S/W in every language, as on the live map's arrows.
  g += ["N", "E", "S", "W"].map((c, i) => `<text x="${[0, 122, 0, -122][i]}" y="${[-116, 4, 124, 4][i]}" text-anchor="middle" font-size="12" font-weight="700" fill="#7c7c80">${c}</text>`).join("");
  if (s.calm) g += `<text y="4" text-anchor="middle" font-size="10" fill="#7c7c80">${t.calm}</text>`;
  const cap = !s.all ? t.roseNone : s.w && !s.calm ? t.roseUp(dirs[Math.round(s.w[1] / 45) % 8]) : t.roseCalm;
  return `<div class="cp-rose"><svg viewBox="-135 -135 270 270" role="group" aria-label="${esc(t.roseLabel)}" direction="ltr">${g}</svg><p>${cap}</p></div>`;
}

// Satellite view of one place: a small fixed Leaflet map of Esri imagery, drawn in the browser (city-page.js).
const sat = (pin, caption, t) => pin
  ? `<figure class="cp-sat" data-sat data-lat="${pin.lat}" data-lon="${pin.lon}"><span class="cp-sat-ring"></span><figcaption>${caption}</figcaption><span class="att">${t.satFoot}</span></figure>`
  : "";
const stat = (v, label) => `<div class="cp-stat"><b>${v}</b><span>${label}</span></div>`;

// The strongest ranks, for the badges on the card: up to four, the city's best first.
function badges(c, l, t, { s, cf, n2, ranks, f30rank }) {
  const R = c.src?.rank || {}, RN = c.src?.ranked || {}, no2 = no2Of(n2, c.id);
  const all = [
    ["fires24", ranks?.all?.get(c.id), ranks?.all?.size, "today"],
    ["no2", no2?.rank, n2?.ranked, "no2"],
    ["kilns", R.kilns, RN.kilns, "kilns"],
    ["fossil", R.fossil, RN.fossil, "power"],
    ["ch4", R.ch4, RN.ch4, "landfill"],
    ["fires30", f30rank?.[0], f30rank?.[1], "fires"],
    ["industry", R.industry, RN.industry, "power"],
  ].filter(([, r, n]) => r && n);
  // Ranks in the top half of their table; a city with none still shows its best two.
  all.sort((a, b) => a[1] / a[2] - b[1] / b[2]);
  const top = all.filter(([, r, n]) => r <= n / 2), pick = (top.length ? top : all.slice(0, 2)).slice(0, 4);
  if (!pick.length) return "";
  return `<div class="cp-badges">${pick.map(([k, r, n, a]) => `<a class="cp-badge" href="#${ID(a, l)}"><b>${t.rk(nf(r, l))} <small>${t.of(nf(n, l))}</small></b><span>${t.b[k]}</span></a>`).join("")}</div>` +
    `<p class="cp-note">${t.rankNote(nf(CITIES.length, l))}</p>`;
}

function shareRow(c, l, t, N) {
  const url = `${SITE}/air/${c.id}/`, text = t.shareText(N);
  return `<div class="cp-share"><a class="wa" href="https://wa.me/?text=${encodeURIComponent(`${text} ${url}`)}" target="_blank" rel="noopener">${t.wa}</a>` +
    `<a href="https://x.com/intent/post?text=${encodeURIComponent(text)}&amp;url=${encodeURIComponent(url)}" target="_blank" rel="noopener">${t.x}</a>` +
    `<button type="button" data-copy="${url}" data-done="${esc(t.copied)}">${t.copy}</button></div>`;
}

const rankStrip = (label, value, r, n, l, t) => {
  if (!r || !n) return "";
  // One tick per city, drawn as one dashed line.
  const step = 300 / n, dash = Math.max(1.5, step - 1.6);
  const ticks = `<line x1="0" x2="300" y1="8" y2="8" stroke="#e6e3dc" stroke-width="8" stroke-dasharray="${dash.toFixed(2)} ${(step - dash).toFixed(2)}"/>`;
  const x = (((r - 1) * 300) / n - 1).toFixed(1), w = Math.max(3, step + 2).toFixed(1);
  return `<div class="cp-rank"><span>${label}${value ? ` <span class="muted">(${value})</span>` : ""}</span><svg viewBox="0 0 300 16" preserveAspectRatio="none" aria-hidden="true" direction="ltr">${ticks}<rect x="${x}" y="0" width="${w}" height="16" rx="1" fill="#d62d20"/></svg><b>${t.rankCell(nf(r, l), nf(n, l))}</b></div>`;
};

// Fire spots each season, one bar per year, the current season red.
function seasonChart(cf, id, l, t, N) {
  const S = cf?.season, sv = cf?.cities?.[id]?.s || [];
  if (!S || !sv.some((v) => v != null)) return "";
  const W = 720, H = 240, pad = 28, max = Math.max(1, ...sv.filter((v) => v != null)), bw = (W - 20) / S.years.length, live = S.to !== "11-30";
  let g = "";
  S.years.forEach((y, i) => {
    const v = sv[i], cur = i === S.years.length - 1 && live, x = 10 + i * bw + 7, w = bw - 14;
    const gaps = new Set([...(S.gaps?.[y] || []), ...(S.missing?.[y] || [])]).size;
    if (v != null) {
      const h = ((H - pad - 28) * v) / max;
      g += `<rect x="${x.toFixed(1)}" y="${(H - pad - h).toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" rx="3" fill="${cur ? "#d62d20" : "#f0a35a"}"><title>${y}: ${nf(v, l)}</title></rect>` +
        `<text x="${(x + w / 2).toFixed(1)}" y="${(H - pad - h - 6).toFixed(1)}" text-anchor="middle" font-size="13" font-weight="${cur ? 700 : 500}" fill="#1d1d1f">${nf(v, l)}${gaps ? "*" : ""}</text>`;
    }
    g += `<text x="${(x + w / 2).toFixed(1)}" y="${H - 8}" text-anchor="middle" font-size="13" fill="${cur ? "#d62d20" : "#7c7c80"}" font-weight="${cur ? 700 : 400}">${y}${cur ? ` (${t.soFar})` : ""}</text>`;
  });
  return `<svg class="ff-bars" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(t.seasonChart(N))}" direction="ltr">${g}</svg>`;
}

// The whole page body for one language. `a` carries air.js's pieces: the lede, the map and its tables.
export function cityBody(c, l, a) {
  const t = T[l], ct = CT[l], n = (v) => nf(v, l), N = a.N, src = c.src || {}, pins = c.pins || {};
  const { s, cf, n2, ranks } = a;
  const f30 = fires30(cf, c.id), no2 = no2Of(n2, c.id);
  const f30rank = (() => {
    if (!cf || !f30.n250) return null;
    let r = 1, tot = 0;
    for (const id in cf.cities) { const o = fires30(cf, id).n250; if (o > 0) tot++; if (o > f30.n250) r++; }
    return [r, tot];
  })();
  const where = (pin) => t.whereKm(n(pin.km), a.dirs[Math.round(pin.deg / 45) % 8]);
  let h = `  <h1>${a.h1}</h1>\n`;

  // 1. The card.
  h += `  <div class="cp-card">\n   <p class="cp-kicker">${t.kicker(N)}</p>\n` +
    `   <div class="cp-aqi" data-air data-card data-lat="${c.lat}" data-lon="${c.lon}" data-lang="${l}" data-unit="${esc(t.aqiUnit)}" data-line="${esc(t.aqiSub)}" data-src="${esc(t.aqiSrc)}" data-bands="${esc(a.bands.join("|"))}">${t.aqiWait}</div>\n` +
    `   <p class="lede">${a.ledeHtml}</p>\n   ${badges(c, l, t, { s, cf, n2, ranks, f30rank })}\n   ${shareRow(c, l, t, N)}\n  </div>\n`;
  const jumps = ["today", "causes", "map", "season", "compare", "details"];
  h += `  <nav class="cp-jump" aria-label="${esc(t.jumpLabel)}">${jumps.map((k) => `<a href="#${ID(k, l)}">${t.jump[k]}</a>`).join("")}</nav>\n`;

  // 2. Today's smoke: the live map and the rose.
  h += `  <div class="cp">\n  <h2 id="${ID("today", l)}">${a.hMap}</h2>\n  <p class="muted">${a.mapNote}</p>\n  <div class="cp-smoke">${a.mapHtml}${rose(s, l, t, a.dirs)}</div>\n`;

  // 3. What's in the air: the tiles, then a story for each.
  const tiles = [], stories = [];
  if (cf) {
    tiles.push(["fires", "fire", t.cFires, n(f30.n250), t.tFires(n(f30.days)), f30rank ? t.tRank(n(f30rank[0]), n(f30rank[1])) : ""]);
    const rows = cf.cities[c.id]?.r || [];
    let best = -1;
    rows.forEach((r, i) => { if (r && (best < 0 || r[1] >= rows[best][1])) best = i; });
    let hl = "";
    if (best >= 0 && rows[best][1] > 0) {
      const d = date(cf.dates[best], l), v = n(rows[best][1]), v50 = rows[best][0] ? n(rows[best][0]) : "";
      hl = best === rows.length - 1 ? t.hlPeakLast(N, d, v, v50) : t.hlPeak(n(f30.days), d, v, v50);
    } else hl = f30.days ? ct.firesNone(N, date(cf.last, l), n(f30.days)) : "";
    const wk = s.week || [], wn = wk.reduce((x, r) => x + r[1], 0), wc = wk.reduce((x, r) => x + r[2], 0);
    const stats = [stat(n(f30.n250), t.s30(n(f30.days))), stat(n(f30.n50), t.s50)];
    if (wn >= 20) stats.push(stat(`${n(pct(wc, wn))}%`, t.sCrop));
    stories.push(["fires", "fire", ct.hFires(N), `<p class="cp-hl">${hl}</p>${fireChart(cf, c.id, l, N)}<div class="cp-stats">${stats.join("")}</div><p class="muted">${ct.firesNote}</p>`]);
  }
  if (n2?.window) {
    const has = no2 && no2.r != null;
    tiles.push(["no2", "car", t.cNo2, has ? ct.x(n(no2.r)) : "–", has ? t.tNo2 : t.tNo2None, has && no2.rank ? t.tRank(n(no2.rank), n(n2.ranked)) : ""]);
    let body = "";
    if (has) {
      let hl = t.hlNo2(N, n(no2.r), n(no2.rank), n(n2.ranked));
      if (no2.prev) { const d = Math.round(((no2.r - no2.prev) / no2.prev) * 100); hl += ct.no2Trend(n(Math.abs(d)), Math.abs(d) < 5 ? 0 : Math.sign(d)); }
      body += `<p class="cp-hl">${hl}</p>${no2Chart(n2, c.id, l, N)}`;
    } else body += `<p class="cp-hl">${ct.no2None(N)}</p>`;
    if (no2?.peak && no2.peak[0] >= 1.5) {
      const [r, kind, site, km] = no2.peak;
      body += `<p>${kind === "traffic" ? (km <= 5 ? ct.no2PeakHere(n(r), KIND[l][kind]) : ct.no2PeakTown(n(r), n(km), site)) : ct.no2Peak(n(r), n(km), KIND[l][kind] || kind, site)}</p>`;
    }
    body += `<p class="muted">${ct.no2Note} ${ct.no2AsOf(date(n2.window[0], l), date(n2.window[1], l, true))}</p>`;
    stories.push(["no2", "car", ct.hNo2(N), body]);
  }
  const k = src.kilns;
  if (k?.survey && k.n) {
    const pm = k.pm25_t_day != null && k.est * 2 >= k.n;
    tiles.push(["kilns", "kiln", t.cKilns, n(k.n), pm ? t.tKilnsPm(n(Math.round(k.pm25_t_day))) : t.tKilns, src.rank?.kilns ? t.tRank(n(src.rank.kilns), n(src.ranked.kilns)) : ""]);
    let hl = t.hlKilns(N, n(k.n)) + (k.pk && k.in ? t.hlKilnsSplit(n(k.pk), n(k.in)) : "") + (pm ? t.hlKilnsPm(n(Math.round(k.pm25_t_day)), n(k.est)) : "");
    const kp = pins.kilns;
    const cap = kp && t.satKilns(n(kp.n), kp.town_km <= 8 && kp.name !== c.name.en ? t.whereTown(esc(kp.name), n(kp.km), a.dirs[Math.round(kp.deg / 45) % 8]) : where(kp));
    const stats = [];
    if (k.zigzag != null) stats.push(stat(`${n(k.zigzag)}%`, t.sZig));
    if (src.rank?.kilns) stats.push(stat(t.tRank(n(src.rank.kilns), n(src.ranked.kilns)), t.sKilnRank));
    stories.push(["kilns", "kiln", t.cKilns, `<p class="cp-hl">${hl}</p>${sat(kp, cap, t)}<div class="cp-stats">${stats.join("")}</div>`]);
  }
  const ch4 = src.ch4, dumps = c.mapped?.landfills || 0;
  if (ch4?.n || dumps) {
    const top = ch4?.top?.[0];
    if (ch4?.n) tiles.push(["landfill", "landfill", t.cLandfill, n(ch4.kg_h), ch4.n === 1 ? t.tCh4(esc(top[0])) : t.tCh4Many(n(ch4.n)), top?.[8] ? t.tRankLf(n(top[8]), n(ch4.of)) : ""]);
    else tiles.push(["landfill", "landfill", t.cLandfill, n(dumps), t.tDumps, ""]);
    let body = "";
    if (top) {
      body += `<p class="cp-hl">${t.hlCh4(esc(top[0]), n(top[6]), n(top[2]), n(top[1]))}${top[8] ? t.hlCh4Rank(n(top[8]), n(ch4.of)) : ""}</p>`;
      const lp = pins.landfill;
      body += sat(lp, lp && t.satSite(esc(lp.name), n(lp.km), a.dirs[Math.round(lp.deg / 45) % 8]), t);
      const stats = [stat(n(top[2]), t.sPlumes), stat(date(top[4], l, true), t.sLast)];
      if (dumps) stats.push(stat(n(dumps), t.sDumps));
      body += `<div class="cp-stats">${stats.join("")}</div><p class="muted">${ct.ch4Note(n(ch4.of))}</p>`;
    } else body += `<p class="cp-hl">${t.hlCh4None(N, n(dumps))}</p>`;
    stories.push(["landfill", "landfill", t.cLandfill, body]);
  }
  const fo = src.fossil || { n: 0, top: [] }, ind = src.industry?.n || 0;
  if (fo.n || ind) {
    tiles.push(["power", "factory", t.cPower, n(fo.n || ind), fo.n ? t.tFossil(n(ind), fo.n === 1) : t.tInd, fo.n && src.rank?.fossil ? t.tRank(n(src.rank.fossil), n(src.ranked.fossil)) : src.rank?.industry ? t.tRank(n(src.rank.industry), n(src.ranked.industry)) : ""]);
    let hl = fo.n ? t.hlPower(N, n(fo.n), n(ind)) : t.hlPowerNone(N, n(ind));
    if (src.co2?.n) hl += t.hlCo2(n(src.co2.n), n(src.co2.t_h));
    const big = fo.top.find((p) => p[2]);
    if (big && fo.top.length > 1) hl += t.hlBig(esc(big[0]), n(Math.round(big[2])));
    let body = `<p class="cp-hl">${hl}</p>`;
    const pp = pins.plant;
    body += sat(pp, pp && t.satSite(esc(pp.name), n(pp.km), a.dirs[Math.round(pp.deg / 45) % 8]), t);
    const mw = fo.top.filter((p) => p[2]);
    if (mw.length > 1) {
      const max = mw[0][2];
      body += `<div class="cp-mw">${mw.map(([name, fuel, v, km]) => `<div><span title="${esc(name)}">${esc(name)} <span class="muted">${FUEL[l][fuel] || ""}${SEP(l)}${ct.km(n(km))}</span></span><i style="width:${((100 * v) / max).toFixed(1)}%"></i><span>${n(Math.round(v))} MW</span></div>`).join("")}</div>`;
    }
    if (src.hot?.n) body += `<p>${ct.hotLine(n(src.hot.n), src.hot.top.length ? ": " + src.hot.top.map(([name, days]) => `${esc(name)} (${n(days)})`).join(SEP(l)) : "", src.hot.n === 1)}</p>`;
    body += `<p class="muted">${ct.plantsNote}</p>`;
    stories.push(["power", "factory", t.cPower, body]);
  }
  h += `  <h2 id="${ID("causes", l)}">${t.hCauses(N)}</h2>\n  <p>${t.causesLede}</p>\n`;
  h += `  <div class="cp-causes">${tiles.map(([key, ic, title, v, sub, r]) =>
    `<a class="cp-cause" href="#${ID(key, l)}" style="${cvars(key)}">${icon(ic)}<span class="t">${title}</span><span class="v">${v}</span><span class="s">${sub}</span>${r ? `<span class="r">${r}</span>` : ""}</a>`).join("")}</div>\n`;
  h += stories.map(([key, ic, title, body]) => `  <section class="cp-story" id="${ID(key, l)}" style="${cvars(key)}"><div class="ic">${icon(ic)}</div><h3>${title}</h3><div class="body">${body}</div></section>\n`).join("");

  // 4. The sources map (drawn in the browser from /sources/city/<id>.json).
  const peak = no2?.peak && no2.peak[0] >= 1.5 ? `${no2.peak[4]},${no2.peak[5]},${no2.peak[0]}` : "";
  h += `  <h2 id="${ID("map", l)}">${t.hSrc(N)}</h2>\n  <p>${t.srcLede}</p>\n  <div class="cp-layers" data-layers-for="srcmap-${l}"></div>\n` +
    `  <div class="ff-map cp-src" id="srcmap-${l}" data-srcmap="/sources/city/${c.id}.json" data-lat="${c.lat}" data-lon="${c.lon}" data-lang="${l}" data-no2="${peak}" data-fail="${esc(t.srcFail)}"></div>\n` +
    `  <p class="muted">${t.srcNote} <a href="/sites/">/sites/</a> · ${ct.sourcesAsOf(date(a.srcBuilt, l, true))}</p>\n`;

  // 5. The seasons.
  const S = cf?.season, sv = cf?.cities?.[c.id]?.s || [];
  if (S && sv.some((v) => v != null)) {
    h += `  <h2 id="${ID("season", l)}">${t.hSeason(N)}</h2>\n  <p>${S.to === "11-30" ? ct.seasonLedeDone(N) : ct.seasonLede(N, date(`2000-${S.to}`, l))}</p>\n`;
    h += `  ${seasonChart(cf, c.id, l, t, N)}\n`;
    const gapYears = S.years.map((y) => [y, new Set([...(S.gaps?.[y] || []), ...(S.missing?.[y] || [])]).size]).filter(([, g]) => g);
    if (gapYears.length) h += `  <p class="muted">${gapYears.map(([y, g]) => t.gapFoot(`${y}: ${ct.gapNote(n(g), g === 1)}`)).join(" ")}</p>\n`;
    const clean = S.years.every((y) => !(S.gaps?.[y] || []).length && !(S.missing?.[y] || []).length) && sv.every((v) => v != null);
    const cur = sv[S.years.length - 1], prevI = S.years.length - 2, prevV = sv[prevI];
    const cleanY = (y) => !(S.gaps?.[y] || []).length && !(S.missing?.[y] || []).length;
    const lines = [];
    if (S.to !== "11-30" && cur != null && prevV && cleanY(S.years.at(-1)) && cleanY(S.years[prevI])) {
      const p = Math.round(((cur - prevV) / prevV) * 100);
      lines.push(p >= 0 ? ct.seasonUp(N, n(p), S.years[prevI]) : ct.seasonDown(N, n(-p), S.years[prevI]));
    }
    if (clean && S.years.length > 2) {
      const live = S.to !== "11-30";
      if (cur < Math.min(...sv.slice(0, -1))) lines.push(t.seasonFewest(N, S.years[0], live));
      else if (cur > Math.max(...sv.slice(0, -1))) lines.push(t.seasonMost(N, S.years[0], live));
    }
    if (lines.length) h += `  <p class="cp-hl" style="--c: var(--cp-fire)">${lines.join(" ")}</p>\n`;
  } else h += `  <span id="${ID("season", l)}"></span>\n`;

  // 6. Against the other cities.
  const R = src.rank || {}, RN = src.ranked || {};
  const strips = [
    [ct.rAll, n(s.all), ranks?.all?.get(c.id), ranks?.all?.size],
    [ct.mFires, n(f30.n250), f30rank?.[0], f30rank?.[1]],
    [ct.mNo2, no2?.r != null ? ct.x(n(no2.r)) : "", no2?.rank, n2?.ranked],
    [ct.mKilns, k?.survey ? n(k.n) : "", R.kilns, RN.kilns],
    [t.mFossil, n(fo.n), R.fossil, RN.fossil],
    [ct.mCh4, ch4?.kg_h ? ct.kgh(n(ch4.kg_h)) : "", R.ch4, RN.ch4],
    [ct.mCo2, src.co2?.t_h ? ct.th(n(src.co2.t_h)) : "", R.co2, RN.co2],
    [ct.mInd, n(ind), R.industry, RN.industry],
    [ct.mHot, n(src.hot?.n || 0), R.hot, RN.hot],
  ].map(([m, v, r, nn]) => rankStrip(m, v, r, nn, l, t)).join("");
  h += `  <h2 id="${ID("compare", l)}">${t.hCompare(N)}</h2>\n  <p>${t.compareLede(N)}</p>\n  <div class="cp-ranks">${strips}</div>\n  <p>${ct.seeAll}</p>\n`;

  // 7. Share.
  h += `  <h2>${t.hShare(N)}</h2>\n  <p>${t.shareLede}</p>\n  <figure class="cp-og"><img src="${ogUrl(c.id)}" alt="${esc(t.ogAlt(N))}" width="1200" height="630" loading="lazy" decoding="async"><p>${a.title}<br><span class="muted">hamarihawa.org</span></p></figure>\n  ${shareRow(c, l, t, N)}\n`;

  // 8. All the numbers, folded.
  const d = (title, body, open) => body ? `  <details class="cp-d"${open ? " open" : ""}><summary>${title}</summary><div>${body}</div></details>\n` : "";
  h += `  <h2 id="${ID("details", l)}">${t.hDetails}</h2>\n  <p class="muted">${t.detailsLede}</p>\n`;
  h += a.tables.map(([title, body]) => d(title, body)).join("");
  h += d(ct.hSeason(N), seasonTable(cf, c.id, l));
  h += d(t.dCh4, ch4Table(src, l));
  h += d(t.dCompare, cityRows(c, l, { cf, n2, f30, f30rank, no2 }));
  h += d(t.dLive, liveRows(c, l, { s, ranks }));
  h += d(t.dQa(N), qaRows(c, l, { N, s, cf, n2, f30, no2, ledeText: a.ledeText }), true);
  h += `  <p class="muted">${ct.dataLine(`/api/city?id=${c.id}`)}</p>\n  </div>\n`;
  return h;
}
