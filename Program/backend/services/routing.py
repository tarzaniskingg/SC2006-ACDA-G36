from typing import List, Dict, Tuple
from .scoring import normalize, composite_score, tie_break_key, explain, compute_risk, compute_comfort
from ..models.schemas import SegmentAssessment, RiskCategory, RouteStep


_VEHICLE_MODE_MAP = {
    "SUBWAY": "Train", "HEAVY_RAIL": "Train", "RAIL": "Train",
    "BUS": "Bus", "TRAM": "Tram", "FERRY": "Ferry",
}


def aggregate_route_risks(segments: List[SegmentAssessment]) -> Tuple[RiskCategory, int, RiskCategory, int, bool]:
    uses_fallback = any(s.crowding.is_fallback or s.delay.is_fallback for s in segments)
    crowd_nums = [s.crowding.numeric for s in segments]
    delay_nums = [s.delay.numeric for s in segments]
    crowd_cats = [s.crowding.category for s in segments]
    delay_cats = [s.delay.category for s in segments]

    if not crowd_cats:
        crowd_cat, crowd_num = RiskCategory.unknown, 2
    elif any(c == RiskCategory.unknown for c in crowd_cats):
        # If some are known, use the worst known; only fully Unknown if ALL are Unknown
        known_nums = [n for n, c in zip(crowd_nums, crowd_cats) if c != RiskCategory.unknown]
        if known_nums:
            crowd_num = max(known_nums)
            crowd_cat = {1: RiskCategory.low, 2: RiskCategory.medium, 3: RiskCategory.high}.get(crowd_num, RiskCategory.medium)
        else:
            crowd_cat, crowd_num = RiskCategory.unknown, 2
    else:
        crowd_num = max(crowd_nums)
        crowd_cat = {1: RiskCategory.low, 2: RiskCategory.medium, 3: RiskCategory.high}.get(crowd_num, RiskCategory.medium)

    if not delay_cats:
        delay_cat, delay_num = RiskCategory.unknown, 2
    elif any(c == RiskCategory.unknown for c in delay_cats):
        known_nums = [n for n, c in zip(delay_nums, delay_cats) if c != RiskCategory.unknown]
        if known_nums:
            delay_num = max(known_nums)
            delay_cat = {1: RiskCategory.low, 2: RiskCategory.medium, 3: RiskCategory.high}.get(delay_num, RiskCategory.medium)
        else:
            delay_cat, delay_num = RiskCategory.unknown, 2
    else:
        delay_num = max(delay_nums)
        delay_cat = {1: RiskCategory.low, 2: RiskCategory.medium, 3: RiskCategory.high}.get(delay_num, RiskCategory.medium)

    return crowd_cat, crowd_num, delay_cat, delay_num, uses_fallback


