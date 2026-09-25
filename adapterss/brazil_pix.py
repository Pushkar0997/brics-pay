"""
Brazil — PIX adapter.

STUB: simulates latency and always succeeds.

PRODUCTION SWAP-IN:
    PIX is operated by the Banco Central do Brasil (BCB) and is unusual
    among these five rails in settling in *real time* (seconds, 24/7):
      - `verify_account` -> DICT (PIX's key-lookup directory) resolution
        of the payee's "chave PIX" (CPF/CNPJ, email, phone, or random
        key) to the receiving institution + account, via a Participant
        institution's DICT API.
      - `debit`/`credit` -> SPI (Sistema de Pagamentos Instantâneos)
        message exchange through a PIX Participant (direct or via a PSP
        that is itself a Participant). Because settlement is real-time
        and (practically) irrevocable once confirmed, this adapter would
        need to return a hard success/failure synchronously rather than
        the "PENDING + async callback" shape the UPI/CIPS adapters use —
        which is a genuine difference in the *state machine* this rail
        drives, not just plumbing.
      - Given PIX's speed, this is also the rail where idempotency
        (common/idempotency.py) matters most in practice: a retried
        request has the least time to be caught by a human before the
        transfer is final.
"""

import asyncio
import logging
import uuid
from decimal import Decimal

from common.models import CurrencyCode, Party
from adapters.base_adapter import RailAdapter, RailResult

logger = logging.getLogger("adapters.brazil_pix")


class BrazilPIXAdapter(RailAdapter):
    rail_name = "PIX"
    country_code = "BR"

    async def debit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("PIX debit: %s %s from %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.03)  # PIX settles in seconds; low simulated latency
        return RailResult(success=True, rail_reference=f"PIX-{uuid.uuid4().hex[:12]}", message="Debit simulated OK")

    async def credit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("PIX credit: %s %s to %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.03)
        return RailResult(success=True, rail_reference=f"PIX-{uuid.uuid4().hex[:12]}", message="Credit simulated OK")

    async def verify_account(self, party: Party) -> bool:
        await asyncio.sleep(0.02)
        return bool(party.account_ref)
