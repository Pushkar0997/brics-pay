"""Shared domain models used across every BRICS Pay service."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4

# Illustrative country -> settlement currency map. Adding a country
# means adding one line here plus one adapter file — the core never
# changes shape.
COUNTRY_CURRENCY: dict[str, str] = {
    "IN": "INR",
    "CN": "CNY",
    "BR": "BRL",
    "RU": "RUB",
    "ZA": "ZAR",
}


class TransactionState(str, Enum):
    CREATED = "CREATED"
    AUTHENTICATED = "AUTHENTICATED"
    RISK_CHECKED = "RISK_CHECKED"
    FX_QUOTED = "FX_QUOTED"
    AUTHORIZED = "AUTHORIZED"
    DEBITED = "DEBITED"
    SETTLING = "SETTLING"
    SETTLED = "SETTLED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str  # ISO 4217, e.g. "INR", "CNY"

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("amount must be positive")
        if len(self.currency) != 3:
            raise ValueError("currency must be a 3-letter ISO code")


@dataclass(frozen=True)
class Party:
    party_id: str
    country: str        # ISO 3166-1 alpha-2, e.g. "IN", "CN"
    account_ref: str    # opaque reference into the domestic rail
    kyc_tier: int = 1    # 1 = basic, 2 = verified, 3 = enhanced


@dataclass
class TransactionRequest:
    payer: Party
    payee: Party
    send_amount: Money
    transaction_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    idempotency_key: str | None = None


@dataclass
class TransactionRecord:
    request: TransactionRequest
    state: TransactionState
    receive_amount: Money | None = None
    fx_rate: Decimal | None = None
    risk_score: float | None = None
    failure_reason: str | None = None
    history: list[TransactionState] = field(default_factory=list)

    def transition(self, new_state: TransactionState) -> None:
        self.history.append(self.state)
        self.state = new_state
