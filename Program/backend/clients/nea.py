"""NEA weather API client — 2-hour weather forecast (free, no key required)."""

import urllib.request
import json
from typing import Any, Dict, Tuple
from ..services.caching import global_cache


def _get_cached(key: str) -> Tuple[Any, float, bool]:
    item = global_cache.get(key)
    if not item:
        return None, 0.0, False
    return item.value, item.retrieved_at, item.is_expired


def _set_cache(key: str, value: Any, ttl: int) -> Tuple[Any, float, bool]:
    item = global_cache.set(key, value=value, ttl_sec=ttl, source="realtime")
    return item.value, item.retrieved_at, False


def _fetch_2hr_forecast():
    url = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
    req = urllib.request.Request(url, headers={"User-Agent": "SGTravelBud/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def get_2hr_forecast() -> Tuple[Dict[str, Any], float, bool]:
    """Fetch NEA 2-hour weather forecast. Cached for 600s."""
    return global_cache.get_or_fetch("nea_2hr_forecast", _fetch_2hr_forecast, 600)
