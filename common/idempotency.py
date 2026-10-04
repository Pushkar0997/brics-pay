"""In-memory idempotency guard.

Swap the dicts for Redis (SET NX with a TTL) in production - the
interface stays the same so callers don't change. In-memory is only
valid for tests and the single-process demo (CONTRACT: INV-2).
"""
from __future__ import annotations

import threading
from typing import Any


class IdempotencyStore:
    def __init__(self) -> None:
        self._in_progress: set[str] = set()
        self._results: dict[str, Any] = {}
        self._lock = threading.Lock()

    def claim(self, key: str) -> tuple[bool, Any | None]:
        """Returns (True, None) if the caller owns the key, or
        (False, stored_result) on a repeat (None while still in flight)."""
        with self._lock:
            if key in self._results:
                return False, self._results[key]
            if key in self._in_progress:
                return False, None
            self._in_progress.add(key)
            return True, None

    def complete(self, key: str, result: Any) -> None:
        with self._lock:
            self._results[key] = result
            self._in_progress.discard(key)

    def release(self, key: str) -> None:
        """Give the key back after a crash so the client can retry."""
        with self._lock:
            self._in_progress.discard(key)

    def check_and_set(self, key: str) -> bool:
        claimed, _ = self.claim(key)
        return claimed


idempotency_store = IdempotencyStore()