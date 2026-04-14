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
    # PCD Forecast updates once per 24h — cache for 6 hours to reduce API calls
    return global_cache.get_or_fetch(
        key,
        lambda: lta_api.get_pcd_forecast(train_line=train_line),
        21600,
    )


def get_pcd_realtime(train_line: str = None) -> Tuple[Dict[str, Any], float, bool]:
    import lta_api
    key = f"pcd_realtime:{train_line}" if train_line else "pcd_realtime"
    return global_cache.get_or_fetch(
        key,
        lambda: lta_api.get_pcd_realtime(train_line=train_line),
        60,  # 60s TTL — real-time data updates every 10 min
    )


def get_train_service_alerts() -> Tuple[Dict[str, Any], float, bool]:
    import lta_api
    return global_cache.get_or_fetch(
        "train_service_alerts",
        lta_api.get_train_service_alerts,
        60,
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
