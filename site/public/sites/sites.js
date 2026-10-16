// Pollution sites directory: persistent sources in Pakistan and North India, by category.
// Static categories come from /sources/sites.json (scripts/build-sites.py); traffic hotspots
// come live from /api/no2.json so they follow the latest two weeks.
(() => {
  "use strict";
  const T = {
    en: {
      dir: "ltr",
      tagline: "What satellites see in the air over Pakistan and North India, today",
      title: "Pollution sites satellites keep catching",
      lede: "These are places that show up again and again in satellite data: in NO₂ maps, methane and CO₂ plumes, or as heat that never goes away. Each one is listed with what was seen and when, and links to the live map.",
      all: "All", pk: "Pakistan", in: "India", loading: "Loading sites…",
      seeMap: "See on map →", showAll: "Show all {n}", near: "near {place}",
      unnamedLandfill: "Landfill near {place}", unnamedPlant: "Plant near {place}", unnamedHot: "Industrial site near {place}",
      traffic: "Traffic hotspots", trafficWhy: "Cities and corridors where nitrogen dioxide piles up, averaged over the last two weeks. In city cores it comes mostly from vehicle engines; plants nearby are listed separately below.",
      trafficHow: "Sentinel-5P TROPOMI NO₂, {from} to {to}. Compared with the usual level over the plains.",
      trafficEv: "the usual NO₂ level", kind_traffic: "City traffic", kind_industry: "Industrial estate", kind_corridor: "Highway / mixed sources", kind_kilns: "Brick-kiln belt",
      landfills: "Landfills leaking methane or burning", landfillsWhy: "Rotting rubbish releases methane, a strong greenhouse gas, and dumps often smoulder, adding smoke and toxic fumes for the people living around them.",
      landfillsHow: "Methane plumes: Carbon Mapper (satellite and aircraft, 2022–2026). Fires: NASA FIRMS 2025. Names: OpenStreetMap.",
      methaneEv: "≈ {rate} kg of methane an hour", seenEv: "seen in {n} plumes, {pct}% of passes ({first}–{last})", heatEv: "burning on {d} days in 2025",
      plants: "Power and industrial plants", plantsWhy: "Coal and gas plants and heavy industry, ranked by the carbon dioxide plume satellites measured. The same chimneys release NO₂ and sulphur dioxide.",
      plantsHow: "CO₂ plumes: Carbon Mapper. Names: OpenStreetMap power plants and industrial estates.",
      co2Ev: "≈ {t} tonnes of CO₂ an hour", fuel_coal: "Coal power plant", fuel_gas: "Gas power plant", fuel_oil: "Oil-fired power plant", fuel_power: "Power plant", fuel_industry: "Industrial plant",
      hot: "Always-hot industrial sites", hotWhy: "Places NASA's fire satellites saw hot on many days through the year: gas flares, furnaces, cement and steel works, refineries. Not crop fires, which move with the seasons.",
      hotHow: "NASA FIRMS VIIRS 2025 archive: spots hot on 20+ days, or flagged by NASA as static land sources.",
      hotEv: "days hot, across {m} months of 2025",
      kilns: "Brick-kiln belts", kilnsWhy: "Districts with the most brick kilns. Old fixed-chimney kilns burn coal, rubber and waste and are among the dirtiest sources near cities; zigzag kilns cut smoke sharply.",
      kilnsHow: "Kiln locations: SentinelKilnDB (IIT Gandhinagar) and the Pakistan IGP kiln dataset, from Sentinel-2 images. PM2.5 estimates: Pakistan dataset, firing season.",
      kilnEv: "kilns", zigEv: "{p}% zigzag (cleaner design)", pmEv: "≈ {t} tonnes of PM2.5 a day in firing season (estimate)",
      foot: "Being on this list means satellites detected pollution or heat at this place. It does not mean any company broke the law, and it doesn't measure each site's share of the air you breathe. Positions can be off by a few hundred metres.",
      credits: "Data: NASA FIRMS and GIBS · Copernicus Sentinel-5P · Carbon Mapper · SentinelKilnDB (CC BY-NC 4.0) · Pakistan IGP Brick Kiln Dataset (CC BY 4.0) · © OpenStreetMap contributors · GeoNames",
    },
    ur: {
      dir: "rtl",
      tagline: "پاکستان اور شمالی ہندوستان کی فضا: آج سیٹلائٹ کیا دیکھ رہے ہیں",
      title: "وہ مقامات جو سیٹلائٹ بار بار پکڑتے ہیں",
      lede: "یہ وہ جگہیں ہیں جو سیٹلائٹ ڈیٹا میں بار بار نظر آتی ہیں: NO₂ کے نقشوں میں، میتھین اور CO₂ کے اخراج میں، یا ایسی گرمی کے طور پر جو کبھی ختم نہیں ہوتی۔ ہر ایک کے ساتھ لکھا ہے کیا اور کب دیکھا گیا، اور تازہ نقشے کا لنک۔",
      all: "سب", pk: "پاکستان", in: "ہندوستان", loading: "مقامات آ رہے ہیں…",
      seeMap: "← نقشے پر دیکھیں", showAll: "تمام {n} دکھائیں", near: "{place} کے قریب",
      unnamedLandfill: "{place} کے قریب کچرا کنڈی", unnamedPlant: "{place} کے قریب پلانٹ", unnamedHot: "{place} کے قریب صنعتی مقام",
      traffic: "ٹریفک ہاٹ اسپاٹ", trafficWhy: "وہ شہر اور شاہراہیں جہاں نائٹروجن ڈائی آکسائیڈ جمع ہوتی ہے، پچھلے دو ہفتوں کی اوسط۔ شہروں کے مرکز میں یہ زیادہ تر گاڑیوں کے انجن سے آتی ہے؛ قریبی پلانٹ نیچے الگ درج ہیں۔",
      trafficHow: "Sentinel-5P TROPOMI NO₂، {from} سے {to}۔ میدانی علاقوں کی عام سطح سے موازنہ۔",
      trafficEv: "گنا عام NO₂ سطح", kind_traffic: "شہری ٹریفک", kind_industry: "صنعتی زون", kind_corridor: "شاہراہ / ملے جلے ذرائع", kind_kilns: "بھٹوں کی پٹی",
      landfills: "میتھین چھوڑتی یا جلتی کچرا کنڈیاں", landfillsWhy: "سڑتا کچرا میتھین چھوڑتا ہے، جو ایک طاقتور گرین ہاؤس گیس ہے، اور ڈھیر اکثر سلگتے رہتے ہیں، آس پاس رہنے والوں کے لیے دھواں اور زہریلی گیسیں۔",
      landfillsHow: "میتھین: Carbon Mapper (سیٹلائٹ اور جہاز، 2022–2026)۔ آگ: NASA FIRMS 2025۔ نام: OpenStreetMap۔",
      methaneEv: "تقریباً {rate} کلو میتھین فی گھنٹہ", seenEv: "{n} بار دیکھا گیا، {pct}% گزرنوں میں ({first}–{last})", heatEv: "2025 میں {d} دن جلتی رہی",
      plants: "بجلی گھر اور صنعتی پلانٹ", plantsWhy: "کوئلے اور گیس کے بجلی گھر اور بھاری صنعت، سیٹلائٹ سے ناپے گئے CO₂ کے اخراج کے لحاظ سے۔ یہی چمنیاں NO₂ اور سلفر ڈائی آکسائیڈ بھی چھوڑتی ہیں۔",
      plantsHow: "CO₂: Carbon Mapper۔ نام: OpenStreetMap۔",
      co2Ev: "تقریباً {t} ٹن CO₂ فی گھنٹہ", fuel_coal: "کوئلے کا بجلی گھر", fuel_gas: "گیس کا بجلی گھر", fuel_oil: "تیل کا بجلی گھر", fuel_power: "بجلی گھر", fuel_industry: "صنعتی پلانٹ",
      hot: "ہمیشہ گرم صنعتی مقامات", hotWhy: "وہ جگہیں جنہیں ناسا کے سیٹلائٹ نے سال بھر کئی دنوں گرم پایا: گیس کے شعلے، بھٹیاں، سیمنٹ اور اسٹیل کے کارخانے، ریفائنریاں۔ فصل کی آگ نہیں، جو موسم کے ساتھ بدلتی ہے۔",
      hotHow: "NASA FIRMS VIIRS 2025: 20 یا زیادہ دن گرم جگہیں، یا ناسا کی مستقل ذریعہ قرار دی گئی۔",
      hotEv: "دن گرم، 2025 کے {m} مہینوں میں",
      kilns: "اینٹوں کے بھٹوں کی پٹیاں", kilnsWhy: "سب سے زیادہ بھٹوں والے اضلاع۔ پرانے فکسڈ چمنی بھٹے کوئلہ، ربڑ اور کچرا جلاتے ہیں اور شہروں کے قریب سب سے گندے ذرائع میں سے ہیں؛ زگ زیگ بھٹے دھواں بہت کم کرتے ہیں۔",
      kilnsHow: "بھٹوں کے مقامات: SentinelKilnDB اور پاکستان IGP بھٹہ ڈیٹا، Sentinel-2 تصاویر سے۔ PM2.5 اندازے: پاکستان ڈیٹا، بھٹے کا موسم۔",
      kilnEv: "بھٹے", zigEv: "{p}% زگ زیگ (صاف ڈیزائن)", pmEv: "بھٹے کے موسم میں تقریباً {t} ٹن PM2.5 روزانہ (اندازہ)",
      foot: "اس فہرست میں ہونے کا مطلب ہے کہ سیٹلائٹ نے یہاں آلودگی یا گرمی پکڑی۔ اس کا مطلب یہ نہیں کہ کسی کمپنی نے قانون توڑا، اور یہ آپ کی ہوا میں ہر مقام کا حصہ نہیں ناپتا۔ جگہ چند سو میٹر ادھر ادھر ہو سکتی ہے۔",
      credits: "ڈیٹا: NASA FIRMS اور GIBS · Copernicus Sentinel-5P · Carbon Mapper · SentinelKilnDB (CC BY-NC 4.0) · Pakistan IGP Brick Kiln Dataset (CC BY 4.0) · © OpenStreetMap · GeoNames",
    },
    hi: {
      dir: "ltr",
      tagline: "पाकिस्तान और उत्तर भारत की हवा: आज उपग्रह क्या देख रहे हैं",
      title: "वे ठिकाने जिन्हें उपग्रह बार-बार पकड़ते हैं",
      lede: "ये वे जगहें हैं जो उपग्रह डेटा में बार-बार दिखती हैं: NO₂ के नक्शों में, मीथेन और CO₂ के गुबार में, या ऐसी गर्मी के रूप में जो कभी ख़त्म नहीं होती। हर एक के साथ लिखा है क्या और कब देखा गया, और लाइव नक्शे का लिंक।",
      all: "सब", pk: "पाकिस्तान", in: "भारत", loading: "ठिकाने आ रहे हैं…",
      seeMap: "नक्शे पर देखें →", showAll: "सभी {n} दिखाएँ", near: "{place} के पास",
      unnamedLandfill: "{place} के पास कचरा डंप", unnamedPlant: "{place} के पास संयंत्र", unnamedHot: "{place} के पास औद्योगिक ठिकाना",
      traffic: "ट्रैफ़िक हॉटस्पॉट", trafficWhy: "वे शहर और हाईवे जहाँ नाइट्रोजन डाइऑक्साइड जमा होती है, पिछले दो हफ़्तों का औसत। शहरों के बीच में यह ज़्यादातर वाहनों के इंजन से आती है; पास के संयंत्र नीचे अलग दिए हैं।",
      trafficHow: "Sentinel-5P TROPOMI NO₂, {from} से {to}। मैदानी इलाक़ों के सामान्य स्तर से तुलना।",
      trafficEv: "गुना सामान्य NO₂ स्तर", kind_traffic: "शहरी ट्रैफ़िक", kind_industry: "औद्योगिक क्षेत्र", kind_corridor: "हाईवे / मिले-जुले स्रोत", kind_kilns: "भट्ठों की पट्टी",
      landfills: "मीथेन छोड़ते या जलते कचरा डंप", landfillsWhy: "सड़ता कचरा मीथेन छोड़ता है, जो एक ताक़तवर ग्रीनहाउस गैस है, और ढेर अक्सर सुलगते रहते हैं, आसपास रहने वालों के लिए धुआँ और ज़हरीली गैसें।",
      landfillsHow: "मीथेन: Carbon Mapper (उपग्रह और विमान, 2022–2026)। आग: NASA FIRMS 2025। नाम: OpenStreetMap।",
      methaneEv: "लगभग {rate} किलो मीथेन प्रति घंटा", seenEv: "{n} बार दिखा, {pct}% बार ({first}–{last})", heatEv: "2025 में {d} दिन जलता रहा",
      plants: "बिजलीघर और औद्योगिक संयंत्र", plantsWhy: "कोयला और गैस बिजलीघर और भारी उद्योग, उपग्रह से नापे गए CO₂ गुबार के हिसाब से। यही चिमनियाँ NO₂ और सल्फ़र डाइऑक्साइड भी छोड़ती हैं।",
      plantsHow: "CO₂: Carbon Mapper। नाम: OpenStreetMap।",
      co2Ev: "लगभग {t} टन CO₂ प्रति घंटा", fuel_coal: "कोयला बिजलीघर", fuel_gas: "गैस बिजलीघर", fuel_oil: "तेल बिजलीघर", fuel_power: "बिजलीघर", fuel_industry: "औद्योगिक संयंत्र",
      hot: "हमेशा गर्म औद्योगिक ठिकाने", hotWhy: "वे जगहें जिन्हें नासा के उपग्रहों ने साल भर कई दिन गर्म पाया: गैस की लपटें, भट्टियाँ, सीमेंट और स्टील कारख़ाने, रिफ़ाइनरी। पराली नहीं, जो मौसम के साथ बदलती है।",
      hotHow: "NASA FIRMS VIIRS 2025: 20 या ज़्यादा दिन गर्म जगहें, या नासा द्वारा स्थायी स्रोत चिह्नित।",
      hotEv: "दिन गर्म, 2025 के {m} महीनों में",
      kilns: "ईंट भट्ठों की पट्टियाँ", kilnsWhy: "सबसे ज़्यादा भट्ठों वाले ज़िले। पुराने फ़िक्स्ड चिमनी भट्ठे कोयला, रबर और कचरा जलाते हैं और शहरों के पास सबसे गंदे स्रोतों में हैं; ज़िगज़ैग भट्ठे धुआँ बहुत घटाते हैं।",
      kilnsHow: "भट्ठों की जगहें: SentinelKilnDB (IIT गांधीनगर) और पाकिस्तान IGP भट्ठा डेटा, Sentinel-2 तस्वीरों से। PM2.5 अनुमान: पाकिस्तान डेटा, भट्ठे का मौसम।",
      kilnEv: "भट्ठे", zigEv: "{p}% ज़िगज़ैग (साफ़ डिज़ाइन)", pmEv: "भट्ठे के मौसम में लगभग {t} टन PM2.5 रोज़ (अनुमान)",
      foot: "इस सूची में होने का मतलब है कि उपग्रह ने यहाँ प्रदूषण या गर्मी पकड़ी। इसका मतलब यह नहीं कि किसी कंपनी ने क़ानून तोड़ा, और यह आपकी हवा में हर ठिकाने का हिस्सा नहीं नापता। जगह कुछ सौ मीटर इधर-उधर हो सकती है।",
      credits: "डेटा: NASA FIRMS और GIBS · Copernicus Sentinel-5P · Carbon Mapper · SentinelKilnDB (CC BY-NC 4.0) · Pakistan IGP Brick Kiln Dataset (CC BY 4.0) · © OpenStreetMap · GeoNames",
    },
  };
  const LOC = { en: "en-GB", ur: "ur-PK", hi: "hi-IN" };
  const ICONS = {
    traffic: '<path d="M5 15h14l-1.5-5h-11zM7 15v3M17 15v3M6.5 10l1.5-3h8l1.5 3"/>',
    landfills: '<path d="M3 20h18M5 20l4-9 3 4 3-6 4 11"/><path d="M9 6c0-2 2-2 2-4M14 7c0-2 2-2 2-4"/>',
    plants: '<path d="M4 20V11l5 3V11l5 3V6h3v14zM15 6V3h2v3"/>',
    hot: '<circle cx="12" cy="12" r="5"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/>',
    kilns: '<path d="M7 20V8h4v12M13 20V5h4v15M5 20h14"/>',
  };
  const SHOW = 12;
  let lang = "en", cc = "", data = null, no2 = null;
  try { lang = localStorage.getItem("hh-lang") || "en"; } catch {}
  if (!T[lang]) lang = "en";
  const t = (k, v) => { let s = T[lang][k] ?? T.en[k] ?? k; if (v) for (const [a, b] of Object.entries(v)) s = s.split(`{${a}}`).join(b); return s; };
  const nf = (n, o) => new Intl.NumberFormat(LOC[lang], o).format(n);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const fmtDay = (d) => new Intl.DateTimeFormat(LOC[lang], { day: "numeric", month: "short" }).format(Date.parse(d + "T12:00:00Z"));
  const year = (d) => (d || "").slice(0, 4);
  const country = (c) => (c === "PK" ? t("pk") : c === "IN" ? t("in") : "");
  const loc = (x) => [x.district, x.state, country(x.cc)].filter(Boolean).filter((v, i, a) => a.indexOf(v) === i).join(", ");
  const mapLink = (x, layer, src, z = 12) => `/#at=${x.lat},${x.lon},${z}${layer ? "&layer=" + layer : ""}${src ? "&src=" + src : ""}`;

  function card(i, title, where, ev, href, c) {
    return `<article class="site sketch" data-cc="${c}"><span class="rank">#${nf(i + 1)}</span><h3>${esc(title)}</h3>
      <span class="loc">${esc(where)}</span><div class="ev">${ev}</div><a class="btn go" href="${href}">${esc(t("seeMap"))}</a></article>`;
  }
  function section(id, title, why, how, cards) {
    const n = cards.length;
    return `<section class="cat" id="${id}"><h2><svg class="ico" viewBox="0 0 24 24">${ICONS[id]}</svg>${esc(title)}</h2>
      <p class="why">${esc(why)}</p><p class="src-note">${esc(how)}</p>
      <div class="grid">${cards.join("") || `<p class="empty">–</p>`}</div>
      ${n > SHOW ? `<button class="btn more" data-more="${id}">${esc(t("showAll", { n: nf(n) }))}</button>` : ""}</section>`;
  }

  function render() {
    document.documentElement.lang = lang;
    document.documentElement.dir = T[lang].dir;
    
    document.querySelectorAll("[data-en]").forEach((el) => { el.textContent = el.dataset[lang] || el.dataset.en; });
    document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));
    const chips = document.querySelectorAll("#ccChips button");
    chips[0].textContent = t("all"); chips[1].textContent = t("pk"); chips[2].textContent = t("in");
    document.getElementById("title").textContent = t("title");
    document.getElementById("lede").textContent = t("lede");
    document.getElementById("foot").textContent = t("foot");
    document.getElementById("credits").textContent = t("credits");
    document.getElementById("loading").textContent = t("loading");
    if (!data) return;

    const pick = (list) => list.filter((x) => !cc || x.cc === cc);
    const sections = [];
    // Traffic hotspots (live)
    if (no2) {
      const hs = no2.hotspots.filter((h) => h[3] !== "plant" && (h[7] === "PK" || h[7] === "IN"))
        .map((h) => ({ lat: h[0], lon: h[1], ratio: h[2], kind: h[3], site: h[4], town: h[6], cc: h[7] }));
      const list = pick(hs);
      sections.push(section("traffic", t("traffic"), t("trafficWhy"),
        t("trafficHow", { from: fmtDay(no2.days[0]), to: fmtDay(no2.days[no2.days.length - 1]) }),
        list.map((h, i) => card(i, h.kind === "traffic" ? h.site : `${h.site}`, `${t("kind_" + h.kind)} · ${h.town}`,
          `<b>${nf(h.ratio, { maximumFractionDigits: 1 })}×</b> ${esc(t("trafficEv"))}`, mapLink(h, "traffic", "", 10), h.cc))));
    }
    // Landfills
    sections.push(section("landfills", t("landfills"), t("landfillsWhy"), t("landfillsHow"), pick(data.landfills).map((x, i) => {
      const ev = [];
      if (x.rate) ev.push(`<b>${nf(x.rate)}</b> kg/h CH₄<small>${esc(t("methaneEv", { rate: nf(x.rate) }))} · ${esc(t("seenEv", { n: nf(x.plumes), pct: nf(x.persistence), first: year(x.first), last: year(x.last) }))}</small>`);
      if (x.heatDays) ev.push(`<small>🔥 ${esc(t("heatEv", { d: nf(x.heatDays) }))}</small>`);
      return card(i, x.unnamed ? t("unnamedLandfill", { place: x.near }) : x.name, loc(x), ev.join(""), mapLink(x, "", "plumes", 14), x.cc);
    })));
    // Plants
    sections.push(section("plants", t("plants"), t("plantsWhy"), t("plantsHow"), pick(data.plants).map((x, i) =>
      card(i, x.unnamed ? t("unnamedPlant", { place: x.near }) : x.name, `${t("fuel_" + x.kind)} · ${loc(x)}`,
        `<b>${nf(x.co2_t_h)}</b> t/h CO₂<small>${esc(t("co2Ev", { t: nf(x.co2_t_h) }))} · ${esc(t("seenEv", { n: nf(x.plumes), pct: nf(x.persistence), first: year(x.first), last: year(x.last) }))}</small>`,
        mapLink(x, "traffic", "plants", 13), x.cc))));
    // Always-hot sites
    sections.push(section("hot", t("hot"), t("hotWhy"), t("hotHow"), pick(data.hot).map((x, i) =>
      card(i, x.unnamed ? t("unnamedHot", { place: x.near }) : x.name, loc(x),
        `<b>${nf(x.days)}</b> ${esc(t("hotEv", { m: nf(x.months) }))}`, mapLink(x, "", "hotspots", 14), x.cc))));
    // Kiln belts
    sections.push(section("kilns", t("kilns"), t("kilnsWhy"), t("kilnsHow"), pick(data.kilnbelts).map((x, i) =>
      card(i, x.name, [x.state, country(x.cc)].filter(Boolean).join(", "),
        `<b>${nf(x.kilns)}</b> ${esc(t("kilnEv"))}<small>${esc(t("zigEv", { p: nf(x.zigzagPct) }))}${x.pm25_t_day ? " · " + esc(t("pmEv", { t: nf(x.pm25_t_day) })) : ""}</small>`,
        mapLink(x, "", "kilns", 10), x.cc))));

    document.getElementById("cats").innerHTML = sections.join("");
    document.getElementById("jump").innerHTML = ["traffic", "landfills", "plants", "hot", "kilns"]
      .filter((id) => document.getElementById(id)).map((id) => `<a href="#${id}">${esc(t(id))}</a>`).join("");
    // Collapse long lists to the first few cards
    document.querySelectorAll(".cat").forEach((sec) => {
      sec.querySelectorAll(".site").forEach((c, i) => { if (i >= SHOW) c.hidden = true; });
    });
    document.querySelectorAll("[data-more]").forEach((b) => b.addEventListener("click", () => {
      document.querySelectorAll(`#${b.dataset.more} .site`).forEach((c) => { c.hidden = false; });
      b.remove(); sketch();
    }));
    sketch();
  }

  function sketch() {
    if (!window.rough) { document.documentElement.classList.add("no-rough"); return; }
    document.querySelectorAll(".sketch").forEach((el, i) => {
      if (el.hidden) return;
      const w = el.clientWidth, h = el.clientHeight;
      if (!w || !h) return;
      el.querySelector(":scope > svg.rough")?.remove();
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("class", "rough"); svg.setAttribute("viewBox", `0 0 ${w} ${h}`); svg.setAttribute("aria-hidden", "true");
      svg.appendChild(rough.svg(svg).rectangle(1.5, 1.5, w - 3, h - 3, { roughness: 1, bowing: 0.8, stroke: "#2b2b2b", strokeWidth: 1.1, seed: 3 + i }));
      el.appendChild(svg);
    });
  }

  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
    lang = b.dataset.lang; try { localStorage.setItem("hh-lang", lang); } catch {} render();
  }));
  document.querySelectorAll("#ccChips button").forEach((b) => b.addEventListener("click", () => {
    cc = b.dataset.cc;
    document.querySelectorAll("#ccChips button").forEach((x) => x.classList.toggle("on", x === b));
    render();
  }));
  let rs; addEventListener("resize", () => { clearTimeout(rs); rs = setTimeout(sketch, 200); });

  render();
  Promise.all([
    fetch(`/sources/sites.json?v=${document.currentScript?.src.split("?v=")[1] || ""}`).then((r) => r.json()),
    fetch("/api/no2.json", { cache: "no-cache" }).then((r) => (r.ok ? r.json() : null)).catch(() => null),
  ]).then(([d, n]) => { data = d; no2 = n; render(); });
})();
