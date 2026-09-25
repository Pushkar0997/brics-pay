"""Risk & compliance service entrypoint - combines fraud scoring and
KYC/AML tier checks into a single approve/deny decision."""
from __future__ import annotations

from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel

from services.risk_compliance.fraud_engine import FraudEngine
from services.risk_compliance.kyc_aml import KycAmlChecker

app = FastAPI(title="BRICS Pay - Risk & Compliance")
fraud_engine = FraudEngine()
kyc_checker = KycAmlChecker()


class CheckRequest(BaseModel):
    payer_country: str
    payee_country: str
    payer_kyc_tier: int
    amount: Decimal
    currency: str


@app.post("/check")
def check(req: CheckRequest) -> dict:
    risk_score = fraud_engine.score(req.amount, req.payer_country, req.payee_country)
    kyc_ok, kyc_reason = kyc_checker.check(req.payer_kyc_tier, req.amount)

    if risk_score >= 0.8:
        return {"approved": False, "reason": "high fraud risk score", "risk_score": risk_score}
    if not kyc_ok:
        return {"approved": False, "reason": kyc_reason, "risk_score": risk_score}
    return {"approved": True, "reason": None, "risk_score": risk_score}


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
