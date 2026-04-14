import threading
import time
from typing import Any, Callable, Dict, Optional


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
        self._locks: Dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()

    def _key_lock(self, key: str) -> threading.Lock:
        """Get or create a per-key lock (prevents duplicate fetches)."""
        with self._locks_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def get(self, key: str) -> Optional[CacheItem]:
        return self._data.get(key)

    def set(self, key: str, value: Any, ttl_sec: int, source: str = "realtime") -> CacheItem:
        item = CacheItem(value=value, ttl_sec=ttl_sec, source=source)
        self._data[key] = item
        return item

    def get_or_fetch(self, key: str, fetcher: Callable[[], Any], ttl_sec: int) -> "tuple[Any, float, bool]":
        """Get from cache or fetch exactly once (other threads wait).

        Returns (value, retrieved_at, was_fallback).
        """
        item = self._data.get(key)
        if item and not item.is_expired:
            return item.value, item.retrieved_at, False

        lock = self._key_lock(key)
        with lock:
            # Double-check after acquiring lock
            item = self._data.get(key)
            if item and not item.is_expired:
                return item.value, item.retrieved_at, False
            try:
                value = fetcher()
                new_item = self.set(key, value, ttl_sec, source="realtime")
                return new_item.value, new_item.retrieved_at, False
            except Exception:
                # Return stale data if available
                if item is not None:
                    return item.value, item.retrieved_at, True
                return {}, 0.0, True

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

