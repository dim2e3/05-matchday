import time


class TTLCache[T]:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            return None
        return value

    def get_stale(self, key: str) -> T | None:
        entry = self._store.get(key)
        return entry[1] if entry is not None else None

    def set(self, key: str, value: T) -> None:
        self._store[key] = (time.monotonic() + self._ttl, value)
