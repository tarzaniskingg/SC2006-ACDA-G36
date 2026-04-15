"""
White Box Testing: RiskAssessmentController._time_based_crowding()
==================================================================
Testing technique: Basis Path Testing (Control Flow)

System Under Test (SUT): backend.services.assessment._time_based_crowding()
Location: backend/services/assessment.py:227

Source code:
    def _time_based_crowding(query_time=None) -> str:
        SGT = timezone(timedelta(hours=8))
        dt = query_time or datetime.now(SGT)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=SGT)
        else:
            dt = dt.astimezone(SGT)
        h, m = dt.hour, dt.minute
        t = h * 60 + m
        wd = dt.weekday()
S1:     if wd < 5:                          # Weekday
S2:         if 420 <= t <= 570:             #   Morning peak 7:00-9:30
                return "High"
S3:         if 1050 <= t <= 1200:           #   Evening peak 5:30-8:00
                return "High"
S4:         if (360<=t<420) or (570<t<=630) or (990<=t<1050) or (1200<t<=1260):
                return "Medium"             #   Shoulder periods
            return "Low"
        else:                               # Weekend
S5:         if 660 <= t <= 1080:            #   Midday busy 11am-6pm
                return "Medium"
            return "Low"

Control Flow Graph (CFG):
=========================

    [START: compute dt, t, wd]
              |
              v
    [D1: wd < 5? (weekday)]
         /          \\
       True         False
        |              |
        v              v
    [D2: 420<=t<=570?]   [D5: 660<=t<=1080?]
     /        \\          /          \\
   True      False     True         False
    |          |        |              |
    v          v        v              v
 [ret High] [D3: 1050<=t<=1200?]  [ret Med]  [ret Low]
             /        \\
           True      False
            |          |
            v          v
         [ret High] [D4: shoulder?]
                     /        \\
                   True      False
                    |          |
                    v          v
                 [ret Med]  [ret Low]

Cyclomatic Complexity:
    Decision points: D1, D2, D3, D4, D5 = 5
    V(G) = 5 + 1 = 6
    (D4 is a compound condition with 4 OR clauses, but as a single
     if-statement it counts as one decision point for basis paths)

Basis Paths (6 linearly independent paths):
    Path 1: START -> D1(T) -> D2(T) -> return "High"
    Path 2: START -> D1(T) -> D2(F) -> D3(T) -> return "High"
    Path 3: START -> D1(T) -> D2(F) -> D3(F) -> D4(T) -> return "Medium"
    Path 4: START -> D1(T) -> D2(F) -> D3(F) -> D4(F) -> return "Low"
    Path 5: START -> D1(F) -> D5(T) -> return "Medium"
    Path 6: START -> D1(F) -> D5(F) -> return "Low"

Test Cases (one per basis path):
    Path 1: wd=1 (Tue), t=480 (8:00am)    -> "High"   (weekday morning peak)
    Path 2: wd=1 (Tue), t=1100 (6:20pm)   -> "High"   (weekday evening peak)
    Path 3: wd=1 (Tue), t=600 (10:00am)   -> "Medium" (weekday shoulder)
    Path 4: wd=1 (Tue), t=840 (2:00pm)    -> "Low"    (weekday off-peak)
    Path 5: wd=5 (Sat), t=720 (12:00pm)   -> "Medium" (weekend midday)
    Path 6: wd=5 (Sat), t=540 (9:00am)    -> "Low"    (weekend off-peak)
"""

import unittest
from datetime import datetime, timezone, timedelta

from backend.services.assessment import _time_based_crowding

SGT = timezone(timedelta(hours=8))


