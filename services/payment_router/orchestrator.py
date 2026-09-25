"""Payment orchestrator - walks a transaction through every stage.

This is the concrete version of the India -> China example: an
Indian user pays a Chinese merchant, and this function is what runs
end to end. Each state transition publishes an event so
reconciliation/analytics/audit can consume it asynchronously without
being on the critical path.
"""
from __future__ import annotations

import httpx

from adapters import get_adapter
from common.models import COUNTRY_CURRENCY, Money, TransactionRecord, TransactionRequest, TransactionState
from event_bus.producer import publish_event
from event_bus.schemas import TransactionEvent
from services.payment_router.state_machine import assert_valid_transition

FX_RATES_ENGINE_URL = "http://fx-rates-engine:8002"
RISK_COMPLIANCE_URL = "http://risk-compliance:8003"
SETTLEMENT_LEDGER_URL = "http://settlement-ledger:8004"


class PaymentFailed(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


async def _emit(record: TransactionRecord) -> None:
    await publish_event(
        TransactionEvent(
            transaction_id=record.request.transaction_id,
            event_type=record.state.value,
            payload={"state": record.state.value},
        )
    )


async def _transition(record: TransactionRecord, target: TransactionState) -> None:
    assert_valid_transition(record.state, target)
    record.transition(target)
    await _emit(record)


async def process_payment(request: TransactionRequest) -> TransactionRecord:
    record = TransactionRecord(request=request, state=TransactionState.CREATED)
    await _emit(record)

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            # 1. Authenticate - the gateway already verified the caller's
            #    token; here we just confirm the payer identity is live.
            await _transition(record, TransactionState.AUTHENTICATED)

            # 2. Risk + KYC/AML screening
            risk_resp = await client.post(
                f"{RISK_COMPLIANCE_URL}/check",
                json={
                    "payer_country": request.payer.country,
                    "payee_country": request.payee.country,
                    "payer_kyc_tier": request.payer.kyc_tier,
                    "amount": str(request.send_amount.amount),
                    "currency": request.send_amount.currency,
                },
            )
            risk_resp.raise_for_status()
            risk = risk_resp.json()
            if not risk["approved"]:
                raise PaymentFailed(risk["reason"])
            record.risk_score = risk["risk_score"]
            await _transition(record, TransactionState.RISK_CHECKED)

            # 3. Live FX quote, e.g. INR -> CNY
            quote_currency = COUNTRY_CURRENCY.get(request.payee.country, request.send_amount.currency)
            fx_resp = await client.get(
                f"{FX_RATES_ENGINE_URL}/quote",
                params={
                    "amount": str(request.send_amount.amount),
                    "base": request.send_amount.currency,
                    "quote": quote_currency,
                },
            )
            fx_resp.raise_for_status()
            quote = fx_resp.json()
            record.fx_rate = quote["rate"]
            record.receive_amount = Money(amount=quote["converted_amount"], currency=quote["quote_currency"])
            await _transition(record, TransactionState.FX_QUOTED)

            # 4. User authorization is assumed granted by the caller
            #    reaching this endpoint (the gateway already collected it)
            await _transition(record, TransactionState.AUTHORIZED)

            # 5. Domestic debit via the payer's national rail adapter
            payer_adapter = get_adapter(request.payer.country)
            debit_result = await payer_adapter.debit(request.payer, request.send_amount)
            if not debit_result.success:
                raise PaymentFailed(f"domestic debit failed: {debit_result.error}")
            await _transition(record, TransactionState.DEBITED)

            # 6. Settlement - net/gross settlement between the two
            #    countries' correspondent accounts
            await _transition(record, TransactionState.SETTLING)
            settle_resp = await client.post(
                f"{SETTLEMENT_LEDGER_URL}/settle",
                json={
                    "transaction_id": request.transaction_id,
                    "payer_country": request.payer.country,
                    "payee_country": request.payee.country,
                    "send_amount": str(request.send_amount.amount),
                    "send_currency": request.send_amount.currency,
                    "receive_amount": str(record.receive_amount.amount),
                    "receive_currency": record.receive_amount.currency,
                },
            )
            settle_resp.raise_for_status()
            await _transition(record, TransactionState.SETTLED)

            # 7. Credit the merchant via their national rail adapter
            payee_adapter = get_adapter(request.payee.country)
            credit_result = await payee_adapter.credit(request.payee, record.receive_amount)
            if not credit_result.success:
                raise PaymentFailed(f"domestic credit failed: {credit_result.error}")

            await _transition(record, TransactionState.CONFIRMED)
            return record

        except PaymentFailed as exc:
            record.failure_reason = exc.reason
            await _transition(record, TransactionState.FAILED)
            return record
