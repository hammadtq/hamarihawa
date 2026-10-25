// Daily fire pages (/fires/, /fires/YYYY-MM-DD/) and district pages (/district/, /district/<slug>/),
// rendered from the daily archive in KV: "days" (per-day totals), "day-YYYY-MM-DD" (that day's spots,
// busiest districts and villages) and "dpages-index" plus "dpages-<cc>-<state>" (per-district season totals,
// built by scripts/build-feed.py).
// The page shell (header, nav, language switch) is site/src/shell.html, written by scripts/build-pages.py.
// Every page is cached at the edge, so a visit rarely costs a KV read.
import SHELL from "./shell.html";
import CITIES from "./cities.json";

const SITE = "https://hamarihawa.org";
const LANGS = ["en", "ur", "hi"];
const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
const MONTHS = {
  en: "January February March April May June July August September October November December".split(" "),
  ur: "جنوری فروری مارچ اپریل مئی جون جولائی اگست ستمبر اکتوبر نومبر دسمبر".split(" "),
  hi: "जनवरी फ़रवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर अक्टूबर नवंबर दिसंबर".split(" "),
};
const COUNTRY = { en: { PK: "Pakistan", IN: "India" }, ur: { PK: "پاکستان", IN: "ہندوستان" }, hi: { PK: "पाकिस्तान", IN: "भारत" } };
const QUIET = 150; // days with fewer spots stay out of search results and the sitemap
const FIRST_DAILY = "2026-10-01"; // every day is archived from here on; before it, only Oct-Nov seasons

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
// Numbers as Intl.NumberFormat prints them for these locales (Latin digits, Indian grouping in Hindi,
// a left-to-right mark before an Urdu minus), without Intl: loading its locale data costs a fresh
// isolate about 6 ms of CPU, more than the rest of a page. Non-integers keep up to 3 decimals, as Intl does.
const nf = (n, l) => {
  const r = Math.round(Math.abs(n) * 1000) / 1000, [i, f] = String(r).split(".");
  const g = i.length <= 3 ? i : l === "hi" ? `${i.slice(0, -3).replace(/\B(?=(\d{2})+$)/g, ",")},${i.slice(-3)}` : i.replace(/\B(?=(\d{3})+$)/g, ",");
  return (n < 0 && r ? (l === "ur" ? "\u200e-" : "-") : "") + g + (f ? `.${f}` : "");
};
const pct = (a, b) => (b ? Math.round((a / b) * 100) : 0);
const fdate = (iso, l, short) => {
  const [y, m, d] = iso.split("-").map(Number);
  return short ? `${d} ${MONTHS[l][m - 1]}` : `${d} ${MONTHS[l][m - 1]} ${y}`;
};
const shift = (iso, days) => new Date(Date.parse(iso + "T00:00:00Z") + days * 86400000).toISOString().slice(0, 10);
const ltr = (s) => `<bdi dir="ltr">${s}</bdi>`;
const dname = (n) => String(n).replace(/^District\s+/, "");

