"""
SC2006 SGTravelBud — White-box & Black-box Test Suite
Control class under test: RouteScoringController  (backend/services/routing.py)

Test design techniques applied
─────────────────────────────
3.2.1  Equivalence Class (EC) + Boundary Value Analysis (BVA)
       → estimate_cost  (all three fare models)
       → aggregate_route_risks  (risk category aggregation)

3.2.2  Basis-Path Testing  (V(G) computed per method)
       → estimate_cost       V(G) = 5   (4 decision nodes + 1)
       → aggregate_route_risks  V(G) = 7   (6 decision nodes + 1)

3.2.3  Test-case minimisation: BVAs subsume interior-EC representatives;
       one test per independent path; combined inputs used where feasible.

Run with:
    cd Program
    python -m pytest tests/test_routing.py -v
"""

import unittest
from backend.models.schemas import (
    RiskCategory, RiskIndicator, SegmentAssessment, RouteStep,
)
from backend.services.routing import (
    aggregate_route_risks,
    estimate_cost,
    compute_realistic_time,
    rank_routes,
    add_explanations,
    build_route_steps,
)


# ════════════════════════════════════════════════════════════════════════════
#  Shared test-data helpers
# ════════════════════════════════════════════════════════════════════════════

def _make_risk(cat: str, numeric: int, is_fallback: bool = False) -> RiskIndicator:
    """Construct a RiskIndicator from shorthand strings."""
    return RiskIndicator(
        category=RiskCategory(cat),
        numeric=numeric,
        source="fallback" if is_fallback else "realtime",
        is_fallback=is_fallback,
    )


def _make_seg(
    crowd_cat: str, crowd_num: int,
    delay_cat: str, delay_num: int,
    crowd_fallback: bool = False,
    delay_fallback: bool = False,
) -> SegmentAssessment:
    """Construct a SegmentAssessment from shorthand args."""
    return SegmentAssessment(
        mode="BUS",
        from_name="Stop A",
        to_name="Stop B",
        crowding=_make_risk(crowd_cat, crowd_num, crowd_fallback),
        delay=_make_risk(delay_cat, delay_num, delay_fallback),
    )


def _make_bus_step(miss_penalty_min: float) -> RouteStep:
    """Bus RouteStep carrying frequency/penalty data."""
    return RouteStep(
        mode="Bus",
        from_name="Stop A",
        to_name="Stop B",
        duration_min=15.0,
        line_name="65",
        bus_frequency={"miss_penalty_min": miss_penalty_min, "frequency_min": 10},
    )


def _make_train_step() -> RouteStep:
    return RouteStep(mode="Train", from_name="A", to_name="B", duration_min=12.0)


def _make_walk_step(dur: float = 5.0) -> RouteStep:
    return RouteStep(mode="Walk", from_name="A", to_name="B", duration_min=dur)


def _make_candidate(
    time_min: float, cost_est: float,
    crowd_num: int = 1, delay_num: int = 1,
    walk_min: float = 0.0, transfers: int = 0,
) -> dict:
    """Minimal route candidate dict as produced by api/routes.py."""
    return {
        "time_min": time_min,
        "cost_est": cost_est,
        "risk_crowding_num": crowd_num,
        "risk_delay_num": delay_num,
        "walk_min": walk_min,
        "transfers": transfers,
        "risk_cat": "Low",
        "steps": [],
        "uses_fallback": False,
    }


# ════════════════════════════════════════════════════════════════════════════
#  3.2.1 + 3.2.2  estimate_cost
#  Basis-path flowgraph (V(G) = 5)
#  Node 1: mode == "taxi"|"driving"?
#    YES → Node 2: distance_km <= 10?
#            YES → Path P1
#            NO  → Path P2
#    NO  → Node 3: mode == "owncar"?
#            YES → Path P3
#            NO  → transit loop
#              Node 4: distance_km <= threshold? → Path P4 (early exit)
#              Loop exhausted           → Path P5
# ════════════════════════════════════════════════════════════════════════════

