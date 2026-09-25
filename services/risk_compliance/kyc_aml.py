"""KYC/AML tier check against control-plane policy."""
from __future__ import annotations

from decimal import Decimal

from control_plane.policy_store import policy_store


class KycAmlChecker:
    def check(self, kyc_tier: int, amount: Decimal) -> tuple[bool, str | None]:
        required_tier = policy_store.required_kyc_tier(amount)
        if kyc_tier < required_tier:
            return False, f"kyc tier {kyc_tier} insufficient, requires tier {required_tier}"
        return True, None
