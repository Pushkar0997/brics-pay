"""
Event schemas for the transaction event stream.

One event is published on every state transition of a transaction. In
production this stream is what reconciliation, regulatory reporting,
customer notifications, and fraud-model retraining all consume — so the
schema is deliberately flat and self-contained (a consumer should never
have to call back into payment_router to make sense of an event).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from common.models import TransactionState


class TransactionEvent(BaseModel):
    event_id: str
    transaction_id: str
    idempotency_key: str
    previous_state: Optional[TransactionState]
    new_state: TransactionState
    payer_country: str
    payee_country: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detail: dict = Field(default_factory=dict)
    source_service: str = "payment_router"

    class Config:
        use_enum_values = True


TOPIC_TRANSACTION_EVENTS = "brics-pay.transaction-events"
