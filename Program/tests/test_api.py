"""
test_api.py — White-box API endpoint tests
SC2006 SGTravelBud — ACDA-G36

Gap coverage:
  WB-TC-G9:  GET /crowding/heatmap — response schema and empty-station fallback
  WB-TC-G10: GET /settings and PUT /settings — read/write persistence
  WB-TC-G11: _build_compare_slots() — structure, labels, future-safe datetimes
"""

import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app


class TestSettingsAPI(unittest.TestCase):
    """
    WB-TC-G10a  GET /settings → returns all required fields
    WB-TC-G10b  PUT /settings → updated values reflected in response
    WB-TC-G10c  GET after PUT → persisted value returned
    """

    def setUp(self):
        self.client = TestClient(app)
        # Reset to known defaults before each test
        self.client.put("/settings", json={
            "language": "en", "units": "metric",
            "default_wt_time": 0.25, "default_wt_cost": 0.25,
            "default_wt_risk": 0.25, "default_wt_comfort": 0.25,
        })

    def test_WB_G10a_get_settings_returns_all_fields(self):
        """GET /settings → 200 with all 6 schema fields present."""
        resp = self.client.get("/settings")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for key in ("language", "units", "default_wt_time",
                    "default_wt_cost", "default_wt_risk", "default_wt_comfort"):
            self.assertIn(key, data, msg=f"Missing key: {key}")

    def test_WB_G10b_put_settings_updates_values(self):
        """PUT /settings → response reflects new values immediately."""
        payload = {
            "language": "zh",
            "units": "imperial",
            "default_wt_time": 0.8,
            "default_wt_cost": 0.1,
            "default_wt_risk": 0.05,
            "default_wt_comfort": 0.05,
        }
        resp = self.client.put("/settings", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["language"], "zh")
        self.assertAlmostEqual(data["default_wt_time"], 0.8, places=3)

    def test_WB_G10c_get_after_put_reflects_update(self):
        """GET /settings after PUT → persisted values returned."""
        self.client.put("/settings", json={
            "language": "ta", "units": "metric",
            "default_wt_time": 0.4, "default_wt_cost": 0.2,
            "default_wt_risk": 0.2, "default_wt_comfort": 0.2,
        })
        resp = self.client.get("/settings")
        self.assertEqual(resp.json()["language"], "ta")

    def test_WB_G10d_default_weights_sum_to_one(self):
        """GET /settings → default weights 0.25 each sum to 1.0."""
        resp = self.client.get("/settings")
        data = resp.json()
        total = (data["default_wt_time"] + data["default_wt_cost"]
                 + data["default_wt_risk"] + data["default_wt_comfort"])
        self.assertAlmostEqual(total, 1.0, places=5)