class TestTimeBasedCrowdingBasisPaths(unittest.TestCase):
    """White box tests: one test case per basis path through _time_based_crowding()."""

    def test_path1_weekday_morning_peak(self):
        """
        Path 1: START -> D1(True) -> D2(True) -> return "High"
        Input:  Tuesday 8:00am (wd=1, t=480)
        Path:   D1: 1<5=True -> D2: 420<=480<=570=True -> return "High"
        Oracle: "High"
        """
        dt = datetime(2026, 4, 14, 8, 0, tzinfo=SGT)  # Tuesday
        self.assertEqual(_time_based_crowding(dt), "High")

    def test_path2_weekday_evening_peak(self):
        """
        Path 2: START -> D1(True) -> D2(False) -> D3(True) -> return "High"
        Input:  Tuesday 6:20pm (wd=1, t=1100)
        Path:   D1: True -> D2: 420<=1100<=570=False -> D3: 1050<=1100<=1200=True -> return "High"
        Oracle: "High"
        """
        dt = datetime(2026, 4, 14, 18, 20, tzinfo=SGT)  # Tuesday
        self.assertEqual(_time_based_crowding(dt), "High")

    def test_path3_weekday_shoulder_period(self):
        """
        Path 3: START -> D1(True) -> D2(False) -> D3(False) -> D4(True) -> return "Medium"
        Input:  Tuesday 10:00am (wd=1, t=600)
        Path:   D1: True -> D2: False -> D3: 1050<=600=False -> D4: 570<600<=630=True -> return "Medium"
        Oracle: "Medium"
        """
        dt = datetime(2026, 4, 14, 10, 0, tzinfo=SGT)  # Tuesday
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_path4_weekday_off_peak(self):
        """
        Path 4: START -> D1(True) -> D2(False) -> D3(False) -> D4(False) -> return "Low"
        Input:  Tuesday 2:00pm (wd=1, t=840)
        Path:   D1: True -> D2: False -> D3: False -> D4: not in any shoulder range -> return "Low"
        Oracle: "Low"
        """
        dt = datetime(2026, 4, 14, 14, 0, tzinfo=SGT)  # Tuesday
        self.assertEqual(_time_based_crowding(dt), "Low")

    def test_path5_weekend_midday(self):
        """
        Path 5: START -> D1(False) -> D5(True) -> return "Medium"
        Input:  Saturday 12:00pm (wd=5, t=720)
        Path:   D1: 5<5=False -> D5: 660<=720<=1080=True -> return "Medium"
        Oracle: "Medium"
        """
        dt = datetime(2026, 4, 18, 12, 0, tzinfo=SGT)  # Saturday
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_path6_weekend_off_peak(self):
        """
        Path 6: START -> D1(False) -> D5(False) -> return "Low"
        Input:  Saturday 9:00am (wd=5, t=540)
        Path:   D1: 5<5=False -> D5: 660<=540=False -> return "Low"
        Oracle: "Low"
        """
        dt = datetime(2026, 4, 18, 9, 0, tzinfo=SGT)  # Saturday
        self.assertEqual(_time_based_crowding(dt), "Low")