class TestEstimateCost(unittest.TestCase):
    """
    TC-ID  Technique   Input                        Expected
    ─────────────────────────────────────────────────────────────
    TC01   EC + BVA    transit,  dist=0              $0.99 (floor)
    TC02   BVA         transit,  dist=3200           $0.99 (upper boundary of bracket)
    TC03   BVA         transit,  dist=3201           $1.09 (crosses into next bracket)
    TC04   BVA         transit,  dist=40200          $1.98 (penultimate bracket)
    TC05   BVA         transit,  dist=40201          $2.20 (max-fare trigger)
    TC06   EC          transit,  dist=6000           $1.29
    TC07   EC          transit,  dist=-500 (neg.)    $0.99 (clamped to 0)
    TC08   EC          transit,  unknown mode        $0.99 (falls to transit branch)
    TC09   Basis P1    taxi,     dist=5000 dur=600   total > $4.00, mode="taxi"
    TC10   Basis P2    taxi,     dist=15000 dur=600  higher than TC09 (>10 km rate)
    TC11   EC          driving,  dist=5000 dur=600   identical path to taxi branch
    TC12   BVA+Basis   taxi,     dur=0               waiting_charge == 0
    TC13   Basis P3    owncar,   dist=10000          $1.20
    TC14   EC          owncar,   dist=0              $0.00
    """

    # ── Transit fare table ──────────────────────────────────────────────────

    def test_TC01_transit_zero_distance_returns_floor_fare(self):
        """EC: distance = 0 → smallest bracket → $0.99."""
        result = estimate_cost(0, 0, "transit")
        self.assertEqual(result["mode"], "transit")
        self.assertEqual(result["total"], 0.99)

    def test_TC02_transit_exactly_at_first_boundary(self):
        """BVA: distance = 3200 m = 3.2 km → still in first bracket → $0.99."""
        result = estimate_cost(3200, 0, "transit")
        self.assertEqual(result["total"], 0.99)

    def test_TC03_transit_one_metre_past_first_boundary(self):
        """BVA: distance = 3201 m crosses into second bracket → $1.09."""
        result = estimate_cost(3201, 0, "transit")
        self.assertEqual(result["total"], 1.09)

    def test_TC04_transit_at_penultimate_bracket(self):
        """BVA: distance = 40200 m = 40.2 km → last table entry → $1.98."""
        result = estimate_cost(40200, 0, "transit")
        self.assertEqual(result["total"], 1.98)

    def test_TC05_transit_beyond_fare_table_triggers_max(self):
        """BVA + Basis P5: distance = 40201 m exceeds table → max fare $2.20."""
        result = estimate_cost(40201, 0, "transit")
        self.assertEqual(result["total"], 2.20)

    def test_TC06_transit_midrange_fare(self):
        """EC: 6000 m = 6.0 km → 6.0 ≤ 6.2 bracket → $1.29."""
        result = estimate_cost(6000, 0, "transit")
        self.assertEqual(result["total"], 1.29)

    def test_TC07_transit_negative_distance_clamped(self):
        """EC (invalid input): negative distance → clamped to 0 → $0.99."""
        result = estimate_cost(-500, 0, "transit")
        self.assertEqual(result["total"], 0.99)

    def test_TC08_unknown_mode_falls_through_to_transit(self):
        """EC (invalid mode): unknown mode string → transit else-branch → $0.99."""
        result = estimate_cost(1000, 0, "bicycle")
        self.assertEqual(result["mode"], "transit")
        self.assertEqual(result["total"], 0.99)

    # ── Taxi meter ──────────────────────────────────────────────────────────

    def test_TC09_taxi_short_distance_basis_path_P1(self):
        """EC + Basis P1: taxi, 5 km (≤10 km branch), 10 min ride."""
        # distance_charge = 5.0 * 0.55 = 2.75
        # idle_min = 10.0 * 0.20 = 2.0
        # waiting = (2.0 * 60 / 45) * 0.22 = 2.6667 * 0.22 ≈ 0.5867
        # total ≈ 4.00 + 2.75 + 0.5867 = 7.34
        result = estimate_cost(5000, 600, "taxi")
        self.assertEqual(result["mode"], "taxi")
        self.assertIn("flag_down", result)
        self.assertEqual(result["flag_down"], 4.00)
        self.assertGreater(result["total"], 4.00)
        self.assertAlmostEqual(result["total"], 7.34, places=1)

    def test_TC10_taxi_long_distance_basis_path_P2(self):
        """Basis P2: taxi, 15 km (>10 km rate kicks in), same duration."""
        # distance_charge = (10 * 0.55) + (5 * 0.629) = 5.5 + 3.145 = 8.645
        result_short = estimate_cost(5000, 600, "taxi")
        result_long  = estimate_cost(15000, 600, "taxi")
        self.assertGreater(result_long["total"], result_short["total"])
        # distance_charge for 15 km should use the higher per-km rate beyond 10 km
        self.assertAlmostEqual(result_long["distance_charge"], 8.645, places=2)

    def test_TC11_driving_mode_uses_taxi_branch(self):
        """EC: mode='driving' enters the taxi branch and labels result mode='taxi'."""
        result = estimate_cost(5000, 600, "driving")
        self.assertEqual(result["mode"], "taxi")
        self.assertAlmostEqual(result["total"], estimate_cost(5000, 600, "taxi")["total"])

    def test_TC12_taxi_zero_duration_no_waiting_charge(self):
        """BVA: duration = 0 s → waiting_charge = 0."""
        result = estimate_cost(5000, 0, "taxi")
        self.assertEqual(result["waiting_charge"], 0.0)
        # total = flag_down + distance_charge only
        expected = round(4.00 + 5.0 * 0.55, 2)
        self.assertAlmostEqual(result["total"], expected, places=2)

    # ── Own car ─────────────────────────────────────────────────────────────

    def test_TC13_owncar_fuel_cost_basis_path_P3(self):
        """Basis P3: own car, 10 km → $0.12 × 10 = $1.20."""
        result = estimate_cost(10000, 0, "owncar")
        self.assertEqual(result["mode"], "owncar")
        self.assertAlmostEqual(result["total"], 1.20, places=2)

    def test_TC14_owncar_zero_distance(self):
        """EC: zero distance → $0.00 fuel cost."""
        result = estimate_cost(0, 0, "owncar")
        self.assertEqual(result["total"], 0.00)

    # ── Return-shape contract ────────────────────────────────────────────────

    def test_all_modes_return_total_key(self):
        """All three branches must include a 'total' key (contract for routes.py)."""
        for mode in ("transit", "taxi", "owncar"):
            with self.subTest(mode=mode):
                result = estimate_cost(5000, 300, mode)
                self.assertIn("total", result)
                self.assertIsInstance(result["total"], float)


