# Draft 6 → draft 7: audit change log (9 Nov 2026)

Draft 6 and its inputs are frozen in `frozen-draft6/` (PDF, article, meta, data.json, scripts, SHA-256 of every input file).
The claim ledger is `ledger.md`; every value is in `data.json` under the same id, rebuilt by `build_evidence.py`.

## Confirmed errors in draft 6, now fixed

1. **Fire geography.** 5,419 was all of Pakistan plus all of India, including southern and eastern states, not "Pakistan and northern India". The headline figure is now the two Punjabs: 2,859 spots. The chart, table, fact card and lede all use that basis.
2. **Season comparison.** This is now recomputed for the two Punjabs, on all satellites and on NOAA-20 alone, for October–November 2019–2026, from 467 archived day summaries. 8 Nov is still the busiest day of 2026 to date on every basis checked. Diwali was not the busiest day in any season from 2019 to 2025 on either basis. "So far" now appears in the title and throughout.
3. **"Indian Punjab more than tripled."** This is true on all satellites (501 → 1,716). On NOAA-20 alone the rise is +66% (208 → 346). Both are now stated.
4. **"Even though more satellites are counting now."** Removed. Suomi NPP stopped on 2 Nov 2026. The past-season comparison now uses NOAA-20 peaks (2019–22: 4,268–6,483; 2025: 911; 2026 so far: 931).
5. **Delhi: "independent vs government" split was wrong.** IQAir attributes:
   - 17 feeds to CPCB (these are the names ending "- DPCC" or "- IITM");
   - 10 unsuffixed feeds to DPCC;
   - 3 feeds to private contributors (Luca, TL, Daniel I).

   The "13 independent sensors" were 10 DPCC feeds plus 3 private ones. Corrected:
   - All 3 private sensors passed 1,000 on Sunday night.
   - 3 DPCC feeds passed 1,000 on Sunday night, and 4 passed it on Saturday night.
   - The CPCB-attributed feeds' night maxima were 192–198, in two clusters that are identical in at least 90% of hours (11 feeds and 5 feeds).
   - The claims that these feeds are "estimates" and that they "dominate the city average" were removed. The cause is unresolved.
6. **Delhi midday baseline.** "200–330" was wrong for the group as a whole: some DPCC feeds were at 551–720 at midday. The private sensors were at 209–222, and the text now says so.
7. **"City average."** IQAir's city figure is the median of station concentrations, so "average" is replaced with "city figure (median)" throughout.
8. **"Top of the US AQI scale" at 500.** Replaced with "AQI 500 = PM2.5 325.4 µg/m³". AQI 646 was recomputed from 398.5 µg/m³ using the EPA 2024 breakpoints.
9. **Forecast claim.** "Anyone checking a free forecast app on Sunday evening would have seen…" was removed. The CAMS series was retrieved on 9 Nov, and the run issued on 8 Nov was not recovered. The comparison is relabelled, and "in a Lahore winter it reads low" is now limited to the hours examined.
10. **Official warning existed.** Dunya News (8 Nov, 16:50 PKT) reports a Punjab EPD special report that warned of exactly this night. It is now reported, attributed to Dunya. The original bulletin was not found.
11. **Causal exclusions.** "Not fire counts alone", "Not stiller air", "Not humidity", "Not Lahore's own evening" and "That leaves…" were rewritten into a section separating what was measured, what the models suggest and the possible contributors.
12. **Partial-day ranking.** Monday's partial daily AQI 380 is no longer ranked against 2 Nov's complete-day 416.
13. **Transport.**
    - The 925 hPa path is labelled as such, not "about 800 m above Lahore". The night mixed layer was 28–51 m, so the upper path may be decoupled from the surface.
    - Arrivals at 00, 03, 06 and 09 PKT were added. All come from the east and had last been in India 2.5–4 h earlier.
    - Corridor sensitivity (10, 20 and 40 km) was added. The 42–47 range is no longer presented as an uncertainty range.
    - Sunday's 10 m path also had an Indian component; "from the north and west" was corrected.
14. **Station-level Lahore numbers were not reproducible.** Draft 6's per-station figures were computed in the browser, and the raw values were not kept.
    - All 52 station histories were re-captured at 16:40 UTC, while Sunday 9 am was still in IQAir's 48-hour window. The raw data is now retained.
    - Recomputed: 48 of 49 rose (Ravi Road was the exception); 26 doubled; the median went from 294 to 645; 39 were above 500.
    - Draft 6 said 48 of 48, 29, 651 and 41. The differences come from IQAir revisions between captures and from one extra station.
