"""Event payloads published at each transaction state transition.

Consumers (reconciliation, analytics, audit) subscribe to these
independently of the live payment path — a slow or failing consumer
never blocks the transaction itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TransactionEvent:
    transaction_id: str
    event_type: str  # matches a TransactionState value
    payload: dict[str, Any]
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
