# AGENTS.md — BRICS Pay

**Read this completely before touching any code.**

**Rigor level:** design exercise with a correct money core (D-001). Architecture and claims are the deliverable; the money path must satisfy `CONTRACT.md`; everything else may be a stub if the claims register says so.

This is a **conceptual academic design**, not affiliated with BRICS. Never write code, comments, docs or commit messages that imply otherwise.

---

## 1. Read order

1. `AGENTS.md` — this file
2. `CONTRACT.md` — what must never break
3. `spec/architecture.md` — stack, structure, capability register, claims register
4. `spec/plan.md` — which milestone is active
5. `spec/tasks.md` — the specific task
6. `AGENT_LOG.md` — top 3 entries, for current state

Read `spec/evals.md` before claiming anything works. Read `spec/smoke.md` before any push touching the money path. Read `spec/decisions.md` before proposing an architectural change — it may already have been rejected. For any change bigger than one task, write a proposal in `spec/changes/` first and wait for approval.

**If a task conflicts with `CONTRACT.md`, the contract wins.** Stop and flag it. Do not silently resolve.

**You do not verify your own work.** Report the task; a separate verifier (`.claude/agents/spec-verifier.md`, or the same prompt in a fresh session) checks it before the checkbox is ticked.

---

## 2. Hard invariants

Full statements in `CONTRACT.md`. Cite them by ID in review.

- **INV-1** Money is conserved — no terminal state leaves a debit without a credit or a refund.
- **INV-2** One payment per idempotency key, across replicas.
- **INV-3** The quote shown is the quote honored.
- **INV-4** Both jurisdictions approve before any debit.
- **INV-5** No country-specific logic outside `adapters/`.
- **INV-6** Only legal state transitions.

Plus two project rules:

- **Zero cost.** No paid services, no cloud deployment. Everything runs locally with Docker Compose.
- **No new infrastructure.** Kafka, Redis, Kubernetes clusters and real rails stay conceptual (D-001). Implement interfaces and in-memory backends, never the real systems.

---

## 3. Stack — pinned

| Layer | Choice | Version |
|---|---|---|
| Language | Python | 3.12 |
| Framework | FastAPI | 0.115.0 |
| Server | uvicorn[standard] | 0.30.6 |
| HTTP client | httpx | 0.27.2 |
| Validation | pydantic | 2.9.2 (v2 API only) |
| Tests | pytest | 8.3.3 |

Do not add a runtime dependency without a `spec/decisions.md` entry.

---

## 4. Working rules

**One task per change.** Do not batch. Do not refactor files you were not asked to touch.

**Keep the happy path's shape.** G-04 pins the state history of a successful payment; M0 changes failure handling, not that sequence.

**Report what you changed:** files created and modified, symbols added or changed, spec files needing updates, and anything noticed but not fixed.

**Update the spec when reality diverges** — in the same commit. A new claim anywhere (README, docstring, slide) needs a claims-register row.

**Do not invent.** If a value, convention or capability is not in `CONTRACT.md` or `spec/architecture.md`, ask.

**Configuration is read at call time**, never bound at import (A-14). This matters for `BRICS_FAIL_CREDIT_COUNTRY` in particular.

**Never write a real secret into a tracked file.** The demo needs none.

---

## 5. Definition of done

- [ ] `python3 -m pytest -q tests` passes
- [ ] `python3 scripts/spec_lint.py` passes
- [ ] The task's cited eval IDs have tests named with those IDs
- [ ] `spec/smoke.md` passes for the affected area
- [ ] Spec and claims register updated if behaviour or claims changed
- [ ] Verified by the verifier, not only the implementer
- [ ] `spec/tasks.md` checkbox ticked from the verifier's report
- [ ] `AGENT_LOG.md` entry written, `BRIEF.md` updated
- [ ] Committed as `<type>(<scope>): <task-id> <summary>`

"It builds" is not done.

---

## 6. Vocabulary

- **payer / payee** — never "sender/receiver" or "user/merchant" in code; "merchant" is fine in prose.
- **send amount / receive amount** — in the payer's and payee's currency respectively.
- **rail** — a national payment system; **adapter** — our code for one rail.
- **refund** — the compensating action after a debit; not "rollback" (nothing is rolled back).
- **honored / conceptual / claimed** — claims-register statuses only.
