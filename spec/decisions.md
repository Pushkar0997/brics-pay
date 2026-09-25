# decisions.md — Decision Log

Every non-obvious decision, why, and what was rejected. **This file exists to stop the next agent from re-opening a settled question or reverting a deliberate choice.**

Entries marked **proposed** were drafted by Claude on 2026-09-25 as defaults and await Pushkar's confirmation. Per A-18, they were formed inside a long single conversation; weigh them accordingly, and change any of them before M0 starts rather than after.

---

## D-001 — Rigor level: design exercise with a correct money core

**Status:** proposed
**Decision:** The architecture, decisions and claims register are the primary deliverable. Code is illustrative, with one exception: the money path (orchestration, idempotency, quotes, state machine) must actually satisfy `CONTRACT.md`. Everything else may be a stub, provided it is labelled `conceptual` in the claims register.
**Rationale:** The project is a presentation, not a product. Implementing Kafka, multi-region deployment or real rail integrations would be weeks of work that proves nothing a diagram cannot. But a payment demo that loses money on a failed credit undermines the whole design the moment someone asks about failure handling — and in a system-design review, someone always does.
**Rejected:**
- *Spec-anchored, everything implemented* — enormous scope, and real rails and regulators cannot be integrated from a student repo anyway.
- *Pure design exercise, code deleted* — throws away the part that makes the design concrete; the working India → China flow is the strongest demo asset.
- *Leave v0 as is* — the known bugs contradict the architecture's own claims (A-19).

**Revisit if:** the project becomes a portfolio piece to be extended toward a real product, or the presentation audience wants a load-test result.

---

## D-002 — Settlement: bilateral deferred net settlement in local currencies

**Status:** proposed
**Decision:** Each pair of countries settles in their own currencies through settlement accounts at designated settlement banks. Obligations are netted per currency pair and settled in windows (conceptually every 15 minutes); a transaction above a large-value threshold settles gross, individually. The ledger records per-transaction obligations; netting is modelled, not executed against real banks.
**Rationale:** This keeps the design's core promise — no dependence on a third currency — without requiring institutions that do not exist. Netting cuts the liquidity each country must hold, which is why real deferred-net-settlement systems use it. Gross settlement for large values bounds the credit risk a netting window creates.
**Rejected:**
- *A common basket unit (SDR-style)* — requires an issuing institution and political agreement that do not exist; building on it would make the whole design rest on an imaginary capability (A-3).
- *USD as a vehicle currency* — defeats the stated purpose of the system.
- *Real-time gross settlement for every payment* — each transaction then needs pre-funded liquidity in the payee's currency; costly at scale, and unnecessary for retail amounts.

**Revisit if:** a real common settlement unit or a multilateral clearing institution is announced.

---

## D-003 — Compliance: federated, with a common minimum

**Status:** proposed
**Decision:** The core runs a shared minimum on every payment (sanctions screening, KYC tier limits from `CONTRACT.md`). Each country supplies its own compliance module alongside its rail adapter, behind a common interface. Both the payer's and the payee's modules must approve before any debit (INV-4).
**Rationale:** Mirrors the design's sovereignty principle: countries keep their own rules, the core only guarantees that both sets ran. A single unified standard would have to be the strictest of five regimes or be rejected by at least one of them.
**Rejected:**
- *One shared standard for all members* — politically infeasible, and it moves regulation into the core, breaking INV-5.
- *Payer-side checks only* — the receiving country has its own obligations; debiting before it approves forces avoidable reversals.
- *Payee-side check after debit* — same problem, later.

**Revisit if:** the members adopt a common AML/CFT framework.

---

## D-004 — Failure after debit: saga with compensation

**Status:** proposed
**Decision:** The payment is a saga. If any step after a successful debit fails (settlement or payee credit), the transaction moves to `REVERSING`, the payer's adapter refunds the debited amount, and the transaction ends `REVERSED`. `NationalRailAdapter` gains a `refund` method. Refund failure is retried with backoff and, after the retry budget, raised to a manual-review queue — never silently dropped.
**Rationale:** National rails expose debit and credit, not "prepare" and "commit"; a distributed transaction across them is impossible. Compensation is the standard answer, and it is what makes INV-1 true.
**Rejected:**
- *Two-phase commit across rails* — the rails do not support it and never will.
- *Credit first, debit second* — shifts the loss onto the system's own liquidity whenever the debit fails.
- *Mark FAILED and reconcile later* — v0's behaviour; money is lost until a human notices.

