# smoke.md — Manual Smoke Checklist

Run before every push that touches the money path, and before the presentation. ~10 minutes.

```
python3 -m pytest -q tests && python3 scripts/spec_lint.py && docker-compose up --build
```

## 1. Build
- [ ] All six containers start; no tracebacks in `docker-compose logs`
- [ ] `curl localhost:8080/healthz` returns `{"status": "ok", ...}`

## 2. Happy path
- [ ] The README's India → China `curl` returns state `CONFIRMED` and `receive_amount` `857.85` `CNY`
- [ ] Repeating the exact same `curl` returns an identical response (INV-2), not a second payment

## 3. Failure path (after M0-PAY-04)
- [ ] Restart with `BRICS_FAIL_CREDIT_COUNTRY=CN`; a new payment returns state `REVERSED`
- [ ] Logs show exactly one debit and one refund for that transaction
- [ ] Unset the variable; a new payment returns `CONFIRMED` again

## 4. Presentation readiness
- [ ] Every claim on the slides appears in `spec/architecture.md` §8
- [ ] The slides say "conceptual design, not affiliated with BRICS" in words
- [ ] The demo runs from a fresh clone following only the README

---

## Failure protocol
1. **Roll back first:** `git checkout v0-baseline` for the demo, or the last green commit
2. Reproduce with a test
3. Add that test to `spec/evals.md`
4. Fix
5. Re-run this checklist in full

Every bug found here adds an item to this file.
