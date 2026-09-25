"""FX & rates engine service entrypoint."""
from __future__ import annotations

from decimal import Decimal

from fastapi import FastAPI, Query

from services.fx_rates_engine.rate_provider import RateProvider

app = FastAPI(title="BRICS Pay - FX & Rates Engine")
rate_provider = RateProvider()


@app.get("/quote")
def quote(amount: Decimal = Query(...), base: str = Query(...), quote: str = Query(...)) -> dict:
    rate, converted = rate_provider.quote(amount, base, quote)
    return {
        "base_currency": base,
        "quote_currency": quote,
        "rate": str(rate),
        "converted_amount": str(converted),
    }


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