// ---------- Text ----------
const T = {
  en: {
    dayH1: (D) => `Fires on ${D}`,
    dayLede: (D, s, l) => `NASA's satellites saw fire at <b>${nf(s.spots, l)}</b> spots across ${s.snc ? "Pakistan and India" : "Pakistan and North India"} on ${D}: <b>${nf(s.pk, l)}</b> in Pakistan and <b>${nf(s.in, l)}</b> in India.`,
    up: (p, prev) => ` That is ${p}% more than the day before (${prev}).`,
    down: (p, prev) => ` That is ${p}% fewer than the day before (${prev}).`,
    same: (prev) => ` About the same as the day before (${prev}).`,
    partial: "This day isn't over yet (Pakistan time), so these numbers will grow. The page updates every 15 minutes.",
    night: (n, p) => `${n} spots (${p}%) were seen on night passes.`,
    crop: (n, p) => `${n} (${p}%) were on farmland and look like crop-residue burning; the rest were in forest, scrub or towns, or at brick kilns and factories. Fire types are our estimate from the ground they were on.`,
    yoy: (a, b, c, e, north) => `Year on year${north ? ", in the northern area covered every year since 2019" : ""}: Suomi NPP, the one satellite that has flown every season${north ? "" : " since 2019"}, saw ${a} spots in Pakistan and ${b} in India on this day, against ${c} and ${e} on the same date last year.`,
    yoyGap: (a, b, north) => `Year on year${north ? ", in the northern area covered every year since 2019" : ""}: Suomi NPP, the one satellite that has flown every season${north ? "" : " since 2019"}, saw ${a} spots in Pakistan and ${b} in India on this day. It returned no usable data on the same date last year, so there is nothing to compare with.`,
    gapCell: "no data",
    hStates: "By province and state", jump: "Jump to:", stTotal: (n) => `${n} Suomi NPP spots this season`,
    hDistricts: "Busiest districts", thDistrict: "District", thState: "Province or state", thCountry: "Country", thSpots: "Spots",
    hPlaces: "Villages with the most fires", place: (p, d, c, n) => `${p} (${d}, ${c}): ${n}`,
    hTwoWeeks: "The last two weeks",
    hYears: "The same date in earlier years", yearsNote: (north) => `Suomi NPP only${north ? ", and only the northern area covered every year since 2019" : ""}, so the years compare fairly.`, thYear: "Year",
    hMap: "Map", mapNote: "Every spot seen that day. Each dot is about 375 m across on the ground; zoom in to see the fields.",
    caveat: (api) => `Counts are a floor: clouds and smoke hide fires, and a fire lit and put out between two satellite passes is never seen. A spot is a 375 m square that looked as hot as a fire, not one field. Days run from midnight to midnight, Pakistan time. Source: NASA FIRMS. This day as data: ${api}. More in <a href="/trends/">Fire trends</a> and the <a href="/report/two-punjabs/">Two Punjabs report</a>.`,
    prev: (D) => `← ${D}`, next: (D) => `${D} →`, allDays: "All days", byDistrict: "Fires by district",
    pk: "Pakistan", in: "India",
    dayTitle: (D, s) => `Fires in ${s?.snc ? "Pakistan and India" : "Pakistan and North India"} on ${D}`,
    dayDesc: (D, s, top, l) => `${nf(s.spots, l)} fire spots seen by NASA satellites on ${D}: ${nf(s.pk, l)} in Pakistan, ${nf(s.in, l)} in India.${top ? ` Busiest districts: ${top}.` : ""}`,
    idxTitle: "Fires today in Pakistan and India", idxH1: "Daily fires",
    idxDesc: "Crop and other fires seen by NASA satellites across Pakistan and India, day by day: totals, busiest districts and villages, and the same date in earlier years.",
    idxLede: (D, s, l) => `On ${D}, the latest full day, NASA's satellites saw fire at <b>${nf(s.spots, l)}</b> spots: <b>${nf(s.pk, l)}</b> in Pakistan and <b>${nf(s.in, l)}</b> in India.`,
    readDay: "Read that day's report", todaySoFar: (n, href) => `Today so far: <a href="${href}">${n} spots</a>.`,
    season: (to, a, b, c, e, north) => `This season, 1 October to ${to}, ${north ? "in the northern area covered every year since 2019, " : ""}Suomi NPP has seen ${a} spots in Pakistan and ${b} in India. By the same date last year it had seen ${c} and ${e}.`,
    hDays: "Day by day", thDate: "Date", thNight: "At night",
    hTopDistricts: (to) => `Busiest districts this season (to ${to})`, allDistricts: "All districts →",
    distH1: "Fires by district", distTitle: "Crop fires by district in Pakistan and India",
    distDesc: "Every district in Pakistan and India with frequent satellite-seen fires: this season against the same dates last year, and every season since 2019.",
    distLede: (to) => `Every district with at least 500 fire spots in our archive since 2019. The columns count only Suomi NPP, so the years compare fairly: this season from 1 October to ${to}, the same dates last year, and the whole of last season.`,
    distNote: "Counts are a floor: clouds and smoke hide fires, and fires lit and put out between satellite passes are never seen. A dash means a district had no Suomi NPP count for those dates.",
    colNow: (y, to) => `${y}, to ${to}`, colLast: (y) => `${y}, same dates`, colFull: (y) => `${y}, whole season`,
    dH1: (n) => `Fires in ${n}`, dTitle: (n, st) => `Crop fires in ${n} district, ${st}`,
    dDesc: (n, st, c, a, to, l) => `${n} (${st}, ${c}): ${nf(a, l)} fire spots this season to ${to}, and every October–November season since 2019, from NASA satellite data.`,
    dLede: (n, st, c, a, to, rank, of, l) => `${n} district (${st}, ${c}) has had <b>${nf(a, l)}</b> fire spots this season, from 1 October to ${to}. That puts it ${ord(rank)} of the ${of} districts in ${c} on our list.`,
    dSn: (a, b, p) => `Counting only Suomi NPP, so the years compare fairly: ${a} this season against ${b} by the same date last year${p}.`,
    chg: (p) => (p > 0 ? ` (up ${p}%)` : p < 0 ? ` (down ${-p}%)` : ""),
    dPeak: (D, n) => `Its busiest day this season was ${D}, with ${n} spots.`,
    hSeasons: "Every season since 2019", thSeason: "Season", thSnTo: (to) => `Suomi NPP, 1 Oct to ${to}`, thSnFull: "Suomi NPP, whole season", thAllFull: "All satellites, whole season",
    hLast30: "The last 30 days", onMap: (href) => `<a href="${href}">See ${"this district"} on the live map</a> · <a href="/trends/">Fire trends</a> · <a href="/district/">All districts</a>`,
    dCaveat: (n) => `Counts are a floor: clouds and smoke hide fires, and fires lit and put out between satellite passes are never seen. A season here is 1 October to 30 November, when rice stubble is burnt. Suomi NPP returned no data on 4–6 November 2024 (a NASA outage), so the 2024 Suomi NPP figures are low. This page counts the days when ${n} was among the 150 busiest districts with at least 2 spots, which leaves out a few quiet days. NOAA-20 and NOAA-21 joined in 2018 and 2023, so all-satellite totals rise partly because more satellites are looking; compare years with the Suomi NPP columns.`,
    notFound: "Page not found", notFoundBody: `We don't have a page here. Try the <a href="/fires/">daily fires</a> or the <a href="/district/">district list</a>.`,
  },
  ur: {
    dayH1: (D) => `${D}: کہاں کہاں آگ لگی`,
    dayLede: (D, s, l) => `${D} کو ناسا کے سیٹلائٹس نے ${s.snc ? "پاکستان اور ہندوستان" : "پاکستان اور شمالی ہندوستان"} میں <b>${nf(s.spots, l)}</b> مقامات پر آگ دیکھی: <b>${nf(s.pk, l)}</b> پاکستان میں اور <b>${nf(s.in, l)}</b> ہندوستان میں۔`,
    up: (p, prev) => ` یہ پچھلے دن (${prev}) سے ${p}% زیادہ ہے۔`,
    down: (p, prev) => ` یہ پچھلے دن (${prev}) سے ${p}% کم ہے۔`,
    same: (prev) => ` یہ تعداد پچھلے دن (${prev}) کے تقریباً برابر ہے۔`,
    partial: "یہ دن (پاکستانی وقت کے مطابق) ابھی ختم نہیں ہوا، اس لیے یہ تعداد بڑھے گی۔ یہ صفحہ ہر 15 منٹ بعد تازہ ہوتا ہے۔",
    night: (n, p) => `${n} مقامات (${p}%) پر آگ رات کے چکر میں نظر آئی۔`,
    crop: (n, p) => `ہمارے اندازے کے مطابق ${n} مقامات (${p}%) کھیتوں میں تھے اور وہاں فصلوں کی باقیات جلائی جا رہی تھیں؛ باقی آگ جنگل، جھاڑیوں یا شہروں میں، یا اینٹوں کے بھٹوں اور کارخانوں پر تھی۔ یہ اندازہ اس زمین سے لگایا گیا ہے جہاں آگ تھی۔`,
    yoy: (a, b, c, e, north) => `پچھلے سال سے موازنہ${north ? "، اس شمالی علاقے میں جو 2019 سے ہر سال ریکارڈ میں ہے" : ""}: Suomi NPP، جو 2019 سے ہر موسم میں کام کرتا رہا ہے، اس دن پاکستان میں ${a} اور ہندوستان میں ${b} مقامات پر آگ دیکھ پایا۔ پچھلے سال اسی تاریخ کو یہ تعداد ${c} اور ${e} تھی۔`,
    yoyGap: (a, b, north) => `پچھلے سال سے موازنہ${north ? "، اس شمالی علاقے میں جو 2019 سے ہر سال ریکارڈ میں ہے" : ""}: Suomi NPP، جو 2019 سے ہر موسم میں کام کرتا رہا ہے، اس دن پاکستان میں ${a} اور ہندوستان میں ${b} مقامات پر آگ دیکھ پایا۔ پچھلے سال اسی تاریخ کو اس سیٹلائٹ کا ڈیٹا دستیاب نہیں تھا، اس لیے موازنہ ممکن نہیں۔`,
    gapCell: "ڈیٹا نہیں",
    hStates: "صوبوں اور ریاستوں کے لحاظ سے", jump: "سیدھا جائیں:", stTotal: (n) => `اس موسم میں Suomi NPP کے ${n} مقامات`,
    hDistricts: "سب سے زیادہ آگ والے اضلاع", thDistrict: "ضلع", thState: "صوبہ یا ریاست", thCountry: "ملک", thSpots: "مقامات",
    hPlaces: "سب سے زیادہ آگ والے دیہات", place: (p, d, c, n) => `${p} (${d}، ${c}): ${n}`,
    hTwoWeeks: "پچھلے دو ہفتے",
    hYears: "پچھلے برسوں میں یہی تاریخ", yearsNote: (north) => `صرف Suomi NPP کی گنتی${north ? "، اور صرف وہ شمالی علاقہ جو 2019 سے ہر سال ریکارڈ میں ہے" : ""}، تاکہ برسوں کا موازنہ درست رہے۔`, thYear: "سال",
    hMap: "نقشہ", mapNote: "اس دن نظر آنے والا ہر مقام۔ ہر نقطہ زمین پر تقریباً 375 میٹر چوڑا ہے؛ کھیت دیکھنے کے لیے نقشہ قریب کریں۔",
    caveat: (api) => `یہ گنتی کم از کم تعداد ہے: بادل اور دھواں آگ کو چھپا لیتے ہیں، اور جو آگ سیٹلائٹ کے دو چکروں کے درمیان لگ کر بجھ جائے وہ کبھی نظر نہیں آتی۔ ایک مقام 375 میٹر کا وہ چوکور ہے جو سیٹلائٹ کو آگ جتنا گرم دکھائی دیا، کوئی ایک کھیت نہیں۔ دن پاکستانی وقت کے مطابق آدھی رات سے آدھی رات تک گنا گیا ہے۔ ذریعہ: ناسا FIRMS۔ اس دن کا ڈیٹا: ${api}۔ مزید کے لیے <a href="/trends/">آگ کا رجحان</a> اور <a href="/report/two-punjabs/">دو پنجاب رپورٹ</a> دیکھیں۔`,
    prev: (D) => `→ ${D}`, next: (D) => `${D} ←`, allDays: "تمام دن", byDistrict: "اضلاع کے لحاظ سے آگ",
    pk: "پاکستان", in: "ہندوستان",
    idxH1: "روزانہ آگ",
    idxLede: (D, s, l) => `${D} کو، جو آخری مکمل دن ہے، ناسا کے سیٹلائٹس نے <b>${nf(s.spots, l)}</b> مقامات پر آگ دیکھی: <b>${nf(s.pk, l)}</b> پاکستان میں اور <b>${nf(s.in, l)}</b> ہندوستان میں۔`,
    readDay: "اس دن کی رپورٹ پڑھیں", todaySoFar: (n, href) => `آج اب تک: <a href="${href}">${n} مقامات</a>۔`,
    season: (to, a, b, c, e, north) => `اس موسم میں، 1 اکتوبر سے ${to} تک، ${north ? "اس شمالی علاقے میں جو 2019 سے ہر سال ریکارڈ میں ہے، " : ""}Suomi NPP نے پاکستان میں ${a} اور ہندوستان میں ${b} مقامات پر آگ دیکھی ہے۔ پچھلے سال اسی تاریخ تک یہ تعداد ${c} اور ${e} تھی۔`,
    hDays: "دن بہ دن", thDate: "تاریخ", thNight: "رات کو",
    hTopDistricts: (to) => `اس موسم میں سب سے زیادہ آگ والے اضلاع (${to} تک)`, allDistricts: "تمام اضلاع ←",
    distH1: "اضلاع کے لحاظ سے آگ",
    distLede: (to) => `ہمارے 2019 سے اب تک کے ریکارڈ میں ہر وہ ضلع جہاں کم از کم 500 مقامات پر آگ دیکھی گئی۔ ان کالموں میں صرف Suomi NPP کی گنتی ہے تاکہ برسوں کا موازنہ درست رہے: اس موسم میں 1 اکتوبر سے ${to} تک، پچھلے سال انہی تاریخوں میں، اور پچھلا پورا موسم۔`,
    distNote: "یہ گنتی کم از کم تعداد ہے: بادل اور دھواں آگ کو چھپا لیتے ہیں، اور جو آگ سیٹلائٹ کے دو چکروں کے درمیان لگ کر بجھ جائے وہ کبھی نظر نہیں آتی۔ جہاں ڈیش ہے وہاں ان تاریخوں کی Suomi NPP گنتی موجود نہیں۔",
    colNow: (y, to) => `${y}، ${to} تک`, colLast: (y) => `${y}، انہی تاریخوں میں`, colFull: (y) => `${y}، پورا موسم`,
    dH1: (n) => `${n} میں آگ`,
    dLede: (n, st, c, a, to, rank, of, l) => `ضلع ${n} (${st}، ${c}) میں اس موسم میں، 1 اکتوبر سے ${to} تک، <b>${nf(a, l)}</b> مقامات پر آگ دیکھی گئی۔ ہماری فہرست میں ${c} کے ${of} اضلاع میں یہ ${rank} نمبر پر ہے۔`,
    dSn: (a, b, p) => `صرف Suomi NPP کی گنتی سے، تاکہ برسوں کا موازنہ درست رہے: اس موسم میں ${a}، جبکہ پچھلے سال اسی تاریخ تک ${b}${p}۔`,
    chg: (p) => (p > 0 ? ` (${p}% زیادہ)` : p < 0 ? ` (${-p}% کم)` : ""),
    dPeak: (D, n) => `اس موسم میں یہاں سب سے زیادہ آگ ${D} کو دیکھی گئی، جب ${n} مقامات پر آگ لگی تھی۔`,
    hSeasons: "2019 سے اب تک ہر موسم", thSeason: "موسم", thSnTo: (to) => `Suomi NPP، 1 اکتوبر سے ${to} تک`, thSnFull: "Suomi NPP، پورا موسم", thAllFull: "تمام سیٹلائٹ، پورا موسم",
    hLast30: "پچھلے 30 دن", onMap: (href) => `<a href="${href}">یہ ضلع تازہ نقشے پر دیکھیں</a> · <a href="/trends/">آگ کا رجحان</a> · <a href="/district/">تمام اضلاع</a>`,
    dCaveat: (n) => `یہ گنتی کم از کم تعداد ہے: بادل اور دھواں آگ کو چھپا لیتے ہیں، اور جو آگ سیٹلائٹ کے دو چکروں کے درمیان لگ کر بجھ جائے وہ کبھی نظر نہیں آتی۔ یہاں موسم سے مراد 1 اکتوبر سے 30 نومبر تک کا عرصہ ہے، جب دھان کی پرالی جلائی جاتی ہے۔ 4 سے 6 نومبر 2024 کو Suomi NPP کا ڈیٹا دستیاب نہیں تھا (ناسا کی خرابی)، اس لیے 2024 کے Suomi NPP اعداد کم ہیں۔ یہ صفحہ صرف وہ دن گنتا ہے جب ${n} ان 150 اضلاع میں شامل تھا جہاں سب سے زیادہ آگ لگی اور کم از کم 2 مقامات پر آگ دیکھی گئی، اس لیے چند خاموش دن رہ جاتے ہیں۔ NOAA-20 اور NOAA-21 بالترتیب 2018 اور 2023 میں شامل ہوئے، اس لیے تمام سیٹلائٹس کی کل تعداد کچھ اس وجہ سے بھی بڑھی ہے کہ اب زیادہ سیٹلائٹ دیکھ رہے ہیں۔ برسوں کا موازنہ Suomi NPP والے کالموں سے کریں۔`,
    notFound: "صفحہ نہیں ملا", notFoundBody: `یہاں کوئی صفحہ نہیں ہے۔ <a href="/fires/">روزانہ آگ</a> یا <a href="/district/">اضلاع کی فہرست</a> دیکھیں۔`,
  },
  hi: {
    dayH1: (D) => `${D}: कहाँ-कहाँ आग लगी`,
    dayLede: (D, s, l) => `${D} को नासा के उपग्रहों ने ${s.snc ? "पाकिस्तान और भारत" : "पाकिस्तान और उत्तर भारत"} में <b>${nf(s.spots, l)}</b> जगहों पर आग देखी: <b>${nf(s.pk, l)}</b> पाकिस्तान में और <b>${nf(s.in, l)}</b> भारत में।`,
    up: (p, prev) => ` यह पिछले दिन (${prev}) से ${p}% ज़्यादा है।`,
    down: (p, prev) => ` यह पिछले दिन (${prev}) से ${p}% कम है।`,
    same: (prev) => ` यह संख्या पिछले दिन (${prev}) के लगभग बराबर है।`,
    partial: "यह दिन (पाकिस्तान के समय के हिसाब से) अभी ख़त्म नहीं हुआ है, इसलिए यह संख्या बढ़ेगी। यह पन्ना हर 15 मिनट में ताज़ा होता है।",
    night: (n, p) => `${n} जगहों (${p}%) पर आग रात वाले चक्कर में दिखी।`,
    crop: (n, p) => `हमारे अनुमान से ${n} जगहें (${p}%) खेतों में थीं और वहाँ फ़सल के अवशेष जलाए जा रहे थे; बाक़ी आग जंगल, झाड़ियों या शहरों में, या ईंट भट्ठों और कारख़ानों पर थी। यह अनुमान उस ज़मीन से लगाया गया है जहाँ आग थी।`,
    yoy: (a, b, c, e, north) => `पिछले साल से तुलना${north ? ", उस उत्तरी इलाक़े में जो 2019 से हर साल रिकॉर्ड में है" : ""}: Suomi NPP, जो 2019 से हर मौसम में काम करता रहा है, ने इस दिन पाकिस्तान में ${a} और भारत में ${b} जगहों पर आग देखी। पिछले साल इसी तारीख़ को ये आँकड़े ${c} और ${e} थे।`,
    yoyGap: (a, b, north) => `पिछले साल से तुलना${north ? ", उस उत्तरी इलाक़े में जो 2019 से हर साल रिकॉर्ड में है" : ""}: Suomi NPP, जो 2019 से हर मौसम में काम करता रहा है, ने इस दिन पाकिस्तान में ${a} और भारत में ${b} जगहों पर आग देखी। पिछले साल इसी तारीख़ को इस उपग्रह का डेटा उपलब्ध नहीं था, इसलिए तुलना संभव नहीं।`,
    gapCell: "डेटा नहीं",
    hStates: "प्रांत और राज्य के हिसाब से", jump: "सीधे जाएँ:", stTotal: (n) => `इस मौसम में Suomi NPP की ${n} जगहें`,
    hDistricts: "सबसे ज़्यादा आग वाले ज़िले", thDistrict: "ज़िला", thState: "प्रांत या राज्य", thCountry: "देश", thSpots: "जगहें",
    hPlaces: "सबसे ज़्यादा आग वाले गाँव", place: (p, d, c, n) => `${p} (${d}, ${c}): ${n}`,
    hTwoWeeks: "पिछले दो हफ़्ते",
    hYears: "पिछले सालों में यही तारीख़", yearsNote: (north) => `सिर्फ़ Suomi NPP की गिनती${north ? ", और सिर्फ़ वह उत्तरी इलाक़ा जो 2019 से हर साल रिकॉर्ड में है" : ""}, ताकि सालों की तुलना सही रहे।`, thYear: "साल",
    hMap: "नक्शा", mapNote: "उस दिन दिखी हर जगह। हर बिंदु ज़मीन पर लगभग 375 मीटर चौड़ा है; खेत देखने के लिए ज़ूम करें।",
    caveat: (api) => `यह गिनती कम से कम संख्या है: बादल और धुआँ आग को छिपा लेते हैं, और जो आग उपग्रह के दो चक्करों के बीच लगकर बुझ जाए वह कभी नहीं दिखती। एक जगह 375 मीटर का वह चौकोर है जो उपग्रह को आग जितना गर्म दिखा, कोई एक खेत नहीं। दिन पाकिस्तान के समय से आधी रात से आधी रात तक गिना गया है। स्रोत: नासा FIRMS। इस दिन का डेटा: ${api}। और जानकारी के लिए <a href="/trends/">आग का रुझान</a> और <a href="/report/two-punjabs/">दो पंजाब रिपोर्ट</a> देखें।`,
    prev: (D) => `← ${D}`, next: (D) => `${D} →`, allDays: "सभी दिन", byDistrict: "ज़िलेवार आग",
    pk: "पाकिस्तान", in: "भारत",
    idxH1: "रोज़ की आग",
    idxLede: (D, s, l) => `${D} को, जो आख़िरी पूरा दिन है, नासा के उपग्रहों ने <b>${nf(s.spots, l)}</b> जगहों पर आग देखी: <b>${nf(s.pk, l)}</b> पाकिस्तान में और <b>${nf(s.in, l)}</b> भारत में।`,
    readDay: "उस दिन की रिपोर्ट पढ़ें", todaySoFar: (n, href) => `आज अब तक: <a href="${href}">${n} जगहें</a>।`,
    season: (to, a, b, c, e, north) => `इस मौसम में, 1 अक्टूबर से ${to} तक, ${north ? "उस उत्तरी इलाक़े में जो 2019 से हर साल रिकॉर्ड में है, " : ""}Suomi NPP ने पाकिस्तान में ${a} और भारत में ${b} जगहों पर आग देखी है। पिछले साल इसी तारीख़ तक ये आँकड़े ${c} और ${e} थे।`,
    hDays: "दिन-ब-दिन", thDate: "तारीख़", thNight: "रात में",
    hTopDistricts: (to) => `इस मौसम में सबसे ज़्यादा आग वाले ज़िले (${to} तक)`, allDistricts: "सभी ज़िले →",
    distH1: "ज़िलेवार आग",
    distLede: (to) => `हमारे 2019 से अब तक के रिकॉर्ड में हर वह ज़िला जहाँ कम से कम 500 जगहों पर आग देखी गई। इन कॉलमों में सिर्फ़ Suomi NPP की गिनती है, ताकि सालों की तुलना सही रहे: इस मौसम में 1 अक्टूबर से ${to} तक, पिछले साल इन्हीं तारीख़ों में, और पिछला पूरा मौसम।`,
    distNote: "यह गिनती कम से कम संख्या है: बादल और धुआँ आग को छिपा लेते हैं, और जो आग उपग्रह के दो चक्करों के बीच लगकर बुझ जाए वह कभी नहीं दिखती। जहाँ डैश है वहाँ उन तारीख़ों की Suomi NPP गिनती मौजूद नहीं है।",
    colNow: (y, to) => `${y}, ${to} तक`, colLast: (y) => `${y}, इन्हीं तारीख़ों में`, colFull: (y) => `${y}, पूरा मौसम`,
    dH1: (n) => `${n} में आग`,
    dLede: (n, st, c, a, to, rank, of, l) => `${n} ज़िले (${st}, ${c}) में इस मौसम में, 1 अक्टूबर से ${to} तक, <b>${nf(a, l)}</b> जगहों पर आग दिखी है। हमारी सूची में ${c} के ${of} ज़िलों में यह ${rank}वें नंबर पर है।`,
    dSn: (a, b, p) => `सिर्फ़ Suomi NPP की गिनती से, ताकि सालों की तुलना सही रहे: इस मौसम में ${a}, जबकि पिछले साल इसी तारीख़ तक ${b}${p}।`,
    chg: (p) => (p > 0 ? ` (${p}% ज़्यादा)` : p < 0 ? ` (${-p}% कम)` : ""),
    dPeak: (D, n) => `इस मौसम में यहाँ सबसे ज़्यादा आग ${D} को दिखी, जब ${n} जगहों पर आग लगी थी।`,
    hSeasons: "2019 से अब तक हर मौसम", thSeason: "मौसम", thSnTo: (to) => `Suomi NPP, 1 अक्टूबर से ${to} तक`, thSnFull: "Suomi NPP, पूरा मौसम", thAllFull: "सभी उपग्रह, पूरा मौसम",
    hLast30: "पिछले 30 दिन", onMap: (href) => `<a href="${href}">यह ज़िला लाइव नक्शे पर देखें</a> · <a href="/trends/">आग का रुझान</a> · <a href="/district/">सभी ज़िले</a>`,
    dCaveat: (n) => `यह गिनती कम से कम संख्या है: बादल और धुआँ आग को छिपा लेते हैं, और जो आग उपग्रह के दो चक्करों के बीच लगकर बुझ जाए वह कभी नहीं दिखती। यहाँ मौसम का मतलब 1 अक्टूबर से 30 नवंबर तक का समय है, जब धान की पराली जलाई जाती है। 4 से 6 नवंबर 2024 को Suomi NPP का डेटा उपलब्ध नहीं था (नासा की ख़राबी), इसलिए 2024 के Suomi NPP आँकड़े कम हैं। यह पन्ना सिर्फ़ वे दिन गिनता है जब ${n} उन 150 ज़िलों में शामिल था जहाँ सबसे ज़्यादा आग लगी और कम से कम 2 जगहों पर आग दिखी, इसलिए कुछ शांत दिन छूट जाते हैं। NOAA-20 और NOAA-21 क्रमशः 2018 और 2023 में जुड़े, इसलिए सभी उपग्रहों की कुल संख्या कुछ इस वजह से भी बढ़ी है कि अब ज़्यादा उपग्रह देख रहे हैं। सालों की तुलना Suomi NPP वाले कॉलमों से करें।`,
    notFound: "पन्ना नहीं मिला", notFoundBody: `यहाँ कोई पन्ना नहीं है। <a href="/fires/">रोज़ की आग</a> या <a href="/district/">ज़िलों की सूची</a> देखें।`,
  },
};
function ord(n) {
  const s = ["th", "st", "nd", "rd"], v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

// ---------- Shell ----------
function render({ path, title, desc, body, jsonld, head = "", scripts = "", noindex = false }) {
  const robots = noindex ? '<meta name="robots" content="noindex, follow">\n' : "";
  const fill = { "@@PATH@@": path, "@@TITLE@@": esc(title), "@@DESC@@": esc(desc), "@@HEAD@@": robots + head, "@@SCRIPTS@@": scripts,
    "@@JSONLD@@": JSON.stringify(jsonld, null, 1).replace(/</g, "\\u003c") };
  for (const l of LANGS) fill[`@@BODY_${l}@@`] = body[l];
  return SHELL.replace(/@@[A-Za-z_]+@@/g, (m) => fill[m] ?? m);
}
const ORG = { "@id": `${SITE}/#org` };
const page = (html, status = 200, maxAge = 300) => new Response(html, { status, headers: { "content-type": "text/html; charset=utf-8", "cache-control": `public, max-age=${maxAge}` } });
const STYLE = `<style>
  .ff-bars { width: 100%; height: auto; display: block; margin: 8px 0 4px; }
  .ff-jump { font-size: 14px; line-height: 1.8; }
  .doc h3 small { font-weight: 400; font-size: 13px; }
  .ff-key { font-size: 13px; color: var(--ink-3); }
  .ff-key i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-inline-end: 4px; vertical-align: -1px; }
  .ff-nav { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin: 26px 0 0; font-size: 15px; }
  .ff-map { height: 420px; border: 1px solid var(--hair); border-radius: 6px; margin-top: 8px; background: #f4f2ec; }
  .doc td.n, .doc th.n { text-align: end; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .doc .muted { color: var(--ink-3); font-size: 14.5px; }
  .doc ul.facts li { margin-top: 4px; }
  @media (max-width: 600px) { .ff-map { height: 320px; } }
</style>\n`;

// Stacked bars, Pakistan under India, one per day. rows: [[iso, pk, in], ...]
function bars(rows, l, { link = true } = {}) {
  if (!rows.length) return "";
  const W = 720, H = 170, pad = 22, bw = (W - 8) / rows.length, max = Math.max(1, ...rows.map((r) => r[1] + r[2]));
  const y = (v) => ((H - pad - 6) * v) / max;
  let g = "";
  rows.forEach(([d, pk, inn], i) => {
    const x = 4 + i * bw, w = Math.max(1, bw - 3), hp = y(pk), hi = y(inn);
    const tip = `${fdate(d, l, true)}: ${nf(pk + inn, l)}`;
    const bar = `<title>${esc(tip)}</title><rect x="${x.toFixed(1)}" y="${(H - pad - hp).toFixed(1)}" width="${w.toFixed(1)}" height="${hp.toFixed(1)}" fill="#d62d20"/>` +
      `<rect x="${x.toFixed(1)}" y="${(H - pad - hp - hi).toFixed(1)}" width="${w.toFixed(1)}" height="${hi.toFixed(1)}" fill="#f0a35a"/>`;
    g += link ? `<a href="/fires/${d}/">${bar}</a>` : `<g>${bar}</g>`;
    if (i === 0 || i === rows.length - 1 || (rows.length > 10 && i === Math.floor(rows.length / 2)))
      g += `<text x="${(i === 0 ? x : i === rows.length - 1 ? x + w : x + w / 2).toFixed(1)}" y="${H - 6}" text-anchor="${i === 0 ? "start" : i === rows.length - 1 ? "end" : "middle"}" font-size="12" fill="#7c7c80">${esc(fdate(d, l, true))}</text>`;
  });
  return `<svg class="ff-bars" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(T[l].hTwoWeeks)}" direction="ltr">${g}</svg>` +
    `<p class="ff-key"><i style="background:#d62d20"></i>${T[l].pk} &nbsp; <i style="background:#f0a35a"></i>${T[l].in}</p>`;
}

// ---------- Data ----------
// "dpages-index" lists every district with the two seasons the listings show; each district's full history
// is in its state's shard (e.shard). The old single "dpages" key is read until the first split upload.
// Parsing the indexes is most of a page's CPU (each grows by a day's entry every day), so an isolate keeps
// what it parsed for as long as KV's own cache would (5 minutes) and the next page it renders skips the parse.
// Pages only read these objects, never change them.
const MEMO = new Map();
async function kvJson(env, key) {
  const m = MEMO.get(key), now = Date.now();
  if (m && now - m.at < 300000) return m.v;
  const v = await env.FEED.get(key, { type: "json", cacheTtl: 300 });
  if (v) MEMO.set(key, { v, at: now });
  return v;
}
async function load(env, withDays = true) {
  const [days, idx] = await Promise.all([withDays ? kvJson(env, "days") : null, kvJson(env, "dpages-index")]);
  const dp = idx || (await kvJson(env, "dpages"));
  return { days: days || {}, dp: dp || { d: {}, recent: [] } };
}
async function district(env, dp, sl) {
  const e = dp.d?.[sl];
  if (!e || !e.shard) return e || null;
  const part = await kvJson(env, e.shard);
  return part?.[sl] ? { ...e, ...part[sl] } : null;
}
// Built once per parsed index, not once per page.
const once = (f) => { const w = new WeakMap(); return (o) => { if (!w.has(o)) w.set(o, f(o)); return w.get(o); }; };
const slugOf = once((dp) => {
  const m = new Map();
  for (const [s, e] of Object.entries(dp.d || {})) m.set(`${e.name}|${e.state}|${e.cc}`, s);
  return (name, state, cc) => m.get(`${name}|${state}|${cc}`);
});
const complete = once((days) => Object.keys(days).filter((d) => !days[d].partial).sort());
// Suomi NPP returned no usable data (NASA's 2-6 Nov 2024 outage, dropped passes) when it saw almost nothing
// on a day the other satellites saw plenty. Its count is then missing, not zero.
const snGap = (e) => !!e && !!e.sn && e.sn[0] < 20 && e.spots >= 200 && e.sn[0] * 20 < e.spots;
// Days built for all of Pakistan and India carry snc, Suomi NPP inside the northern box (25-35.5 N,
// 66-88.5 E) that the archive covered until October 2026; days built before that only cover the box.
// Two whole-region days compare on sn; otherwise both sides use the box (snc, or sn on an old day).
const whole = (e) => !!e?.snc;
const snOf = (e) => e?.snc || e?.sn;
const snPair = (a, b) => (whole(a) && whole(b) ? [a.sn, b.sn, false] : [snOf(a), snOf(b), true]);

// ---------- /fires/YYYY-MM-DD/ ----------
async function dayPage(env, d) {
  const { days, dp } = await load(env);
  const s = days[d];
  if (!s) return null;
  // Day files carry every spot (up to ~1 MB on a peak day). The page only needs what comes before
  // "fields", so parse that slice and leave the spots, which the map fetches from /api/day, unparsed.
  const txt = await env.FEED.get(`day-${d}`, { cacheTtl: 900 });
  const cut = txt ? txt.indexOf(',"fields":') : -1;
  const day = txt ? JSON.parse(cut > 0 ? txt.slice(0, cut) + "}" : txt) : null;
  const slug = slugOf(dp);
  const prevD = shift(d, -1), nextD = shift(d, 1);
  const lyKey = `${+d.slice(0, 4) - 1}${d.slice(4)}`;
  const prev = days[prevD], ly = days[lyKey];
  const districts = (day?.districts || []).filter((r) => r[0] && r[0] !== "?" && r[0] !== r[1]).slice(0, 10);
  const places = (day?.places || []).slice(0, 8);
  // Every province and state with fires that day (v2 day files carry summary.states: [spots, night, ...]).
  const states = Object.entries(day?.summary?.states || {}).map(([k, v]) => [...k.split("|"), v[0], v[1]])
    .filter((r) => r[1] && r[2] > 0).sort((a, b) => b[2] - a[2]);
  // The two weeks up to this day, as long as the archive has them back to back.
  const two = [];
  for (let i = 13; i >= 0; i--) { const k = shift(d, -i); if (days[k] && whole(days[k]) === whole(s)) two.push([k, days[k].pk, days[k].in]); }
  const years = [];
  for (let y = 2019; y < +d.slice(0, 4); y++) { const k = `${y}${d.slice(4)}`; if (days[k]?.sn) years.push([y, k]); }
  // The table compares the whole region only when every year in it was built for the whole region.
  const yNorth = !years.every(([, k]) => whole(days[k])) || !whole(s);
  const ySn = (e) => (yNorth ? snOf(e) : e.sn);
  const top = districts.slice(0, 3).map((r) => dname(r[0])).join(", ");
  const body = {};
  for (const l of LANGS) {
    const t = T[l], D = fdate(d, l), n = (v) => nf(v, l);
    let lede = t.dayLede(D, s, l);
    if (prev && !s.partial && whole(prev) === whole(s)) {
      const p = pct(s.spots - prev.spots, prev.spots);
      lede += Math.abs(p) < 5 ? t.same(n(prev.spots)) : p > 0 ? t.up(p, n(prev.spots)) : t.down(-p, n(prev.spots));
    }
    const facts = [t.night(n(s.night), pct(s.night, s.spots)), t.crop(n(s.crop), pct(s.crop, s.spots))];
    const [c, lc, north] = snPair(s, ly);
    if (lc && c) facts.push(snGap(ly) ? t.yoyGap(n(c[1]), n(c[2]), north) : t.yoy(n(c[1]), n(c[2]), n(lc[1]), n(lc[2]), north));
    const link = (r) => { const sl = slug(r[0], r[1], r[2]); const nm = esc(dname(r[0])); return sl ? `<a href="/district/${sl}/">${nm}</a>` : nm; };
    const api = `<a href="/api/day?d=${d}"><code>/api/day?d=${d}</code></a>`;
    body[l] = `  <h1>${t.dayH1(D)}</h1>
  <p class="lede">${lede}</p>
${s.partial ? `  <p class="muted">${t.partial}</p>\n` : ""}  <ul class="facts">${facts.map((f) => `<li>${f}</li>`).join("")}</ul>
${districts.length ? `  <h2>${t.hDistricts}</h2>
  <div class="table-wrap"><table><thead><tr><th>${t.thDistrict}</th><th>${t.thState}</th><th>${t.thCountry}</th><th class="n">${t.thSpots}</th></tr></thead><tbody>
${districts.map((r) => `   <tr><td>${link(r)}</td><td>${esc(r[1])}</td><td>${COUNTRY[l][r[2]] || ""}</td><td class="n">${n(r[3])}</td></tr>`).join("\n")}
  </tbody></table></div>\n` : ""}${states.length > 1 ? `  <h2>${t.hStates}</h2>
  <div class="table-wrap"><table><thead><tr><th>${t.thState}</th><th>${t.thCountry}</th><th class="n">${t.thSpots}</th><th class="n">${t.thNight}</th></tr></thead><tbody>
${states.map((r) => `   <tr><td>${esc(r[1])}</td><td>${COUNTRY[l][r[0]] || ""}</td><td class="n">${n(r[2])}</td><td class="n">${n(r[3])}</td></tr>`).join("\n")}
  </tbody></table></div>\n` : ""}${places.length ? `  <h2>${t.hPlaces}</h2>
  <ul>${places.map((p) => `<li>${esc(t.place(p[0], dname(p[1]), COUNTRY[l][p[2]] || "", n(p[3])))}</li>`).join("")}</ul>\n` : ""}${two.length > 1 ? `  <h2>${t.hTwoWeeks}</h2>\n  ${bars(two, l)}\n` : ""}${years.length ? `  <h2>${t.hYears}</h2>
  <p>${t.yearsNote(yNorth)}</p>
  <div class="table-wrap"><table><thead><tr><th>${t.thYear}</th><th class="n">${t.pk}</th><th class="n">${t.in}</th></tr></thead><tbody>
${years.map(([y, k], _, __, sn = ySn(days[k])) => `   <tr><td><a href="/fires/${k}/">${y}</a></td>${snGap(days[k]) ? `<td class="n" colspan="2">${t.gapCell}</td>` : `<td class="n">${n(sn[1])}</td><td class="n">${n(sn[2])}</td>`}</tr>`).join("\n")}
   <tr><td><b>${d.slice(0, 4)}</b></td><td class="n"><b>${n(ySn(s)?.[1] ?? 0)}</b></td><td class="n"><b>${n(ySn(s)?.[2] ?? 0)}</b></td></tr>
  </tbody></table></div>\n` : ""}  <h2>${t.hMap}</h2>
  <p class="muted">${t.mapNote}</p>
  <div class="ff-map" data-day="${d}"></div>
  <p class="muted" style="margin-top:18px">${t.caveat(api)}</p>
  <nav class="ff-nav">${days[prevD] ? `<a href="/fires/${prevD}/">${t.prev(fdate(prevD, l))}</a>` : "<span></span>"}<a href="/fires/">${t.allDays}</a>${days[nextD] ? `<a href="/fires/${nextD}/">${t.next(fdate(nextD, l))}</a>` : "<span></span>"}</nav>`;
  }
  const D = fdate(d, "en");
  const jsonld = { "@context": "https://schema.org", "@type": "WebPage", "@id": `${SITE}/fires/${d}/#page`, name: T.en.dayTitle(D, s), url: `${SITE}/fires/${d}/`,
    inLanguage: LANGS, publisher: ORG, isPartOf: { "@id": `${SITE}/#website` }, datePublished: shift(d, 1),
    mainEntity: { "@type": "Dataset", name: `Satellite fire spots in ${s.snc ? "Pakistan and India" : "Pakistan and North India"}, ${D}`, description: T.en.dayDesc(D, s, top, "en"),
      temporalCoverage: d, spatialCoverage: s.snc ? "Pakistan and India" : "Pakistan and North India (25-35.5 N, 66-88.5 E)", license: "https://creativecommons.org/licenses/by/4.0/",
      creator: ORG, isBasedOn: "https://firms.modaps.eosdis.nasa.gov/",
      distribution: [{ "@type": "DataDownload", encodingFormat: "application/json", contentUrl: `${SITE}/api/day?d=${d}` }] } };
  const html = render({ path: `/fires/${d}/`, title: T.en.dayTitle(D, s), desc: T.en.dayDesc(D, s, top, "en"), body, jsonld, noindex: s.spots < QUIET,
    head: STYLE + '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">\n',
    scripts: '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>\n<script src="/fires/fires.js?v=2"></script>\n' });
  return { html, fresh: s.partial || d >= shift(complete(days).at(-1) || d, -1) };
}

// ---------- /fires/ ----------
async function indexPage(env) {
  const { days, dp } = await load(env);
  const done = complete(days);
  const last = done.at(-1);
  if (!last) return null;
  const today = Object.keys(days).find((d) => days[d].partial);
  const slug = slugOf(dp);
  const recent = Object.keys(days).sort().filter((d) => d > shift(last, -30)).reverse();
  // Season so far against the same dates last year (Suomi NPP only).
  let season = null;
  if (dp.season && last.slice(5) >= "10-01" && last.slice(5) <= "11-30") {
    const y = +last.slice(0, 4), keys = [];
    for (const yy of [y, y - 1]) for (let k = `${yy}-10-01`; k <= `${yy}-${last.slice(5)}`; k = shift(k, 1)) if (days[k]?.sn) keys.push(k);
    // Whole region only when both seasons so far were built for it; otherwise the northern box.
    const north = !keys.every((k) => whole(days[k]));
    const sum = (yy) => { const t = [0, 0]; for (const k of keys) if (k.startsWith(`${yy}-`)) { const c = north ? snOf(days[k]) : days[k].sn; t[0] += c[1]; t[1] += c[2]; } return t; };
    season = [sum(y), sum(y - 1), north];
  }
  const topD = Object.entries(dp.d || {}).map(([sl, e]) => [sl, e, e.s?.[dp.season]?.[3] || 0]).filter((x) => x[2] > 0).sort((a, b) => b[2] - a[2]).slice(0, 10);
  const body = {};
  for (const l of LANGS) {
    const t = T[l], n = (v) => nf(v, l), to = fdate(last, l);
    body[l] = `  <h1>${t.idxH1}</h1>
  <p class="lede">${t.idxLede(fdate(last, l), days[last], l)} <a href="/fires/${last}/">${t.readDay}</a>.</p>
${today ? `  <p>${t.todaySoFar(n(days[today].spots), `/fires/${today}/`)}</p>\n` : ""}${season ? `  <p>${t.season(to, n(season[0][0]), n(season[0][1]), n(season[1][0]), n(season[1][1]), season[2])}</p>\n` : ""}  ${bars(recent.filter((d) => !days[d].partial && whole(days[d]) === whole(days[last])).reverse().map((d) => [d, days[d].pk, days[d].in]), l)}
  <h2>${t.hDays}</h2>
  <div class="table-wrap"><table><thead><tr><th>${t.thDate}</th><th class="n">${t.pk}</th><th class="n">${t.in}</th><th class="n">${t.thNight}</th></tr></thead><tbody>
${recent.map((d) => `   <tr><td><a href="/fires/${d}/">${fdate(d, l)}</a></td><td class="n">${n(days[d].pk)}</td><td class="n">${n(days[d].in)}</td><td class="n">${n(days[d].night)}</td></tr>`).join("\n")}
  </tbody></table></div>
${topD.length ? `  <h2>${t.hTopDistricts(to)}</h2>
  <div class="table-wrap"><table><thead><tr><th>${t.thDistrict}</th><th>${t.thCountry}</th><th class="n">${t.thSpots}</th></tr></thead><tbody>
${topD.map(([sl, e, v]) => `   <tr><td><a href="/district/${sl}/">${esc(dname(e.name))}</a></td><td>${COUNTRY[l][e.cc]}</td><td class="n">${n(v)}</td></tr>`).join("\n")}
  </tbody></table></div>
  <p><a href="/district/">${t.allDistricts}</a></p>\n` : ""}  <p class="muted" style="margin-top:18px">${t.caveat(`<a href="/api/days"><code>/api/days</code></a>`)}</p>`;
  }
  const jsonld = { "@context": "https://schema.org", "@type": "CollectionPage", "@id": `${SITE}/fires/#page`, name: T.en.idxTitle, url: `${SITE}/fires/`,
    inLanguage: LANGS, publisher: ORG, isPartOf: { "@id": `${SITE}/#website` }, dateModified: last,
    hasPart: recent.slice(0, 30).map((d) => ({ "@type": "WebPage", name: T.en.dayTitle(fdate(d, "en"), days[d]), url: `${SITE}/fires/${d}/` })) };
  return render({ path: "/fires/", title: T.en.idxTitle, desc: T.en.idxDesc, body, jsonld, head: STYLE });
}

// ---------- /district/ ----------
async function districtIndex(env) {
  const { dp } = await load(env, false);
  if (!dp.last) return null;
  const y = dp.season, to = dp.to, toIso = `${y}-${to}`;
  const rows = Object.entries(dp.d).map(([sl, e]) => [sl, e, e.s?.[y]?.[1] ?? 0, e.s?.[y - 1]?.[1], e.s?.[y - 1]?.[0]]);
  const body = {};
  for (const l of LANGS) {
    const t = T[l], n = (v) => (v == null ? "–" : nf(v, l)), toL = fdate(toIso, l, true);
    const head = `<thead><tr><th>${t.thDistrict}</th><th class="n">${t.colNow(y, toL)}</th><th class="n">${t.colLast(y - 1)}</th><th class="n">${t.colFull(y - 1)}</th></tr></thead>`;
    const table = (cc) => {
      const groups = new Map();
      for (const r of rows.filter((r) => r[1].cc === cc)) {
        if (!groups.has(r[1].state)) groups.set(r[1].state, []);
        groups.get(r[1].state).push(r);
      }
      const sts = [...groups].map(([st, rs]) => [st, rs.sort((a, b) => b[2] - a[2] || (b[4] ?? 0) - (a[4] ?? 0)), rs.reduce((x, r) => x + (r[2] || 0), 0)])
        .sort((a, b) => b[2] - a[2] || b[1].length - a[1].length);
      const id = (st) => `${l}-${cc.toLowerCase()}-${st.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
      return `  <h2>${COUNTRY[l][cc]}</h2>
  <p class="ff-jump">${t.jump} ${sts.map(([st]) => `<a href="#${id(st)}">${esc(st)}</a>`).join(" · ")}</p>
${sts.map(([st, rs, tot]) => `  <h3 id="${id(st)}">${esc(st)} <small class="muted">${t.stTotal(n(tot))}</small></h3>
  <div class="table-wrap"><table>${head}<tbody>
${rs.map(([sl, e, a, b, c]) => `   <tr><td><a href="/district/${sl}/">${esc(dname(e.name))}</a></td><td class="n">${n(a)}</td><td class="n">${n(b)}</td><td class="n">${n(c)}</td></tr>`).join("\n")}
  </tbody></table></div>`).join("\n")}`;
    };
    body[l] = `  <h1>${t.distH1}</h1>\n  <p class="lede">${t.distLede(fdate(toIso, l))}</p>\n${table("PK")}\n${table("IN")}\n  <p class="muted" style="margin-top:18px">${t.distNote} <a href="/fires/">${t.allDays}</a></p>`;
  }
  const jsonld = { "@context": "https://schema.org", "@type": "CollectionPage", "@id": `${SITE}/district/#page`, name: T.en.distTitle, url: `${SITE}/district/`,
    inLanguage: LANGS, publisher: ORG, isPartOf: { "@id": `${SITE}/#website` }, dateModified: dp.last };
  return render({ path: "/district/", title: T.en.distTitle, desc: T.en.distDesc, body, jsonld, head: STYLE });
}

// ---------- /district/<slug>/ ----------
async function districtPage(env, sl) {
  const { dp } = await load(env, false);
  const e = await district(env, dp, sl);
  // A district published under an older name (before "District Jalaun" became "Jalaun", say) moves to its new address.
  if (!e) return dp.alias?.[sl] ? { moved: dp.alias[sl] } : null;
  const y = dp.season, to = dp.to, toIso = `${y}-${to}`, name = dname(e.name);
  const now = e.s?.[y] || [0, 0, 0, 0], last = e.s?.[y - 1];
  const seasons = Object.entries(e.s || {}).sort((a, b) => b[0] - a[0]);
  const r30 = (dp.recent || []).map((d, i) => [d, e.cc === "PK" ? e.r[i] : 0, e.cc === "IN" ? e.r[i] : 0]);
  const mapHref = `/#at=${e.lat},${e.lon},10`;
  const body = {};
  for (const l of LANGS) {
    const t = T[l], n = (v) => (v == null ? "–" : nf(v, l)), c = COUNTRY[l][e.cc], toL = fdate(toIso, l);
    let lede = t.dLede(esc(name), esc(e.state), c, now[3], toL, e.rank, e.of, l);
    const facts = [];
    if (now[1] != null && last?.[1] != null) facts.push(t.dSn(n(now[1]), n(last[1]), last[1] ? t.chg(pct(now[1] - last[1], last[1])) : ""));
    if (e.peak) facts.push(t.dPeak(`<a href="/fires/${e.peak[0]}/">${fdate(e.peak[0], l)}</a>`, n(e.peak[1])));
    body[l] = `  <h1>${t.dH1(esc(name))}</h1>
  <p class="lede">${lede}</p>
${facts.length ? `  <ul class="facts">${facts.map((f) => `<li>${f}</li>`).join("")}</ul>\n` : ""}  <h2>${t.hSeasons}</h2>
  <div class="table-wrap"><table><thead><tr><th>${t.thSeason}</th><th class="n">${t.thSnTo(fdate(toIso, l, true))}</th><th class="n">${t.thSnFull}</th><th class="n">${t.thAllFull}</th></tr></thead><tbody>
${seasons.map(([yr, v]) => `   <tr><td>${+yr === y ? `<b>${yr}</b>` : yr}</td><td class="n">${n(v[1])}</td><td class="n">${+yr === y && to < "11-30" ? "…" : n(v[0])}</td><td class="n">${+yr === y && to < "11-30" ? "…" : n(v[2])}</td></tr>`).join("\n")}
  </tbody></table></div>
${r30.some((r) => r[1] + r[2]) ? `  <h2>${t.hLast30}</h2>\n  ${bars(r30, l)}\n` : ""}  <p>${t.onMap(mapHref)}</p>
  <p class="muted" style="margin-top:18px">${t.dCaveat(esc(name))}</p>`;
  }
  const jsonld = { "@context": "https://schema.org", "@type": "WebPage", "@id": `${SITE}/district/${sl}/#page`, name: T.en.dTitle(name, e.state), url: `${SITE}/district/${sl}/`,
    inLanguage: LANGS, publisher: ORG, isPartOf: { "@id": `${SITE}/#website` }, dateModified: dp.last,
    about: { "@type": "AdministrativeArea", name: `${name}, ${e.state}, ${COUNTRY.en[e.cc]}`, geo: { "@type": "GeoCoordinates", latitude: e.lat, longitude: e.lon } } };
  return render({ path: `/district/${sl}/`, title: T.en.dTitle(name, e.state), desc: T.en.dDesc(name, e.state, COUNTRY.en[e.cc], now[3], fdate(toIso, "en"), "en"),
    body, jsonld, head: STYLE });
}

// ---------- sitemap of the generated pages ----------
async function sitemap(env) {
  const { days, dp } = await load(env);
  const done = complete(days);
  const urls = [[`${SITE}/fires/`, done.at(-1)], [`${SITE}/district/`, dp.last]];
  for (const d of done) if (d >= FIRST_DAILY && days[d].spots >= QUIET) urls.push([`${SITE}/fires/${d}/`, shift(d, 1)]);
  for (const sl of Object.keys(dp.d || {}).sort()) urls.push([`${SITE}/district/${sl}/`, dp.last]);
  // The city pages (src/air.js) change with every feed run.
  const today = new Date(Date.now() + 5 * 3600000).toISOString().slice(0, 10);
  urls.push([`${SITE}/air/`, today], ...CITIES.map((c) => [`${SITE}/air/${c.id}/`, today]));
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    urls.filter((u) => u[1]).map(([u, m]) => `  <url><loc>${u}</loc><lastmod>${m}</lastmod></url>`).join("\n") + "\n</urlset>\n";
}

function notFound() {
  const body = {};
  for (const l of LANGS) body[l] = `  <h1>${T[l].notFound}</h1>\n  <p>${T[l].notFoundBody}</p>`;
  return page(render({ path: "/fires/", title: T.en.notFound, desc: T.en.notFound, body, jsonld: {}, noindex: true }), 404, 300);
}

// Shared with the city pages (src/air.js).
export { SITE, LANGS, MONTHS, COUNTRY, ORG, STYLE, esc, nf, pct, dname, render, page, kvJson, notFound };

// Returns a Response for /fires/…, /district/… and /sitemap-daily.xml, or null for any other path.
export async function pages(url, env, ctx, edgeCached) {
  const p = url.pathname;
  if (p === "/fires" || p === "/district") return Response.redirect(`${url.origin}${p}/`, 301);
  if (/^\/(fires\/\d{4}-\d{2}-\d{2}|district\/[a-z0-9-]+)$/.test(p)) return Response.redirect(`${url.origin}${p}/`, 301);
  if (p === "/sitemap-daily.xml")
    return edgeCached(ctx, p, 3600, async () => new Response(await sitemap(env), { headers: { "content-type": "application/xml; charset=utf-8", "cache-control": "public, max-age=3600" } }));
  if (p === "/fires/") return edgeCached(ctx, p, 600, async () => { const h = await indexPage(env); return h ? page(h) : notFound(); });
  if (p === "/district/") return edgeCached(ctx, p, 3600, async () => { const h = await districtIndex(env); return h ? page(h) : notFound(); });
  let m = p.match(/^\/fires\/(\d{4}-\d{2}-\d{2})\/$/);
  if (m) {
    // Settled days change only when the archive is rebuilt; the last two days fill in through the day.
    const pkToday = new Date(Date.now() + 5 * 3600000).toISOString().slice(0, 10);
    const res = await edgeCached(ctx, p, m[1] < shift(pkToday, -2) ? 86400 : 900, async () => {
      const r = await dayPage(env, m[1]);
      return r ? page(r.html, 200, r.fresh ? 300 : 3600) : notFound();
    });
    return res;
  }
  m = p.match(/^\/district\/([a-z0-9-]+)\/$/);
  if (m) return edgeCached(ctx, p, 3600, async () => {
    const h = await districtPage(env, m[1]);
    return h?.moved ? Response.redirect(`${url.origin}/district/${h.moved}/`, 301) : h ? page(h) : notFound();
  });
  if (p.startsWith("/fires/") || p.startsWith("/district/")) return p === "/fires/fires.js" ? null : notFound();
  return null;
}
