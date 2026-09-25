"""
Russia — SPFS (System for Transfer of Financial Messages) adapter.

STUB: simulates latency and always succeeds.

PRODUCTION SWAP-IN:
    SPFS is the Bank of Russia's SWIFT-alternative messaging system:
      - `verify_account` -> participant-bank lookup against the Bank of
        Russia's SPFS participant directory (SPFS uses its own BIC-like
        participant codes; a real adapter maps `party.bank_code` to an
        SPFS participant ID).
      - `debit`/`credit` -> SPFS financial messages (SPFS supports a
        SWIFT-MT-compatible message format for participants migrating
        from SWIFT) sent through a bank that holds direct SPFS
        membership, again using `transaction_id` as the message's unique
        reference for idempotent resends.
      - Sanctions-exposure screening for RUB-leg transactions needs to be
        unusually conservative given the shifting international
        sanctions landscape around Russian counterparties — in practice
        this adapter would refuse to even attempt a rail call until
        `risk_compliance` has returned a CLEAR (not just a low fraud
        score), and would log the compliance decision alongside the rail
        reference for audit.
"""

import asyncio
import logging
import uuid
from decimal import Decimal

from common.models import CurrencyCode, Party
from adapters.base_adapter import RailAdapter, RailResult

logger = logging.getLogger("adapters.russia_spfs")


class RussiaSPFSAdapter(RailAdapter):
    rail_name = "SPFS"
    country_code = "RU"

    async def debit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("SPFS debit: %s %s from %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.07)
        return RailResult(success=True, rail_reference=f"SPFS-{uuid.uuid4().hex[:12]}", message="Debit simulated OK")

    async def credit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        logger.info("SPFS credit: %s %s to %s (txn=%s)", amount, currency, party.account_ref, transaction_id)
        await asyncio.sleep(0.07)
        return RailResult(success=True, rail_reference=f"SPFS-{uuid.uuid4().hex[:12]}", message="Credit simulated OK")

    async def verify_account(self, party: Party) -> bool:
        await asyncio.sleep(0.02)
        return bool(party.account_ref) and bool(party.bank_code)
