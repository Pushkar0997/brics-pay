"""Control plane service: identity, policy and config.

Intentionally separate from the payment path (services/) so it can
be deployed, scaled and rolled back independently of it.
"""
from __future__ import annotations

from fastapi import FastAPI

from control_plane.policy_store import policy_store

app = FastAPI(title="BRICS Pay - Control Plane")


@app.get("/policies/fx")
def get_fx_policy() -> dict:
    return {"spread_bps": policy_store.fx.spread_bps}


@app.get("/policies/risk")
def get_risk_policy() -> dict:
    return {
        "max_unverified_amount": str(policy_store.risk.max_unverified_amount),
        "high_risk_score_threshold": policy_store.risk.high_risk_score_threshold,
    }


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
