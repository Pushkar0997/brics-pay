"""
China — CIPS (Cross-Border Interbank Payment System) adapter.

STUB: simulates latency and always succeeds.

PRODUCTION SWAP-IN:
    CIPS is a direct-participant / indirect-participant model:
      - Most foreign PSPs connect as an *indirect participant* through a
        CIPS *direct participant* bank, exchanging ISO 20022 messages
        (pacs.008 for credit transfer, pacs.002 for status) over CIPS's
        own network (CIPS uses SWIFT as a messaging carrier option, or a
        direct CIPS terminal for direct participants).
      - `verify_account` -> a beneficiary-bank BIC/CNAPS-code lookup to
        confirm the payee's bank participates in CIPS (directly or via a
        correspondent), before attempting settlement.
      - `debit`/`credit` -> construct and send a pacs.008 message via the
        direct participant, using `transaction_id` as the end-to-end ID
        so a resend after a timeout is recognized as the same payment.
        CIPS settlement finality is confirmed asynchronously via pacs.002
        status messages, same "PENDING then callback" shape as the UPI
        adapter's note above.
      - CNY is a managed-float / capital-controlled currency: a real
        adapter would also need to check the transaction against PBOC
        cross-border RMB reporting thresholds and attach the required
        trade/services documentation references for anything above the
        reporting floor.
"""

import asyncio
import logging
import uuid
from decimal import Decimal

from common.models import CurrencyCode, Party
from adapters.base_adapter import RailAdapter, RailResult

logger = logging.getLogger("adapters.china_cips")


class ChinaCIPSAdapter(RailAdapter):
    rail_name = "CIPS"
    country_code = "CN"

    async def debit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("CIPS debit: %s %s from %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.06)
        return RailResult(success=True, rail_reference=f"CIPS-{uuid.uuid4().hex[:12]}", message="Debit simulated OK")

    async def credit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("CIPS credit: %s %s to %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.06)
        return RailResult(success=True, rail_reference=f"CIPS-{uuid.uuid4().hex[:12]}", message="Credit simulated OK")

    async def verify_account(self, party: Party) -> bool:
        await asyncio.sleep(0.02)
        return bool(party.account_ref) and bool(party.bank_code)
