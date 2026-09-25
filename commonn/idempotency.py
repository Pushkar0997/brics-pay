"""
Idempotency-key guard.

Cross-border payment APIs must be safe to retry: a bank's PSP might time
out waiting for a response and resend the exact same request. Without an
idempotency guard, that retry becomes a second, real transfer of money.

This in-memory implementation is a stand-in for a production store — see
the class docstring for the swap-in.
"""

import time
from dataclasses import dataclass
from threading import Lock
from typing import Optional

from common.config import settings


@dataclass
class _Entry:
    transaction_id: str
    created_at: float


class IdempotencyStore:
    """
    STUB: process-local dict guarded by a lock.

    PRODUCTION SWAP-IN: Redis (or DynamoDB with a TTL attribute), using
    `SET key value NX EX <ttl>` so the "claim this key" check-and-set is
    atomic across replicas of the API gateway — a process-local dict only
    protects one pod, which is useless the moment you run more than one
    replica (and payment_router's HPA scales to 200 pods under load, see
    infra/k8s/payment-router-hpa.yaml).
    """

    def __init__(self, ttl_seconds: Optional[int] = None):
        self._ttl = ttl_seconds or settings.idempotency_ttl_seconds
        self._store: dict[str, _Entry] = {}
        self._lock = Lock()

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [k for k, e in self._store.items() if now - e.created_at > self._ttl]
        for k in expired:
            del self._store[k]

    def claim(self, idempotency_key: str, transaction_id: str) -> tuple[bool, Optional[str]]:
        """
        Attempt to claim `idempotency_key` for `transaction_id`.

        Returns (claimed, existing_transaction_id):
          - (True, None)               -> key was free, now claimed by this transaction
          - (False, existing_txn_id)   -> key already claimed by an earlier transaction;
                                           caller should return that transaction's state
                                           instead of processing again.
        """
        with self._lock:
            self._evict_expired()
            existing = self._store.get(idempotency_key)
            if existing is not None:
                return False, existing.transaction_id
            self._store[idempotency_key] = _Entry(transaction_id=transaction_id, created_at=time.time())
            return True, None


# Process-wide singleton for the demo. See class docstring re: Redis swap-in
# once this runs as more than one replica.
idempotency_store = IdempotencyStore()