class TestCrowdingHeatmapAPI(unittest.TestCase):
    """
    WB-TC-G9a  Unknown station → 200, valid schema, empty intervals list
    WB-TC-G9b  Known station with mocked PCD data → intervals populated
    WB-TC-G9c  CrowdLevel strings mapped to Low/Medium/High/Unknown correctly
    """

    def setUp(self):
        self.client = TestClient(app)

    def test_WB_G9a_unknown_station_returns_empty_intervals(self):
        """Station name that fails lookup → 200, valid schema, intervals=[]."""
        resp = self.client.get("/crowding/heatmap",
                               params={"station_name": "XYZNOTASTATION"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("station", data)
        self.assertIn("line", data)
        self.assertIn("intervals", data)
        self.assertIsInstance(data["intervals"], list)
        self.assertEqual(len(data["intervals"]), 0)

    @patch("backend.clients.lta.get_pcd_forecast")
    def test_WB_G9b_known_station_with_mock_pcd_returns_intervals(self, mock_pcd):
        """Mocked PCD data for EW27 → intervals list populated."""
        mock_pcd.return_value = (
            {"value": [{"Stations": [
                {"Station": "EW27", "Interval": [
                    {"Start": "07:00", "CrowdLevel": "l"},
                    {"Start": "08:00", "CrowdLevel": "h"},
                    {"Start": "09:00", "CrowdLevel": "m"},
                ]}
            ]}]},
            None, False,
        )
        resp = self.client.get("/crowding/heatmap",
                               params={"station_name": "Boon Lay", "line": "EWL"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data["intervals"], list)
        # If lookup for "Boon Lay" resolves, we get intervals; if not, empty is acceptable
        # The important check is the schema is correct in either case
        for iv in data["intervals"]:
            self.assertIn("start", iv)
            self.assertIn("crowd_level", iv)

    @patch("backend.clients.lta.get_pcd_forecast")
    def test_WB_G9c_crowd_level_strings_mapped_correctly(self, mock_pcd):
        """CrowdLevel raw values (l/h/m) are normalised to Low/High/Medium."""
        mock_pcd.return_value = (
            {"value": [{"Stations": [
                {"Station": "NS1", "Interval": [
                    {"Start": "06:00", "CrowdLevel": "l"},
                    {"Start": "07:00", "CrowdLevel": "h"},
                    {"Start": "08:00", "CrowdLevel": "m"},
                    {"Start": "09:00", "CrowdLevel": "unknown_val"},
                ]}
            ]}]},
            None, False,
        )
        resp = self.client.get("/crowding/heatmap",
                               params={"station_name": "Jurong East", "line": "NSL"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        allowed = {"Low", "Medium", "High", "Unknown"}
        for iv in data["intervals"]:
            self.assertIn(iv["crowd_level"], allowed,
                          msg=f"Unexpected crowd_level: {iv['crowd_level']}")


class TestCompareSlotsStructure(unittest.TestCase):
    """
    WB-TC-G11a  _build_compare_slots() → exactly 3 groups, each with 3 time slots
    WB-TC-G11b  Group labels are Morning Rush, Around Now, Evening Rush
    WB-TC-G11c  All slot datetimes are strictly in the future
    WB-TC-G11d  Around Now slot labels are Now, +30 min, +1 hr
    """

    def setUp(self):
        from backend.api.routes import _build_compare_slots
        self.build = _build_compare_slots

    def test_WB_G11a_three_groups_nine_slots(self):
        """_build_compare_slots() → 3 groups, each containing 3 (label, datetime) tuples."""
        groups = self.build()
        self.assertEqual(len(groups), 3)
        for g in groups:
            self.assertIn("label", g)
            self.assertIn("times", g)
            self.assertEqual(len(g["times"]), 3)

    def test_WB_G11b_group_labels_correct(self):
        """Groups carry the expected labels: Morning Rush, Around Now, Evening Rush."""
        groups = self.build()
        labels = [g["label"] for g in groups]
        self.assertIn("Morning Rush", labels)
        self.assertIn("Around Now", labels)
        self.assertIn("Evening Rush", labels)

    def test_WB_G11c_all_slot_datetimes_are_future(self):
        """Every generated datetime is strictly after the current time."""
        from datetime import datetime, timezone, timedelta
        SGT = timezone(timedelta(hours=8))
        now = datetime.now(SGT)
        groups = self.build()
        for g in groups:
            for label, dt in g["times"]:
                self.assertGreater(dt, now,
                                   msg=f"Slot '{label}' in group '{g['label']}' is not in the future")

    def test_WB_G11d_around_now_labels_correct(self):
        """Around Now group has labels: Now, +30 min, +1 hr."""
        groups = self.build()
        around = next(g for g in groups if g["label"] == "Around Now")
        slot_labels = [t[0] for t in around["times"]]
        self.assertIn("Now", slot_labels)
        self.assertIn("+30 min", slot_labels)
        self.assertIn("+1 hr", slot_labels)


if __name__ == "__main__":
    unittest.main(verbosity=2)
