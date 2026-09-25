# AGENT_LOG

Append-only. **Newest entry at the top.** Never edit past entries — append corrections as new ones.

Every session writes an entry, including failed sessions. "Noticed, did not fix" may not be empty without a reason.

---

## 2026-09-25 — Claude Opus 5.5 / claude.ai — pre-M0 (spec)

**Milestone:** none active yet — spec system written
**Tasks attempted:** none (spec session)
**Landed:** CONTRACT.md (INV-1..6), AGENTS.md, BRIEF.md, spec/ (product, architecture with capability and claims registers, plan M0–M2, tasks, evals, smoke, decisions D-001..D-008), enforcement layer (spec_lint, pre-commit, CI non-strict, Claude Code hooks, verifier). Verified with `spec_lint` and the M0-TST-02 starter tests.
**Did not land:** nothing attempted beyond the spec
**Blockers:** D-001..D-008 are proposed defaults — need Pushkar's confirmation. Presentation date and audience unknown.
**Noticed, did not fix:** v0 bugs recorded as M0/M1 tasks — refund missing after debit (orchestrator.py), per-process idempotency that burns keys on crash (common/idempotency.py), hot shard (partitioning.py hashes the region name only), direct control-plane import (risk_compliance/kyc_aml.py), synchronous chain described as event-driven. README "stub vs real logic" section corrected in this session: idempotency and partitioning moved from "real logic" to "known broken".
**Spec changes:** all files created
**Next action:** Pushkar confirms decisions and date; then M0-TST-01, starting in a new `tests/conftest.py`