# ════════════════════════════════════════════════════════════════════════════
#  3.2.1 + 3.2.2  aggregate_route_risks
#  Basis-path flowgraph (V(G) = 7)
#  Node 1: segments empty?
#    YES → Path P1
#    NO  →
#      Node 2: any crowd Unknown?
#        YES → Node 3: any known crowd nums?
#                YES → Path P4 (max-of-known)
#                NO  → Path P3 (all Unknown)
#        NO  → Path P2 (max of all)
#      [Mirror for delay: Nodes 4,5,6]
#      Node 7: any is_fallback?
#        YES → Path P6 (uses_fallback=True)
# ════════════════════════════════════════════════════════════════════════════

class TestAggregateRouteRisks(unittest.TestCase):
    """
    TC-ID  Technique      Segments                        Expected (crowd, delay, fb)
    ───────────────────────────────────────────────────────────────────────────────
    TC15   EC + Basis P1  []  (empty)                     Unknown,2, Unknown,2, False
    TC16   Basis P2       [Low crowd, Low delay]           Low,1, Low,1, False
    TC17   EC             [High crowd, Low delay]          High,3, Low,1, False
    TC18   Basis P3       [Unknown crowd, Low delay]       Unknown,2, Low,1, False
    TC19   Basis P4       [Unknown+High crowd, Low delay]  High,3, Low,1, False
    TC20   EC             [Low crowd, Unknown delay]       Low,1, Unknown,2, False
    TC21   EC             [Low crowd, Low delay] fb=True   Low,1, Low,1, True
    TC22   EC             [Medium, High] crowd             High,3 crowd
    TC23   EC             two segments, worst wins         max propagates correctly
    TC24   BVA            numeric boundary: all Medium=2   Medium,2 both dims
    """

    def test_TC15_empty_segments_returns_unknown(self):
        """Basis P1: no segments → all Unknown, uses_fallback=False."""
        cc, cn, dc, dn, fb = aggregate_route_risks([])
        self.assertEqual(cc, RiskCategory.unknown)
        self.assertEqual(cn, 2)
        self.assertEqual(dc, RiskCategory.unknown)
        self.assertEqual(dn, 2)
        self.assertFalse(fb)

    def test_TC16_all_low_returns_low(self):
        """Basis P2: all segments Low → route is Low for both dims."""
        segs = [_make_seg("Low", 1, "Low", 1)]
        cc, cn, dc, dn, fb = aggregate_route_risks(segs)
        self.assertEqual(cc, RiskCategory.low)
        self.assertEqual(cn, 1)
        self.assertEqual(dc, RiskCategory.low)
        self.assertEqual(dn, 1)
        self.assertFalse(fb)

    def test_TC17_high_crowd_propagates(self):
        """EC: one High-crowd segment → route crowd = High."""
        segs = [_make_seg("High", 3, "Low", 1)]
        cc, cn, dc, dn, _ = aggregate_route_risks(segs)
        self.assertEqual(cc, RiskCategory.high)
        self.assertEqual(cn, 3)

    def test_TC18_all_unknown_crowd_returns_unknown(self):
        """Basis P3: all crowd Unknown (no known) → crowd = Unknown."""
        segs = [_make_seg("Unknown", 2, "Low", 1)]
        cc, cn, dc, dn, _ = aggregate_route_risks(segs)
        self.assertEqual(cc, RiskCategory.unknown)
        self.assertEqual(cn, 2)

    def test_TC19_mixed_unknown_and_high_known_wins(self):
        """Basis P4: crowd has Unknown + High → known High dominates Unknown."""
        segs = [
            _make_seg("Unknown", 2, "Low", 1),
            _make_seg("High",    3, "Low", 1),
        ]
        cc, cn, dc, dn, _ = aggregate_route_risks(segs)
        self.assertEqual(cc, RiskCategory.high)
        self.assertEqual(cn, 3)

    def test_TC20_unknown_delay_propagates_independently(self):
        """EC: crowd=Low, delay=Unknown → only delay is Unknown."""
        segs = [_make_seg("Low", 1, "Unknown", 2)]
        cc, cn, dc, dn, _ = aggregate_route_risks(segs)
        self.assertEqual(cc, RiskCategory.low)
        self.assertEqual(dc, RiskCategory.unknown)

    def test_TC21_fallback_flag_detected(self):
        """EC: segment with is_fallback=True → uses_fallback=True."""
        segs = [_make_seg("Low", 1, "Low", 1, crowd_fallback=True)]
        _, _, _, _, fb = aggregate_route_risks(segs)
        self.assertTrue(fb)

    def test_TC21b_delay_fallback_also_detected(self):
        """EC: segment with delay is_fallback=True → uses_fallback=True."""
        segs = [_make_seg("Low", 1, "Low", 1, delay_fallback=True)]
        _, _, _, _, fb = aggregate_route_risks(segs)
        self.assertTrue(fb)

    def test_TC22_medium_and_high_max_is_high(self):
        """EC: two segments, Medium and High crowd → route = High."""
        segs = [
            _make_seg("Medium", 2, "Low", 1),
            _make_seg("High",   3, "Low", 1),
        ]
        cc, cn, _, _, _ = aggregate_route_risks(segs)
        self.assertEqual(cc, RiskCategory.high)
        self.assertEqual(cn, 3)

    def test_TC23_multiple_segments_worst_delay_wins(self):
        """EC: [Low delay, High delay] → route delay = High."""
        segs = [
            _make_seg("Low", 1, "Low",  1),
            _make_seg("Low", 1, "High", 3),
        ]
        _, _, dc, dn, _ = aggregate_route_risks(segs)
        self.assertEqual(dc, RiskCategory.high)
        self.assertEqual(dn, 3)

    def test_TC24_all_medium_boundary(self):
        """BVA: all Medium (numeric=2) → both dims = Medium, num=2."""
        segs = [_make_seg("Medium", 2, "Medium", 2)]
        cc, cn, dc, dn, _ = aggregate_route_risks(segs)
        self.assertEqual(cc, RiskCategory.medium)
        self.assertEqual(cn, 2)
        self.assertEqual(dc, RiskCategory.medium)
        self.assertEqual(dn, 2)

    def test_TC25_return_type_is_five_tuple(self):
        """Contract: function always returns exactly 5 values with correct types."""
        result = aggregate_route_risks([_make_seg("Low", 1, "Low", 1)])
        self.assertEqual(len(result), 5)
        cc, cn, dc, dn, fb = result
        self.assertIsInstance(cc, RiskCategory)
        self.assertIsInstance(cn, int)
        self.assertIsInstance(dc, RiskCategory)
        self.assertIsInstance(dn, int)
        self.assertIsInstance(fb, bool)


