# CONTRACT — BRICS Pay

**The correctness core. An agent that reads only this file must not be able to break the domain.**

Precedence: this file outranks every other document. If something here conflicts with a task, the task is wrong — stop and flag it.

This is a conceptual design, but the money path is held to real rules. A payment
system that loses money in its own demo teaches the wrong lesson, however many
boxes the diagram has.

---

## Invariants

### INV-1 — Money is conserved

**Rule:** Every transaction ends in exactly one terminal state. `CONFIRMED` means the payer was debited and the payee credited. `FAILED` means the payer was never debited. `REVERSED` means the payer was debited and that debit was refunded in full. No terminal state leaves a debit without either a credit or a refund.
**Why:** A payer debited with nothing on the other side is lost money — the one failure a payment system cannot have.
**Violated by:** marking a transaction `FAILED` after the debit succeeded, because the failure happened in a later step (settlement or credit). This is exactly what v0 does in `orchestrator.py`.
**Detected by:** INV-1-T — inject a credit failure after a successful debit and assert the final state is `REVERSED` and the adapter's `refund` was called once with the original amount.

### INV-2 — One payment per idempotency key

**Rule:** Any number of requests with the same idempotency key, on any replica, produce at most one debit. Every repeat returns the stored result of the first request, not a new one and not a bare "duplicate" message.
**Why:** Clients retry on timeouts. Without this, a slow network charges the user twice.
**Violated by:** an in-process idempotency store (each replica has its own), and recording the key before processing so a crash burns it. v0 does both.
**Detected by:** INV-2-T — two store instances sharing one backend; the second call with the same key returns the first call's result and the adapter's `debit` was called once.

### INV-3 — The quote shown is the quote honored

**Rule:** The payee receives exactly the `receive_amount` of the quote the payer authorized. A quote is valid for `QUOTE_TTL_SECONDS`. An expired quote is rejected with `QUOTE_EXPIRED`; it is never silently re-priced.
**Why:** The user agreed to a specific amount. Paying a different one — even a better one — is a broken promise and, for a merchant, a reconciliation error.
**Violated by:** fetching a fresh rate at credit time instead of carrying the locked quote through.
**Detected by:** INV-3-T (credited amount equals the quote's `receive_amount`), N-03 (expired quote rejected).

### INV-4 — Both jurisdictions approve before any debit

**Rule:** No debit is attempted until the compliance checks of both the payer's country and the payee's country have approved the transaction.
**Why:** A cross-border payment is regulated at both ends. Debiting and then discovering the receiving side refuses it forces a reversal that should never have been needed.
**Violated by:** running only the payer-side check, or running the payee-side check after the debit.
**Detected by:** INV-4-T — payee-side compliance rejects; assert state `FAILED` and `debit` never called.

### INV-5 — The core contains no country-specific logic

**Rule:** Country-specific behaviour — rail protocols, compliance rules, residency — lives only in `adapters/` (and the per-country compliance modules defined in D-003). The only country list in core code is `COUNTRY_CURRENCY` in `common/models.py`.
**Why:** This is the design's central claim: adding a country means adding an adapter, never changing the core.
**Violated by:** an `if country == "CN":` branch in a service because it was the quickest fix.
**Detected by:** INV-5-T — a test that scans `services/`, `common/` and `control_plane/` for ISO country-code literals outside `COUNTRY_CURRENCY` and fails on any hit.

### INV-6 — Only legal state transitions

**Rule:** A transaction moves only along the transitions in `VALID_TRANSITIONS` (`services/payment_router/state_machine.py`). Terminal states have no outgoing transitions.
**Why:** INV-1 is only checkable if the state history is trustworthy.
**Violated by:** setting `record.state` directly instead of going through `assert_valid_transition`.
**Detected by:** INV-6-T and N-01.

---

## Pinned conventions

| Concern | Decision |
|---|---|
| Money type | `decimal.Decimal`, never `float`. In JSON, amounts are strings: `"10000.00"`. |
| Rounding | Quantize to the currency's minor unit with `ROUND_HALF_EVEN`. All five currencies in scope use 2 decimal places. |
| FX rate direction | `rate` = units of quote currency per 1 unit of base currency. `receive = send × effective_rate`. INR→CNY rate `0.0857850` means ₹1 buys ¥0.0857850. |
| Spread | Applied by lowering the rate: `effective_rate = mid × (1 − spread_bps / 10000)`. The payer is never shown the mid rate as if it were the price. |
| Currency codes | ISO 4217, uppercase: `INR`, `CNY`, `BRL`, `RUB`, `ZAR`. |
| Country codes | ISO 3166-1 alpha-2, uppercase: `IN`, `CN`, `BR`, `RU`, `ZA`. |
| Transaction ID | UUID4 string, lowercase, generated by the payment router. |
| Idempotency key | Client-supplied, 1–128 chars, scoped per payer: the stored key is `<payer_id>:<idempotency_key>`. |
| Timestamps | UTC, timezone-aware, ISO 8601 in JSON: `2026-09-25T10:30:00Z`. |
| Error shape | `{"code": "SCREAMING_SNAKE", "message": "...", "details": {...}}`. |
| State names | Uppercase `TransactionState` values. v1 adds `REVERSING` and `REVERSED` (D-004). |
| Ledger partition key | Region from payer country (residency), then hash of `transaction_id` within the region (spread). See D-006. |

---

## Exact values

```
QUOTE_TTL_SECONDS       = 30
DEFAULT_SPREAD_BPS      = 25
REFERENCE_BAND_PCT      = 2      # reject a market quote more than 2% from the reference rate
LEDGER_PARTITIONS       = 16     # per region
KYC_TIER_THRESHOLDS     = {10000: 1, 100000: 2, 1000000: 3}   # amount in send currency -> minimum tier
```

---

## Reference examples

| Input | Expected output |
|---|---|
| Quote 10000.00 INR → CNY, mid `0.086`, spread 25 bps | effective rate `0.0857850`, receive `857.85` CNY |
| Same idempotency key sent twice | one debit; both responses identical |
| Debit succeeds, payee credit fails | final state `REVERSED`; one refund of `10000.00` INR |
| Authorize a quote 31 s after it was issued | rejected, `QUOTE_EXPIRED`; no debit |
| Transition `CREATED` → `SETTLED` | `ValueError`, state unchanged |

---

## Never do this

- **Never mark a transaction `FAILED` after a successful debit** — because the money is then gone with no record that it must come back. Transition to `REVERSING` and refund.
- **Never use `float` for money or rates** — because binary floating point cannot represent `0.1`, and rounding errors accumulate into real discrepancies. Use `Decimal`.
- **Never re-fetch a rate after authorization** — because it breaks INV-3. Carry the locked quote.
- **Never keep idempotency or ledger state only in process memory in any path described as multi-replica** — because every replica then has its own truth. The in-memory backend is allowed only behind the shared-store interface, for tests and the single-process demo.
- **Never add a country-specific branch outside `adapters/`** — because it breaks the design's central claim (INV-5). Add or extend an adapter.
- **Never describe a stub as working** — in code comments, README, or slides. Stubs are listed in `spec/architecture.md` and labelled conceptual.

---

## Changing this file

Requires explicit human approval. An agent proposing a change here stops and asks; it does not edit and report. (Enforced by `scripts/protect-contract.sh` in Claude Code.)