15. **"What would settle it."** Rewritten as "What could test it". Samples alone cannot apportion sources; some markers have other sources.
16. **PDF.** Fixed:
    - data.json links pointed to localhost;
    - card outlines crossed the text;
    - headings were orphaned;
    - there were no page numbers.

    The "Five cities in Pakistan's Punjab" chart, which includes Islamabad, was renamed.

## Checked and confirmed

- **Diwali date:** 8 Nov 2026, from India Post's holiday list.
- **Timestamp convention:** IQAir hover labels show "09:00–10:00" for the bar stored as "09:00". Stored labels are hour starts. The drawn tick labels sit one bar off, but that is a rendering quirk only.
- **Trajectory code:** it interpolates u/v components, not angles; the "from" convention and the backward sign are correct; times are UTC (timezone=GMT); the GFS model is gfs_seamless.
- **Values that did not change:** all the Lahore city-figure hourly values, the Multan, Faisalabad, Gujranwala and Islamabad figures, and the weather means.

## Unresolved, and qualified in the text

- **Delhi's CPCB-attributed feeds:** why they differ from the DPCC feeds for the same sites. Not checked against CPCB or DPCC records.
- **CAMS:** the run that was available on Sunday evening, and whether it included any fireworks emissions.
- **EPD warning:** the original bulletin and its issue time.
- **Delhi feeds:** station coordinates and instrument types are not shown on IQAir pages.
- **Past Diwali dates (2019–2025):** standard calendar dates, not re-checked against official notices.
- **Fire counts:** these are consistent with HamariHawa's own archive but have not been re-derived from NASA's raw rows for this report.
- **IQAir values:** these are platform-displayed values with no independent QA, and IQAir revises them. For example, Lahore at 9 am read 646 at the first capture and 648 later.

# Draft 7 → draft 8 (follow-up review, 9 Nov 2026)

1. **40 km fire corridor.** `traj.py` `along()` used a fixed 0.25° × 0.3° box that cut short the 40 km search. The box is now derived from R before the haversine test. The 9 am paths are now:
   - 10 m: 22 / 47 / 146 at 10 / 20 / 40 km;
   - 925 hPa: 19 / 42 / 146;
   - each 40 km total is 126 IN + 20 PK.

   Draft 7 said "about 95", which was wrong. The 10 km and 20 km figures are unchanged. The text now calls this a proximity screen.
2. **Border crossing.** The longitude ≥ 74.57 shortcut is replaced with the map's country polygons. The first backward sample inside India is 3–4.75 h before arrival; for the 9 am, 925 hPa path it is 04:45, not 06:00. The prose now says the paths "crossed from the Indian side during the preceding several hours".
3. **Times and labels.**
   - Ravi Road's peak of 457 is in the hour from 04:00, not 03:00.
   - "Doubled" is now "AQI+ readings at least twice as high", an index ratio.
   - City-figure peaks are given with their own times: Multan 700 at 02:00, Lahore 646 at 09:00, Faisalabad 612 at 11:00.
   - The Delhi chart's midnight and noon ticks now sit at the right fractional positions.
4. **Delhi similarity.** The figure is now calculated directly over the 13 overnight readings (18:30–06:30 IST): the 11-feed group matched in 12 of 13 and the 5-feed group in 13 of 13. Over the whole capture it is 37/46 and 41/47. The graph-clustering threshold is no longer presented as a measured agreement.
5. **Fire scopes.**
   - The whole-country NOAA-20 maximum now uses `sn[0]` (1,974), stored separately from the northern-plains box `snc[0]` (1,276). Both fall on 8 Nov.
   - The methods now say 2019–2025 come from SP processing and 2026 from NRT; 931 vs 911 is marked provisional.
   - "Within 400 m" is now "same ~400 m grid cell".
   - NOAA-20 gaps (e.g. 1 Oct 2023) are flagged, and maxima are described as "busiest recorded".
   - The chart note now reads: "The 2026 Diwali coincidence also holds using NOAA-20 alone."
6. **Prose.**
   - "The hotspot archive does not measure fireworks emissions."
   - Delhi readings are "consistent with a fireworks contribution".
   - "Around Lahore, the modelled winds turned…"
   - The unsupported "fireworks were set off on both sides of the border" became "it was Diwali night".
7. **PDF.**
   - The Urdu reference no longer splits across pages and the stray glyph is gone.
   - The season chart and the map now follow their text, so pages 2 and 7 are filled.
   - The season chart's footer is on two lines and no longer clipped.

Remaining limitations are as listed above, unchanged.
