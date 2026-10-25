#!/usr/bin/env python3
"""Tests for build-feed.py's write budget and tiers. Run: python3 -I scripts/test_feed.py"""
import importlib.util, os, unittest

spec = importlib.util.spec_from_file_location("bf", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build-feed.py"))
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)


class PublisherTest(unittest.TestCase):
    def test_unchanged_values_are_skipped(self):
        pub = bf.Publisher(False, {}, "")
        self.assertTrue(pub.put("a", b"1"))
        self.assertFalse(pub.put("a", b"1"))
        self.assertTrue(pub.put("a", b"2"))
        self.assertEqual(pub.state["writes"], 2)

    def test_same_part_decides(self):
        pub = bf.Publisher(False, {}, "")
        self.assertTrue(pub.put("f", b"gen=1;x", b"x"))
        self.assertFalse(pub.put("f", b"gen=2;x", b"x"))

    def test_limit_keeps_one_write_for_state(self):
        pub = bf.Publisher(False, {}, "")
        pub.state["writes"] = bf.Publisher.LIMIT - 2
        self.assertTrue(pub.put("a", b"1"))
        self.assertFalse(pub.put("b", b"1"))
        self.assertEqual(pub.skipped, ["b"])

    def test_new_utc_day_resets_count(self):
        pub = bf.Publisher(False, {"wday": "2000-01-01", "writes": 849}, "")
        self.assertEqual(pub.state["writes"], 0)


class TiersTest(unittest.TestCase):
    def test_first_run_publishes_both(self):
        self.assertEqual(bf.tiers_due({}, "r1", 10_000, "2026-10-23"), (True, True))

    def test_unchanged_source_publishes_nothing(self):
        st = {"tiers": {"fast": {"src": "r1", "at": 0}, "slow": {"src": "r1", "at": 0, "pkday": "2026-10-23"}}}
        self.assertEqual(bf.tiers_due(st, "r1", 10_000, "2026-10-23"), (False, False))

    def test_intervals(self):
        st = {"tiers": {"fast": {"src": "r1", "at": 0}, "slow": {"src": "r1", "at": 0, "pkday": "d"}}}
        self.assertEqual(bf.tiers_due(st, "r2", bf.FAST - 1, "d"), (False, False))
        self.assertEqual(bf.tiers_due(st, "r2", bf.FAST, "d"), (True, False))
        self.assertEqual(bf.tiers_due(st, "r2", bf.SLOW, "d"), (True, True))

    def test_slow_tier_not_stranded(self):
        # The fast tier saw r2 first; a later run with no new NASA data must still let the hourly tier publish r2.
        st = {"tiers": {"fast": {"src": "r2", "at": 3000}, "slow": {"src": "r1", "at": 0, "pkday": "d"}}}
        self.assertEqual(bf.tiers_due(st, "r2", 3600, "d"), (False, True))

    def test_pakistan_midnight_closes_the_day(self):
        st = {"tiers": {"fast": {"src": "r1", "at": 0}, "slow": {"src": "r1", "at": 0, "pkday": "2026-10-23"}}}
        self.assertEqual(bf.tiers_due(st, "r1", 10_000, "2026-10-24"), (False, True))


def pt(si, t, lat, lon, night=False):
    return {"si": si, "sat": bf.SOURCES[si][1], "t": t, "lat": lat, "lon": lon, "night": night, "frp": 1.0, "conf": "nominal"}


