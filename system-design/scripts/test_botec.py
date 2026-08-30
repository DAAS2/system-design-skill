"""Golden-value tests for botec.py. Run: python -m unittest test_botec -v"""

import io
import contextlib
import unittest

import botec


class TestMath(unittest.TestCase):
    def test_qps(self):
        self.assertAlmostEqual(botec.qps_from_events(86_400_000), 1_000.0)
        self.assertAlmostEqual(botec.qps_from_events(1_000_000), 11.574, places=3)

    def test_storage_flat(self):
        # 5M writes/day x 1000 B x 3x replication x 5 yr flat
        expected = 5_000_000 * 1000 * 365 * 5 * 3
        self.assertAlmostEqual(
            botec.storage_total(5_000_000, 1000, 5, 3.0, 1.0), expected)

    def test_storage_growth_compounds(self):
        # growth 2x/yr: year1=1, year2=2, year3=4 => 7x one year's worth
        base = 1_000_000 * 10 * 365 * 1
        got = botec.storage_total(1_000_000, 10, 3, 1.0, 2.0)
        self.assertAlmostEqual(got, base * 7)

    def test_bandwidth(self):
        # 10k rps x 10 KB = 100 MB/s = 800 Mbit/s
        self.assertAlmostEqual(botec.bandwidth(10_000, 10_000), 800e6)

    def test_human_bytes(self):
        self.assertEqual(botec.human_bytes(0), "0 B")
        self.assertEqual(botec.human_bytes(1024), "1.00 KiB")
        self.assertIn("GiB", botec.human_bytes(15_000_000_000))
        self.assertIn("TiB", botec.human_bytes(2.7375e13))


class TestCli(unittest.TestCase):
    def run_cmd(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = botec.main(list(argv))
        self.assertEqual(rc, 0)
        return buf.getvalue()

    def test_full_worksheet_golden(self):
        out = self.run_cmd(
            "full", "--dau", "1000000", "--reads-per-user", "50",
            "--writes-per-user", "5", "--write-size", "1000",
            "--read-size", "10000", "--peak-factor", "3")
        self.assertIn("578.7", out)       # avg read QPS
        self.assertIn("1,736.1", out)     # peak read QPS (x3)
        self.assertIn("57.9", out)        # avg write QPS
        self.assertIn("13.97 GiB", out)   # storage/day 3x replication
        self.assertIn("24.90 TiB", out)   # 5-yr storage
        self.assertIn("Decisions these numbers force:", out)

    def test_full_forces_cache_at_high_read(self):
        out = self.run_cmd(
            "full", "--dau", "10000000", "--reads-per-user", "200",
            "--writes-per-user", "2", "--peak-factor", "3")
        self.assertIn("cache layer is mandatory", out)

    def test_servers(self):
        out = self.run_cmd("servers", "--peak-rps", "100000", "--per-server-rps", "2000")
        self.assertIn("50", out)

    def test_cache(self):
        out = self.run_cmd("cache", "--objects-per-day", "5000000", "--bytes-per-object", "1000")
        self.assertIn("953.67 MiB", out)

    def test_nines_and_latency(self):
        self.assertIn("99.999", self.run_cmd("nines"))
        self.assertIn("Cross-region", self.run_cmd("latency"))


if __name__ == "__main__":
    unittest.main()
