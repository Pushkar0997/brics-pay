# plan.md — Milestones

Sequential. Do not start M(n+1) before M(n)'s exit criteria are met.

**Currently active: M0.** (Blocked on confirming D-001 to D-008 — see BRIEF.)

Estimates assume focused hours, not calendar days. The presentation deadline is not yet set; once it is, cut from M2's optional items first, never from M0.

---

## M0 — Correct money path ⏱ ~8–10 h · cost ₹0

The architecture's credibility rests on the payment path being right. Every invariant in `CONTRACT.md` becomes true and tested before anything else changes.

**Deliverables**
- Test harness and the first passing tests
- Saga compensation (refund, `REVERSING`, `REVERSED`)
- Quote lock with TTL, carried through to credit
- Shared-backend idempotency with result replay and leases
- Payee-side compliance before debit
- Fault injection so a failed credit can be demonstrated live

**Exit criteria**
- [ ] INV-1-T through INV-6-T pass
- [ ] N-01 through N-06 pass
- [ ] G-01, G-03, G-04 pass
- [ ] `smoke.md` §3 passes, including the forced-failure run ending `REVERSED`
- [ ] Every M0 claim in the claims register moved from `claimed` to `honored` with evidence
- [ ] Verdict recorded in `spec/evals.md` §7 by the verifier, not the implementer

**Risk:** the saga refactor tempts a rewrite of the whole orchestrator. Don't — change the failure handling, keep the happy path's shape so G-04's history stays identical.

---

## M1 — Claims made true ⏱ ~8 h · cost ₹0

Every remaining `claimed` row becomes `honored` or is honestly relabelled `conceptual`.

**Deliverables**
- D-006 partitioning (region, then hash)
- D-007 hybrid execution: settlement and payee credit driven by events, consumers idempotent
- Data plane reads a cached policy snapshot, no runtime import of `control_plane`
- `spec_lint` strict in CI

**Exit criteria**
- [ ] G-02 passes
- [ ] G-04 still passes with settlement and credit running as event consumers
- [ ] No `claimed` rows remain in the claims register
- [ ] CI runs `spec_lint --strict` and is green

---

## M2 — Presentation ⏱ ~5 h · cost ₹0

The design, told honestly.

**Deliverables**
- Architecture diagram regenerated from the claims register: honored and conceptual parts visually distinct
- v0 → v1 comparison: the four bugs, why each broke a claim, how each was fixed (tag `v0-baseline` vs current)
- README rewritten around the design, with the claims register linked
- *Optional:* a local load test measuring the interactive path's p99 on one machine

**Exit criteria**
- [ ] Every claim on a slide maps to a claims-register row
- [ ] A reviewer can run the demo from the README alone in under 10 minutes
- [ ] The presentation states in words that this is a conceptual design, not a deployed or endorsed system

---

## Sequencing rules
- M0 blocks everything. A presentation built on v0 would show a system that loses money.
- M1 before M2, because slides drawn before claims are true get redrawn.
- The optional load test is the first thing cut under deadline pressure.

## Anti-goals for the current stage

Things that will feel productive and are not, until M1 is complete:

- Adding more countries or adapters — the design claim is already demonstrated by five
- A real Kafka, Redis or Kubernetes deployment — conceptual by decision (D-001)
- A frontend or mobile UI — the audience is judging the architecture
- Live FX feeds or real rail integrations
- More boxes on the diagram

If you find yourself doing one of these, check which milestone is active.
