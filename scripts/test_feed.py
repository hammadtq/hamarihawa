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
