"""
White Box Testing: CostEstimationController._is_peak()
=======================================================
Testing technique: Basis Path Testing (Control Flow)

System Under Test (SUT): backend.services.routing._is_peak()
Location: backend/services/routing.py:52

Source code:
    def _is_peak(dt: datetime) -> bool:
        wd = dt.weekday()          # 0=Mon..6=Sun
        h, m = dt.hour, dt.minute
        t = h * 60 + m
S1:     if wd < 5 and 360 <= t <= 569:    # Mon-Fri 6:00am-9:29am
            return True
S2:     if t >= 1020:                       # Mon-Sun 5:00pm-11:59pm
            return True
S3:     if wd >= 5 and 600 <= t <= 839:    # Sat-Sun 10:00am-1:59pm
            return True
        return False

Control Flow Graph (CFG):
=========================

    [START: compute wd, h, m, t]
              |
              v
    [D1: wd < 5 AND 360 <= t <= 569?]
         /          \\
       True         False
        |              |
        v              v
    [return True]   [D2: t >= 1020?]
                     /          \\
                   True         False
                    |              |
                    v              v
               [return True]   [D3: wd >= 5 AND 600 <= t <= 839?]
                                /          \\
                              True         False
                               |              |
                               v              v
                          [return True]   [return False]

Cyclomatic Complexity:
    V(G) = E - N + 2 = 8 - 7 + 2 = 3
    OR: V(G) = number of decision points + 1 = 3 + 1 = 4
    (Note: each compound condition counts as one decision point here
     since Python short-circuits the entire `if` as one branch)

    Actually, let's count properly:
    - 3 decision points (D1, D2, D3)
    - V(G) = 3 + 1 = 4

Basis Paths (4 linearly independent paths):
    Path 1: START -> D1(True) -> return True
    Path 2: START -> D1(False) -> D2(True) -> return True
    Path 3: START -> D1(False) -> D2(False) -> D3(True) -> return True
    Path 4: START -> D1(False) -> D2(False) -> D3(False) -> return False

Test Cases (one per basis path):
    Path 1: wd=1 (Tue), t=480 (8:00am)    -> True  (weekday morning peak)
    Path 2: wd=1 (Tue), t=1080 (6:00pm)   -> True  (evening peak)
    Path 3: wd=5 (Sat), t=720 (12:00pm)   -> True  (weekend midday)
    Path 4: wd=1 (Tue), t=840 (2:00pm)    -> False  (off-peak)
"""

import unittest
from datetime import datetime, timezone, timedelta

from backend.services.routing import _is_peak

SGT = timezone(timedelta(hours=8))


class TestIsPeakBasisPaths(unittest.TestCase):
    """White box tests: one test case per basis path through _is_peak()."""

    def test_path1_weekday_morning_peak(self):
        """
        Path 1: START -> D1(True) -> return True
        Input:  Tuesday 8:00am (wd=1, t=480)
        Path:   D1: wd<5=True AND 360<=480<=569=True -> return True
        Oracle: True
        """
        dt = datetime(2026, 4, 14, 8, 0, tzinfo=SGT)  # Tuesday
        self.assertTrue(_is_peak(dt))

    def test_path2_evening_peak(self):
        """
        Path 2: START -> D1(False) -> D2(True) -> return True
        Input:  Tuesday 6:00pm (wd=1, t=1080)
        Path:   D1: wd<5=True BUT 360<=1080<=569=False -> D2: 1080>=1020=True -> return True
        Oracle: True
        """
        dt = datetime(2026, 4, 14, 18, 0, tzinfo=SGT)  # Tuesday
        self.assertTrue(_is_peak(dt))

    def test_path3_weekend_midday_peak(self):
        """
        Path 3: START -> D1(False) -> D2(False) -> D3(True) -> return True
        Input:  Saturday 12:00pm (wd=5, t=720)
        Path:   D1: wd<5=False -> D2: 720>=1020=False -> D3: wd>=5=True AND 600<=720<=839=True -> return True
        Oracle: True
        """
        dt = datetime(2026, 4, 18, 12, 0, tzinfo=SGT)  # Saturday
        self.assertTrue(_is_peak(dt))

    def test_path4_off_peak(self):
        """
        Path 4: START -> D1(False) -> D2(False) -> D3(False) -> return False
        Input:  Tuesday 2:00pm (wd=1, t=840)
        Path:   D1: wd<5=True BUT 360<=840<=569=False -> D2: 840>=1020=False -> D3: wd>=5=False -> return False
        Oracle: False
        """
        dt = datetime(2026, 4, 14, 14, 0, tzinfo=SGT)  # Tuesday
        self.assertFalse(_is_peak(dt))


class TestIsPeakBranchCoverage(unittest.TestCase):
    """Additional tests to achieve 100% branch coverage."""

    def test_weekday_just_before_morning_peak(self):
        """Branch: D1 false due to t < 360 (weekday 5:59am)."""
        dt = datetime(2026, 4, 14, 5, 59, tzinfo=SGT)
        # 5:59am = 359 min, not in morning peak, not evening, not weekend
        # But hour < 6 so it's actually not late_night in _is_peak context
        # t=359 < 360: D1 false, t=359 < 1020: D2 false, wd<5: D3 false
        self.assertFalse(_is_peak(dt))

    def test_weekday_just_after_morning_peak(self):
        """Branch: D1 false due to t > 569 (weekday 9:30am)."""
        dt = datetime(2026, 4, 14, 9, 30, tzinfo=SGT)  # t = 570
        self.assertFalse(_is_peak(dt))

    def test_weekend_off_peak_morning(self):
        """Branch: D3 false due to t < 600 (Saturday 9:00am)."""
        dt = datetime(2026, 4, 18, 9, 0, tzinfo=SGT)  # Saturday, t=540
        self.assertFalse(_is_peak(dt))

    def test_weekend_off_peak_afternoon(self):
        """Branch: D3 false due to t > 839 (Saturday 2:00pm)."""
        dt = datetime(2026, 4, 18, 14, 0, tzinfo=SGT)  # Saturday, t=840
        # t=840 < 1020 so D2 false, wd>=5 but t > 839 so D3 false
        self.assertFalse(_is_peak(dt))

    def test_weekend_evening_peak(self):
        """Branch: Weekend evening is still peak via D2 (Saturday 6pm)."""
        dt = datetime(2026, 4, 18, 18, 0, tzinfo=SGT)  # Saturday, t=1080
        self.assertTrue(_is_peak(dt))

    def test_sunday(self):
        """Branch: Sunday midday via D3 (Sunday 11am)."""
        dt = datetime(2026, 4, 19, 11, 0, tzinfo=SGT)  # Sunday, t=660
        self.assertTrue(_is_peak(dt))

    def test_midnight(self):
        """Branch: Midnight (t=0) is off-peak for _is_peak."""
        dt = datetime(2026, 4, 14, 0, 0, tzinfo=SGT)
        self.assertFalse(_is_peak(dt))


if __name__ == "__main__":
    unittest.main()
