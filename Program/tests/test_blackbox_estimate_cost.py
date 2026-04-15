"""
Black Box Testing: CostEstimationController.estimate_cost()
============================================================
Testing technique: Equivalence Class (EC) + Boundary Value Testing (BVT)

System Under Test (SUT): backend.services.routing.estimate_cost()
Location: backend/services/routing.py:85

Function signature:
    estimate_cost(distance_m, duration_s, mode, departure_time=None,
                  origin_lat=None, origin_lng=None) -> dict

Input parameters and their equivalence classes:
-----------------------------------------------
P1: mode (str) - Discrete
    Valid EC:   {"driving", "taxi"} -> taxi fare,  {"owncar"} -> fuel cost,
                {"transit", anything else} -> public transit fare
    Invalid EC: N/A (defaults to transit for unknown modes)

P2: distance_m (float) - Range
    For taxi:   EC1: <=0 (clamped to 0), EC2: 0<d<=1000 (flag-down only),
                EC3: 1000<d<=10000 (tier 1), EC4: d>10000 (tier 2)
    For transit: EC1: <=0, EC2: 0<d<=3200 ($0.99), ..., EC_last: d>40200 ($2.20)
    BV (taxi meters): {-1, 0, 999, 1000, 1001, 9999, 10000, 10001}
    BV (transit meters): {0, 3199, 3200, 3201, 40199, 40200, 40201}

P3: duration_s (float) - Range
    EC1: <=0 (clamped to 0), EC2: >0 (normal)
    BV: {-1, 0, 1}

P4: departure_time (datetime) - Range (for taxi surcharges)
    EC1: Peak period (weekday 6am-9:29am, any day 5pm-11:59pm, weekend 10am-1:59pm)
    EC2: Late night (midnight-5:59am) - supersedes peak
    EC3: Off-peak (no surcharge)
    EC4: None (defaults to now)

P5: departure_time (datetime) - Range (for transit discounts)
    EC1: Early bird (weekday before 7:45am)
    EC2: Off-peak (weekday 9:30am-4pm, or weekend)
    EC3: Peak (no discount)

P6: origin_lat/lng - Discrete (taxi airport surcharge)
    EC1: Changi Airport coords (lat 1.330-1.365, lng 103.975-104.005)
    EC2: Non-airport coords
    EC3: None
    BV (lat): {1.329, 1.330, 1.365, 1.366}
    BV (lng): {103.974, 103.975, 104.005, 104.006}
"""

import unittest
from datetime import datetime, timezone, timedelta

from backend.services.routing import estimate_cost

SGT = timezone(timedelta(hours=8))


