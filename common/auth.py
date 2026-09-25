"""Auth dependency shared by every FastAPI service.

Real deployments would verify a JWT against the control plane's JWKS
endpoint and enforce mTLS between services (zero-trust). This stub
just checks for a bearer token — replace before this touches real
money.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status


async def require_caller(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "empty token")
    # TODO: verify signature against control-plane JWKS, check expiry/audience
    return token
