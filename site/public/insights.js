// "Where does our air come from?" (published source-apportionment studies) and
// "What can we do about transport?" (evidence-backed actions), in EN / UR / HI.
// Numbers are copied from the cited reports; see report/data/research-source-apportionment.md.
(() => {
  "use strict";
  const HH = window.HH;
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

  const COLORS = {
    transport: "#d62d20", industry: "#5a508c", kilns: "#7a4a2a", waste: "#6e7a3c", crop: "#e0a21a",
    residential: "#c26a3a", dust: "#b9a98a", power: "#2b2b2b", other: "#c9c4b9", biomass: "#e0a21a",
  };
  const L = {
    en: {
      title: "Where does our air come from?",
      sub: "Shares of fine-dust (PM2.5) pollution by source, from published studies. Studies measure different things (what is emitted vs. what ends up in the air you breathe), so numbers differ. We show each with its source.",
      emitted: "share of PM2.5 emitted", inAir: "share of PM2.5 in the air",
      transport: "Vehicles", industry: "Industry", kilns: "Brick kilns", waste: "Waste burning", crop: "Crop burning",
      residential: "Home cooking & heating", dust: "Dust (road, soil, construction)", power: "Power plants", other: "Other", biomass: "Biomass & crop burning",
      liveTitle: "Delhi, live estimate", liveText: "Delhi's official forecast model (IITM Decision Support System) splits pollution by source every day. In the 2025 burning season (15 Oct to 30 Nov), crop burning averaged 4.9% of Delhi's PM2.5 (15.5% in 2024), peaking at 22% on 12 Nov. Vehicles were nearly half of Delhi's own local share.",
      dispute: "Who to blame is politically contested. Punjab's government says about 30% of Lahore's smog comes from India; the World Bank estimates 13% of Punjab's PM2.5 comes from neighbouring countries; and about 30% of Indian Punjab's pollution comes from Pakistani Punjab. Smoke crosses the border both ways.",
      trTitle: "What can we do about transport?",
      trSub: "Vehicles are one of the biggest sources almost everywhere in the region, and the one most of us touch every day.",
      gov: "What works (ask your government for this)", you: "What you can do",
      g1h: "Clean fuel everywhere", g1: "In Pakistan, only about 40% of diesel met Euro-5 standards in 2025, and only one of five refineries made Euro-5 fuel. India moved the whole country to BS-VI (Euro-6 level) fuel and vehicles in April 2020. Clean fuel is the base everything else needs.",
      g2h: "Fix the dirtiest few vehicles first", g2: "Diesel trucks and buses are about 20% of Pakistan's fleet but over 65% of transport's PM2.5. In Delhi, two- and three-wheelers (50%) and heavy diesel vehicles (30%) dominate road-transport pollution. Real fitness tests, particle filters and retiring old trucks give the biggest gain per rupee.",
      g3h: "Electric buses and metros", g3: "A study of Delhi's electric-bus rollout estimated a 75% cut in emissions from the bus fleet and about 1,370 deaths avoided a year. Good public transport also cuts your own exposure: in Delhi, metro riders breathed about 72 µg/m³ against much more for people walking or in rickshaws.",
      g4h: "Odd-even is an emergency brake, not a cure", g4: "Delhi's odd-even car rule cut daytime PM2.5 by roughly 10–16% in January 2016, but had no measurable effect in April 2016, when the air was moving. Useful for winter smog emergencies only.",
      g5h: "Tackle road dust", g5: "Dust from roads, soil and building sites was 17% of Delhi's winter PM2.5 and 38% in summer. Paving road edges, covering construction and wet-sweeping are cheap.",
      y1h: "Take the metro or bus on bad days", y1: "You'll breathe less smoke than walking or in a rickshaw, and add less to it.",
      y2h: "Don't idle, keep your engine tuned", y2: "A smoky exhaust means unburnt fuel. Get it fixed, check tyre pressure, and switch off at long signals.",
      y3h: "Report smoky vehicles", y3: "Pakistan: EPA Punjab helpline 1373 or the Green Punjab app. India: CPCB's SAMEER app. Punjab fined or seized thousands of smoke-emitting vehicles in recent drives; complaints help direct them.",
      y4h: "Choose cleaner when you buy", y4: "If you're buying a motorbike, rickshaw or car, an electric or hybrid one cuts street-level pollution where people breathe it.",
      srcs: "Sources",
      places: { lahore: "Lahore", isb: "Islamabad & Rawalpindi", punjab: "Punjab (Pakistan)", delhi: "Delhi (winter)" },
    },
    ur: {
      title: "ہماری ہوا کہاں سے آلودہ ہوتی ہے؟",
      sub: "شائع شدہ تحقیق کے مطابق باریک ذرات (PM2.5) میں ہر ذریعے کا حصہ۔ مختلف مطالعے مختلف چیزیں ناپتے ہیں (کچھ یہ کہ کیا خارج ہوتا ہے، اور کچھ یہ کہ آپ کی سانس کی ہوا تک کیا پہنچتا ہے)، اس لیے ان کے اعداد بھی مختلف ہیں۔ ہر عدد کے ساتھ اس کا ماخذ دیا گیا ہے۔",
      emitted: "خارج ہونے والے PM2.5 میں حصہ", inAir: "ہوا میں موجود PM2.5 میں حصہ",
      transport: "گاڑیاں", industry: "صنعت", kilns: "اینٹوں کے بھٹے", waste: "کچرا جلانا", crop: "فصل جلانا",
      residential: "گھریلو کھانا پکانا اور گرمائش", dust: "گرد (سڑک، مٹی، تعمیرات)", power: "بجلی گھر", other: "دیگر", biomass: "لکڑی اور فصل جلانا",
      liveTitle: "دہلی، روزانہ اندازہ", liveText: "دہلی کا سرکاری ماڈل (IITM ڈیسیژن سپورٹ سسٹم) روزانہ آلودگی کو ذرائع میں بانٹتا ہے۔ 2025 کے فصل جلانے کے موسم (15 اکتوبر تا 30 نومبر) میں دہلی کے PM2.5 میں فصل جلانے کا اوسط حصہ 4.9% رہا (2024 میں 15.5%)، اور 12 نومبر کو یہ سب سے زیادہ، یعنی 22%، تک پہنچا۔ دہلی کی اپنی مقامی آلودگی میں تقریباً آدھا حصہ گاڑیوں کا تھا۔",
      dispute: "ذمہ دار کون ہے، یہ سوال سیاسی بن چکا ہے۔ پنجاب حکومت کا کہنا ہے کہ لاہور کی اسموگ کا تقریباً 30% ہندوستان سے آتا ہے؛ عالمی بینک کے مطابق پنجاب کے PM2.5 کا 13% پڑوسی ممالک سے آتا ہے؛ اور ہندوستانی پنجاب کی تقریباً 30% آلودگی پاکستانی پنجاب سے آتی ہے۔ دھواں دونوں جانب سے سرحد پار کرتا ہے۔",
      trTitle: "ٹریفک کی آلودگی کا کیا کریں؟",
      trSub: "اس خطے میں تقریباً ہر جگہ گاڑیاں آلودگی کے سب سے بڑے ذرائع میں سے ہیں، اور یہی وہ ذریعہ ہے جس سے ہم سب کا روز واسطہ پڑتا ہے۔",
      gov: "کیا کام کرتا ہے (حکومت سے یہ مانگیں)", you: "آپ کیا کر سکتے ہیں",
      g1h: "ہر جگہ صاف ایندھن", g1: "پاکستان میں 2025 میں صرف تقریباً 40% ڈیزل یورو-5 معیار پر تھا، اور پانچ میں سے صرف ایک ریفائنری یورو-5 ایندھن بناتی تھی۔ ہندوستان نے اپریل 2020 میں پورے ملک میں BS-VI (یورو-6 درجہ) ایندھن اور گاڑیاں نافذ کیں۔ باقی ہر قدم کا انحصار صاف ایندھن پر ہی ہے۔",
      g2h: "سب سے گندی گاڑیاں پہلے ٹھیک کریں", g2: "ڈیزل ٹرک اور بسیں پاکستان کی گاڑیوں کا تقریباً 20% ہیں، مگر ٹرانسپورٹ سے نکلنے والے PM2.5 کا 65% سے زیادہ انہی سے آتا ہے۔ دہلی میں دو اور تین پہیوں والی گاڑیاں (50%) اور بھاری ڈیزل گاڑیاں (30%) سڑک کی آلودگی پر حاوی ہیں۔ گاڑیوں کے حقیقی فٹنس ٹیسٹ، ذرات کے فلٹر اور پرانے ٹرکوں کو سڑکوں سے ہٹانا سب سے مؤثر اقدامات ہیں۔",
      g3h: "الیکٹرک بسیں اور میٹرو", g3: "دہلی میں الیکٹرک بسوں پر ایک تحقیق کے مطابق بسوں کا اخراج 75% کم ہوا اور ہر سال تقریباً 1,370 جانیں بچیں۔ اچھی پبلک ٹرانسپورٹ آپ کے اپنے پھیپھڑوں کو بھی بچاتی ہے: دہلی میں میٹرو کے مسافروں نے تقریباً 72 µg/m³ والی ہوا میں سانس لی، جو پیدل چلنے والوں یا رکشے میں سفر کرنے والوں سے کہیں کم ہے۔",
      g4h: "جفت-طاق اصول ہنگامی بریک ہے، علاج نہیں", g4: "دہلی کے جفت-طاق اصول نے جنوری 2016 میں دن کے PM2.5 کو تقریباً 10 سے 16% کم کیا، مگر اپریل 2016 میں، جب ہوا چل رہی تھی، اس کا کوئی اثر نہیں ہوا۔ یہ صرف سردیوں کی ہنگامی اسموگ کے لیے مفید ہے۔",
      g5h: "سڑک کی گرد کم کریں", g5: "دہلی میں سڑک، مٹی اور تعمیرات کی گرد سردیوں میں PM2.5 کا 17% اور گرمیوں میں 38% تھی۔ سڑکوں کے کنارے پکے کرنا، تعمیرات کو ڈھانپنا اور پانی سے صفائی سستے حل ہیں۔",
      y1h: "خراب دنوں میں میٹرو یا بس لیں", y1: "پیدل چلنے یا رکشے کے مقابلے میں آپ کی سانس میں کم دھواں جائے گا، اور آپ خود بھی اس میں کم اضافہ کریں گے۔",
      y2h: "انجن بند کریں اور اسے ٹھیک رکھیں", y2: "سائلنسر سے دھواں نکلنے کا مطلب ہے کہ ایندھن پوری طرح نہیں جل رہا۔ انجن ٹھیک کروائیں، ٹائروں میں ہوا چیک کریں، اور لمبے سگنل پر انجن بند کر دیں۔",
      y3h: "دھواں چھوڑتی گاڑیوں کی اطلاع دیں", y3: "پاکستان: ای پی اے پنجاب ہیلپ لائن 1373 یا گرین پنجاب ایپ۔ ہندوستان: CPCB کی SAMEER ایپ۔ پنجاب میں حالیہ مہمات کے دوران دھواں چھوڑنے والی ہزاروں گاڑیوں پر جرمانے ہوئے یا انہیں ضبط کیا گیا؛ شکایات سے حکام کو پتا چلتا ہے کہ کارروائی کہاں کرنی ہے۔",
      y4h: "خریدتے وقت صاف انتخاب کریں", y4: "اگر آپ موٹر سائیکل، رکشہ یا گاڑی خرید رہے ہیں تو الیکٹرک یا ہائبرڈ کا انتخاب کریں؛ اس سے گلیوں میں، جہاں لوگ سانس لیتے ہیں، آلودگی کم ہوتی ہے۔",
      srcs: "ماخذ",
      places: { lahore: "لاہور", isb: "اسلام آباد اور راولپنڈی", punjab: "پنجاب (پاکستان)", delhi: "دہلی (سردیاں)" },
    },
    hi: {
      title: "हमारी हवा कहाँ से गंदी होती है?",
      sub: "प्रकाशित शोध के अनुसार बारीक धूल (PM2.5) में किस स्रोत का कितना हिस्सा है। अलग-अलग अध्ययन अलग चीज़ें नापते हैं: कुछ यह कि कितना धुआँ निकलता है, और कुछ यह कि आपकी साँस की हवा तक कितना पहुँचता है। इसीलिए आँकड़े आपस में मेल नहीं खाते। हर आँकड़े के साथ उसका स्रोत दिया गया है।",
      emitted: "निकलने वाले PM2.5 में हिस्सा", inAir: "हवा में मौजूद PM2.5 में हिस्सा",
      transport: "वाहन", industry: "उद्योग", kilns: "ईंट भट्ठे", waste: "कचरा जलाना", crop: "पराली जलाना",
      residential: "घरेलू खाना पकाना और गर्मी", dust: "धूल (सड़क, मिट्टी, निर्माण)", power: "बिजलीघर", other: "अन्य", biomass: "लकड़ी और पराली जलाना",
      liveTitle: "दिल्ली, रोज़ाना अनुमान", liveText: "दिल्ली का सरकारी मॉडल (IITM डिसीज़न सपोर्ट सिस्टम) हर दिन हिसाब लगाता है कि प्रदूषण किस स्रोत से कितना आया। 2025 के पराली के मौसम (15 अक्टूबर से 30 नवंबर) में दिल्ली के PM2.5 में पराली का औसत हिस्सा 4.9% रहा (2024 में 15.5%), और 12 नवंबर को यह सबसे ज़्यादा 22% तक पहुँचा। दिल्ली के अपने स्थानीय प्रदूषण में लगभग आधा हिस्सा गाड़ियों का था।",
      dispute: "दोष किसका है, यह सवाल राजनीतिक है। पाकिस्तानी पंजाब की सरकार का कहना है कि लाहौर की स्मॉग का लगभग 30% भारत से आता है; विश्व बैंक के अनुसार पाकिस्तानी पंजाब के PM2.5 का 13% पड़ोसी देशों से आता है; और भारतीय पंजाब का लगभग 30% प्रदूषण पाकिस्तानी पंजाब से आता है। धुआँ दोनों तरफ़ से सरहद पार करता है।",
      trTitle: "वाहनों के प्रदूषण का क्या करें?",
      trSub: "इस पूरे इलाक़े में लगभग हर जगह गाड़ियाँ प्रदूषण के सबसे बड़े स्रोतों में से हैं, और यही वह स्रोत है जिससे हम सबका रोज़ वास्ता पड़ता है।",
      gov: "क्या कारगर है (सरकार से यह माँगें)", you: "आप क्या कर सकते हैं",
      g1h: "हर जगह साफ़ ईंधन", g1: "2025 में पाकिस्तान का सिर्फ़ लगभग 40% डीज़ल यूरो-5 मानक का था, और पाँच में से सिर्फ़ एक रिफ़ाइनरी यूरो-5 ईंधन बनाती थी। भारत ने अप्रैल 2020 में पूरे देश में BS-VI (यूरो-6 स्तर) का ईंधन और गाड़ियाँ लागू कर दीं। बाक़ी हर उपाय साफ़ ईंधन पर ही टिका है।",
      g2h: "सबसे गंदे वाहन पहले ठीक करें", g2: "पाकिस्तान में डीज़ल ट्रक और बसें कुल गाड़ियों का लगभग 20% हैं, लेकिन परिवहन से निकलने वाले PM2.5 का 65% से ज़्यादा इन्हीं से आता है। दिल्ली में सड़क के प्रदूषण में दोपहिया और तिपहिया गाड़ियों (50%) और भारी डीज़ल गाड़ियों (30%) का सबसे बड़ा हाथ है। सख़्त फ़िटनेस जाँच, कण फ़िल्टर और पुराने ट्रक हटाना सबसे असरदार उपाय हैं।",
      g3h: "इलेक्ट्रिक बसें और मेट्रो", g3: "दिल्ली की इलेक्ट्रिक बसों पर हुए एक अध्ययन के अनुसार इनसे बसों का उत्सर्जन 75% घटा और हर साल लगभग 1,370 मौतें टलीं। अच्छा सार्वजनिक परिवहन आपकी अपनी साँसों को भी बचाता है: दिल्ली में मेट्रो से सफ़र करने वालों ने लगभग 72 µg/m³ वाली हवा में साँस ली, जो पैदल चलने वालों या रिक्शा में बैठने वालों से कहीं कम है।",
      g4h: "ऑड-ईवन आपात ब्रेक है, इलाज नहीं", g4: "जनवरी 2016 में दिल्ली के ऑड-ईवन नियम से दिन के PM2.5 में लगभग 10–16% की कमी आई, लेकिन अप्रैल 2016 में, जब हवा चल रही थी, कोई असर नहीं दिखा। यह सिर्फ़ सर्दियों की आपात स्मॉग के लिए ठीक है।",
      g5h: "सड़क की धूल रोकें", g5: "दिल्ली में सर्दियों के PM2.5 का 17% और गर्मियों का 38% हिस्सा सड़क, मिट्टी और निर्माण की धूल का था। सड़क के किनारे पक्के करना, निर्माण स्थलों को ढकना और पानी से सफ़ाई करना सस्ते उपाय हैं।",
      y1h: "ख़राब दिनों में मेट्रो या बस लें", y1: "पैदल चलने या रिक्शा के मुक़ाबले आपकी साँस में कम धुआँ जाएगा, और आप ख़ुद भी कम धुआँ फैलाएँगे।",
      y2h: "इंजन ठीक रखें, रुकने पर बंद करें", y2: "अगर साइलेंसर से धुआँ निकल रहा है, तो इसका मतलब है कि ईंधन पूरा नहीं जल रहा। गाड़ी ठीक करवाएँ, टायरों की हवा जाँचते रहें, और लंबे सिग्नल पर इंजन बंद कर दें।",
      y3h: "धुआँ छोड़ते वाहनों की शिकायत करें", y3: "भारत: CPCB का SAMEER ऐप। पाकिस्तान: EPA पंजाब हेल्पलाइन 1373 या Green Punjab ऐप। शिकायतों से अधिकारियों को पता चलता है कि कार्रवाई कहाँ करनी है।",
      y4h: "नई गाड़ी लें तो साफ़ विकल्प चुनें", y4: "अगर आप मोटरसाइकिल, रिक्शा या कार ख़रीद रहे हैं, तो इलेक्ट्रिक या हाइब्रिड चुनें। इससे सड़क के स्तर पर प्रदूषण घटता है, ठीक वहाँ जहाँ लोग साँस लेते हैं।",
      srcs: "स्रोत",
      places: { lahore: "लाहौर", isb: "इस्लामाबाद और रावलपिंडी", punjab: "पंजाब (पाकिस्तान)", delhi: "दिल्ली (सर्दियाँ)" },
    },
  };

  // Each study: what it measures, where, and its shares (sum to ~100).
  const STUDIES = [
    { id: "lahore", lat: 31.55, lon: 74.34, metric: "emitted", parts: { transport: 35, industry: 28, kilns: 17, waste: 6, other: 14 },
      cite: "PAQI, Unveiling Pakistan's Air Pollution (2025), Lahore, base year 2021", url: "https://zenodo.org/records/17629179" },
    { id: "isb", lat: 33.65, lon: 73.06, metric: "emitted", parts: { transport: 53, kilns: 18, waste: 11, industry: 9, other: 9 },
      cite: "PAQI (2025), Islamabad–Rawalpindi airshed, base year 2021", url: "https://zenodo.org/records/17629179" },
    { id: "punjab", lat: 31.2, lon: 72.7, metric: "inAir", parts: { dust: 25, residential: 23, transport: 16, industry: 16, crop: 13, waste: 7 },
      cite: "World Bank, Towards Clean Air for Punjab (2024), via Punjab Clean Air Program documents", url: "https://documents1.worldbank.org/curated/en/099122424102011829/pdf/P508222137d9a00c1934e1dec002d9866b.pdf" },
    { id: "delhi", lat: 28.61, lon: 77.21, metric: "inAir", parts: { transport: 28, dust: 17, industry: 16, biomass: 14, residential: 10, kilns: 8, power: 6, other: 1 },
      cite: "TERI & ARAI, Source Apportionment of PM2.5 & PM10 of Delhi NCR (2018), winter; industry 30% incl. brick kilns 8% and power 6%", url: "https://www.teriin.org/sites/default/files/2018-08/AQM-SA_0.pdf" },
  ];
  const TR_SOURCES = [
    ["Pakistan fuel quality (National Assembly committee, 2025)", "https://www.pakwheels.com/blog/?p=217200"],
    ["PAQI 2025: diesel trucks/buses share", "https://zenodo.org/records/17629179"],
    ["Road transport impact on PM2.5 over Delhi (2022)", "https://www.sciencedirect.com/science/article/pii/S2590162122000545"],
    ["Delhi electric bus benefits (2022)", "https://www.sciencedirect.com/science/article/abs/pii/S0301479722016000"],
    ["On-road PM2.5 exposure in Delhi transport modes", "https://www.sciencedirect.com/science/article/abs/pii/S1352231015304556"],
    ["EPIC: odd-even evaluation", "https://epic.uchicago.edu/insights/yes-delhi-it-worked/"],
    ["IITM DSS 2025 season analysis (CREA via PTI)", "https://www.business-standard.com/india-news/delhi-air-pollution-in-2025-65-per-cent-traced-from-outside-city-126010300515_1.html"],
  ];

  let current = null;
  function nearestStudy() {
    const me = HH.state.local;
    if (!me) return "punjab";
    let best = "punjab", bd = Infinity;
    for (const s of STUDIES) {
      const d = Math.hypot(s.lat - me.lat, (s.lon - me.lon) * Math.cos((me.lat * Math.PI) / 180));
      if (d < bd) { bd = d; best = s.id; }
    }
    return bd < 3 ? best : "punjab";
  }

  function render() {
    const lang = HH.state.lang, T = L[lang] || L.en;
    if (!current) current = nearestStudy();
    const s = STUDIES.find((x) => x.id === current);
    const tabs = STUDIES.map((x) => `<button data-st="${x.id}" class="${x.id === current ? "on" : ""}">${esc(T.places[x.id])}</button>`).join("");
    const order = Object.entries(s.parts).sort((a, b) => b[1] - a[1]);
    const bar = order.map(([k, v]) => `<span class="seg" style="flex:${v};background:${COLORS[k]}" title="${esc(T[k])} ${v}%"><b>${v >= 7 ? v + "%" : ""}</b></span>`).join("");
    const legend = order.map(([k, v]) => `<li><i style="background:${COLORS[k]}"></i>${esc(T[k])} <b class="num">${v}%</b></li>`).join("");
    $("#whereBox").innerHTML = `
      <h2 class="sec-title small">${esc(T.title)}</h2>
      <p class="sec-sub">${esc(T.sub)}</p>
      <div class="chips st-tabs">${tabs}</div>
      <div class="share-card sketch" data-seed="71">
        <div class="metric">${esc(T[s.metric])}</div>
        <div class="bar100">${bar}</div>
        <ul class="seg-legend">${legend}</ul>
        <p class="cite">${esc(T.srcs)}: <a href="${s.url}" target="_blank" rel="noopener">${esc(s.cite)}</a></p>
      </div>
      <div class="two">
        <div class="live sketch" data-seed="72"><h3>${esc(T.liveTitle)}</h3><p>${esc(T.liveText)}</p></div>
        <div class="live sketch" data-seed="73"><p>${esc(T.dispute)}</p></div>
      </div>`;
    $("#whereBox").querySelectorAll("[data-st]").forEach((b) => b.addEventListener("click", () => { current = b.dataset.st; render(); }));

    const card = (h, p) => `<div class="do sketch"><h3>${esc(T[h])}</h3><p>${esc(T[p])}</p></div>`;
    $("#transportBox").innerHTML = `
      <h2 class="sec-title small">${esc(T.trTitle)}</h2>
      <p class="sec-sub">${esc(T.trSub)}</p>
      <h3 class="tr-h">${esc(T.gov)}</h3>
      <div class="dos tr">${["g1", "g2", "g3", "g4", "g5"].map((k) => card(k + "h", k)).join("")}</div>
      <h3 class="tr-h">${esc(T.you)}</h3>
      <div class="dos">${["y1", "y2", "y3", "y4"].map((k) => card(k + "h", k)).join("")}</div>
      <details class="how sketch"><summary>${esc(T.srcs)}</summary><ul>${TR_SOURCES.map(([n, u]) => `<li><a href="${u}" target="_blank" rel="noopener">${esc(n)}</a></li>`).join("")}</ul></details>`;
    window.dispatchEvent(new Event("hh:sketch"));
  }
  render();
  window.addEventListener("hh:lang", render);
  window.addEventListener("hh:local", () => { current = null; render(); });
})();
