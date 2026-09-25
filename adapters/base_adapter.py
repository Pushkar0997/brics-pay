"""Abstract interface every national rail adapter must implement.

This is the isolation boundary between BRICS Pay's global core and
each country's domestic protocol, regulation and data-residency
rules - the core only ever talks to this interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from common.models import Money, Party


@dataclass
class AdapterResult:
    success: bool
    rail_reference: str | None = None
    error: str | None = None


class NationalRailAdapter(ABC):
    country_code: str

    @abstractmethod
    async def debit(self, party: Party, amount: Money) -> AdapterResult:
        """Pull funds from the payer's domestic account."""

    @abstractmethod
    async def credit(self, party: Party, amount: Money) -> AdapterResult:
        """Push funds into the payee's domestic account."""
