"""Payment router service entrypoint - internal-only, called by the
API gateway."""
from __future__ import annotations

from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from common.idempotency import idempotency_store
from common.models import Money, Party, TransactionRequest
from services.payment_router.orchestrator import process_payment
from datetime import datetime, timezone

app = FastAPI(title="BRICS Pay - Payment Router")
transactions: list[dict] = []  # in-memory demo log

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
    # Keys are scoped per payer (CONTRACT: pinned conventions).
    key = f"{req.payer_id}:{req.idempotency_key}"
    claimed, stored = idempotency_store.claim(key)
    if not claimed:
        if stored is not None:
            return stored  # identical to the first response
        raise HTTPException(status_code=409, detail="payment with this idempotency key is in progress")

    try:
        request = TransactionRequest(
            payer=Party(party_id=req.payer_id, country=req.payer_country, account_ref=req.payer_account_ref),
            payee=Party(party_id=req.payee_id, country=req.payee_country, account_ref=req.payee_account_ref),
            send_amount=Money(amount=req.send_amount, currency=req.send_currency),
            idempotency_key=req.idempotency_key,
        )
        record = await process_payment(request)
    except ValueError as exc:
        idempotency_store.release(key)  # nothing happened; let the client retry
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        idempotency_store.release(key)
        raise

    response = {
        "transaction_id": record.request.transaction_id,
        "state": record.state.value,
        "receive_amount": str(record.receive_amount.amount) if record.receive_amount else None,
        "receive_currency": record.receive_amount.currency if record.receive_amount else None,
        "failure_reason": record.failure_reason,
    }
    transactions.append({
        **response,
        "payer_country": req.payer_country,
        "payee_country": req.payee_country,
        "send_amount": str(req.send_amount),
        "send_currency": req.send_currency,
        "history": [st.value for st in record.history] + [record.state.value],
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    idempotency_store.complete(key, response)
    return response


@app.get("/internal/transactions")
def list_transactions() -> list[dict]:
    return list(reversed(transactions))


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}