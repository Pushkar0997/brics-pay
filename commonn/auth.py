"""
Zero-trust auth stub.

WHAT THIS IS: a FastAPI dependency that requires a bearer token on every
inbound request, so no service in the mesh silently trusts "requests from
inside the docker network are safe".

WHAT THIS IS NOT: this does not verify a signature, does not check token
expiry, and does not consult the control plane's policy store per call.
It compares against one static shared secret from settings.

PRODUCTION SWAP-IN:
    Replace `verify_bearer_token` with a call that:
      1. Verifies a short-lived JWT (RS256) signed by the control plane,
         with `aud` scoped to this service and `exp` < 5 minutes.
      2. Extracts the calling service's identity (SPIFFE ID / mTLS client
         cert CN) and checks it against `control_plane/policy_store.py`
         for "is service X allowed to call service Y, endpoint Z".
      3. Runs over mTLS at the transport layer in addition to the token
         check (defense in depth) — e.g. via a service mesh sidecar
         (Istio/Linkerd) so application code doesn't have to hand-roll TLS.
    None of that changes the shape of this dependency — call sites in each
    service's main.py stay identical.
"""

from fastapi import Header, HTTPException, status

from common.config import settings


async def verify_bearer_token(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()

    # --- STUB: constant-time-ish compare against one shared secret --------
    # Production swap-in: JWT signature verification + policy_store lookup,
    # see module docstring.
    if token != settings.static_bearer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token",
        )
    return token