class TestEstimateCostTaxiMode(unittest.TestCase):
    """Black box tests for estimate_cost() with mode='taxi'/'driving'."""

    # ---------------------------------------------------------------
    # EC Tests: Distance tiers (P2)
    # ---------------------------------------------------------------

    def test_taxi_zero_distance(self):
        """EC P2-EC1: distance_m=0, only flag-down charge applies."""
        result = estimate_cost(0, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["mode"], "taxi")
        self.assertEqual(result["flag_down"], 4.60)
        self.assertEqual(result["distance_charge"], 0.0)
        self.assertGreater(result["total"], 0)

    def test_taxi_negative_distance(self):
        """EC P2-EC1: distance_m<0, clamped to 0."""
        result = estimate_cost(-1000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["distance_charge"], 0.0)

    def test_taxi_within_flagdown_distance(self):
        """EC P2-EC2: 0 < distance <= 1km, covered by flag-down."""
        result = estimate_cost(500, 300, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["distance_charge"], 0.0)

    def test_taxi_tier1_distance(self):
        """EC P2-EC3: 1km < distance <= 10km, tier 1 rate ($0.27/400m)."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        # 5km: (5-1) * (0.27/0.4) = 4 * 0.675 = 2.70
        self.assertAlmostEqual(result["distance_charge"], 2.70, places=2)

    def test_taxi_tier2_distance(self):
        """EC P2-EC4: distance > 10km, tier 2 rate ($0.27/350m after 10km)."""
        result = estimate_cost(15000, 1200, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        # Tier 1: 9km * (0.27/0.4) = 6.075
        # Tier 2: 5km * (0.27/0.35) = 3.857
        # Total distance_charge = 6.075 + 3.857 = 9.932
        expected_tier1 = 9 * (0.27 / 0.4)
        expected_tier2 = 5 * (0.27 / 0.35)
        self.assertAlmostEqual(result["distance_charge"],
                               round(expected_tier1 + expected_tier2, 2), places=2)

    # ---------------------------------------------------------------
    # BV Tests: Distance boundaries (P2)
    # ---------------------------------------------------------------

    def test_taxi_bv_distance_at_1km(self):
        """BV P2: On boundary 1000m - still flag-down only."""
        result = estimate_cost(1000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["distance_charge"], 0.0)

    def test_taxi_bv_distance_just_above_1km(self):
        """BV P2: Just above 1000m - tier 1 kicks in.
        Note: 1001m = 1.001km, charge = 0.001*0.675 = 0.0007 rounds to 0.0.
        Use 1100m (1.1km) to show tier 1 visibly activates."""
        result = estimate_cost(1100, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertGreater(result["distance_charge"], 0.0)

    def test_taxi_bv_distance_at_10km(self):
        """BV P2: On boundary 10000m - still tier 1."""
        result = estimate_cost(10000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        expected = 9 * (0.27 / 0.4)
        self.assertAlmostEqual(result["distance_charge"], round(expected, 2), places=2)

    def test_taxi_bv_distance_just_above_10km(self):
        """BV P2: Just above 10000m - tier 2 kicks in.
        Note: 10001m difference too small after rounding.
        Use 10500m (10.5km) to show tier 2 visibly activates."""
        result = estimate_cost(10500, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        tier1_only = round(9 * (0.27 / 0.4), 2)
        # 10.5km: tier2 portion = 0.5km * (0.27/0.35) = 0.386
        self.assertGreater(result["distance_charge"], tier1_only)

    # ---------------------------------------------------------------
    # EC Tests: Duration / waiting charge (P3)
    # ---------------------------------------------------------------

    def test_taxi_zero_duration(self):
        """EC P3-EC1: duration_s=0, no waiting charge."""
        result = estimate_cost(5000, 0, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["waiting_charge"], 0.0)

    def test_taxi_normal_duration(self):
        """EC P3-EC2: duration_s>0, generates waiting charge."""
        result = estimate_cost(5000, 1200, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        # 1200s = 20min, idle = 20*0.20=4min, charges = (4*60/45)*0.27
        expected_waiting = (4 * 60 / 45) * 0.27
        self.assertAlmostEqual(result["waiting_charge"],
                               round(expected_waiting, 2), places=2)

    # ---------------------------------------------------------------
    # EC Tests: Departure time surcharges (P4)
    # ---------------------------------------------------------------

    def test_taxi_peak_weekday_morning(self):
        """EC P4-EC1a: Weekday 8:00am = peak, 25% surcharge."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 8, 0, tzinfo=SGT))  # Tue
        self.assertGreater(result["peak_surcharge"], 0)
        self.assertEqual(result["late_night_surcharge"], 0.0)

    def test_taxi_peak_evening(self):
        """EC P4-EC1b: Any day 6:00pm = peak, 25% surcharge."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 18, 0, tzinfo=SGT))
        self.assertGreater(result["peak_surcharge"], 0)

    def test_taxi_peak_weekend_midday(self):
        """EC P4-EC1c: Saturday 11:00am = peak."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 18, 11, 0, tzinfo=SGT))  # Sat
        self.assertGreater(result["peak_surcharge"], 0)

    def test_taxi_late_night(self):
        """EC P4-EC2: 3:00am = late night, 50% surcharge, peak=0."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 3, 0, tzinfo=SGT))
        self.assertGreater(result["late_night_surcharge"], 0)
        self.assertEqual(result["peak_surcharge"], 0.0)

    def test_taxi_off_peak(self):
        """EC P4-EC3: Weekday 2:00pm = off-peak, no surcharge."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["peak_surcharge"], 0.0)
        self.assertEqual(result["late_night_surcharge"], 0.0)

    # ---------------------------------------------------------------
    # BV Tests: Peak time boundaries (P4)
    # ---------------------------------------------------------------

    def test_taxi_bv_peak_morning_start(self):
        """BV P4: 5:59am weekday = NOT peak (just below 6:00am boundary)."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 5, 59, tzinfo=SGT))
        # 5:59am is late night (hour < 6), so late_night_surcharge applies
        self.assertGreater(result["late_night_surcharge"], 0)

    def test_taxi_bv_peak_morning_on(self):
        """BV P4: 6:00am weekday = peak start (on boundary)."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 6, 0, tzinfo=SGT))
        self.assertGreater(result["peak_surcharge"], 0)

    def test_taxi_bv_peak_morning_end(self):
        """BV P4: 9:29am weekday = still peak (on boundary, 569 min)."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 9, 29, tzinfo=SGT))
        self.assertGreater(result["peak_surcharge"], 0)

    def test_taxi_bv_peak_morning_just_after(self):
        """BV P4: 9:30am weekday = NOT peak (just above boundary, 570 min)."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 9, 30, tzinfo=SGT))
        self.assertEqual(result["peak_surcharge"], 0.0)

    def test_taxi_bv_peak_evening_start(self):
        """BV P4: 4:59pm = NOT peak (just below 5:00pm boundary, 1019 min)."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 16, 59, tzinfo=SGT))
        self.assertEqual(result["peak_surcharge"], 0.0)

    def test_taxi_bv_peak_evening_on(self):
        """BV P4: 5:00pm = peak start (on boundary, 1020 min)."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 17, 0, tzinfo=SGT))
        self.assertGreater(result["peak_surcharge"], 0)

    # ---------------------------------------------------------------
    # BV Tests: Late night boundary
    # ---------------------------------------------------------------

    def test_taxi_bv_late_night_last_hour(self):
        """BV: 5:59am = late night (hour=5, still < 6)."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 5, 59, tzinfo=SGT))
        self.assertGreater(result["late_night_surcharge"], 0)

    def test_taxi_bv_late_night_end(self):
        """BV: 6:00am = NOT late night (hour=6, on boundary)."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 6, 0, tzinfo=SGT))
        self.assertEqual(result["late_night_surcharge"], 0.0)

    # ---------------------------------------------------------------
    # EC Tests: Booking fee (depends on peak/late-night)
    # ---------------------------------------------------------------

    def test_taxi_booking_fee_peak(self):
        """EC: Peak/late-night booking fee = $3.30."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 8, 0, tzinfo=SGT))
        self.assertEqual(result["booking_fee"], 3.30)

    def test_taxi_booking_fee_offpeak(self):
        """EC: Off-peak booking fee = $2.30."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["booking_fee"], 2.30)

    # ---------------------------------------------------------------
    # EC Tests: Changi Airport surcharge (P6)
    # ---------------------------------------------------------------

    def test_taxi_airport_surcharge_after_5pm(self):
        """EC P6-EC1a: Changi Airport origin after 5pm = $8.00."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 18, 0, tzinfo=SGT),
                               origin_lat=1.350, origin_lng=103.990)
        self.assertEqual(result["airport_surcharge"], 8.00)

    def test_taxi_airport_surcharge_before_5pm(self):
        """EC P6-EC1b: Changi Airport origin before 5pm = $6.00."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT),
                               origin_lat=1.350, origin_lng=103.990)
        self.assertEqual(result["airport_surcharge"], 6.00)

    def test_taxi_no_airport_surcharge(self):
        """EC P6-EC2: Non-airport origin = $0 surcharge."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 18, 0, tzinfo=SGT),
                               origin_lat=1.300, origin_lng=103.800)
        self.assertEqual(result["airport_surcharge"], 0.0)

    def test_taxi_none_coords(self):
        """EC P6-EC3: None coords = $0 surcharge."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 18, 0, tzinfo=SGT))
        self.assertEqual(result["airport_surcharge"], 0.0)

    # ---------------------------------------------------------------
    # BV Tests: Airport bounding box (P6)
    # ---------------------------------------------------------------

    def test_taxi_bv_airport_lat_just_below(self):
        """BV P6: lat=1.329 (just below Changi box) = no surcharge."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT),
                               origin_lat=1.329, origin_lng=103.990)
        self.assertEqual(result["airport_surcharge"], 0.0)

    def test_taxi_bv_airport_lat_on_lower(self):
        """BV P6: lat=1.330 (on lower boundary) = surcharge applies."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT),
                               origin_lat=1.330, origin_lng=103.990)
        self.assertEqual(result["airport_surcharge"], 6.00)

    def test_taxi_bv_airport_lat_on_upper(self):
        """BV P6: lat=1.365 (on upper boundary) = surcharge applies."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT),
                               origin_lat=1.365, origin_lng=103.990)
        self.assertEqual(result["airport_surcharge"], 6.00)

    def test_taxi_bv_airport_lat_just_above(self):
        """BV P6: lat=1.366 (just above Changi box) = no surcharge."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT),
                               origin_lat=1.366, origin_lng=103.990)
        self.assertEqual(result["airport_surcharge"], 0.0)


