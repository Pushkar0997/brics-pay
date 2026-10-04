"""Public entry point: auth, request validation, routing to the
payment-router service. This is the only service exposed externally;
everything behind it is internal-only (zero-trust internal mesh)."""
from __future__ import annotations

from decimal import Decimal
import os
from pathlib import Path 
from fastapi.responses import FileResponse
import httpx
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from common.auth import require_caller
from common.config import load_settings

settings = load_settings("api-gateway")
app = FastAPI(title="BRICS Pay - API Gateway")

PAYMENT_ROUTER_URL = os.environ.get("PAYMENT_ROUTER_URL", "http://payment-router:8001")


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

SERVICES = {
    "api-gateway": None,
    "payment-router": PAYMENT_ROUTER_URL,
    "fx-rates-engine": os.environ.get("FX_RATES_ENGINE_URL", "http://fx-rates-engine:8002"),
    "risk-compliance": os.environ.get("RISK_COMPLIANCE_URL", "http://risk-compliance:8003"),
    "settlement-ledger": os.environ.get("SETTLEMENT_LEDGER_URL", "http://settlement-ledger:8004"),
}


@app.get("/v1/transactions")
async def list_transactions(caller: str = Depends(require_caller)) -> list:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{PAYMENT_ROUTER_URL}/internal/transactions")
        resp.raise_for_status()
        return resp.json()


@app.get("/v1/services/health")
async def services_health(caller: str = Depends(require_caller)) -> dict:
    result = {"api-gateway": "up"}
    async with httpx.AsyncClient(timeout=2) as client:
        for name, url in SERVICES.items():
            if url is None:
                continue
            try:
                r = await client.get(f"{url}/healthz")
                result[name] = "up" if r.status_code == 200 else "down"
            except httpx.HTTPError:
                result[name] = "down"
    return result


@app.get("/dashboard", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(Path(__file__).parent / "dashboard.html")

SERVICES = {
    "api-gateway": None,
    "payment-router": PAYMENT_ROUTER_URL,
    "fx-rates-engine": os.environ.get("FX_RATES_ENGINE_URL", "http://fx-rates-engine:8002"),
    "risk-compliance": os.environ.get("RISK_COMPLIANCE_URL", "http://risk-compliance:8003"),
    "settlement-ledger": os.environ.get("SETTLEMENT_LEDGER_URL", "http://settlement-ledger:8004"),
}


@app.get("/v1/transactions")
async def list_transactions(caller: str = Depends(require_caller)) -> list:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{PAYMENT_ROUTER_URL}/internal/transactions")
        resp.raise_for_status()
        return resp.json()


@app.get("/v1/services/health")
async def services_health(caller: str = Depends(require_caller)) -> dict:
    result = {"api-gateway": "up"}
    async with httpx.AsyncClient(timeout=2) as client:
        for name, url in SERVICES.items():
            if url is None:
                continue
            try:
                r = await client.get(f"{url}/healthz")
                result[name] = "up" if r.status_code == 200 else "down"
            except httpx.HTTPError:
                result[name] = "down"
    return result


@app.get("/dashboard", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(Path(__file__).parent / "dashboard.html")