**Revisit if:** never, for the retail path.

---

## D-005 — Idempotency: shared store, result replay, set after completion

**Status:** proposed
**Decision:** Idempotency moves behind an `IdempotencyBackend` interface with two implementations: in-memory (tests, single-process demo) and a shared store (Redis-style, conceptual for this project). The key is claimed atomically as `IN_PROGRESS`, the final response is stored against it, and repeats return that stored response. A claim left `IN_PROGRESS` past a lease timeout can be retried.
**Rationale:** Fixes both v0 bugs: per-replica state and keys burned by crashes. Returning the stored result instead of `duplicate_ignored` is what clients actually need.
**Rejected:**
- *Per-process set (v0)* — breaks with a second replica, which the autoscaler guarantees.
- *Rely on client-generated transaction IDs alone* — the same bug moves into every client.

**Revisit if:** the store's lease timeout causes double-processing in testing.

---

## D-006 — Ledger partitioning: region, then hash

**Status:** proposed
**Decision:** The partition is chosen in two steps: region from the payer's country (data residency), then `hash(transaction_id) mod LEDGER_PARTITIONS` within that region (load spread).
**Rationale:** v0 hashed the region name alone, so every Indian transaction landed in one partition — a hot shard that contradicts the scalability claim. Region-first keeps residency; hash-second spreads load.
**Rejected:**
- *Region only (v0)* — one partition per country.
- *Global hash only* — spreads load but breaks data residency, one of the design's sovereignty claims.

**Revisit if:** a single region's load exceeds what 16 partitions can hold — raise `LEDGER_PARTITIONS` for that region.

---

## D-007 — Execution model: synchronous where the user waits, events after

**Status:** proposed
**Decision:** The interactive path — authenticate, compliance, quote, authorize, debit — stays synchronous, because the user is waiting for an answer. Everything after the debit (settlement, payee credit, notifications, reconciliation) is driven by events on the event bus, each consumer idempotent. The architecture is described as "hybrid: synchronous authorization, event-driven settlement", not "event-driven".
**Rationale:** This is how real payment systems work, and it makes the architecture's claim true instead of dropping it. Fully asynchronous authorization would leave the user with no confirmation of whether they were charged.
**Rejected:**
- *Keep the fully synchronous chain (v0) and keep claiming "event-driven"* — the claim is false (A-19).
- *Fully event-driven including authorization* — the user cannot be told the result synchronously; worse UX, and no simpler.

**Revisit if:** latency measurements show the synchronous path breaking its budget.

---

## D-008 — FX: market rate from liquidity providers, locked quote, reference band

**Status:** proposed
**Decision:** Rates come from designated FX liquidity providers (a static table in this project, labelled conceptual). A quote locks the rate for `QUOTE_TTL_SECONDS`. A market rate more than `REFERENCE_BAND_PCT` away from the central-bank reference rate is rejected as a sanity check.
**Rationale:** Central-bank reference rates are published about once a day and cannot be honoured intraday by anyone providing liquidity. Market rates can, but need a lock so the user pays what they saw (INV-3), and a band so a bad feed cannot price a payment absurdly.
**Rejected:**
- *Central-bank reference rates only* — stale within hours; liquidity providers would refuse to trade at them.
- *Market rate with no lock* — the payer sees one amount and the payee receives another.
- *No reference band* — one bad tick from a provider prices real payments.

**Revisit if:** the members publish an intraday official rate.

---

## Template

```
## D-0XX — <short title>

**Status:** proposed | decided | superseded by D-0YY
**Decision:** <what>
**Rationale:** <why, including what breaks without it>
**Rejected:** <alternatives, each with why not>
**Revisit if:** <condition>
```

Rules: add the entry the day the decision is made — backfilled logs are fiction. Supersede rather than delete. The rejected list is the part that does the work.
