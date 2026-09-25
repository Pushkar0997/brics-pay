"""
The abstract interface every national-rail adapter implements.

The orchestrator only ever calls these three methods. It does not know
or care whether "debit" means calling UPI's NPCI switch, CIPS's message
gateway, or PIX's DICT/SPI APIs — that translation is each adapter's
entire job. This is what lets `orchestrator.py` read as five lines of
"debit payer, credit payee" instead of five country-specific branches.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from decimal import Decimal

from common.models import CurrencyCode, Party


@dataclass
class RailResult:
    """Outcome of a single rail call (debit or credit)."""

    success: bool
    rail_reference: str | None  # the rail's own transaction/trace ID
    message: str
    retryable: bool = False


class RailAdapter(abc.ABC):
    """
    One adapter per national payment rail.

    Implementations in this demo are no-ops that simulate latency and
    always succeed — see each file's module docstring for what a real
    integration involves. The interface itself (debit/credit/verify) is
    the part meant to be production-shaped already: three async calls,
    each returning a RailResult, each expected to be idempotent on
    `rail_reference` so retries after a timeout don't double-move money.
    """

    rail_name: str
    country_code: str

    @abc.abstractmethod
    async def debit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        """Pull funds from `party`'s account on this rail."""
        raise NotImplementedError

    @abc.abstractmethod
    async def credit(self, party: Party, amount: Decimal, currency: CurrencyCode, transaction_id: str) -> RailResult:
        """Push funds into `party`'s account on this rail."""
        raise NotImplementedError

    @abc.abstractmethod
    async def verify_account(self, party: Party) -> bool:
        """Confirm the account reference is valid/reachable before attempting a transfer."""
        raise NotImplementedError