# ════════════════════════════════════════════════════════════════════════════
#  3.2.1  compute_realistic_time
#  EC partitions: no steps / steps without bus_frequency / steps with penalty
# ════════════════════════════════════════════════════════════════════════════

class TestComputeRealisticTime(unittest.TestCase):
    """
    TC-ID  Input                          Expected
    ───────────────────────────────────────────────────────
    TC26   no steps                        time_min unchanged
    TC27   walk + train (no frequency)     time_min unchanged
    TC28   one bus, miss_penalty=10        +5.0 min buffer
    TC29   two buses, penalties 10 & 8     +5.0 + 4.0 = +9.0 min
    TC30   bus step with no penalty key    no buffer added
    TC31   BVA: time_min=0                 0.0 + penalty
    """

    def test_TC26_no_steps_returns_base_time(self):
        """EC: empty steps → realistic time equals Google time."""
        self.assertEqual(compute_realistic_time(30.0, []), 30.0)

    def test_TC27_non_bus_steps_add_no_penalty(self):
        """EC: only Walk and Train steps → no bus penalty."""
        steps = [_make_walk_step(5.0), _make_train_step()]
        self.assertEqual(compute_realistic_time(30.0, steps), 30.0)

    def test_TC28_one_bus_adds_half_miss_penalty(self):
        """EC: one bus with miss_penalty=10 → +5.0 min."""
        steps = [_make_bus_step(miss_penalty_min=10)]
        self.assertEqual(compute_realistic_time(30.0, steps), 35.0)

    def test_TC29_two_buses_penalties_accumulate(self):
        """EC: two buses (penalties 10, 8) → +5.0 + 4.0 = +9.0 min."""
        steps = [_make_bus_step(10), _make_bus_step(8)]
        self.assertEqual(compute_realistic_time(20.0, steps), 29.0)

    def test_TC30_bus_step_missing_penalty_key_adds_nothing(self):
        """EC: bus step with bus_frequency dict but no miss_penalty_min key."""
        step = RouteStep(
            mode="Bus",
            from_name="A",
            to_name="B",
            duration_min=10.0,
            bus_frequency={"frequency_min": 15},   # no miss_penalty_min
        )
        self.assertEqual(compute_realistic_time(30.0, [step]), 30.0)

    def test_TC31_bva_zero_base_time(self):
        """BVA: base time = 0 → only the penalty is returned."""
        steps = [_make_bus_step(miss_penalty_min=6)]
        self.assertEqual(compute_realistic_time(0.0, steps), 3.0)


# ════════════════════════════════════════════════════════════════════════════
#  3.2.1  rank_routes
#  EC partitions: empty list / single route / multiple routes with clear winner
# ════════════════════════════════════════════════════════════════════════════

