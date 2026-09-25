"""Settlement ledger service entrypoint."""
from __future__ import annotations

from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel

from services.settlement_ledger.ledger import LedgerEntry, ledger

app = FastAPI(title="BRICS Pay - Settlement Ledger")


class SettleRequest(BaseModel):
    transaction_id: str
    payer_country: str
    payee_country: str
    send_amount: Decimal
    send_currency: str
    receive_amount: Decimal
    receive_currency: str


@app.post("/settle")
def settle(req: SettleRequest) -> dict:
    entry = LedgerEntry(
        transaction_id=req.transaction_id,
        payer_country=req.payer_country,
        payee_country=req.payee_country,
        send_amount=req.send_amount,
        send_currency=req.send_currency,
        receive_amount=req.receive_amount,
        receive_currency=req.receive_currency,
    )
    partition = ledger.append(entry)
    return {"transaction_id": req.transaction_id, "status": "settled", "partition": partition}


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
