"""Adapter for Russia's domestic financial messaging rail. Stub -
would call an SPFS-participant bank gateway in production."""
from __future__ import annotations

import asyncio
from uuid import uuid4

from adapters.base_adapter import AdapterResult, NationalRailAdapter
from common.models import Money, Party


class RussiaSpfsAdapter(NationalRailAdapter):
    country_code = "RU"

    async def debit(self, party: Party, amount: Money) -> AdapterResult:
        await asyncio.sleep(0)
        return AdapterResult(success=True, rail_reference=f"spfs-{uuid4().hex[:10]}")

    async def credit(self, party: Party, amount: Money) -> AdapterResult:
        await asyncio.sleep(0)
        return AdapterResult(success=True, rail_reference=f"spfs-{uuid4().hex[:10]}")
