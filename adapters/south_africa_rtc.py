"""Adapter for South Africa's real-time clearing rail. Stub - would
call a BankservAfrica RTC gateway in production."""
from __future__ import annotations

import asyncio
from uuid import uuid4

from adapters.base_adapter import AdapterResult, NationalRailAdapter
from common.models import Money, Party


class SouthAfricaRtcAdapter(NationalRailAdapter):
    country_code = "ZA"

    async def debit(self, party: Party, amount: Money) -> AdapterResult:
        await asyncio.sleep(0)
        return AdapterResult(success=True, rail_reference=f"rtc-{uuid4().hex[:10]}")

    async def credit(self, party: Party, amount: Money) -> AdapterResult:
        await asyncio.sleep(0)
        return AdapterResult(success=True, rail_reference=f"rtc-{uuid4().hex[:10]}")