class TestRankRoutes(unittest.TestCase):
    """
    TC-ID  Input                       Expected
    ───────────────────────────────────────────────────────
    TC32   empty candidates            []
    TC33   single route                score = 0.0
    TC34   two routes, A clearly wins  A ranked first
    TC35   result has score + norm keys set
    TC36   3 routes unsorted           ascending score order
    """

    _EQUAL_WEIGHTS = {"time": 0.25, "cost": 0.25, "risk": 0.25, "comfort": 0.25}

    def test_TC32_empty_candidates_returns_empty(self):
        """EC: no candidates → empty list."""
        self.assertEqual(rank_routes([], self._EQUAL_WEIGHTS), [])

    def test_TC33_single_route_gets_score_zero(self):
        """EC: one route → all normalised values = 0.0 → score = 0.0."""
        c = [_make_candidate(30.0, 1.50)]
        ranked = rank_routes(c, self._EQUAL_WEIGHTS)
        self.assertEqual(len(ranked), 1)
        self.assertAlmostEqual(ranked[0]["score"], 0.0, places=6)

    def test_TC34_better_route_ranked_first(self):
        """EC: Route A faster/cheaper/lower risk → A before B."""
        a = _make_candidate(20.0, 1.50, crowd_num=1, delay_num=1, walk_min=0, transfers=0)
        b = _make_candidate(45.0, 5.00, crowd_num=3, delay_num=3, walk_min=15, transfers=2)
        ranked = rank_routes([b, a], self._EQUAL_WEIGHTS)   # pass B first
        self.assertEqual(ranked[0]["time_min"], 20.0)       # A should come out first

    def test_TC35_normalized_score_fields_written(self):
        """Contract: rank_routes must write normalized_* and score onto every route."""
        a = _make_candidate(20.0, 2.0)
        b = _make_candidate(40.0, 4.0)
        ranked = rank_routes([a, b], self._EQUAL_WEIGHTS)
        for r in ranked:
            for key in ("normalized_time", "normalized_cost",
                        "normalized_risk", "normalized_comfort", "score"):
                self.assertIn(key, r, msg=f"Missing field: {key}")

    def test_TC36_score_order_is_ascending(self):
        """Contract: returned list must be sorted ascending by score."""
        routes = [
            _make_candidate(10.0, 1.0),
            _make_candidate(50.0, 10.0),
            _make_candidate(30.0, 5.0),
        ]
        ranked = rank_routes(routes, self._EQUAL_WEIGHTS)
        scores = [r["score"] for r in ranked]
        self.assertEqual(scores, sorted(scores))

    def test_TC37_higher_time_weight_promotes_fastest_route(self):
        """EC: weight on time → fastest route scores best."""
        a = _make_candidate(10.0, 10.0, crowd_num=3)   # fast but costly + risky
        b = _make_candidate(60.0,  1.0, crowd_num=1)   # slow but cheap + safe
        weights = {"time": 0.9, "cost": 0.033, "risk": 0.033, "comfort": 0.033}
        ranked = rank_routes([a, b], weights)
        self.assertEqual(ranked[0]["time_min"], 10.0)


# ════════════════════════════════════════════════════════════════════════════
#  3.2.1  add_explanations
#  EC: correct top-weight key drives explanation content
# ════════════════════════════════════════════════════════════════════════════

class TestAddExplanations(unittest.TestCase):
    """
    TC-ID  Top weight  Expected explanation prefix
    ────────────────────────────────────────────────────
    TC38   time        "Fastest option at N min"
    TC39   cost        "Cheapest at $X.XX"
    TC40   risk        "Lowest risk: Cat"
    TC41   comfort     "Most comfortable: ..."
    TC42   empty list  no error raised
    """

    def _route(self, time_min=25.0, cost_est=2.0, risk_cat="Low",
               walk_min=5.0, transfers=1):
        return {
            "time_min": time_min,
            "cost_est": cost_est,
            "risk_cat": risk_cat,
            "walk_min": walk_min,
            "transfers": transfers,
            "steps": [],
            "uses_fallback": False,
        }

    def test_TC38_top_weight_time(self):
        """EC: time is top weight → explanation mentions fastest + minutes."""
        routes = [self._route(time_min=25)]
        add_explanations(routes, {"time": 0.7, "cost": 0.1, "risk": 0.1, "comfort": 0.1})
        self.assertIn("25", routes[0]["explanation"])
        self.assertIn("Fastest", routes[0]["explanation"])

    def test_TC39_top_weight_cost(self):
        """EC: cost is top weight → explanation mentions cheapest + amount."""
        routes = [self._route(cost_est=1.50)]
        add_explanations(routes, {"time": 0.1, "cost": 0.7, "risk": 0.1, "comfort": 0.1})
        self.assertIn("Cheapest", routes[0]["explanation"])
        self.assertIn("1.50", routes[0]["explanation"])

    def test_TC40_top_weight_risk(self):
        """EC: risk is top weight → explanation mentions lowest risk + category."""
        routes = [self._route(risk_cat="Low")]
        add_explanations(routes, {"time": 0.1, "cost": 0.1, "risk": 0.7, "comfort": 0.1})
        self.assertIn("Lowest risk", routes[0]["explanation"])

    def test_TC41_top_weight_comfort(self):
        """EC: comfort is top weight → explanation mentions walk + transfers."""
        routes = [self._route(walk_min=8, transfers=2)]
        add_explanations(routes, {"time": 0.1, "cost": 0.1, "risk": 0.1, "comfort": 0.7})
        exp = routes[0]["explanation"]
        self.assertIn("comfortable", exp.lower())

    def test_TC42_empty_routes_no_error(self):
        """EC: empty list → no exception."""
        add_explanations([], {"time": 0.25, "cost": 0.25, "risk": 0.25, "comfort": 0.25})

    def test_TC43_explanation_key_set_on_each_route(self):
        """Contract: every route must have an 'explanation' string after call."""
        routes = [self._route(), self._route(time_min=50)]
        add_explanations(routes, {"time": 0.25, "cost": 0.25, "risk": 0.25, "comfort": 0.25})
        for r in routes:
            self.assertIn("explanation", r)
            self.assertIsInstance(r["explanation"], str)


