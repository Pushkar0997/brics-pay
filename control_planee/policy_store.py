"""
Policy store: which service is allowed to call which.

This is explicitly NOT on the payment critical path — if this service is
down, in-flight payments still process (each service's common/auth.py
falls back to the static shared-secret check). The control plane is where
you'd evolve to make those per-hop decisions dynamic and centrally
auditable without touching the critical path's latency budget.

Policy shape: a simple allow-list, service -> set of services it may call.
A production version of this would be:
  - Backed by a real store (etcd / a small Postgres table), not a dict.
  - Consulted by common/auth.py on every request (with a short local
    cache + push-based invalidation, so the policy store being briefly
    unreachable doesn't take down the payment path it's meant to protect).
  - Versioned, so a policy change can be rolled back the same way code is.
"""

from dataclasses import dataclass, field


@dataclass
class ServicePolicy:
    allowed_callers: set[str] = field(default_factory=set)


# Default policy graph for this demo's topology.
_POLICY: dict[str, ServicePolicy] = {
    "api_gateway": ServicePolicy(allowed_callers=set()),  # externally exposed; no internal caller
    "payment_router": ServicePolicy(allowed_callers={"api_gateway"}),
    "fx_rates_engine": ServicePolicy(allowed_callers={"payment_router"}),
    "risk_compliance": ServicePolicy(allowed_callers={"payment_router"}),
    "settlement_ledger": ServicePolicy(allowed_callers={"payment_router"}),
    "control_plane": ServicePolicy(allowed_callers={"payment_router", "api_gateway"}),
}


def is_call_allowed(caller: str, callee: str) -> bool:
    policy = _POLICY.get(callee)
    if policy is None:
        # Unknown callee: fail closed.
        return False
    return caller in policy.allowed_callers


def get_policy_graph() -> dict[str, list[str]]:
    return {callee: sorted(p.allowed_callers) for callee, p in _POLICY.items()}