class TestTimeBasedCrowdingBranchCoverage(unittest.TestCase):
    """Additional tests for 100% branch coverage of all shoulder sub-conditions."""

    # ---------------------------------------------------------------
    # Shoulder period sub-conditions in D4
    # ---------------------------------------------------------------

    def test_shoulder_early_morning(self):
        """D4 sub-condition 1: 360 <= t < 420 (6:00-6:59am weekday)."""
        dt = datetime(2026, 4, 14, 6, 30, tzinfo=SGT)  # t=390
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_shoulder_post_morning(self):
        """D4 sub-condition 2: 570 < t <= 630 (9:31-10:30am weekday)."""
        dt = datetime(2026, 4, 14, 10, 15, tzinfo=SGT)  # t=615
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_shoulder_pre_evening(self):
        """D4 sub-condition 3: 990 <= t < 1050 (4:30-5:29pm weekday)."""
        dt = datetime(2026, 4, 14, 16, 45, tzinfo=SGT)  # t=1005
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_shoulder_post_evening(self):
        """D4 sub-condition 4: 1200 < t <= 1260 (8:01-9:00pm weekday)."""
        dt = datetime(2026, 4, 14, 20, 30, tzinfo=SGT)  # t=1230
        self.assertEqual(_time_based_crowding(dt), "Medium")

    # ---------------------------------------------------------------
    # Boundary values for each decision point
    # ---------------------------------------------------------------

    def test_bv_morning_peak_start(self):
        """BV D2: t=419 (6:59am) = not morning peak."""
        dt = datetime(2026, 4, 14, 6, 59, tzinfo=SGT)  # t=419
        # 419 < 420 so D2 false; 360<=419<420 so D4 true -> Medium
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_bv_morning_peak_on_lower(self):
        """BV D2: t=420 (7:00am) = morning peak starts."""
        dt = datetime(2026, 4, 14, 7, 0, tzinfo=SGT)  # t=420
        self.assertEqual(_time_based_crowding(dt), "High")

    def test_bv_morning_peak_on_upper(self):
        """BV D2: t=570 (9:30am) = morning peak ends."""
        dt = datetime(2026, 4, 14, 9, 30, tzinfo=SGT)  # t=570
        self.assertEqual(_time_based_crowding(dt), "High")

    def test_bv_morning_peak_just_after(self):
        """BV D2: t=571 (9:31am) = shoulder period."""
        dt = datetime(2026, 4, 14, 9, 31, tzinfo=SGT)  # t=571
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_bv_evening_peak_just_before(self):
        """BV D3: t=1049 (5:29pm) = shoulder, not evening peak."""
        dt = datetime(2026, 4, 14, 17, 29, tzinfo=SGT)  # t=1049
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_bv_evening_peak_on_lower(self):
        """BV D3: t=1050 (5:30pm) = evening peak starts."""
        dt = datetime(2026, 4, 14, 17, 30, tzinfo=SGT)  # t=1050
        self.assertEqual(_time_based_crowding(dt), "High")

    def test_bv_evening_peak_on_upper(self):
        """BV D3: t=1200 (8:00pm) = evening peak ends."""
        dt = datetime(2026, 4, 14, 20, 0, tzinfo=SGT)  # t=1200
        self.assertEqual(_time_based_crowding(dt), "High")

    def test_bv_evening_peak_just_after(self):
        """BV D3: t=1201 (8:01pm) = shoulder period."""
        dt = datetime(2026, 4, 14, 20, 1, tzinfo=SGT)  # t=1201
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_bv_weekend_midday_just_before(self):
        """BV D5: t=659 (10:59am Sat) = weekend off-peak."""
        dt = datetime(2026, 4, 18, 10, 59, tzinfo=SGT)  # Saturday, t=659
        self.assertEqual(_time_based_crowding(dt), "Low")

    def test_bv_weekend_midday_on_lower(self):
        """BV D5: t=660 (11:00am Sat) = weekend midday starts."""
        dt = datetime(2026, 4, 18, 11, 0, tzinfo=SGT)  # Saturday, t=660
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_bv_weekend_midday_on_upper(self):
        """BV D5: t=1080 (6:00pm Sat) = weekend midday ends."""
        dt = datetime(2026, 4, 18, 18, 0, tzinfo=SGT)  # Saturday, t=1080
        self.assertEqual(_time_based_crowding(dt), "Medium")

    def test_bv_weekend_midday_just_after(self):
        """BV D5: t=1081 (6:01pm Sat) = weekend off-peak."""
        dt = datetime(2026, 4, 18, 18, 1, tzinfo=SGT)  # Saturday, t=1081
        self.assertEqual(_time_based_crowding(dt), "Low")

    # ---------------------------------------------------------------
    # Edge cases: timezone handling
    # ---------------------------------------------------------------

    def test_none_input_uses_current_time(self):
        """Edge: None input should not crash (uses datetime.now)."""
        result = _time_based_crowding(None)
        self.assertIn(result, ["Low", "Medium", "High"])

    def test_naive_datetime(self):
        """Edge: Naive datetime (no tzinfo) should be treated as SGT."""
        dt = datetime(2026, 4, 14, 8, 0)  # naive, no tzinfo
        result = _time_based_crowding(dt)
        self.assertEqual(result, "High")  # weekday morning peak

    def test_utc_datetime_converted_to_sgt(self):
        """Edge: UTC datetime should be converted to SGT before evaluation.
        UTC 23:00 = SGT 07:00 next day (morning peak if weekday)."""
        # Monday 23:00 UTC = Tuesday 07:00 SGT
        dt = datetime(2026, 4, 13, 23, 0, tzinfo=timezone.utc)  # Monday UTC
        result = _time_based_crowding(dt)
        # SGT: Tuesday 7:00am, t=420, weekday morning peak
        self.assertEqual(result, "High")


if __name__ == "__main__":
    unittest.main()
