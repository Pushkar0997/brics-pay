"""
Shared domain models used by every service in the BRICS-Pay demo.

These are intentionally framework-light (pydantic only) so they can be
imported by FastAPI services, the event bus, and plain scripts/tests
without pulling in service-specific dependencies.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

class CountryCode(str, Enum):
    """ISO-3166 alpha-2 codes for the five rails this demo wires up."""

    INDIA = "IN"
    CHINA = "CN"
    BRAZIL = "BR"
    RUSSIA = "RU"
    SOUTH_AFRICA = "ZA"


class CurrencyCode(str, Enum):
    INR = "INR"
    CNY = "CNY"
    BRL = "BRL"
    RUB = "RUB"
    ZAR = "ZAR"
    USD = "USD"  # kept as a fallback / FX-quoting anchor, never settled in


# Rail (national payment system) each country is wired to. One rail per
# country in this demo; real deployments may support several per country.
COUNTRY_RAILS = {
    CountryCode.INDIA: "UPI",
    CountryCode.CHINA: "CIPS",
    CountryCode.BRAZIL: "PIX",
    CountryCode.RUSSIA: "SPFS",
    CountryCode.SOUTH_AFRICA: "RTC",
}

COUNTRY_CURRENCY = {
    CountryCode.INDIA: CurrencyCode.INR,
    CountryCode.CHINA: CurrencyCode.CNY,
    CountryCode.BRAZIL: CurrencyCode.BRL,
    CountryCode.RUSSIA: CurrencyCode.RUB,
    CountryCode.SOUTH_AFRICA: CurrencyCode.ZAR,
}


class TransactionState(str, Enum):
    """
    Legal states in the cross-border payment lifecycle.

    The *only* place transitions between these are allowed to happen is
    `services/payment_router/state_machine.py`. Every other service reports
    outcomes upward and lets the router decide the next state — this keeps
    the state machine the single source of truth for "what can happen next",
    which matters a lot once you have five countries' worth of regulators
    asking "how do you guarantee a payment can't be settled twice".
    """

    CREATED = "CREATED"
    RISK_SCREENING = "RISK_SCREENING"
    RISK_REJECTED = "RISK_REJECTED"
    COMPLIANCE_HOLD = "COMPLIANCE_HOLD"          # manual KYC/AML review
    FX_QUOTED = "FX_QUOTED"
    DEBIT_INITIATED = "DEBIT_INITIATED"           # payer-side rail call started
    DEBIT_CONFIRMED = "DEBIT_CONFIRMED"
    DEBIT_FAILED = "DEBIT_FAILED"
    SETTLING = "SETTLING"                         # ledger posting in progress
    CREDIT_INITIATED = "CREDIT_INITIATED"         # payee-side rail call started
    CREDIT_CONFIRMED = "CREDIT_CONFIRMED"
    CREDIT_FAILED = "CREDIT_FAILED"
    COMPLETED = "COMPLETED"
    REVERSING = "REVERSING"                       # compensating transaction running
    REVERSED = "REVERSED"
    FAILED = "FAILED"


TERMINAL_STATES = {
    TransactionState.COMPLETED,
    TransactionState.REVERSED,
    TransactionState.FAILED,
    TransactionState.RISK_REJECTED,
}


# --------------------------------------------------------------------------
# Value objects
# --------------------------------------------------------------------------

class Money(BaseModel):
    """
    Fixed-point money. We use Decimal (not float) everywhere financial
    amounts are handled — float rounding errors in a settlement ledger are
    the kind of bug that ends careers.
    """

    amount: Decimal = Field(..., gt=Decimal("0"))
    currency: CurrencyCode

    @field_validator("amount")
    @classmethod
    def _quantize(cls, v: Decimal) -> Decimal:
        # Two decimal places is fine for every currency in this demo; a real
        # system would look up each currency's minor-unit exponent (JPY=0,
        # BHD=3, etc.) from ISO 4217 rather than hardcoding 2.
        return v.quantize(Decimal("0.01"))

    def __str__(self) -> str:
        return f"{self.amount} {self.currency.value}"

    class Config:
        json_encoders = {Decimal: str}


class Party(BaseModel):
    """Either side of a transaction — payer or payee."""

    party_id: str
    display_name: str
    country: CountryCode
    account_ref: str = Field(..., description="Opaque account identifier on the national rail")
    bank_code: Optional[str] = None

    @property
    def rail(self) -> str:
        return COUNTRY_RAILS[self.country]

    @property
    def home_currency(self) -> CurrencyCode:
        return COUNTRY_CURRENCY[self.country]


# --------------------------------------------------------------------------
# Transaction request / record
# --------------------------------------------------------------------------

class TransactionRequest(BaseModel):
    """What the API gateway accepts from a calling bank/PSP."""

    idempotency_key: str = Field(..., min_length=8)
    payer: Party
    payee: Party
    send_amount: Money = Field(..., description="Amount debited from the payer, in payer's currency")
    purpose_code: str = Field(..., description="ISO 20022-style purpose code, e.g. 'TRADE_SETTLEMENT'")
    reference: Optional[str] = None

    @field_validator("send_amount")
    @classmethod
    def _currency_matches_payer(cls, v: Money, info):
        payer = info.data.get("payer")
        if payer is not None and v.currency != payer.home_currency:
            raise ValueError(
                f"send_amount currency {v.currency} does not match payer's "
                f"home currency {payer.home_currency}"
            )
        return v


class FXQuote(BaseModel):
    base_currency: CurrencyCode
    quote_currency: CurrencyCode
    mid_rate: Decimal
    applied_rate: Decimal  # mid_rate adjusted by spread
    spread_bps: int
    quoted_at: datetime


class RiskAssessment(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    decision: str  # "PASS" | "REJECT" | "HOLD"
    reasons: list[str] = Field(default_factory=list)
    model_version: str = "isoforest-v1+iqr-v1"


class ComplianceCheck(BaseModel):
    kyc_tier: str          # "TIER_1" | "TIER_2" | "TIER_3"
    aml_screened: bool
    sanctions_hit: bool
    decision: str          # "CLEAR" | "HOLD" | "BLOCK"
    notes: list[str] = Field(default_factory=list)


class LedgerEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str
    shard: str
    account_ref: str
    direction: str  # "DEBIT" | "CREDIT"
    amount: Money
    posted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TransactionRecord(BaseModel):
    """
    The full server-side record. This is what gets persisted, published to
    the event bus on every transition, and returned to callers who poll
    GET /transactions/{id}.
    """

    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    idempotency_key: str
    state: TransactionState = TransactionState.CREATED
    payer: Party
    payee: Party
    send_amount: Money
    receive_amount: Optional[Money] = None
    fx_quote: Optional[FXQuote] = None
    risk_assessment: Optional[RiskAssessment] = None
    compliance_check: Optional[ComplianceCheck] = None
    ledger_entries: list[LedgerEntry] = Field(default_factory=list)
    purpose_code: str
    reference: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    history: list[dict] = Field(default_factory=list)
    error: Optional[str] = None

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    class Config:
        json_encoders = {Decimal: str}