class TestEstimateCostOwnCarMode(unittest.TestCase):
    """Black box tests for estimate_cost() with mode='owncar'."""

    def test_owncar_basic(self):
        """EC: Own car mode returns fuel cost only."""
        result = estimate_cost(10000, 600, "owncar")
        self.assertEqual(result["mode"], "owncar")
        # 10km * $0.12/km = $1.20
        self.assertAlmostEqual(result["fuel_cost"], 1.20, places=2)
        self.assertAlmostEqual(result["total"], 1.20, places=2)

    def test_owncar_zero_distance(self):
        """EC: Zero distance = $0.00 fuel."""
        result = estimate_cost(0, 600, "owncar")
        self.assertEqual(result["fuel_cost"], 0.0)
        self.assertEqual(result["total"], 0.0)

    def test_owncar_no_surcharges(self):
        """EC: Own car has no peak/late-night surcharges."""
        result = estimate_cost(10000, 600, "owncar")
        self.assertNotIn("peak_surcharge", result)
        self.assertNotIn("booking_fee", result)


class TestEstimateCostTransitMode(unittest.TestCase):
    """Black box tests for estimate_cost() with mode='transit'."""

    # ---------------------------------------------------------------
    # EC Tests: Distance fare brackets (P2)
    # ---------------------------------------------------------------

    def test_transit_shortest_bracket(self):
        """EC P2-EC2: 0-3.2km = $0.99 base fare."""
        result = estimate_cost(2000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT))
        self.assertEqual(result["mode"], "transit")
        self.assertEqual(result["base_fare"], 0.99)

    def test_transit_second_bracket(self):
        """EC: 3.2-4.2km = $1.09 base fare."""
        result = estimate_cost(3500, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT))
        self.assertEqual(result["base_fare"], 1.09)

    def test_transit_max_fare(self):
        """EC: >40.2km = $2.20 max fare."""
        result = estimate_cost(50000, 3000, "transit",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT))
        self.assertEqual(result["base_fare"], 2.20)

    # ---------------------------------------------------------------
    # BV Tests: Fare bracket boundaries (P2)
    # ---------------------------------------------------------------

    def test_transit_bv_first_bracket_on(self):
        """BV: 3.2km (on boundary) = $0.99."""
        result = estimate_cost(3200, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT))
        self.assertEqual(result["base_fare"], 0.99)

    def test_transit_bv_first_bracket_just_above(self):
        """BV: 3.201km (just above) = $1.09."""
        result = estimate_cost(3201, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT))
        self.assertEqual(result["base_fare"], 1.09)

    def test_transit_bv_max_bracket_on(self):
        """BV: 40.2km (on boundary) = $1.98 (last bracket)."""
        result = estimate_cost(40200, 3000, "transit",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT))
        self.assertEqual(result["base_fare"], 1.98)

    def test_transit_bv_max_bracket_just_above(self):
        """BV: 40.201km (just above) = $2.20 (max fare)."""
        result = estimate_cost(40201, 3000, "transit",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT))
        self.assertEqual(result["base_fare"], 2.20)

    # ---------------------------------------------------------------
    # EC Tests: Transit discounts (P5)
    # ---------------------------------------------------------------

    def test_transit_early_bird_discount(self):
        """EC P5-EC1: Weekday 7:30am = early bird, $0.50 off."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 7, 30, tzinfo=SGT))  # Tue
        self.assertEqual(result["early_bird_discount"], 0.50)
        self.assertEqual(result["off_peak_discount"], 0.0)

    def test_transit_offpeak_weekday(self):
        """EC P5-EC2a: Weekday 10:00am = off-peak, $0.50 off."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 10, 0, tzinfo=SGT))
        self.assertEqual(result["off_peak_discount"], 0.50)
        self.assertEqual(result["early_bird_discount"], 0.0)

    def test_transit_offpeak_weekend(self):
        """EC P5-EC2b: Saturday any time = off-peak, $0.50 off."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 18, 14, 0, tzinfo=SGT))  # Sat
        self.assertEqual(result["off_peak_discount"], 0.50)

    def test_transit_peak_no_discount(self):
        """EC P5-EC3: Weekday 8:30am = peak, no discount."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 8, 30, tzinfo=SGT))
        self.assertEqual(result["early_bird_discount"], 0.0)
        self.assertEqual(result["off_peak_discount"], 0.0)

    # ---------------------------------------------------------------
    # BV Tests: Transit discount boundaries (P5)
    # ---------------------------------------------------------------

    def test_transit_bv_early_bird_just_before_cutoff(self):
        """BV P5: 7:44am weekday = still early bird (464 min < 465)."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 7, 44, tzinfo=SGT))
        self.assertEqual(result["early_bird_discount"], 0.50)

    def test_transit_bv_early_bird_at_cutoff(self):
        """BV P5: 7:45am weekday = NOT early bird (465 min, boundary)."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 7, 45, tzinfo=SGT))
        self.assertEqual(result["early_bird_discount"], 0.0)

    def test_transit_bv_offpeak_start(self):
        """BV P5: 9:30am weekday = off-peak starts (570 min, on boundary)."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 9, 30, tzinfo=SGT))
        self.assertEqual(result["off_peak_discount"], 0.50)

    def test_transit_bv_offpeak_just_before(self):
        """BV P5: 9:29am weekday = NOT off-peak (569 min, just below)."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 9, 29, tzinfo=SGT))
        self.assertEqual(result["off_peak_discount"], 0.0)

    def test_transit_bv_offpeak_end(self):
        """BV P5: 4:00pm weekday = still off-peak (960 min, on boundary)."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 16, 0, tzinfo=SGT))
        self.assertEqual(result["off_peak_discount"], 0.50)

    def test_transit_bv_offpeak_just_after(self):
        """BV P5: 4:01pm weekday = NOT off-peak (961 min, just above)."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 16, 1, tzinfo=SGT))
        self.assertEqual(result["off_peak_discount"], 0.0)

    # ---------------------------------------------------------------
    # EC Tests: Total fare is non-negative
    # ---------------------------------------------------------------

    def test_transit_fare_never_negative(self):
        """EC: Even with discount, total fare >= 0."""
        result = estimate_cost(1000, 300, "transit",
                               departure_time=datetime(2026, 4, 14, 7, 0, tzinfo=SGT))
        self.assertGreaterEqual(result["total"], 0.00)