def estimate_cost(distance_m: float, duration_s: float, mode: str) -> dict:
    """
    Return a cost breakdown dict with itemised components.

    Public transit: Singapore adult card fare (TransitLink distance-based).
    Taxi/driving:   ComfortDelGro metered fare structure.
    """
    distance_km = max(0.0, distance_m) / 1000.0
    duration_min = max(0.0, duration_s) / 60.0

    if mode == "driving":
        # ComfortDelGro taxi meter (2024 rates)
        flag_down = 4.00
        # First 10km: $0.22 per 400m = $0.55/km
        # After 10km: $0.22 per 350m ≈ $0.629/km
        if distance_km <= 10:
            distance_charge = distance_km * 0.55
        else:
            distance_charge = (10 * 0.55) + ((distance_km - 10) * 0.629)
        # Waiting / slow speed: $0.22 per 45s of waiting
        # Approximate idle time as 20% of total duration for city driving
        idle_min = duration_min * 0.20
        waiting_charge = (idle_min * 60 / 45) * 0.22
        total = flag_down + distance_charge + waiting_charge
        return {
            "total": round(total, 2),
            "flag_down": round(flag_down, 2),
            "distance_charge": round(distance_charge, 2),
            "distance_km": round(distance_km, 2),
            "waiting_charge": round(waiting_charge, 2),
            "mode": "taxi",
        }
    else:
        # Singapore public transit — adult card fare (TransitLink 2024)
        # Distance-based fare table (approximate per-km brackets):
        #   0 - 3.2 km:  $0.99
        #   3.2 - 4.2:   $1.09
        #   4.2 - 5.2:   $1.19
        #   5.2 - 6.2:   $1.29
        #   6.2 - 7.2:   $1.29
        #   7.2 - 8.2:   $1.36
        #   8.2 - 9.2:   $1.38
        #   9.2 - 10.2:  $1.40
        #   10.2 - 11.2: $1.42
        #   11.2 - 12.2: $1.44
        #   ... +$0.02 per km after that, capped at ~$2.20 (40.2km+)
        fare_table = [
            (3.2, 0.99), (4.2, 1.09), (5.2, 1.19), (6.2, 1.29),
            (7.2, 1.29), (8.2, 1.36), (9.2, 1.38), (10.2, 1.40),
            (11.2, 1.42), (12.2, 1.44), (13.2, 1.46), (14.2, 1.48),
            (15.2, 1.50), (16.2, 1.52), (17.2, 1.54), (18.2, 1.56),
            (19.2, 1.58), (20.2, 1.60), (22.2, 1.62), (24.2, 1.66),
            (26.2, 1.70), (28.2, 1.74), (30.2, 1.78), (32.2, 1.82),
            (34.2, 1.86), (36.2, 1.90), (38.2, 1.94), (40.2, 1.98),
        ]
        fare = 2.20  # max fare (40.2km+)
        for threshold, f in fare_table:
            if distance_km <= threshold:
                fare = f
                break
        return {
            "total": round(fare, 2),
            "base_fare": round(fare, 2),
            "distance_km": round(distance_km, 2),
            "mode": "transit",
        }


def build_route_steps(route: Dict, segments: List[SegmentAssessment]) -> Tuple[List[RouteStep], str, int]:
    """
    Build rich RouteStep list from the Google route + assessed segments.
    Returns (steps, path_summary, transfer_count).
    """
    mode = route.get("requested_mode", "transit")

    # Driving: single step
    if mode == "driving":
        leg = (route.get("legs") or [{}])[0]
        dur_s = (leg.get("duration") or {}).get("value", 0)
        dist_m = (leg.get("distance") or {}).get("value", 0)
        start = leg.get("start_address") or "Origin"
        end = leg.get("end_address") or "Destination"
        seg = segments[0] if segments else None
        step = RouteStep(
            mode="Drive",
            from_name=start,
            to_name=end,
            duration_min=round(dur_s / 60.0, 1),
            distance_m=dist_m,
            delay=seg.delay if seg else None,
        )
        return [step], f"Drive to {end}", 0

    try:
        google_steps = route["legs"][0]["steps"]
    except Exception:
        return [], "", 0

    # Build a lookup: (dep_stop, arr_stop) -> SegmentAssessment for transit segments
    seg_lookup: Dict[Tuple[str, str], SegmentAssessment] = {}
    for seg in segments:
        seg_lookup[(seg.from_name, seg.to_name)] = seg

    route_steps: List[RouteStep] = []
    summary_parts: List[str] = []
    transit_count = 0

    for gstep in google_steps:
        tm = gstep.get("travel_mode")
        dur_s = (gstep.get("duration") or {}).get("value", 0)
        dist_m = (gstep.get("distance") or {}).get("value", 0)

        if tm == "WALKING":
            dur_min = round(dur_s / 60.0, 1)
            if dur_min < 0.5:
                continue  # skip trivial walks
            # Figure out where the walk goes
            start_loc = gstep.get("start_location") or {}
            end_loc = gstep.get("end_location") or {}
            # Use surrounding transit stops for better naming
            from_name = "Start"
            to_name = "Next stop"
            route_steps.append(RouteStep(
                mode="Walk",
                from_name=from_name,
                to_name=to_name,
                duration_min=dur_min,
                distance_m=dist_m,
            ))
            summary_parts.append(f"Walk {dur_min}min")

        elif tm == "TRANSIT":
            transit_count += 1
            details = gstep.get("transit_details", {})
            line = details.get("line", {})
            vehicle_raw = ((line.get("vehicle", {}) or {}).get("type") or "").upper()
            mode_name = _VEHICLE_MODE_MAP.get(vehicle_raw, vehicle_raw.title() or "Transit")
            line_name = line.get("short_name") or line.get("name") or ""
            dep_stop = (details.get("departure_stop") or {}).get("name", "")
            arr_stop = (details.get("arrival_stop") or {}).get("name", "")
            dep_time = (details.get("departure_time") or {}).get("text")
            arr_time = (details.get("arrival_time") or {}).get("text")
            headsign = details.get("headsign")
            num_stops = details.get("num_stops")

            # Find matching assessment segment
            seg = seg_lookup.get((dep_stop, arr_stop))

            route_steps.append(RouteStep(
                mode=mode_name,
                from_name=dep_stop,
                to_name=arr_stop,
                duration_min=round(dur_s / 60.0, 1),
                distance_m=dist_m,
                line_name=line_name,
                num_stops=num_stops,
                departure_time=dep_time,
                arrival_time=arr_time,
                headsign=headsign,
                crowding=seg.crowding if seg else None,
                delay=seg.delay if seg else None,
            ))
            summary_parts.append(f"{mode_name} {line_name} ({dep_stop} -> {arr_stop})")

    # Improve walk step names using surrounding transit stops
    _fix_walk_names(route_steps, route)

    transfers = max(0, transit_count - 1)
    path_summary = " -> ".join(summary_parts)
    return route_steps, path_summary, transfers


