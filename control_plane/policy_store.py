"""Control-plane policy cache.

The data plane pulls policy on startup and periodically thereafter,
then keeps using its last-known-good copy if the control plane is
unreachable — this is what keeps payments flowing during a
control-plane incident.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class FxPolicy:
    spread_bps: int = 25  # basis points markup over the mid-market rate


@dataclass
class RiskPolicy:
    max_unverified_amount: Decimal = Decimal("50000")
    high_risk_score_threshold: float = 0.8


@dataclass
class KycPolicy:
    min_tier_by_amount: dict = field(
        default_factory=lambda: {
            Decimal("10000"): 1,
            Decimal("100000"): 2,
            Decimal("1000000"): 3,
        }
    )


class PolicyStore:
    """Seeded with defaults; a real deployment loads these from a
    config service and hot-reloads on change, versioned per country."""

    def __init__(self) -> None:
        self.fx = FxPolicy()
        self.risk = RiskPolicy()
        self.kyc = KycPolicy()

    def required_kyc_tier(self, amount: Decimal) -> int:
        tier = 1
        for threshold, required in sorted(self.kyc.min_tier_by_amount.items()):
            if amount >= threshold:
                tier = required
        return tier


policy_store = PolicyStore()
