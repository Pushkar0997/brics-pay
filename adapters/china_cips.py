"""Adapter for China's cross-border interbank payment rail. Stub -
would call a CIPS-participant bank gateway in production."""
from __future__ import annotations

import asyncio
from uuid import uuid4

from adapters.base_adapter import AdapterResult, NationalRailAdapter
from common.models import Money, Party


class ChinaCipsAdapter(NationalRailAdapter):
    country_code = "CN"

    async def debit(self, party: Party, amount: Money) -> AdapterResult:
        await asyncio.sleep(0)
        return AdapterResult(success=True, rail_reference=f"cips-{uuid4().hex[:10]}")

    async def credit(self, party: Party, amount: Money) -> AdapterResult:
        await asyncio.sleep(0)
        return AdapterResult(success=True, rail_reference=f"cips-{uuid4().hex[:10]}")
