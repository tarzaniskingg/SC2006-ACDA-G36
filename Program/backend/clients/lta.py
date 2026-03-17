from typing import Any, Dict, Tuple
from ..services.caching import global_cache
from ..core.config import get_settings


def _get_cached(key: str) -> Tuple[Any, float, bool]:
    item = global_cache.get(key)
    if not item:
        return None, 0.0, False
    return item.value, item.retrieved_at, item.is_expired


def _set_cache(key: str, value: Any, ttl: int) -> Tuple[Any, float, bool]:
    item = global_cache.set(key, value=value, ttl_sec=ttl, source="realtime")
    return item.value, item.retrieved_at, False


def get_bus_arrival(bus_stop_code: str) -> Tuple[Dict[str, Any], float, bool]:
    key = f"bus_arrival:{bus_stop_code}"
    cached_val, ts, expired = _get_cached(key)
    if cached_val and not expired:
        return cached_val, ts, False
    try:
        import lta_api  # from Program/

        data = lta_api.get_bus_arrival(bus_stop_code)
        val, ts, _ = _set_cache(key, data, get_settings().ttl_bus_arrival)
        return val, ts, False
    except Exception:
        if cached_val is not None:
            return cached_val, ts, True
        return {}, 0.0, True


def get_pcd_forecast(train_line: str = None) -> Tuple[Dict[str, Any], float, bool]:
    key = f"pcd_forecast:{train_line}" if train_line else "pcd_forecast"
    cached_val, ts, expired = _get_cached(key)
    if cached_val and not expired:
        return cached_val, ts, False
    try:
        import lta_api

        data = lta_api.get_pcd_forecast(train_line=train_line)
        val, ts, _ = _set_cache(key, data, get_settings().ttl_pcd)
        return val, ts, False
    except Exception:
        if cached_val is not None:
            return cached_val, ts, True
        return {}, 0.0, True


def get_train_service_alerts() -> Tuple[Dict[str, Any], float, bool]:
    key = "train_service_alerts"
    cached_val, ts, expired = _get_cached(key)
    if cached_val and not expired:
        return cached_val, ts, False
    try:
        import lta_api

        data = lta_api.get_train_service_alerts()
        val, ts, _ = _set_cache(key, data, 60)  # 60s TTL
        return val, ts, False
    except Exception:
        if cached_val is not None:
            return cached_val, ts, True
        return {}, 0.0, True


def get_est_travel_times() -> Tuple[Dict[str, Any], float, bool]:
    key = "est_travel_times"
    cached_val, ts, expired = _get_cached(key)
    if cached_val and not expired:
        return cached_val, ts, False
    try:
        import lta_api

        data = lta_api.get_est_travel_time()
        val, ts, _ = _set_cache(key, data, get_settings().ttl_est_travel)
        return val, ts, False
    except Exception:
        if cached_val is not None:
            return cached_val, ts, True
        return {}, 0.0, True


def get_taxi_availability() -> Tuple[Dict[str, Any], float, bool]:
    key = "taxi_availability"
    cached_val, ts, expired = _get_cached(key)
    if cached_val and not expired:
        return cached_val, ts, False
    try:
        import lta_api

        data = lta_api.get_taxi_availability()
        val, ts, _ = _set_cache(key, data, get_settings().ttl_taxi)
        return val, ts, False
    except Exception:
        if cached_val is not None:
            return cached_val, ts, True
        return {}, 0.0, True


def get_traffic_speed_bands() -> Tuple[Dict[str, Any], float, bool]:
    key = "traffic_speed_bands"
    cached_val, ts, expired = _get_cached(key)
    if cached_val and not expired:
        return cached_val, ts, False
    try:
        import lta_api

        data = lta_api.get_traffic_speed_bands()
        val, ts, _ = _set_cache(key, data, get_settings().ttl_speed_bands)
        return val, ts, False
    except Exception:
        if cached_val is not None:
            return cached_val, ts, True
        return {}, 0.0, True


def get_bus_stops() -> Tuple[Any, float, bool]:
    key = "bus_stops"
    cached_val, ts, expired = _get_cached(key)
    if cached_val and not expired:
        return cached_val, ts, False
    try:
        import lta_api

        data = lta_api.get_bus_stops()
        # Cache for 24 hours — bus stop list rarely changes
        val, ts, _ = _set_cache(key, data, 86400)
        return val, ts, False
    except Exception:
        if cached_val is not None:
            return cached_val, ts, True
        return [], 0.0, True


def get_carpark_availability() -> Tuple[Dict[str, Any], float, bool]:
    key = "carpark_availability"
    cached_val, ts, expired = _get_cached(key)
    if cached_val and not expired:
        return cached_val, ts, False
    try:
        import lta_api

        data = lta_api.get_carpark_availability()
        val, ts, _ = _set_cache(key, data, get_settings().ttl_carpark)
        return val, ts, False
    except Exception:
        if cached_val is not None:
            return cached_val, ts, True
        return {}, 0.0, True
