"""In-memory idempotency guard.

Swap the set for Redis (SETNX with a TTL) in production — the
interface stays the same so callers don't change.
"""
from __future__ import annotations

import threading


class IdempotencyStore:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._lock = threading.Lock()

    def check_and_set(self, key: str) -> bool:
        """Returns True the first time `key` is seen, False on replay."""
        with self._lock:
            if key in self._seen:
                return False
            self._seen.add(key)
            return True


idempotency_store = IdempotencyStore()
