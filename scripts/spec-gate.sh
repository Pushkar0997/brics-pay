#!/usr/bin/env bash
# spec-gate.sh — one entry point for every enforcement surface.
#
#   scripts/spec-gate.sh commit   git pre-commit: spec lint + fast tests
#   scripts/spec-gate.sh ci       CI: strict spec lint + full test suite
#   scripts/spec-gate.sh quick    Claude Code PostToolUse: fast tests only
#   scripts/spec-gate.sh stop     Claude Code Stop: refuse to end a session
#                                 with failing tests or no AGENT_LOG entry
#
# Configure the two commands below once per project. Keep FAST_TESTS under
# ~20 seconds or agents (and you) will start routing around it.
set -uo pipefail

FAST_TESTS="${SPEC_FAST_TESTS:-python3 -m pytest -q -p no:cacheprovider tests}"
FULL_TESTS="${SPEC_FULL_TESTS:-$FAST_TESTS}"

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
mode="${1:-commit}"

run() { bash -c "$1" >/tmp/spec-gate.out 2>&1; local rc=$?; [ $rc -ne 0 ] && tail -40 /tmp/spec-gate.out >&2; return $rc; }

case "$mode" in
  commit)
    python3 scripts/spec_lint.py || exit 1
    run "$FAST_TESTS" || { echo "spec-gate: fast tests failed — commit blocked" >&2; exit 1; }
    ;;
  ci)
    # Non-strict until M1 closes: open 'claimed' rows are expected until then.
    # Task M1-OPS-02 sets SPEC_LINT_STRICT=1 in the workflow.
    if [ "${SPEC_LINT_STRICT:-0}" = "1" ]; then python3 scripts/spec_lint.py --strict || exit 1
    else python3 scripts/spec_lint.py || exit 1; fi
    run "$FULL_TESTS" || exit 1
    ;;
  quick)
    # Exit 2 feeds stderr back to Claude so it fixes the break immediately.
    run "$FAST_TESTS" || { echo "Tests are failing after your last edit. Fix before continuing." >&2; exit 2; }
    ;;
  stop)
    input="$(cat)"
    # Avoid infinite loops: if we already blocked once this turn, let it stop.
    if echo "$input" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then exit 0; fi
    # Ignore spec/log files and build/test caches (running tests must not count as a change).
    changed_code="$(git status --porcelain 2>/dev/null \
      | grep -vE '(AGENT_LOG|BRIEF)\.md|spec/|__pycache__|\.pyc$|\.pytest_cache|node_modules|\.next/|dist/|build/|\.cache' \
      | head -1)"
    [ -z "$changed_code" ] && exit 0   # nothing changed: a read-only session may end freely
    if ! run "$FAST_TESTS"; then
      echo "Do not end the session: tests are failing. Fix them, or record the failure honestly in AGENT_LOG.md as 'Did not land'." >&2; exit 2
    fi
    if ! git status --porcelain | grep -q 'AGENT_LOG.md'; then
      echo "Code changed but AGENT_LOG.md has no new entry. Run the closing-session prompt: add the log entry and update BRIEF.md." >&2; exit 2
    fi
    ;;
  *) echo "usage: spec-gate.sh commit|ci|quick|stop" >&2; exit 64 ;;
esac
exit 0
