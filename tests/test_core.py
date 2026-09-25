"""Starter tests (M0-TST-02). These check behaviour v0 already has, so they pass today.

Each test name carries the eval ID it checks (spec/evals.md).
"""
from decimal import Decimal

import pytest

from common.models import Money, TransactionState
from services.fx_rates_engine.rate_provider import RateProvider
from services.payment_router.state_machine import VALID_TRANSITIONS, assert_valid_transition


def test_G01_inr_to_cny_quote():
    rate, received = RateProvider(spread_bps=25).quote(Decimal("10000.00"), "INR", "CNY")
    assert rate == Decimal("0.0857850")
    assert received == Decimal("857.85")


def test_N01_illegal_transition_rejected():
    with pytest.raises(ValueError):
        assert_valid_transition(TransactionState.CREATED, TransactionState.SETTLED)


@pytest.mark.parametrize("amount,currency", [(Decimal("0"), "INR"), (Decimal("-1"), "INR"), (Decimal("10"), "RUPEE")])
def test_N05_invalid_money_rejected(amount, currency):
    with pytest.raises(ValueError):
        Money(amount=amount, currency=currency)


HAPPY_PATH = [
    TransactionState.CREATED, TransactionState.AUTHENTICATED, TransactionState.RISK_CHECKED,
    TransactionState.FX_QUOTED, TransactionState.AUTHORIZED, TransactionState.DEBITED,
    TransactionState.SETTLING, TransactionState.SETTLED, TransactionState.CONFIRMED,
]


def test_INV6_happy_path_transitions_legal_and_terminals_closed():
    """Partial INV-6-T: the happy-path history is legal; terminal states have no exits.
    Full INV-6-T (checking a real run's recorded history) lands with M0-TST-01's fixtures."""
    for current, nxt in zip(HAPPY_PATH, HAPPY_PATH[1:]):
        assert_valid_transition(current, nxt)
    assert VALID_TRANSITIONS[TransactionState.CONFIRMED] == set()
    assert VALID_TRANSITIONS[TransactionState.FAILED] == set()
