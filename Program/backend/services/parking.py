"""Carpark availability service — finds nearby carparks at driving destination."""

from typing import Dict, List, Optional
from ..clients import lta as lta_client
from .geo import haversine_m as _haversine_m


def find_nearby_carparks(
    dest_lat: float,
    dest_lng: float,
    radius_m: float = 800,
    max_results: int = 5,
) -> Optional[Dict]:
    """
    Find carparks near a destination using LTA CarParkAvailability API.
    Returns structured data with availability status, or None if no data.
    """
    data, ts, was_fallback = lta_client.get_carpark_availability()
    if not data:
        return None

    items = data.get("value") or []
    if not items:
        return None

    nearby = []
    seen_ids = set()

    for cp in items:
        # Only car lots
        if cp.get("LotType") != "C":
            continue

        # Deduplicate by CarParkID
        cpid = cp.get("CarParkID", "")
        if cpid in seen_ids:
            continue
        seen_ids.add(cpid)

        # Parse location "lat lng"
        loc = cp.get("Location") or ""
        try:
            parts = loc.split()
            if len(parts) < 2:
                continue
            cp_lat = float(parts[0])
            cp_lng = float(parts[1])
        except (ValueError, IndexError):
            continue

        dist = _haversine_m(dest_lat, dest_lng, cp_lat, cp_lng)
        if dist > radius_m:
            continue

        try:
            available = int(cp.get("AvailableLots", 0))
        except (TypeError, ValueError):
            available = 0

        nearby.append({
            "name": cp.get("Development") or f"Carpark {cpid}",
            "available_lots": available,
            "distance_m": round(dist),
            "area": cp.get("Area") or "",
            "agency": cp.get("Agency") or "",
        })

    if not nearby:
        return None

    # Sort by distance, take top results
    nearby.sort(key=lambda x: x["distance_m"])
    nearby = nearby[:max_results]

    total_available = sum(cp["available_lots"] for cp in nearby)

    if total_available == 0:
        status = "full"
    elif total_available <= 20:
        status = "limited"
    else:
        status = "available"

    return {
        "nearby_count": len(nearby),
        "total_available_lots": total_available,
        "status": status,
        "carparks": nearby,
    }
