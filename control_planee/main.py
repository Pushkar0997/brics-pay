"""
Control plane service.

Exposes the service-identity policy graph. Deliberately tiny: this is the
seam where a real deployment would grow JWT issuance
(`POST /tokens {service, audience} -> short-lived JWT`) and dynamic policy
management (`PUT /policies/{service}`), without those additions touching
any of the payment-critical services.
"""

from fastapi import FastAPI

from control_plane.policy_store import get_policy_graph, is_call_allowed

app = FastAPI(title="BRICS-Pay Control Plane", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "control_plane"}


@app.get("/policies")
def policies():
    """Full policy graph — who may call whom. Used for debugging/audits."""
    return get_policy_graph()


@app.get("/policies/check")
def check(caller: str, callee: str):
    return {"caller": caller, "callee": callee, "allowed": is_call_allowed(caller, callee)}
