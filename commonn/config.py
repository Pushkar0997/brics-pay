"""
Environment-based configuration. Every service imports `settings` from
here instead of reading `os.environ` directly, so all tunables are
documented in one place and docker-compose.yml only needs to set env vars,
never edit code.
"""

import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    # --- service identity -------------------------------------------------
    service_name: str = os.getenv("SERVICE_NAME", "unknown-service")
    environment: str = os.getenv("ENVIRONMENT", "local")

    # --- inter-service URLs (docker-compose service names as hostnames) ---
    api_gateway_url: str = os.getenv("API_GATEWAY_URL", "http://api_gateway:8000")
    payment_router_url: str = os.getenv("PAYMENT_ROUTER_URL", "http://payment_router:8001")
    fx_rates_url: str = os.getenv("FX_RATES_URL", "http://fx_rates_engine:8002")
    risk_compliance_url: str = os.getenv("RISK_COMPLIANCE_URL", "http://risk_compliance:8003")
    settlement_ledger_url: str = os.getenv("SETTLEMENT_LEDGER_URL", "http://settlement_ledger:8004")
    control_plane_url: str = os.getenv("CONTROL_PLANE_URL", "http://control_plane:8005")

    # --- auth (zero-trust stub, see common/auth.py) ------------------------
    # In production this would be mTLS + short-lived JWTs issued by the
    # control plane per hop, checked against a policy store on every call.
    static_bearer_token: str = os.getenv("STATIC_BEARER_TOKEN", "demo-token-change-me")

    # --- risk/compliance thresholds ----------------------------------------
    fraud_score_reject_threshold: float = float(os.getenv("FRAUD_SCORE_REJECT_THRESHOLD", "0.85"))
    fraud_score_hold_threshold: float = float(os.getenv("FRAUD_SCORE_HOLD_THRESHOLD", "0.55"))
    kyc_tier2_limit_usd_equiv: float = float(os.getenv("KYC_TIER2_LIMIT_USD_EQUIV", "10000"))
    kyc_tier1_limit_usd_equiv: float = float(os.getenv("KYC_TIER1_LIMIT_USD_EQUIV", "1000"))

    # --- fx --------------------------------------------------------------
    fx_default_spread_bps: int = int(os.getenv("FX_DEFAULT_SPREAD_BPS", "35"))

    # --- ledger ------------------------------------------------------------
    ledger_shard_count: int = int(os.getenv("LEDGER_SHARD_COUNT", "5"))

    # --- idempotency --------------------------------------------------------
    idempotency_ttl_seconds: int = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", str(24 * 3600)))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
