import unittest

from backend.services.scoring import normalize, composite_score, tie_break_key


class TestScoring(unittest.TestCase):
    def test_normalize_basic(self):
        vals = [10, 20, 30]
        n = normalize(vals)
        self.assertEqual(n[0], 0.0)
        self.assertEqual(n[-1], 1.0)

    def test_normalize_identical(self):
        vals = [5, 5, 5]
        n = normalize(vals)
        self.assertEqual(n, [0.0, 0.0, 0.0])

    def test_composite_score_equal_weights(self):
        # time=0.0, reliability=0.5, crowding=1.0, budget=0.0
        norm = {"time": 0.0, "reliability": 0.5, "crowding": 1.0, "budget": 0.0}
        weights = {"time": 0.25, "reliability": 0.25, "crowding": 0.25, "budget": 0.25}
        s = composite_score(norm, weights)
        self.assertAlmostEqual(s, 0.375, places=6)

    def test_tie_breaker(self):
        a = {"risk_delay_num": 1, "risk_crowding_num": 2, "transfers": 1, "time_min": 20, "cost_est": 10}
        b = {"risk_delay_num": 2, "risk_crowding_num": 1, "transfers": 0, "time_min": 10, "cost_est": 5}
        self.assertLess(tie_break_key(a), tie_break_key(b))


if __name__ == "__main__":
    unittest.main()
