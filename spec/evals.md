# evals.md — Evaluation

## 1. How to run

```
pip install -r requirements.txt -r requirements-dev.txt
python3 -m pytest -q tests
python3 scripts/spec_lint.py
```

Both must exit 0 before any push. CI runs the same via `scripts/spec-gate.sh ci`.

Test naming: every test carries its eval ID in its name — `test_G01_...`, `test_N03_...`, `test_INV1_...`. `spec_lint` warns about any ID below that no test references.

## 2. Golden values

| ID | Input | Expected |
|---|---|---|
| G-01 | Quote 10000.00 INR → CNY, mid 0.086, spread 25 bps | effective rate `0.0857850`, receive `857.85` |
| G-02 | 10,000 synthetic IN transactions through the D-006 partition rule | every one of the 16 IN partitions receives between 450 and 800 entries (mean 625); v0 puts all 10,000 in one |
| G-03 | Quote issued at t, authorized at t+29 s | accepted |
| G-04 | Full India → China flow with all stubs succeeding | final state `CONFIRMED`; history `CREATED → AUTHENTICATED → RISK_CHECKED → FX_QUOTED → AUTHORIZED → DEBITED → SETTLING → SETTLED → CONFIRMED` |

## 3. Invariant tests

| ID | Invariant | Assertion |
|---|---|---|
| INV-1-T | Money is conserved | Payee credit forced to fail after a successful debit → final state `REVERSED`; payer adapter `refund` called exactly once with `10000.00 INR` |
| INV-2-T | One payment per idempotency key | Two store instances on one shared backend; same key twice → identical responses, `debit` called once |
| INV-3-T | Quote honored | Credited amount equals the authorized quote's `receive_amount`, even if the rate table changes between quote and credit |
| INV-4-T | Both jurisdictions approve | Payee-country compliance rejects → state `FAILED`, `debit` never called |
| INV-5-T | No country logic in core | Scan of `services/`, `common/`, `control_plane/` finds no ISO country-code string literals outside `COUNTRY_CURRENCY` |
| INV-6-T | Legal transitions only | Every transition in G-04's history is in `VALID_TRANSITIONS`; terminal states have none |

## 4. Negative tests

| ID | Assertion |
|---|---|
| N-01 | Transition `CREATED → SETTLED` raises `ValueError` and leaves the state unchanged |
| N-02 | KYC tier 1 payer sending 100000 INR is rejected before any debit |
| N-03 | Authorizing a quote at t+31 s is rejected with `QUOTE_EXPIRED`; no debit |
| N-04 | A request that crashes mid-processing leaves its idempotency key retryable after the lease expires, not burned |
| N-05 | `Money` with amount ≤ 0 or a non-3-letter currency raises `ValueError` |
| N-06 | Refund failure after the retry budget leaves the transaction in `REVERSING` and on the manual-review queue — never `FAILED`, never `REVERSED` |

## 5. Telemetry

Not in scope. Events on the bus are the audit trail for the demo.

## 6. Pre-push gate

- [ ] `pytest` passes
- [ ] `spec_lint` passes (strict from M1 close onward)
- [ ] `smoke.md` passes for any change to the money path
- [ ] No claim added to README or slides without a claims-register row

## 7. Recorded verdicts

*Written **after** a milestone, not before. PASS only where a test or recorded run backs it. Never round up a PARTIAL.*

No milestone has closed yet.
