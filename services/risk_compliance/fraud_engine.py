"""Rule-based fraud scoring stub.

A real deployment replaces this with a trained model served behind
the same interface - `score()` is the only contract callers need."""
from __future__ import annotations

from decimal import Decimal


class FraudEngine:
    def score(self, amount: Decimal, payer_country: str, payee_country: str) -> float:
        score = 0.05  # baseline
        if amount > Decimal("500000"):
            score += 0.3
        if payer_country != payee_country:
            score += 0.1  # cross-border adds baseline risk
        return min(score, 1.0)
