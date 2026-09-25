"""
India — UPI (Unified Payments Interface) adapter.

STUB: `debit`/`credit`/`verify_account` simulate network latency and
always succeed. No real message is sent anywhere.

PRODUCTION SWAP-IN:
    UPI cross-border settlement in practice runs through a sponsor bank
    that is a UPI member, using NPCI's UPI APIs (or a PSP aggregator
    sitting on top of them):
      - `verify_account`  -> NPCI "Validate VPA/Account" API, confirming
        the payee's VPA (`name@bank`) or account+IFSC resolves to a real,
        active account before attempting a transfer.
      - `debit`  -> a "Collect" or "Pay" request via the sponsor bank's
        UPI switch integration, using `transaction_id` as the UPI
        transaction reference so retries are idempotent on NPCI's side
        too. Response is asynchronous — the sponsor bank's switch sends a
        callback/webhook, so a real adapter would return a "PENDING"
        result here and the orchestrator would await a confirmation
        event rather than a synchronous return.
      - `credit`  -> analogous "Pay" call crediting the beneficiary VPA.
      - All calls need request signing per NPCI's spec and run over the
        sponsor bank's dedicated leased line / VPN into the UPI switch,
        not the public internet.
"""

import asyncio
import logging
import uuid
from decimal import Decimal

from common.models import CurrencyCode, Party
from adapters.base_adapter import RailAdapter, RailResult

logger = logging.getLogger("adapters.india_upi")


class IndiaUPIAdapter(RailAdapter):
    rail_name = "UPI"
    country_code = "IN"

    async def debit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("UPI debit: %s %s from %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.05)  # simulated NPCI round-trip
        return RailResult(success=True, rail_reference=f"UPI-{uuid.uuid4().hex[:12]}", message="Debit simulated OK")

    async def credit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("UPI credit: %s %s to %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.05)
        return RailResult(success=True, rail_reference=f"UPI-{uuid.uuid4().hex[:12]}", message="Credit simulated OK")

    async def verify_account(self, party: Party) -> bool:
        await asyncio.sleep(0.02)
        return bool(party.account_ref)
