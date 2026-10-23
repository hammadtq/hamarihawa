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


class BudgetSimulation(unittest.TestCase):
    def test_a_busy_day_stays_under_budget(self):
        """192 runs a day (GitHub's schedule plus the Worker's dispatch), NASA's files changing on 57 of them
        (as measured on 23 Oct 2026). Slow tier: 8 keys plus about 14 district shards once a day."""
        st, writes, day = {}, 0, "d"
        changes = set(range(0, 192, 192 // 57 + 1)) | {5, 6, 7}
        rev = 0
        for run in range(192):
            now = run * 450
            if run in changes:
                rev += 1
            fast, slow = bf.tiers_due(st, f"r{rev}", now, day)
            n = (2 if fast else 0) + (8 if slow else 0)
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
