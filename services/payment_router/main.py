"""Payment router service entrypoint - internal-only, called by the
API gateway."""
from __future__ import annotations

from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel

from common.idempotency import idempotency_store
from common.models import Money, Party, TransactionRequest
from services.payment_router.orchestrator import process_payment

app = FastAPI(title="BRICS Pay - Payment Router")


class RouteRequest(BaseModel):
    payer_id: str
    payer_country: str
    payer_account_ref: str
    payee_id: str
    payee_country: str
    payee_account_ref: str
    send_amount: Decimal
    send_currency: str
    idempotency_key: str


@app.post("/internal/route")
async def route(req: RouteRequest) -> dict:
    if not idempotency_store.check_and_set(req.idempotency_key):
        return {"status": "duplicate_ignored", "idempotency_key": req.idempotency_key}

    request = TransactionRequest(
        payer=Party(party_id=req.payer_id, country=req.payer_country, account_ref=req.payer_account_ref),
        payee=Party(party_id=req.payee_id, country=req.payee_country, account_ref=req.payee_account_ref),
        send_amount=Money(amount=req.send_amount, currency=req.send_currency),
        idempotency_key=req.idempotency_key,
    )
    record = await process_payment(request)
    return {
        "transaction_id": record.request.transaction_id,
        "state": record.state.value,
        "receive_amount": str(record.receive_amount.amount) if record.receive_amount else None,
        "receive_currency": record.receive_amount.currency if record.receive_amount else None,
        "failure_reason": record.failure_reason,
    }


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