# ════════════════════════════════════════════════════════════════════════════
#  3.2.1  build_route_steps  (selected EC)
# ════════════════════════════════════════════════════════════════════════════

class TestBuildRouteSteps(unittest.TestCase):
    """
    TC-ID  Input                               Expected
    ────────────────────────────────────────────────────────────
    TC44   driving route                        single Drive step, transfers=0
    TC45   malformed route (no legs)            empty list returned
    TC46   transit route, 1 bus step            1 step, mode="Bus", transfers=0
    TC47   transit route, 2 transit steps       transfers=1
    TC48   driving route, segment attached      delay propagated to Drive step
    """

    def _driving_route(self, start="Origin", end="Destination",
                       dur_s=1200, dist_m=8000):
        return {
            "requested_mode": "driving",
            "legs": [{
                "start_address": start,
                "end_address": end,
                "duration": {"value": dur_s},
                "distance": {"value": dist_m},
                "steps": [],
            }],
        }

    def _transit_step(self, dep, arr, line_name, veh_type="BUS", dur_s=600):
        return {
            "travel_mode": "TRANSIT",
            "duration": {"value": dur_s},
            "distance": {"value": 3000},
            "transit_details": {
                "departure_stop": {"name": dep},
                "arrival_stop": {"name": arr},
                "line": {
                    "short_name": line_name,
                    "vehicle": {"type": veh_type},
                },
                "num_stops": 4,
                "departure_time": {"text": "10:00 AM"},
                "arrival_time": {"text": "10:10 AM"},
                "headsign": "Bedok",
            },
        }

    def test_TC44_driving_returns_single_drive_step(self):
        """EC: driving mode → exactly one Drive step, 0 transfers."""
        route = self._driving_route()
        steps, summary, transfers = build_route_steps(route, [])
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].mode, "Drive")
        self.assertEqual(transfers, 0)

    def test_TC45_malformed_route_returns_empty(self):
        """EC: route with no legs → empty steps, empty summary, 0 transfers."""
        route = {"requested_mode": "transit", "legs": []}
        steps, summary, transfers = build_route_steps(route, [])
        self.assertEqual(steps, [])
        self.assertEqual(transfers, 0)

    def test_TC46_single_transit_step_bus(self):
        """EC: one bus step → mode='Bus', transfers=0."""
        route = {
            "requested_mode": "transit",
            "legs": [{
                "start_address": "Home",
                "end_address": "School",
                "steps": [self._transit_step("Tampines Int", "Bedok Int", "65", "BUS")],
            }],
        }
        seg = _make_seg("Low", 1, "Low", 1)
        steps, summary, transfers = build_route_steps(route, [seg])
        transit_steps = [s for s in steps if s.mode == "Bus"]
        self.assertEqual(len(transit_steps), 1)
        self.assertEqual(transit_steps[0].line_name, "65")
        self.assertEqual(transfers, 0)

    def test_TC47_two_transit_steps_gives_one_transfer(self):
        """EC: Bus then Train → transfers=1."""
        route = {
            "requested_mode": "transit",
            "legs": [{
                "start_address": "Home",
                "end_address": "Office",
                "steps": [
                    self._transit_step("Tampines Int", "Tanah Merah", "65",  "BUS"),
                    self._transit_step("Tanah Merah",  "City Hall",   "EWL", "SUBWAY"),
                ],
            }],
        }
        segs = [
            _make_seg("Low", 1, "Low", 1),
            _make_seg("Medium", 2, "Low", 1),
        ]
        steps, _, transfers = build_route_steps(route, segs)
        self.assertEqual(transfers, 1)

    def test_TC48_driving_segment_delay_attached_to_step(self):
        """EC: driving route with one segment → delay propagated to Drive step."""
        route = self._driving_route()
        seg = _make_seg("Unknown", 2, "High", 3)
        steps, _, _ = build_route_steps(route, [seg])
        self.assertIsNotNone(steps[0].delay)
        self.assertEqual(steps[0].delay.category, RiskCategory.high)


# ════════════════════════════════════════════════════════════════════════════
#  Gap WB-TC-G1  compute_comfort  — FR-1.4: comfort = 0.6*walk + 0.4*transfer
# ════════════════════════════════════════════════════════════════════════════

