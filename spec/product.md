# product.md — BRICS Pay

## 1. One-line definition
A conceptual system design showing how a person in one BRICS country could pay a merchant in another in their own currency, with the merchant paid in theirs — on top of each country's existing payment rails rather than replacing them.

## 2. The problem
Cross-border retail payments between these economies typically route through correspondent banks and a third currency, adding cost, delay and exposure to that currency. Each country already has a strong domestic real-time rail (UPI, Pix and others) but they do not interoperate. The design question is how to connect them while each country keeps control of its currency, rules and data.

## 3. Target user
**Primary:** the evaluators and audience of a university system-design presentation — people who will probe failure handling, scale and sovereignty.
**Secondary:** a technical reader of the GitHub repo judging the design and the engineering discipline behind it.
**Explicitly not the target:** actual payers, merchants, banks or regulators. Nothing here is fit for real money.

## 4. Core promise
> After seeing this, a reviewer can explain how a cross-border payment would flow through federated national rails, where it could fail, and why the design handles each failure — and can verify every claim against the code or see it honestly labelled conceptual.

## 5. Non-goals
- **A working payment product** — real rails, banks and regulators cannot be integrated from a student repository.
- **A position on BRICS monetary policy** — settlement choices are engineering defaults (D-002, D-008), not political recommendations.
- **Production infrastructure** — Kafka, Kubernetes and multi-region deployment are shown in the design, not deployed (D-001).
- **A user interface** — the audience evaluates the architecture.
- **Any implication of official status** — the project is not affiliated with or endorsed by BRICS or any member institution.

## 6. Success metrics
1. Every claim in the presentation maps to a claims-register row that is `honored` or `conceptual` — target: 100%, zero `claimed`.
2. The India → China demo, including the forced-failure reversal, runs live from the README in under 10 minutes.

**Anti-metric — do not optimise:** the number of components, services or boxes on the diagram. It rises easily and makes the design look more impressive while making it less true.

## 7. Kill criteria
If the presentation is cancelled or the deadline leaves under ~10 hours, stop after M0 and present v0's architecture with the claims register as the honest-limitations slide.

## 8. Glossary
- **Rail** — a country's domestic payment system (UPI, Pix, CIPS, SPFS, RTC).
- **Adapter** — the only code that knows a specific rail; translates the core's debit / credit / refund into that rail's protocol.
- **Quote** — a locked exchange rate and receive amount, valid for `QUOTE_TTL_SECONDS`.
- **Saga** — a multi-step transaction where a failure after a completed step triggers compensating steps (here: a refund) instead of a rollback.
- **Honored / conceptual / claimed** — the three statuses in the claims register (`spec/architecture.md` §8).
- **Settlement** — moving the actual funds between countries' settlement accounts, after the user-facing payment completes.
