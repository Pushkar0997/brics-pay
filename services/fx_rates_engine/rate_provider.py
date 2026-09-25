"""Rate discovery + spread application.

Backed here by a static seed table standing in for a live market-data
feed. Swap `_MID_MARKET_RATES` for a real provider integration -
callers don't change."""
from __future__ import annotations

from decimal import Decimal

_MID_MARKET_RATES: dict[tuple[str, str], Decimal] = {
    ("INR", "CNY"): Decimal("0.086"),
    ("CNY", "INR"): Decimal("11.63"),
    ("INR", "BRL"): Decimal("0.068"),
    ("INR", "RUB"): Decimal("0.94"),
    ("INR", "ZAR"): Decimal("0.22"),
    ("INR", "USD"): Decimal("0.012"),
}


class RateProvider:
    def __init__(self, spread_bps: int = 25) -> None:
        self.spread_bps = spread_bps

    def mid_market_rate(self, base: str, quote: str) -> Decimal:
        if base == quote:
            return Decimal("1")
        try:
            return _MID_MARKET_RATES[(base, quote)]
        except KeyError:
            raise ValueError(f"no rate available for {base}->{quote}")

    def quote(self, amount: Decimal, base: str, quote_ccy: str) -> tuple[Decimal, Decimal]:
        mid = self.mid_market_rate(base, quote_ccy)
        spread_multiplier = Decimal(1) - (Decimal(self.spread_bps) / Decimal(10_000))
        effective_rate = mid * spread_multiplier
        return effective_rate, (amount * effective_rate).quantize(Decimal("0.01"))
