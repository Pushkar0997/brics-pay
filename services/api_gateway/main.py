"""Public entry point: auth, request validation, routing to the
payment-router service. This is the only service exposed externally;
everything behind it is internal-only (zero-trust internal mesh)."""
from __future__ import annotations

from decimal import Decimal

import httpx
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from common.auth import require_caller
from common.config import load_settings

settings = load_settings("api-gateway")
app = FastAPI(title="BRICS Pay - API Gateway")

PAYMENT_ROUTER_URL = "http://payment-router:8001"


class PaymentRequest(BaseModel):
    payer_id: str
    payer_country: str
    payer_account_ref: str
    payee_id: str
    payee_country: str
    payee_account_ref: str
    send_amount: Decimal
    send_currency: str
    idempotency_key: str


@app.post("/v1/payments")
async def create_payment(req: PaymentRequest, caller: str = Depends(require_caller)) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{PAYMENT_ROUTER_URL}/internal/route",
            json=req.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return resp.json()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "region": settings.region}
