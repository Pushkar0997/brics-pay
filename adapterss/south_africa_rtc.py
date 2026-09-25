"""
South Africa — RTC (Real-Time Clearing) adapter.

STUB: simulates latency and always succeeds.

PRODUCTION SWAP-IN:
    RTC is BankservAfrica's real-time low-value payment clearing system:
      - `verify_account` -> account-verification service (AVS) lookup
        against the receiving bank to confirm account number, type, and
        holder-name match before attempting a transfer — South African
        banks widely support AVS specifically to catch typo'd beneficiary
        details before money moves.
      - `debit`/`credit` -> ISO 8583 or ISO 20022 messages (BankservAfrica
        has been migrating RTC toward ISO 20022) submitted through a
        clearing bank that participates in RTC, again using
        `transaction_id` as the message's unique end-to-end reference.
      - Confirmation is near-real-time (RTC clears within roughly 60
        seconds), so like the PIX adapter this would return a synchronous
        success/failure rather than a long-lived "PENDING" state.
"""

import asyncio
import logging
import uuid
from decimal import Decimal

from common.models import CurrencyCode, Party
from adapters.base_adapter import RailAdapter, RailResult

logger = logging.getLogger("adapters.south_africa_rtc")


class SouthAfricaRTCAdapter(RailAdapter):
    rail_name = "RTC"
    country_code = "ZA"

    async def debit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("RTC debit: %s %s from %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.04)
        return RailResult(success=True, rail_reference=f"RTC-{uuid.uuid4().hex[:12]}", message="Debit simulated OK")

    async def credit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("RTC credit: %s %s to %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.04)
        return RailResult(success=True, rail_reference=f"RTC-{uuid.uuid4().hex[:12]}", message="Credit simulated OK")

    async def verify_account(self, party: Party) -> bool:
        await asyncio.sleep(0.02)
        return bool(party.account_ref)