def _fix_walk_names(steps: List[RouteStep], route: Dict) -> None:
    """Fill in walk step from/to names using adjacent transit stops and route addresses."""
    leg = (route.get("legs") or [{}])[0]
    start_addr = leg.get("start_address") or "Origin"
    end_addr = leg.get("end_address") or "Destination"

    for i, step in enumerate(steps):
        if step.mode != "Walk":
            continue
        # from_name: previous transit arrival stop, or route start
        prev_transit = None
        for j in range(i - 1, -1, -1):
            if steps[j].mode != "Walk":
                prev_transit = steps[j]
                break
        # to_name: next transit departure stop, or route end
        next_transit = None
        for j in range(i + 1, len(steps)):
            if steps[j].mode != "Walk":
                next_transit = steps[j]
                break

        step.from_name = prev_transit.to_name if prev_transit else start_addr
        step.to_name = next_transit.from_name if next_transit else end_addr


def rank_routes(candidate_routes: List[Dict], weights: Dict[str, float]) -> List[Dict]:
    """Rank routes using 4 dimensions: time, cost, risk, comfort."""
    # Compute combined risk and comfort raw values
    for r in candidate_routes:
        r["risk_num"] = compute_risk(r.get("risk_crowding_num", 2), r.get("risk_delay_num", 2))
        r["comfort_num"] = compute_comfort(r.get("walk_min", 0.0), r.get("transfers", 0))

    times = [r.get("time_min", 0.0) for r in candidate_routes]
    costs = [r.get("cost_est", 0.0) for r in candidate_routes]
    risks = [r.get("risk_num", 2.0) for r in candidate_routes]
    comforts = [r.get("comfort_num", 0.0) for r in candidate_routes]

    nt = normalize(times)
    nc = normalize(costs)
    nr = normalize(risks)
    nf = normalize(comforts)

    for i, r in enumerate(candidate_routes):
        r["normalized_time"] = nt[i]
        r["normalized_cost"] = nc[i]
        r["normalized_risk"] = nr[i]
        r["normalized_comfort"] = nf[i]
        r["score"] = composite_score(
            {
                "time": r["normalized_time"],
                "cost": r["normalized_cost"],
                "risk": r["normalized_risk"],
                "comfort": r["normalized_comfort"],
            },
            weights,
        )

    ranked = sorted(candidate_routes, key=lambda r: (r["score"], tie_break_key(r)))
    return ranked


def add_explanations(routes: List[Dict], weights: Dict[str, float]) -> None:
    sorted_w = sorted(
        [("time", weights.get("time", 0.0)), ("cost", weights.get("cost", 0.0)),
         ("risk", weights.get("risk", 0.0)), ("comfort", weights.get("comfort", 0.0))],
        key=lambda x: x[1],
        reverse=True,
    )
    top_key = sorted_w[0][0]
    for r in routes:
        r["explanation"] = explain(r, top_key)
