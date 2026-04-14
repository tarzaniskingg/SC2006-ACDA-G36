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
    import lta_api
    return global_cache.get_or_fetch(
        f"bus_arrival:{bus_stop_code}",
        lambda: lta_api.get_bus_arrival(bus_stop_code),
        get_settings().ttl_bus_arrival,
    )


def get_pcd_forecast(train_line: str = None) -> Tuple[Dict[str, Any], float, bool]:
    import lta_api
    key = f"pcd_forecast:{train_line}" if train_line else "pcd_forecast"
    return global_cache.get_or_fetch(
        key,
        lambda: lta_api.get_pcd_forecast(train_line=train_line),
        get_settings().ttl_pcd,
    )


def get_train_service_alerts() -> Tuple[Dict[str, Any], float, bool]:
    import lta_api
    return global_cache.get_or_fetch(
        "train_service_alerts",
        lta_api.get_train_service_alerts,
        60,
    )


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
    import lta_api
    return global_cache.get_or_fetch(
        "traffic_speed_bands",
        lta_api.get_traffic_speed_bands,
        get_settings().ttl_speed_bands,
    )


def get_bus_stops() -> Tuple[Any, float, bool]:
    import lta_api
    return global_cache.get_or_fetch("bus_stops", lta_api.get_bus_stops, 86400)


def get_carpark_availability() -> Tuple[Dict[str, Any], float, bool]:
    import lta_api
    return global_cache.get_or_fetch(
        "carpark_availability",
        lta_api.get_carpark_availability,
        get_settings().ttl_carpark,
    )
