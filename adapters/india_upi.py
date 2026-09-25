"""Adapter for India's UPI rail. Stub - would call NPCI's UPI switch
in production."""
from __future__ import annotations

import asyncio
from uuid import uuid4

from adapters.base_adapter import AdapterResult, NationalRailAdapter
from common.models import Money, Party


class IndiaUpiAdapter(NationalRailAdapter):
    country_code = "IN"

    async def debit(self, party: Party, amount: Money) -> AdapterResult:
        await asyncio.sleep(0)  # placeholder for a real UPI switch call
        return AdapterResult(success=True, rail_reference=f"upi-{uuid4().hex[:10]}")

    async def credit(self, party: Party, amount: Money) -> AdapterResult:
        await asyncio.sleep(0)
        return AdapterResult(success=True, rail_reference=f"upi-{uuid4().hex[:10]}")
