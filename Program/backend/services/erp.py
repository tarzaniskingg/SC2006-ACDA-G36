"""ERP gantry proximity calculation for driving routes."""

import json
import math
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple


_FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")
_erp_gantries: Optional[List[Dict]] = None


def _load_gantries() -> List[Dict]:
    global _erp_gantries
    if _erp_gantries is not None:
        return _erp_gantries
    path = os.path.join(_FIXTURES_DIR, "erp_gantries.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _erp_gantries = json.load(f)
    except Exception:
        _erp_gantries = []
    return _erp_gantries


def _haversine_m(lat1, lng1, lat2, lng2):
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _decode_polyline(encoded: str) -> List[Tuple[float, float]]:
    """Decode Google's encoded polyline into list of (lat, lng) tuples."""
    points = []
    index = 0
    lat = lng = 0
    while index < len(encoded):
        for coord in range(2):
            shift = result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if coord == 0:
                lat += delta
            else:
                lng += delta
        points.append((lat / 1e5, lng / 1e5))
    return points


def _get_rate_for_time(schedule: List[Dict], dt: datetime) -> float:
    """Look up ERP rate from a gantry's schedule for the given time."""
    sgt = dt.astimezone(timezone(timedelta(hours=8))) if dt.tzinfo else dt
    day = sgt.strftime("%A")
    time_str = sgt.strftime("%H:%M")
    is_weekday = day not in ("Saturday", "Sunday")

    for slot in schedule:
        if slot.get("day") == "weekday" and not is_weekday:
            continue
        if slot.get("day") == "saturday" and day != "Saturday":
            continue
        if slot.get("start", "") <= time_str < slot.get("end", ""):
            return slot.get("rate", 0.0)
    return 0.0


def calculate_erp(
    overview_polyline: Optional[str],
    departure_time: Optional[datetime] = None,
) -> Optional[Dict]:
    """
    Calculate ERP charges for a driving route by checking proximity
    of the route polyline to known ERP gantry locations.
    """
    if not overview_polyline:
        return None

    gantries = _load_gantries()
    if not gantries:
        return None

    points = _decode_polyline(overview_polyline)
    if not points:
        return None

    dt = departure_time or datetime.now(timezone(timedelta(hours=8)))

    # Check each gantry: if any polyline point is within 80m, consider it passed
    passed_gantries = []
    for gantry in gantries:
        glat = gantry.get("lat", 0)
        glng = gantry.get("lng", 0)
        for plat, plng in points:
            if _haversine_m(plat, plng, glat, glng) < 80:
                rate = _get_rate_for_time(gantry.get("schedule", []), dt)
                if rate > 0:
                    passed_gantries.append({
                        "name": gantry.get("name", "ERP Gantry"),
                        "charge": rate,
                    })
                break  # don't double-count same gantry

    total = sum(g["charge"] for g in passed_gantries)
    if not passed_gantries:
        return None

    return {
        "total": round(total, 2),
        "gantries": passed_gantries,
    }
