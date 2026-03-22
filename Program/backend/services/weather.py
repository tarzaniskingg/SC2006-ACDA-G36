"""Weather-aware routing — matches NEA 2-hour forecast areas to route coordinates."""

import math
from typing import Optional, Dict, Tuple
from ..clients import nea

# NEA 24 forecast areas → approximate centroid lat/lng
_NEA_AREAS = {
    "Ang Mo Kio": (1.3691, 103.8454),
    "Bedok": (1.3236, 103.9273),
    "Bishan": (1.3526, 103.8352),
    "Boon Lay": (1.3199, 103.7066),
    "Bukit Batok": (1.3590, 103.7637),
    "Bukit Merah": (1.2819, 103.8239),
    "Bukit Panjang": (1.3774, 103.7719),
    "Bukit Timah": (1.3294, 103.7885),
    "Central Water Catchment": (1.3800, 103.8050),
    "Changi": (1.3544, 103.9890),
    "Choa Chu Kang": (1.3840, 103.7470),
    "Clementi": (1.3162, 103.7649),
    "City": (1.2921, 103.8545),
    "Geylang": (1.3201, 103.8918),
    "Hougang": (1.3612, 103.8863),
    "Jalan Bahar": (1.3474, 103.6998),
    "Jurong East": (1.3329, 103.7436),
    "Jurong Island": (1.2660, 103.6990),
    "Jurong West": (1.3404, 103.7090),
    "Kallang": (1.3117, 103.8628),
    "Lim Chu Kang": (1.4226, 103.7174),
    "Mandai": (1.4040, 103.8120),
    "Marine Parade": (1.3030, 103.8990),
    "Novena": (1.3205, 103.8430),
    "Pasir Ris": (1.3721, 103.9474),
    "Paya Lebar": (1.3580, 103.8920),
    "Pioneer": (1.3150, 103.6985),
    "Pulau Tekong": (1.3988, 104.0366),
    "Pulau Ubin": (1.4044, 103.9625),
    "Punggol": (1.3984, 103.9072),
    "Queenstown": (1.2942, 103.7861),
    "Seletar": (1.4040, 103.8700),
    "Sembawang": (1.4491, 103.8185),
    "Sengkang": (1.3868, 103.8914),
    "Sentosa": (1.2494, 103.8303),
    "Serangoon": (1.3554, 103.8679),
    "Southern Islands": (1.2330, 103.8320),
    "Sungei Kadut": (1.4130, 103.7500),
    "Tampines": (1.3496, 103.9568),
    "Tanglin": (1.3077, 103.8130),
    "Tengah": (1.3640, 103.7220),
    "Toa Payoh": (1.3343, 103.8563),
    "Tuas": (1.3000, 103.6500),
    "Western Islands": (1.2600, 103.7350),
    "Western Water Catchment": (1.4050, 103.6940),
    "Woodlands": (1.4382, 103.7891),
    "Yishun": (1.4304, 103.8354),
}

# Rain-related forecast keywords from NEA
_RAIN_KEYWORDS = {"rain", "shower", "thundery", "drizzle", "storm"}


def _haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _nearest_area(lat: float, lng: float) -> Optional[str]:
    best, best_d = None, 999
    for name, (alat, alng) in _NEA_AREAS.items():
        d = _haversine_km(lat, lng, alat, alng)
        if d < best_d:
            best_d = d
            best = name
    return best if best_d < 10 else None


def get_weather_for_route(
    origin_lat: float, origin_lng: float,
    dest_lat: float, dest_lng: float,
) -> Optional[Dict]:
    """
    Get weather forecast relevant to a route.
    Returns dict with forecast string, rain flag, and affected areas.
    """
    data, ts, was_fallback = nea.get_2hr_forecast()
    if not data:
        return None

    try:
        items = data.get("items") or []
        if not items:
            return None
        forecasts_list = items[0].get("forecasts") or []
        forecast_map = {f["area"]: f["forecast"] for f in forecasts_list}

        origin_area = _nearest_area(origin_lat, origin_lng)
        dest_area = _nearest_area(dest_lat, dest_lng)

        areas_checked = {}
        rain_detected = False
        for area in [origin_area, dest_area]:
            if area and area in forecast_map:
                fc = forecast_map[area]
                areas_checked[area] = fc
                if any(kw in fc.lower() for kw in _RAIN_KEYWORDS):
                    rain_detected = True

        if not areas_checked:
            return None

        return {
            "forecasts": areas_checked,
            "rain": rain_detected,
            "valid_period": items[0].get("valid_period", {}),
        }
    except Exception:
        return None
