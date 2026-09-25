# architecture.md — BRICS Pay

## 1. Stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| Language | Python | 3.12 | Matches the Dockerfile base image |
| Web framework | FastAPI | 0.115.0 | Typed request models, one pattern for every service |
| ASGI server | uvicorn[standard] | 0.30.6 | FastAPI default |
| HTTP client | httpx | 0.27.2 | Async client for service-to-service calls |
| Validation | pydantic | 2.9.2 | v2 API only — do not generate v1 `class Config` code |
| Tests | pytest | 8.3.3 | Dev-only, in `requirements-dev.txt` |
| Local runtime | Docker Compose | — | Six services on one machine |
| Orchestration (illustrative) | Kubernetes manifests | apps/v1, autoscaling/v2 | Present to show the scaling story; not deployed |

## 2. Structure

```
brics-pay/
├── common/            ← shared models, config, auth, idempotency. No service imports another service; they share only this.
├── event_bus/         ← pub/sub interface. In-memory implementation only; the interface is what a Kafka backend would implement.
├── control_plane/     ← policy and config. Data-plane services read a cached copy; they never import this package at runtime (target state, see claims).
├── services/
│   ├── api_gateway/       ← the only externally exposed service
│   ├── payment_router/    ← orchestrator, state machine, saga. The money path lives here.
│   ├── fx_rates_engine/   ← quotes and locks rates
│   ├── risk_compliance/   ← common-minimum checks; calls per-country modules
│   └── settlement_ledger/ ← partitioned ledger, netting model
├── adapters/          ← one file per country rail. The ONLY place country-specific logic may live (INV-5).
├── infra/k8s/         ← illustrative manifests, not applied anywhere
├── tests/             ← pytest; every test named or docstringed with the eval ID it checks
└── spec/              ← this system
```

## 3. Data model

- **TransactionRequest** — payer, payee, send amount, idempotency key, transaction ID, created_at.
- **TransactionRecord** — request, current state, state history, locked quote (rate, receive amount, expiry), risk score, failure reason.
- **LedgerEntry** — append-only; one per settlement obligation, keyed by transaction ID, placed by the D-006 partition rule.
- **Idempotency record** — `<payer_id>:<key>` → status (`IN_PROGRESS` | `DONE`), stored response, lease expiry.

Expensive to reverse: the ledger entry shape and the partition key. Everything else is cheap.

## 4. Capability register

**Consult before building anything. Never build on an unsupported capability.**

| Capability | Status | Needed for |
|---|---|---|
| India → China payment end to end (single process / Compose) | supported | the demo |
| State machine with legal-transition enforcement | supported | INV-6 |
| Static FX quote with spread | supported | INV-3 |
| Adapter registry, one file per country | supported | INV-5 |
| Refund / compensation | **not supported** | INV-1 — added in M0 (M0-PAY-02) |
| Quote lock with TTL | **not supported** | INV-3 — added in M0 (M0-FX-01) |
| Shared idempotency with result replay | **not supported** | INV-2 — added in M0 (M0-IDM-01) |
| Payee-side compliance check before debit | **not supported** | INV-4 — added in M0 (M0-CMP-01) |
| Event-driven settlement and credit | **not supported** | D-007 — added in M1 |
| Real national rail integration | **not supported** | never, in this project — stubs by design |
| Live FX feed | **not supported** | never, in this project |
| Real message broker (Kafka/Pulsar) | **not supported** | never, in this project — interface only |
| Multi-region deployment | **not supported** | never, in this project — shown in the architecture only |

## 5. Scale assumptions

- Building for: a single-machine demo and a design that argues convincingly for billions of transactions per day.
- The scale targets in the original brief are **design targets**, not measured results. Never present them as achieved.
- First thing to break at real scale: the shared idempotency store and the per-region ledger write path.
- Expensive to reverse: the ledger partition key, the transaction state set.

## 6. Performance budget

Conceptual targets for the design, not measured claims:

- Interactive path (authenticate → debit): p99 under 1 s.
- Payee confirmation: under 5 s after debit.

Measured in this project only if M2 includes the optional load test.

## 7. Security and privacy

- Stored about users: party IDs, country, account reference, KYC tier. No names, no documents.
- Never logged: account references in full (mask all but the last 4 characters), bearer tokens.
- Auth: v0 checks only that a bearer token is present. This is a stub and is listed as such below.
- Secrets: none required by the demo. If any are added, they live in `.env` (gitignored) and reach services via Compose `env_file`.

## 8. Architecture claims register

Every property the diagrams, README or presentation assert. A claim is **honored** (code and a test back it), **conceptual** (deliberately not built; shown in the design only), or **claimed** (asserted but not yet true — each one is a task).

| Claim | Status | Evidence |
|---|---|---|
| Adding a country needs only a new adapter file | claimed | INV-5-T, added in M0 |
| Money is never lost on a failed payment | claimed | INV-1-T, added in M0 |
| Retries never double-charge | claimed | INV-2-T, added in M0 |
| The payee receives exactly the quoted amount | claimed | INV-3-T, added in M0 |
| Hybrid execution: synchronous authorization, event-driven settlement | claimed | M1-EVT tasks |
| Ledger is partitioned for load and residency | claimed | G-02, M1-LED-01 (v0 has a hot shard) |
| Data plane keeps working when the control plane is down | claimed | M1-CTL-01 (v0 imports the control plane directly) |
| Stateless, horizontally scalable services | claimed | depends on D-005 shared idempotency, M0 |
| Multi-region active-active deployment | conceptual | shown in the architecture diagram only |
| Kafka/Pulsar-style partitioned event streaming | conceptual | in-memory bus implements the interface only |
| Kubernetes autoscaling | conceptual | manifests present, never applied |
| Integration with UPI, Pix, CIPS, SPFS, RTC | conceptual | adapters are stubs returning success |
| Live FX rates from liquidity providers | conceptual | static table |
| Zero-trust auth, mTLS, HSM key management | conceptual | token-presence stub only |
