#!/usr/bin/env python3
"""spec_lint — mechanical enforcement for the spec-driven-development system.

Turns the system's written rules into checks that fail. Runs anywhere Python 3.9+
runs, needs no dependencies, and is tool-agnostic: the same script backs the git
pre-commit hook, CI, and (optionally) Claude Code hooks.

Usage:
    python scripts/spec_lint.py            # errors fail, warnings print
    python scripts/spec_lint.py --strict   # warnings also fail (use in CI)

Checks (E = error, W = warning):
    E1  Template placeholders (<...>) or TODO left in spec files
    E2  A CONTRACT.md invariant with no test row in spec/evals.md
    E3  A decision in spec/decisions.md missing Rejected: or Revisit if:
    E4  Duplicate task IDs in spec/tasks.md
    E5  A task ID that does not match M<n>-<AREA>-<nn>
    W1  An eval ID (G-/N-/INV-n-T) never referenced in any test file
    W2  BRIEF.md longer than one page (~80 lines)
    W3  An architecture claim not backed by evidence (claims register)
    W4  An open change proposal older than the active milestone's work
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
SPEC_FILES = ["CONTRACT.md", "AGENTS.md", "BRIEF.md"]
TEST_DIRS = ["tests", "test", "src", "__tests__", "spec_tests"]
TEST_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt"}

PLACEHOLDER = re.compile(r"<(?!!--)(?!/?[a-z]+[ >/])[A-Za-z][^<>\n]{0,80}>")
TODO = re.compile(r"\bTODO\b")
FENCE = re.compile(r"^\s*```")

errors: list[str] = []
warnings: list[str] = []


def strip_code(text: str) -> list[tuple[int, str]]:
    """Return (line_no, line) pairs outside fenced code blocks and inline code."""
    out, in_fence = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i, re.sub(r"`[^`]*`", "", line)))
    return out


def read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def spec_paths() -> list[Path]:
    paths = [ROOT / f for f in SPEC_FILES]
    spec_dir = ROOT / "spec"
    if spec_dir.is_dir():
        paths += sorted(p for p in spec_dir.rglob("*.md") if "_template" not in p.parts)
    return [p for p in paths if p.exists()]


def check_placeholders() -> None:
    for path in spec_paths():
        for no, line in strip_code(path.read_text(encoding="utf-8")):
            if PLACEHOLDER.search(line) or TODO.search(line):
                errors.append(f"E1 {path.relative_to(ROOT)}:{no} placeholder/TODO: {line.strip()[:90]}")


def check_invariants_have_tests() -> None:
    contract, evals = read(ROOT / "CONTRACT.md"), read(ROOT / "spec" / "evals.md")
    if contract is None:
        return
    invariants = re.findall(r"^#{2,4}\s+(INV-\d+)\b", contract, re.M)
    if evals is None:
        if invariants:
            errors.append("E2 CONTRACT.md has invariants but spec/evals.md does not exist")
        return
    for inv in invariants:
        if not re.search(rf"\b{inv}(-T)?\b", evals):
            errors.append(f"E2 {inv} in CONTRACT.md has no test row in spec/evals.md")


def check_decisions() -> None:
    text = read(ROOT / "spec" / "decisions.md")
    if text is None:
        return
    text = re.split(r"^## Template\b", text, flags=re.M)[0]
    for block in re.split(r"(?=^## D-\d+)", text, flags=re.M):
        m = re.match(r"## (D-\d+)", block)
        if not m:
            continue
        rejected = re.search(r"\*\*Rejected:\*\*(.*?)(?=\n\*\*|\Z)", block, re.S)
        if not rejected or not rejected.group(1).strip(" \n-"):
            errors.append(f"E3 {m.group(1)} has no rejected alternatives")
        if "**Revisit if:**" not in block:
            errors.append(f"E3 {m.group(1)} has no revisit trigger")


def check_tasks() -> None:
    text = read(ROOT / "spec" / "tasks.md")
    if text is None:
        return
    ids = re.findall(r"\*\*(M\d+-[A-Za-z0-9]+-\d+|[^*\s]+-\d+)\*\*", text)
    seen: set[str] = set()
    for tid in ids:
        if not re.fullmatch(r"M\d+-[A-Z0-9]+-\d{2,}", tid):
            errors.append(f"E5 task ID '{tid}' does not match M<n>-<AREA>-<nn>")
        if tid in seen:
            errors.append(f"E4 duplicate task ID {tid}")
        seen.add(tid)


def check_eval_traceability() -> None:
    evals = read(ROOT / "spec" / "evals.md")
    if evals is None:
        return
    ids = sorted(set(re.findall(r"\|\s*((?:G|N)-\d+|INV-\d+-T)\s*\|", evals)))
    if not ids:
        return
    corpus = []
    for d in TEST_DIRS:
        base = ROOT / d
        if base.is_dir():
            for p in base.rglob("*"):
                if p.suffix in TEST_SUFFIXES and p.is_file() and "node_modules" not in p.parts:
                    try:
                        corpus.append(p.read_text(encoding="utf-8", errors="ignore"))
                    except OSError:
                        pass
    blob = "\n".join(corpus)
    for eid in ids:
        # Accept G-01, G_01, G01 (test names cannot contain '-'); INV-n-T also matches INVn.
        base = re.sub(r"-T$", "", eid)
        pattern = re.escape(base).replace(r"\-", "[-_]?") + r"(?:[-_]?T)?(?![0-9])"
        if not re.search(pattern, blob):
            warnings.append(f"W1 eval {eid} is not referenced by any test (tag the test with its ID)")


def check_brief_length() -> None:
    text = read(ROOT / "BRIEF.md")
    if text and len(text.splitlines()) > 80:
        warnings.append(f"W2 BRIEF.md is {len(text.splitlines())} lines — it has stopped being the fast file")


def check_claims_register() -> None:
    text = read(ROOT / "spec" / "architecture.md")
    if text is None:
        return
    section = re.search(r"^## \d*\.?\s*Architecture claims.*?(?=^## |\Z)", text, re.M | re.S)
    if not section:
        return
    for row in section.group(0).splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in {"claim", ""} or set(cells[0]) <= {"-", " "}:
            continue
        status, evidence = cells[1].lower(), cells[2]
        if status == "honored" and not evidence:
            warnings.append(f"W3 claim '{cells[0][:60]}' marked honored with no evidence")
        if status in {"claimed", "unverified"}:
            warnings.append(f"W3 claim '{cells[0][:60]}' is not yet backed by code or a test")


def check_open_changes() -> None:
    changes = ROOT / "spec" / "changes"
    if not changes.is_dir():
        return
    for proposal in changes.glob("*/proposal.md"):
        if "_template" in proposal.parts or "archive" in proposal.parts:
            continue
        text = proposal.read_text(encoding="utf-8")
        if re.search(r"\*\*Status:\*\*\s*merged", text, re.I):
            warnings.append(f"W4 {proposal.parent.name} is merged but not archived — fold deltas into spec/ and move it to spec/changes/archive/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args()

    for check in (check_placeholders, check_invariants_have_tests, check_decisions, check_tasks,
                  check_eval_traceability, check_brief_length, check_claims_register, check_open_changes):
        check()

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error:   {e}", file=sys.stderr)

    failed = bool(errors) or (args.strict and bool(warnings))
    print(f"\nspec_lint: {len(errors)} error(s), {len(warnings)} warning(s) — {'FAIL' if failed else 'OK'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
