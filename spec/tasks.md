# tasks.md — Backlog

One task = one change = one commit. Tick the box and add a one-line note when done — ticked only from the verifier's report.

Task ID format: `M<milestone>-<AREA>-<nn>`. Each task names the requirement or eval it satisfies.

---

## M0 — Correct money path

### Tests
- [ ] **M0-TST-01** Add a shared fixture (`tests/conftest.py`) that builds a `TransactionRequest` and in-memory fake adapters recording every debit, credit and refund call — enables every test below. (`pytest.ini` and `tests/` already exist from the spec session.)
- [ ] **M0-TST-02** Add G-01, N-01, N-05, INV-6-T tests against existing code in `tests/test_core.py` — these should pass on v0. *Written 2026-09-25 in the spec session; awaiting verifier. INV-6-T is partial until M0-TST-01's fixtures exist.*

### Payments (`services/payment_router/`, `adapters/`, `common/models.py`)
- [ ] **M0-PAY-01** Add `REVERSING` and `REVERSED` to `TransactionState` and their transitions to `VALID_TRANSITIONS` (from any post-`DEBITED` state to `REVERSING`; `REVERSING` → `REVERSED`) — D-004, INV-6
- [ ] **M0-PAY-02** Add `refund(party, amount)` to `NationalRailAdapter` and all five adapters — D-004
- [ ] **M0-PAY-03** In `orchestrator.py`, route any failure after `DEBITED` to `REVERSING` → refund → `REVERSED`, with retry and a manual-review queue on refund failure — INV-1, INV-1-T, N-06
- [ ] **M0-PAY-04** Add a fault-injection setting (`BRICS_FAIL_CREDIT_COUNTRY`, read at call time, not import time — see A-14) that makes that country's adapter fail `credit` — enables smoke §3

### FX (`services/fx_rates_engine/`)
- [ ] **M0-FX-01** Quotes return `quote_id`, `expires_at`; authorization rejects expired quotes with `QUOTE_EXPIRED`; the orchestrator credits the locked `receive_amount` — INV-3, INV-3-T, G-03, N-03

### Idempotency (`common/idempotency.py`, `services/payment_router/main.py`)
- [ ] **M0-IDM-01** Replace the set with an `IdempotencyBackend` interface: atomic claim as `IN_PROGRESS`, store final response, lease expiry; in-memory implementation shared by reference in tests — D-005, INV-2-T, N-04
- [ ] **M0-IDM-02** Router returns the stored response on a repeat key instead of `duplicate_ignored` — INV-2

### Compliance (`services/risk_compliance/`, `adapters/`)
- [ ] **M0-CMP-01** Add a per-country compliance hook to the adapter interface (default: approve); orchestrator requires payer and payee approval before debit — D-003, INV-4-T, N-02

### Architecture guard
- [ ] **M0-ARC-01** Add INV-5-T: scan core packages for country-code literals outside `COUNTRY_CURRENCY`

### Closing
- [ ] **M0-DOC-01** Move M0 claims to `honored` with evidence in `spec/architecture.md` §8; record the M0 verdict in `spec/evals.md` §7 from the verifier's report

---

## M1 — Claims made true

- [ ] **M1-LED-01** Implement D-006 partitioning in `services/settlement_ledger/partitioning.py`; add G-02
- [ ] **M1-EVT-01** Make settlement a consumer of `DEBITED` events; idempotent on `transaction_id` — D-007
- [ ] **M1-EVT-02** Make payee credit a consumer of `SETTLED` events; failure emits the event that triggers compensation — D-007, INV-1 still holds
- [ ] **M1-CTL-01** Data-plane services read a policy snapshot fetched from the control plane and cached with last-known-good fallback; remove the direct import in `kyc_aml.py`
- [ ] **M1-OPS-01** Update `docker-compose.yml` so the demo still runs end to end after M1-EVT
- [ ] **M1-OPS-02** Set `SPEC_LINT_STRICT=1` in `.github/workflows/spec-gate.yml`
- [ ] **M1-DOC-01** Claims register has no `claimed` rows; M1 verdict recorded

---

## M2 — Presentation

- [ ] **M2-DOC-01** Regenerate the architecture diagram from the claims register, honored vs conceptual visually distinct
- [ ] **M2-DOC-02** Write the v0 → v1 comparison (bugs, broken claims, fixes)
- [ ] **M2-DOC-03** Rewrite README around the design; link the claims register

---

## Backlog — unscheduled, do not start

- Local load test for the interactive path's p99 — optional M2 item; do only if time remains
- A sixth adapter (e.g. UAE) — only if the presentation specifically wants to demonstrate extensibility live
- Netting-window simulation in the ledger — interesting, not needed to argue D-002
