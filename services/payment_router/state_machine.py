"""Transaction state machine - the legal transitions for a payment."""
from __future__ import annotations

from common.models import TransactionState

VALID_TRANSITIONS: dict[TransactionState, set[TransactionState]] = {
    TransactionState.CREATED: {TransactionState.AUTHENTICATED, TransactionState.FAILED},
    TransactionState.AUTHENTICATED: {TransactionState.RISK_CHECKED, TransactionState.FAILED},
    TransactionState.RISK_CHECKED: {TransactionState.FX_QUOTED, TransactionState.FAILED},
    TransactionState.FX_QUOTED: {TransactionState.AUTHORIZED, TransactionState.FAILED},
    TransactionState.AUTHORIZED: {TransactionState.DEBITED, TransactionState.FAILED},
    TransactionState.DEBITED: {TransactionState.SETTLING, TransactionState.FAILED},
    TransactionState.SETTLING: {TransactionState.SETTLED, TransactionState.FAILED},
    TransactionState.SETTLED: {TransactionState.CONFIRMED},
    TransactionState.CONFIRMED: set(),
    TransactionState.FAILED: set(),
}


def assert_valid_transition(current: TransactionState, target: TransactionState) -> None:
    if target not in VALID_TRANSITIONS[current]:
        raise ValueError(f"illegal transition {current} -> {target}")
