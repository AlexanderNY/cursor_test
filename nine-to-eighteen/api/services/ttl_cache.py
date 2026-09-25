"""Process-local TTL cache with deep-copied values."""
from __future__ import annotations

import copy
import time
from threading import Lock
from typing import Any, Optional


class TtlCache:
    def __init__(self, ttl_sec: float = 300) -> None:
        self._ttl = float(ttl_sec)
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        now = time.monotonic()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, value = item
            if now >= expires_at:
                del self._data[key]
                return None
            return copy.deepcopy(value)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = (time.monotonic() + self._ttl, copy.deepcopy(value))

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
