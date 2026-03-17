from typing import List, Dict


RISK_NUMERIC = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Unknown": 2,
}


def normalize(values: List[float], invert: bool = False) -> List[float]:
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        return [0.0 for _ in values]
    rng = vmax - vmin
    norms = [(v - vmin) / rng for v in values]
    if invert:
        return [1.0 - n for n in norms]
    return norms


def compute_risk(crowding_num: int, delay_num: int) -> float:
    """Combine crowding and delay into a single risk score (1-3 scale)."""
    return max(crowding_num, delay_num)


def compute_comfort(walk_min: float, transfers: int) -> float:
    """Combine walking time and transfers into a single comfort score.
    Higher = less comfortable. Both are normalized to roughly 0-10 range
    before combining so neither dominates.
    """
    # Walk: cap at 30 min for normalization (above 30 is equally bad)
    walk_score = min(walk_min, 30.0) / 3.0  # 0-10 range
    # Transfers: 0-5 range mapped to 0-10
    transfer_score = min(transfers, 5) * 2.0  # 0-10 range
    return 0.6 * walk_score + 0.4 * transfer_score


def composite_score(normalized: Dict[str, float], weights: Dict[str, float]) -> float:
    """Weighted sum over the 4 dimensions: time, cost, risk, comfort."""
    keys = ["time", "cost", "risk", "comfort"]
    total_w = sum(weights.get(k, 0.0) for k in keys) or 1.0
    w = {k: weights.get(k, 0.0) / total_w for k in keys}
    return sum(w[k] * normalized.get(k, 0.0) for k in keys)


def tie_break_key(route: Dict) -> tuple:
    """Tie-breaker: risk → comfort → time → cost."""
    return (
        route.get("risk_num", 99),
        route.get("comfort_num", 99),
        route.get("time_min", 1e9),
        route.get("cost_est", 1e9),
    )


def explain(route: Dict, top_weight: str) -> str:
    pieces = []
    if top_weight == "time":
        pieces.append(f"Fastest option at {int(route.get('time_min', 0))} min")
    elif top_weight == "risk":
        risk_cat = route.get("risk_cat", "Unknown")
        pieces.append(f"Lowest risk: {risk_cat}")
    elif top_weight == "comfort":
        walk = route.get("walk_min", 0)
        trf = route.get("transfers", 0)
        pieces.append(f"Most comfortable: {round(walk)} min walk, {trf} transfer{'s' if trf != 1 else ''}")
    elif top_weight == "cost":
        pieces.append(f"Cheapest at ${route.get('cost_est', 0):.2f}")

    # Per-step crowding highlights
    steps = route.get("steps", [])
    crowded = []
    clear = []
    for s in steps:
        if not isinstance(s, dict):
            continue
        c = s.get("crowding")
        if not c:
            continue
        cat = c.get("category", "Unknown") if isinstance(c, dict) else "Unknown"
        label = f"{s.get('mode', '')} {s.get('line_name', '')}".strip()
        if cat == "High":
            crowded.append(label)
        elif cat == "Low":
            clear.append(label)

    if crowded:
        pieces.append(f"Crowded: {', '.join(crowded)}")
    if clear:
        pieces.append(f"Not crowded: {', '.join(clear)}")

    walk = route.get("walk_min", 0)
    if walk > 0:
        pieces.append(f"{round(walk)} min walking")

    if route.get("uses_fallback"):
        pieces.append("(some data is estimated)")
    return ". ".join(pieces)
