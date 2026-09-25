# BRIEF — BRICS Pay

*One page. Read in 3 minutes. Rewritten whenever state changes.*

**What this is:** a conceptual system design for cross-border payments across BRICS national rails — payer pays in their currency, payee receives theirs. Academic project, not affiliated with BRICS.

**Repo:** https://github.com/Pushkar0997/brics-pay · **Baseline:** tag `v0-baseline`

---

## Where things stand

**Milestone:** M0 — Correct money path (not started)
**Exit criteria:** all six CONTRACT invariants tested and passing; a forced credit failure ends `REVERSED`
**Progress:** 0 of 12 tasks

**Last done:** spec system written (2026-09-25)
**Next:** Pushkar confirms or changes D-001 to D-008, and sets the presentation date. Then M0-TST-01.

**Open questions for Pushkar:**
1. Presentation audience and date — sizes M2 and decides whether the load test happens
2. D-002 settlement and D-008 FX source — proposed defaults, need a yes or a change

---

## Prompt for the next session

Copy this into any coding agent once the decisions are confirmed:

```
Read AGENTS.md, then CONTRACT.md, then spec/plan.md and spec/tasks.md.
Then read the top 3 entries of AGENT_LOG.md.

Tell me which milestone is active and which task you propose next.
Do not write code yet.
```

---

## Three things most likely to break

1. `services/payment_router/orchestrator.py` — the saga refactor; easy to break G-04's happy-path history while fixing failures
2. `common/idempotency.py` — lease and claim logic; the crash case (N-04) is the subtle one
3. The claims register drifting from the slides — a claim added in PowerPoint is a claim nobody checks

---

## Where everything is

| Need | File |
|---|---|
| What must never break | `CONTRACT.md` |
| Rules for agents | `AGENTS.md` |
| What happened when | `AGENT_LOG.md` |
| What this is and why | `spec/product.md` |
| Stack, capabilities, claims | `spec/architecture.md` |
| Milestones | `spec/plan.md` |
| The backlog | `spec/tasks.md` |
| How correctness is proven | `spec/evals.md` |
| Pre-push checklist | `spec/smoke.md` |
| Why things are the way they are | `spec/decisions.md` |

---

## Standing rules

- Cost ceiling: ₹0 — local Docker Compose only
- Anti-metric (do not optimise): number of components on the diagram
- Real metric: every presented claim honored or labelled conceptual
