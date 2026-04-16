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


def compute_comfort(walk_min: float, transfers: int, rain: bool = False) -> float:
    """Combine walking time and transfers into a single comfort score.
    Higher = less comfortable. Both are normalized to roughly 0-10 range
    before combining so neither dominates.
    When rain is forecasted, a flat penalty scaled by walking time is added
    so that even heavy-walk routes (which already hit the cap) are penalized.
    """
    # Walk: cap at 30 min for normalization (above 30 is equally bad)
    walk_score = min(walk_min, 30.0) / 3.0  # 0-10 range
    # Transfers: 0-5 range mapped to 0-10
    transfer_score = min(transfers, 5) * 2.0  # 0-10 range
    base = 0.6 * walk_score + 0.4 * transfer_score
    if rain and walk_min > 0:
        # Rain penalty: +3 per 10 min of walking (uncapped, proportional to exposure)
        rain_penalty = (walk_min / 10.0) * 3.0
        return base + rain_penalty
    return base


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


def _raw(route: Dict, key: str) -> float:
    """Raw comparable value for a factor (lower = better for all)."""
    if key == "time":
        return route.get("time_min", 0)
    if key == "cost":
        return route.get("cost_est", 0)
    if key == "risk":
        return route.get("risk_num", 0)
    if key == "comfort":
        return route.get("comfort_num", 0)
    return 0


def _value_label(route: Dict, key: str) -> str:
    """Short label for a factor's current value."""
    if key == "time":
        return f"{int(route.get('time_min', 0))} min"
    if key == "cost":
        return f"${route.get('cost_est', 0):.2f}"
    if key == "risk":
        return f"{route.get('risk_cat', 'Unknown').lower()} risk"
    if key == "comfort":
        walk = round(route.get("walk_min", 0))
        trf = route.get("transfers", 0)
        return f"{walk} min walk, {trf} transfer{'s' if trf != 1 else ''}"
    return ""


def _best_label(route: Dict, key: str) -> str:
    """Superlative phrase for the #1 route on a factor."""
    if key == "time":
        return f"Fastest at {int(route.get('time_min', 0))} min"
    if key == "cost":
        return f"Cheapest at ${route.get('cost_est', 0):.2f}"
    if key == "risk":
        return f"Lowest risk ({route.get('risk_cat', 'Unknown').lower()})"
    if key == "comfort":
        walk = round(route.get("walk_min", 0))
        trf = route.get("transfers", 0)
        return f"Most comfortable ({walk} min walk, {trf} transfer{'s' if trf != 1 else ''})"
    return ""


def _edge_label(route: Dict, key: str, better: bool) -> str:
    """Comparative phrase vs another route (better=True: advantage, False: disadvantage)."""
    if better:
        if key == "time":
            return f"faster at {int(route.get('time_min', 0))} min"
        if key == "cost":
            return f"cheaper at ${route.get('cost_est', 0):.2f}"
        if key == "risk":
            return f"lower risk ({route.get('risk_cat', 'Unknown').lower()})"
        if key == "comfort":
            walk = round(route.get("walk_min", 0))
            trf = route.get("transfers", 0)
            return f"more comfortable ({walk} min walk, {trf} transfer{'s' if trf != 1 else ''})"
    else:
        if key == "time":
            return f"slower ({int(route.get('time_min', 0))} min)"
        if key == "cost":
            return f"pricier (${route.get('cost_est', 0):.2f})"
        if key == "risk":
            return f"higher risk ({route.get('risk_cat', 'Unknown').lower()})"
        if key == "comfort":
            walk = round(route.get("walk_min", 0))
            trf = route.get("transfers", 0)
            return f"less comfortable ({walk} min walk, {trf} transfer{'s' if trf != 1 else ''})"
    return ""


def _build_explanation(route: Dict, rank: int, all_routes: List[Dict],
                       factor_order: List[str], all_same: Dict[str, bool]) -> str:
    pieces: List[str] = []
    top = factor_order[0]

    # First factor (by priority) that actually differs across routes
    diff = next((k for k in factor_order if not all_same[k]), None)

    # --- Lead sentence ---
    if rank == 0:
        if diff and diff == top:
            # Top priority differentiates — lead with it
            pieces.append(_best_label(route, top))
        elif diff:
            # Top priority is identical for all routes — say so, highlight differentiator
            stats = [_value_label(route, k) for k in factor_order
                     if k != top and not all_same.get(k, True)][:2]
            stat_str = ", ".join(stats) if stats else _value_label(route, diff)
            pieces.append(
                f"Best overall \u2014 {stat_str} (all routes have {_value_label(route, top)})"
            )
        else:
            pieces.append(f"Top ranked \u2014 {_value_label(route, top)}")
    else:
        best = all_routes[0]
        adv = next(
            (k for k in factor_order
             if not all_same[k] and _raw(route, k) < _raw(best, k)), None)
        dis = next(
            (k for k in factor_order
             if not all_same[k] and _raw(route, k) > _raw(best, k)), None)

        if adv and dis:
            pieces.append(
                f"{_edge_label(route, adv, True).capitalize()} but {_edge_label(route, dis, False)}"
            )
        elif adv:
            pieces.append(_edge_label(route, adv, True).capitalize())
        elif dis:
            pieces.append(_edge_label(route, dis, False).capitalize())
        else:
            pieces.append(f"Similar to top route \u2014 {_value_label(route, top)}")

    # --- Per-step crowding highlights ---
    steps = route.get("steps", [])
    crowded, clear = [], []
    for s in steps:
        if not isinstance(s, dict):
            continue
        c = s.get("crowding")
        if not c or not isinstance(c, dict):
            continue
        cat = c.get("category", "Unknown")
        label = f"{s.get('mode', '')} {s.get('line_name', '')}".strip()
        if cat == "High":
            crowded.append(label)
        elif cat == "Low":
            clear.append(label)

    if crowded:
        pieces.append(f"Crowded: {', '.join(crowded)}")
    if clear:
        pieces.append(f"Not crowded: {', '.join(clear)}")

    # Walking info (skip if comfort was already the lead to avoid repetition)
    used_comfort = (diff == "comfort") if rank == 0 else False
    if not used_comfort:
        walk = route.get("walk_min", 0)
        if walk > 0:
            pieces.append(f"{round(walk)} min walking")

    if route.get("uses_fallback"):
        pieces.append("(some data is estimated)")

    return ". ".join(pieces)