class BurstFilterTest(unittest.TestCase):
    T = 1_760_000_000_000

    def burst(self):
        # 60 Suomi NPP daytime detections in one Thar cell (27N 72E) within a few minutes.
        return [pt(0, self.T + i * 1000, 27.2 + (i % 10) * 0.05, 72.2 + (i // 10) * 0.1) for i in range(60)]

    def test_unwitnessed_burst_is_kept(self):
        pts = self.burst()
        self.assertEqual(len(bf.drop_bursts(pts)), 60)

    def test_burst_dropped_when_another_satellite_saw_the_area(self):
        # NOAA-20 flew over the same area 40 min later and saw one fire nearby, nothing in the cell.
        pts = self.burst() + [pt(1, self.T + 40 * 60000, 29.5, 73.5)]
        self.assertEqual(len(bf.drop_bursts(pts)), 1)

    def test_far_away_detection_is_not_a_witness(self):
        # NOAA-20 at the same longitude but over southern India (12.5N) must not count as having seen the Thar.
        pts = self.burst() + [pt(1, self.T + 40 * 60000, 12.5, 73.5)]
        self.assertEqual(len(bf.drop_bursts(pts)), 61)

    def test_outside_the_thar_is_never_checked(self):
        pts = [pt(0, self.T + i * 1000, 30.2 + (i % 10) * 0.05, 75.2 + (i // 10) * 0.1) for i in range(60)]
        pts.append(pt(1, self.T + 40 * 60000, 31.5, 76.5))
        self.assertEqual(len(bf.drop_bursts(pts)), 61)


class CountryTest(unittest.TestCase):
    def test_plain_cases(self):
        for lat, lon, want in ((31.55, 74.34, "PK"), (31.63, 74.87, "IN"), (24.86, 67.0, "PK"), (13.08, 80.27, "IN"),
                               (27.72, 85.32, None), (23.81, 90.41, None), (29.08, 88.01, None), (20.0, 65.0, None)):
            self.assertEqual(bf.country_of(lat, lon), want, (lat, lon))

    def test_border_near_firozpur_is_india(self):
        # Fires the old code named after villages across the border in Kasur (checked against OpenStreetMap).
        self.assertEqual(bf.country_of(31.3648, 74.5988), "IN")

    def test_kashmir_follows_who_administers_it(self):
        # India's outline covers all of Jammu and Kashmir and Ladakh; Pakistan's covers Azad Kashmir and
        # Gilgit-Baltistan. Where both claim the ground, the nearest village's country decides.
        self.assertEqual(bf.country_of(34.08, 74.80), "IN")      # Srinagar
        self.assertEqual(bf.country_of(34.37, 73.47), "PK+IN")   # Muzaffarabad
        csv = "latitude,longitude,acq_date,acq_time,confidence,frp,daynight\n"
        for lat, lon in ((34.37, 73.47), (33.98, 73.77), (34.08, 74.80), (33.15, 73.75)):
            csv += f"{lat},{lon},2026-10-20,0800,n,5.0,D\n"
        got = {(round(p["lat"], 2), round(p["lon"], 2)): (p["cc"], p["state"]) for p in bf.build(24, [csv, None, None, None])["_all"]}
        self.assertEqual(got[(34.37, 73.47)][0], "PK")   # Muzaffarabad
        self.assertEqual(got[(33.98, 73.77)][0], "PK")   # Bagh
        self.assertEqual(got[(33.15, 73.75)][0], "PK")   # Mirpur
        self.assertEqual(got[(34.08, 74.8)][0], "IN")    # Srinagar

    def test_whole_region_and_neighbours(self):
        csv = "latitude,longitude,acq_date,acq_time,confidence,frp,daynight\n"
        for lat, lon in ((35.92, 74.31), (19.08, 72.88), (8.09, 77.54), (25.12, 62.33), (27.70, 85.32), (23.81, 90.41), (6.93, 79.86)):
            csv += f"{lat},{lon},2026-10-20,0800,n,5.0,D\n"
        got = {(round(p["lat"], 2), round(p["lon"], 2)): p["cc"] for p in bf.build(24, [csv, None, None, None])["_all"]}
        self.assertEqual(got, {(35.92, 74.31): "PK", (19.08, 72.88): "IN", (8.09, 77.54): "IN", (25.12, 62.33): "PK"})  # Gilgit, Mumbai, Kanyakumari, Gwadar


class ComparisonTest(unittest.TestCase):
    def test_snc_counts_only_the_northern_box(self):
        csv = "latitude,longitude,acq_date,acq_time,confidence,frp,daynight\n"
        for lat, lon in ((31.40, 74.20), (31.60, 75.10), (19.08, 72.88)):  # Kasur, Amritsar, Mumbai
            csv += f"{lat},{lon},2026-10-20,0800,n,5.0,D\n"
        s = bf.day_files(bf.build(24, [csv, None, None, None])["_all"])["2026-10-20"]["summary"]
        self.assertEqual(s["sn"], [3, 1, 2, 0, 0, 0])
        self.assertEqual(s["snc"], [2, 1, 1, 0, 0, 0])
        self.assertNotIn("states", bf.index_entry(s, False))
        self.assertIn("snc", bf.index_entry(s, False))

    def test_districts_outside_the_box_have_no_year_comparison(self):
        days = [f"2026-10-{d:02d}" for d in range(1, 26)]
        rows = [["Okara", "Punjab", "PK", 30, 30.8, 73.4, 10, 10], ["Angul", "Odisha", "IN", 30, 20.8, 85.1, 0, 10]]
        dist = {x: rows for x in days}
        dist["2026-10-01"] = [r[:7] for r in rows]  # one day from before the rebuild
        d = bf.district_index({x: {"spots": 1} for x in days}, dist)["d"]
        self.assertEqual(d["okara"]["s"]["2026"][0], 250)  # box counts: 25 days x 10
        self.assertIsNone(d["angul"]["s"]["2026"][0])
        self.assertEqual(d["angul"]["s"]["2026"][2], 750)


class SlugTest(unittest.TestCase):
    def _dist(self, rows):
        days = [f"2025-10-{d:02d}" for d in range(1, 26)]
        return {d: {"spots": 1} for d in days}, {d: rows for d in days}

    def test_existing_slug_survives_a_new_namesake(self):
        index, dist = self._dist([["Hyderabad", "Sindh", "PK", 30, 25.4, 68.4, 10]])
        first = bf.district_index(index, dist)
        self.assertIn("hyderabad", first["d"])
        index, dist = self._dist([["Hyderabad", "Sindh", "PK", 30, 25.4, 68.4, 10], ["Hyderabad", "Telangana", "IN", 30, 17.4, 78.5, 10]])
        self.assertEqual(sorted(bf.district_index(index, dist)["d"]), ["hyderabad-sindh", "hyderabad-telangana"])
        got = bf.district_index(index, dist, first)["d"]
        self.assertEqual(got["hyderabad"]["state"], "Sindh")
        self.assertEqual(got["hyderabad-telangana"]["state"], "Telangana")


class WindowTest(unittest.TestCase):
    def test_24h_feed_is_cut_to_24_hours(self):
        """NASA's "24 h" file can hold 36 hours; the feed keeps only the 24 up to the newest detection."""
        head = "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        rows = [f"30.{i:02d}1,73.{i:02d}1,330,0.4,0.4,{d},{t},N,VIIRS,n,2.0NRT,290,5,D\n"
                for i, (d, t) in enumerate([("2026-10-23", "0800"), ("2026-10-24", "0800"), ("2026-10-24", "2000")])]
        f = bf.build(24, [head + "".join(rows), None, None, None])
        self.assertEqual(len(f["_all"]), 2)


class RebuildTest(unittest.TestCase):
    days = [f"2025-10-{d:02d}" for d in range(1, 26)]

    def test_renamed_district_gets_an_alias(self):
        old = bf.district_index({d: {} for d in self.days}, {d: [["District Jalaun", "Uttar Pradesh", "IN", 30, 26.1, 79.4, 5]] for d in self.days})
        self.assertIn("district-jalaun", old["d"])
        new = bf.district_index({d: {} for d in self.days}, {d: [["Jalaun", "Uttar Pradesh", "IN", 30, 26.1, 79.4, 5, 5]] for d in self.days}, old)
        self.assertEqual(new["alias"], {"district-jalaun": "jalaun"})
        again = bf.district_index({d: {} for d in self.days}, {d: [["Jalaun", "Uttar Pradesh", "IN", 30, 26.1, 79.4, 5, 5]] for d in self.days},
                                  bf.split_dpages(new)[0])
        self.assertEqual(again["alias"], {"district-jalaun": "jalaun"})  # kept on later runs

    def test_alias_survives_a_rebuild_in_parts(self):
        idx = {d: {} for d in self.days}
        both = bf.district_index(idx, {d: [["District Jalaun", "Uttar Pradesh", "IN", 30, 26.1, 79.4, 5],
                                           ["Jalaun", "Uttar Pradesh", "IN", 30, 26.1, 79.4, 5, 5]] for d in self.days},
                                 bf.split_dpages(bf.district_index(idx, {d: [["District Jalaun", "Uttar Pradesh", "IN", 30, 26.1, 79.4, 5]] for d in self.days}))[0])
        self.assertIn("district-jalaun", both["d"])
        self.assertIn("jalaun", both["d"])
        after = bf.district_index(idx, {d: [["Jalaun", "Uttar Pradesh", "IN", 30, 26.1, 79.4, 5, 5]] for d in self.days}, bf.split_dpages(both)[0])
        self.assertEqual(after["alias"], {"district-jalaun": "jalaun"})

    def test_whole_district_counts_once_rebuilt(self):
        rows = [["Angul", "Odisha", "IN", 30, 20.8, 85.1, 0, 10]]
        d = bf.district_index({x: {"snc": [1] * 6} for x in self.days}, {x: rows for x in self.days})["d"]
        self.assertEqual(d["angul"]["s"]["2025"][0], 250)

    def test_no_whole_district_while_a_season_day_is_old(self):
        rows = [["Angul", "Odisha", "IN", 30, 20.8, 85.1, 0, 10]]
        idx = {x: {"snc": [1] * 6} for x in self.days}
        idx[self.days[0]] = {}
        d = bf.district_index(idx, {x: rows for x in self.days})["d"]
        self.assertIsNone(d["angul"]["s"]["2025"][0])


class CitySmokeTest(unittest.TestCase):
    def test_bins_distance_and_slugs(self):
        lahore = next(c for c in bf.CITIES if c["id"] == "lahore")
        lat, lon = lahore["lat"], lahore["lon"]
        fire = lambda dlat, dlon, kind="crop", d="Sheikhupura": {"lat": lat + dlat, "lon": lon + dlon, "t": 1000,
                                                                 "district": d, "state": "Punjab", "cc": "PK", "kind": kind}
        north = [fire(0.9, 0), fire(0.9, 0, "town")]       # ~100 km due north: bin 0
        east = [fire(0, 1.0, d="Kasur")]                   # ~95 km east (initial bearing just under 90): bin 17
        far, close = fire(3.0, 0), fire(0.001, 0)          # ~330 km and ~0.1 km: both left out, as the cards do
        dp = {"d": {"sheikhupura": {"name": "Sheikhupura", "state": "Punjab", "cc": "PK"}}}
        out = bf.city_smoke(north + east + [far, close], north, dp, 1)
        c = out["cities"]["lahore"]
        rows = {(out["districts"][r[0]][0], r[1]): r[2:] for r in c["a"]}
        self.assertEqual(rows[("Sheikhupura", 0)][:2], [2, 1])
        self.assertEqual(rows[("Kasur", 17)][:2], [1, 1])
        self.assertEqual(len(c["a"]), 2)
        self.assertAlmostEqual(rows[("Sheikhupura", 0)][2], 100, delta=3)
        self.assertEqual(out["districts"][c["w"][0][0]], ["Sheikhupura", "Punjab", "PK", "sheikhupura"])
        self.assertEqual(c["w"][0][1:3], [2, 1])
        self.assertEqual(c["n7"], 2)
        self.assertEqual(out["latest"], 1000)


class BudgetSimulation(unittest.TestCase):
    def test_a_busy_day_stays_under_budget(self):
        """192 runs a day (GitHub's schedule plus the Worker's dispatch), NASA's files changing on 57 of them
        (as measured on 23 Oct 2026). Fast tier: fires-24-v2, kml-24 and cities. Slow tier: 8 keys plus about
        14 district shards once a day."""
        st, writes, day = {}, 0, "d"
        changes = set(range(0, 192, 192 // 57 + 1)) | {5, 6, 7}
        rev = 0
        for run in range(192):
            now = run * 450
            if run in changes:
                rev += 1
            fast, slow = bf.tiers_due(st, f"r{rev}", now, day)
            n = (3 if fast else 0) + (8 if slow else 0)
            if run == 40 and slow:
                n += 15
            if n:
                writes += n + 1  # the state key
            for name, ran in (("fast", fast), ("slow", slow)):
                if ran:
                    st.setdefault("tiers", {})[name] = {"src": f"r{rev}", "at": now, "pkday": day}
        self.assertLess(writes, 500, writes)
        print(f"\n  simulated day: {writes} KV writes")


if __name__ == "__main__":
    unittest.main(verbosity=1)