class TestEstimateCostModeSelection(unittest.TestCase):
    """Black box tests for mode parameter (P1) equivalence classes."""

    def test_mode_driving(self):
        """EC P1: mode='driving' returns taxi fare structure."""
        result = estimate_cost(5000, 600, "driving",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["mode"], "taxi")
        self.assertIn("flag_down", result)

    def test_mode_taxi(self):
        """EC P1: mode='taxi' returns taxi fare structure."""
        result = estimate_cost(5000, 600, "taxi",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["mode"], "taxi")

    def test_mode_owncar(self):
        """EC P1: mode='owncar' returns fuel-only structure."""
        result = estimate_cost(5000, 600, "owncar")
        self.assertEqual(result["mode"], "owncar")
        self.assertIn("fuel_cost", result)

    def test_mode_transit(self):
        """EC P1: mode='transit' returns transit fare structure."""
        result = estimate_cost(5000, 600, "transit",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["mode"], "transit")
        self.assertIn("base_fare", result)

    def test_mode_unknown_defaults_to_transit(self):
        """EC P1: Unknown mode defaults to transit."""
        result = estimate_cost(5000, 600, "bicycle",
                               departure_time=datetime(2026, 4, 14, 14, 0, tzinfo=SGT))
        self.assertEqual(result["mode"], "transit")


if __name__ == "__main__":
    unittest.main()