class TestComputeComfort(unittest.TestCase):
    """
    WB-TC-G1a  zero walk, zero transfers         → 0.0 (best comfort)
    WB-TC-G1b  30 min walk, 5 transfers          → 10.0 (worst comfort)
    WB-TC-G1c  walk > 30 min capped at 30        → same as 30 min
    WB-TC-G1d  transfers > 5 capped at 5         → same as 5 transfers
    WB-TC-G1e  typical 8 min walk, 1 transfer    → formula value
    WB-TC-G1f  walk only, no transfers           → purely walk contribution
    """

    def setUp(self):
        from backend.services.scoring import compute_comfort
        self.compute_comfort = compute_comfort

    def test_WB_G1a_zero_walk_zero_transfers_returns_zero(self):
        """FR-1.4: 0 min walk + 0 transfers → comfort = 0.0 (best)."""
        self.assertAlmostEqual(self.compute_comfort(0.0, 0), 0.0, places=6)

    def test_WB_G1b_max_walk_max_transfers_returns_max(self):
        """FR-1.4: 30 min walk + 5 transfers → comfort = 10.0 (worst)."""
        # walk_score = 30/3 = 10.0; transfer_score = 5*2 = 10.0
        # comfort = 0.6*10 + 0.4*10 = 10.0
        self.assertAlmostEqual(self.compute_comfort(30.0, 5), 10.0, places=6)

    def test_WB_G1c_walk_beyond_30_is_capped(self):
        """FR-1.4: walk > 30 min is capped — identical to 30 min result."""
        self.assertAlmostEqual(
            self.compute_comfort(60.0, 0), self.compute_comfort(30.0, 0), places=6
        )

    def test_WB_G1d_transfers_beyond_5_are_capped(self):
        """FR-1.4: transfers > 5 is capped — identical to 5 transfers result."""
        self.assertAlmostEqual(
            self.compute_comfort(0.0, 6), self.compute_comfort(0.0, 5), places=6
        )

    def test_WB_G1e_typical_8min_walk_1_transfer(self):
        """FR-1.4: 8 min walk + 1 transfer → formula produces correct value."""
        # walk_score = 8/3 ≈ 2.6667; transfer_score = 1*2 = 2.0
        # comfort = 0.6*2.6667 + 0.4*2.0 = 1.6 + 0.8 = 2.4
        expected = 0.6 * (8.0 / 3.0) + 0.4 * (1 * 2.0)
        self.assertAlmostEqual(self.compute_comfort(8.0, 1), expected, places=5)

    def test_WB_G1f_walk_only_no_transfers(self):
        """FR-1.4: 15 min walk, 0 transfers → 60% walk contribution only."""
        # walk_score = 15/3 = 5.0; transfer_score = 0
        # comfort = 0.6*5.0 = 3.0
        self.assertAlmostEqual(self.compute_comfort(15.0, 0), 3.0, places=5)


# ════════════════════════════════════════════════════════════════════════════
#  Gap WB-TC-G4  estimate_cost() — mid-range fare bracket coverage
# ════════════════════════════════════════════════════════════════════════════

class TestEstimateCostFareBrackets(unittest.TestCase):
    """
    WB-TC-G4a  10 km  → ≤10.2 bracket → $1.40
    WB-TC-G4b  15 km  → ≤15.2 bracket → $1.50
    WB-TC-G4c  20 km  → ≤20.2 bracket → $1.60
    WB-TC-G4d  25 km  → ≤26.2 bracket → $1.70
    """

    def test_WB_G4a_transit_10km_bracket(self):
        """transit, 10000 m = 10.0 km → ≤10.2 bracket → $1.40."""
        result = estimate_cost(10000, 0, "transit")
        self.assertAlmostEqual(result["total"], 1.40, places=2)

    def test_WB_G4b_transit_15km_bracket(self):
        """transit, 15000 m = 15.0 km → ≤15.2 bracket → $1.50."""
        result = estimate_cost(15000, 0, "transit")
        self.assertAlmostEqual(result["total"], 1.50, places=2)

    def test_WB_G4c_transit_20km_bracket(self):
        """transit, 20000 m = 20.0 km → ≤20.2 bracket → $1.60."""
        result = estimate_cost(20000, 0, "transit")
        self.assertAlmostEqual(result["total"], 1.60, places=2)

    def test_WB_G4d_transit_25km_bracket(self):
        """transit, 25000 m = 25.0 km → ≤26.2 bracket → $1.70."""
        result = estimate_cost(25000, 0, "transit")
        self.assertAlmostEqual(result["total"], 1.70, places=2)


# ════════════════════════════════════════════════════════════════════════════
#  Gap WB-TC-G6  aggregate_route_risks() — asymmetric Unknown distribution
# ════════════════════════════════════════════════════════════════════════════

class TestAggregateRouteRisksAsymmetric(unittest.TestCase):
    """
    WB-TC-G6a  crowd=mixed(Unknown+High), delay=all Low  → crowd=High, delay=Low
    WB-TC-G6b  crowd=all Low, delay=mixed(Unknown+Medium) → crowd=Low, delay=Medium
    """

    def test_WB_G6a_crowd_mixed_delay_all_known(self):
        """Crowd Unknown+High while delay is all Low → each dimension resolved independently."""
        segs = [
            _make_seg("Unknown", 2, "Low", 1),
            _make_seg("High",    3, "Low", 1),
        ]
        cc, cn, dc, dn, _ = aggregate_route_risks(segs)
        self.assertEqual(cc, RiskCategory.high)
        self.assertEqual(cn, 3)
        self.assertEqual(dc, RiskCategory.low)
        self.assertEqual(dn, 1)

    def test_WB_G6b_crowd_all_known_delay_mixed(self):
        """Crowd all Low while delay has Unknown+Medium → each resolved independently."""
        segs = [
            _make_seg("Low", 1, "Unknown", 2),
            _make_seg("Low", 1, "Medium",  2),
        ]
        cc, cn, dc, dn, _ = aggregate_route_risks(segs)
        self.assertEqual(cc, RiskCategory.low)
        self.assertEqual(cn, 1)
        self.assertEqual(dc, RiskCategory.medium)
        self.assertEqual(dn, 2)


