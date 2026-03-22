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


def get_2hr_forecast() -> Tuple[Dict[str, Any], float, bool]:
    """Fetch NEA 2-hour weather forecast. Cached for 600s."""
    key = "nea_2hr_forecast"
    cached_val, ts, expired = _get_cached(key)
    if cached_val and not expired:
        return cached_val, ts, False
    try:
        url = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
        req = urllib.request.Request(url, headers={"User-Agent": "SGTravelBud/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        val, ts, _ = _set_cache(key, data, 600)
        return val, ts, False
    except Exception:
        if cached_val is not None:
            return cached_val, ts, True
        return {}, 0.0, True
