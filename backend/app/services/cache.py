"""Tiny cache abstraction. In-memory TTL implementation; a Redis one would implement the same
two methods (see README, "Next steps" - not implemented)."""

import time
from typing import Any, Protocol


class Cache(Protocol):
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl: float = 30) -> None: ...
    def delete(self, key: str) -> None: ...


class MemoryCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._data.get(key)
        if not item:
            return None
        expires, value = item
        if expires < time.monotonic():
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: float = 30) -> None:
        self._data[key] = (time.monotonic() + ttl, value)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