# ════════════════════════════════════════════════════════════════════════════
#  Gap WB-TC-G7  compute_realistic_time() — 3+ bus segments
# ════════════════════════════════════════════════════════════════════════════

class TestComputeRealisticTimeExtended(unittest.TestCase):
    """
    WB-TC-G7a  three bus steps (penalties 10, 8, 6) → +5+4+3 = +12 min total
    """

    def test_WB_G7a_three_buses_accumulate_correctly(self):
        """Three buses with penalties 10, 8, 6 → buffer = 5.0+4.0+3.0 = 12.0 min."""
        steps = [_make_bus_step(10), _make_bus_step(8), _make_bus_step(6)]
        self.assertAlmostEqual(compute_realistic_time(20.0, steps), 32.0, places=1)


# ════════════════════════════════════════════════════════════════════════════
#  Gap WB-TC-G8  build_route_steps() — unmatched segment lookup
# ════════════════════════════════════════════════════════════════════════════

class TestBuildRouteStepsLookupMiss(unittest.TestCase):
    """
    WB-TC-G8a  transit step whose dep/arr stops don't match any segment
               → step is built with crowding=None, delay=None (no crash)
    """

    def _transit_route_with_stop(self, dep, arr):
        return {
            "requested_mode": "transit",
            "legs": [{
                "start_address": "Home",
                "end_address": "Office",
                "steps": [{
                    "travel_mode": "TRANSIT",
                    "duration": {"value": 600},
                    "distance": {"value": 3000},
                    "transit_details": {
                        "departure_stop": {"name": dep},
                        "arrival_stop":   {"name": arr},
                        "line": {"short_name": "99", "vehicle": {"type": "BUS"}},
                        "num_stops": 3,
                        "departure_time": {"text": "9:00 AM"},
                        "arrival_time":   {"text": "9:10 AM"},
                        "headsign": "East",
                    },
                }],
            }],
        }

    def test_WB_G8a_unmatched_segment_produces_none_crowding(self):
        """Transit step dep/arr not matching segment → crowding=None, delay=None, no crash."""
        route = self._transit_route_with_stop("Stop X", "Stop Y")
        # Segment with different stop names → no match in lookup
        seg = SegmentAssessment(
            mode="BUS",
            from_name="Different A",
            to_name="Different B",
            crowding=_make_risk("High", 3),
            delay=_make_risk("High", 3),
        )
        steps, _, _ = build_route_steps(route, [seg])
        bus_steps = [s for s in steps if s.mode == "Bus"]
        self.assertEqual(len(bus_steps), 1)
        self.assertIsNone(bus_steps[0].crowding)
        self.assertIsNone(bus_steps[0].delay)


# ════════════════════════════════════════════════════════════════════════════
#  Gap WB-TC-G5  rank_routes() — cost / risk / comfort weight dominance
# ════════════════════════════════════════════════════════════════════════════

class TestRankRoutesWeightSensitivity(unittest.TestCase):
    """
    WB-TC-G5a  cost-dominant weight    → cheapest route ranked first
    WB-TC-G5b  risk-dominant weight    → lowest risk route ranked first
    WB-TC-G5c  comfort-dominant weight → lowest comfort_num route ranked first
    """

    def test_WB_G5a_cost_dominant_promotes_cheapest(self):
        """cost weight=0.9 → cheapest route ranked first."""
        cheap     = _make_candidate(60.0, 1.0, crowd_num=2, walk_min=10, transfers=2)
        expensive = _make_candidate(20.0, 10.0, crowd_num=1, walk_min=0, transfers=0)
        weights = {"time": 0.033, "cost": 0.9, "risk": 0.033, "comfort": 0.033}
        ranked = rank_routes([expensive, cheap], weights)
        self.assertAlmostEqual(ranked[0]["cost_est"], 1.0, places=1)

    def test_WB_G5b_risk_dominant_promotes_safest(self):
        """risk weight=0.9 → lowest risk_num route ranked first."""
        safe  = _make_candidate(60.0, 5.0, crowd_num=1, delay_num=1)
        risky = _make_candidate(20.0, 2.0, crowd_num=3, delay_num=3)
        weights = {"time": 0.033, "cost": 0.033, "risk": 0.9, "comfort": 0.033}
        ranked = rank_routes([risky, safe], weights)
        self.assertEqual(ranked[0]["risk_crowding_num"], 1)

    def test_WB_G5c_comfort_dominant_promotes_most_comfortable(self):
        """comfort weight=0.9 → route with 0 walk + 0 transfers ranked first."""
        comfortable   = _make_candidate(40.0, 3.0, walk_min=0,  transfers=0)
        uncomfortable = _make_candidate(20.0, 2.0, walk_min=20, transfers=3)
        weights = {"time": 0.033, "cost": 0.033, "risk": 0.033, "comfort": 0.9}
        ranked = rank_routes([uncomfortable, comfortable], weights)
        self.assertEqual(ranked[0]["walk_min"], 0.0)
        self.assertEqual(ranked[0]["transfers"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
