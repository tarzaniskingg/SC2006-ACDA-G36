import time
from typing import Any, Dict, Optional


class CacheItem:
    def __init__(self, value: Any, ttl_sec: int, source: str = "realtime") -> None:
        self.value = value
        self.ttl_sec = ttl_sec
        self.source = source
        self.retrieved_at = time.time()

    @property
    def is_expired(self) -> bool:
        return time.time() - self.retrieved_at > self.ttl_sec


class TTLCache:
    def __init__(self) -> None:
        self._data: Dict[str, CacheItem] = {}

    def get(self, key: str) -> Optional[CacheItem]:
        return self._data.get(key)

    def set(self, key: str, value: Any, ttl_sec: int, source: str = "realtime") -> CacheItem:
        item = CacheItem(value=value, ttl_sec=ttl_sec, source=source)
        self._data[key] = item
        return item

    def invalidate(self, key: Optional[str] = None) -> None:
        if key is None:
            self._data.clear()
        else:
            self._data.pop(key, None)

    def status(self) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for k, v in self._data.items():
            out[k] = {
                "last_retrieved": v.retrieved_at,
                "ttl_sec": v.ttl_sec,
                "is_fallback": v.source == "fallback" or v.is_expired,
                "source": v.source,
            }
        return out


global_cache = TTLCache()

