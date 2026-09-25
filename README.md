# BRICS Pay — conceptual reference implementation

A **conceptual, illustrative codebase** for the BRICS Pay system design
discussed earlier: a hypothetical cross-border payment interoperability
layer. It is not affiliated with, endorsed by, or descriptive of any real
BRICS institution or deployed system.

## Layout

- `common/` — shared models, config, auth, idempotency (used by every service)
- `event_bus/` — lightweight pub/sub abstraction standing in for Kafka/Pulsar
- `control_plane/` — identity/policy/config service, independent of the payment path
- `services/`
  - `api_gateway/` — public entry point, auth + routing
  - `payment_router/` — orchestrator + transaction state machine (the core flow)
  - `fx_rates_engine/` — currency conversion + rate quoting
  - `risk_compliance/` — fraud scoring + KYC/AML checks
  - `settlement_ledger/` — geo-partitioned ledger + settlement
- `adapters/` — one file per national payment rail (India/UPI, China/CIPS,
  Brazil/PIX, Russia/SPFS, South Africa/RTC). Adding a country means adding
  one adapter file here — the core never changes.
- `infra/k8s/` — example Deployment + HorizontalPodAutoscaler for one
  service, illustrating the horizontal-scaling story

## Running locally

```bash
pip install -r requirements.txt
docker-compose up --build
```

Then, once every container is up:

```bash
curl -X POST http://localhost:8080/v1/payments \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "payer_id": "user-in-1", "payer_country": "IN", "payer_account_ref": "upi:user@bank",
    "payee_id": "merchant-cn-1", "payee_country": "CN", "payee_account_ref": "cips:merchant-acct",
    "send_amount": "10000", "send_currency": "INR",
    "idempotency_key": "demo-tx-001"
  }'
```

`services/payment_router/orchestrator.py` is the file that actually walks
through the India → China example: auth → risk/KYC → FX quote → domestic
debit → settlement → merchant credit → confirmation, publishing an event
at each step.

## What's a stub vs. what's real logic

Real logic: the state machine, the orchestration flow, geo-partitioning,
idempotency, the control-plane/data-plane separation, and the adapter
interface pattern.

Stubbed for the demo: the FX rate table (static, not a live feed), the
national rail calls (return success after a no-op `sleep(0)`), the event
bus (in-process queue instead of Kafka/Pulsar), and auth (checks a token
is present, doesn't verify a signature). Each stub has a comment marking
what a production implementation would plug in.
