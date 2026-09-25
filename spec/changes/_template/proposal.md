# CH-<nnn> — <short name>

**Status:** proposed | approved | in progress | merged | abandoned
**Milestone:** <M-n this lands in>
**Author/model:** <who proposed it>

## Why
<The problem this change solves, in one paragraph. If it is not tied to the active
milestone or a real defect, it probably belongs in the backlog instead.>

## What changes (delta against current spec)
Only what differs from spec/ today. Not a restatement of the system.

**ADDED requirements**
- R-<nnn>: WHEN <trigger> THE system SHALL <observable response>.

**MODIFIED requirements**
- <file + section>: <old> → <new>

**REMOVED requirements**
- <file + section>: <what goes, and why>

## Out of scope
- <at least one explicit exclusion — agents expand scope unless the door is closed>

## Open questions (clarify pass)
- <each ambiguity, with a proposed default. None may remain when status → approved.>

## Decisions
- <link to spec/decisions.md entries this change creates, or "none">

## Tasks
- [ ] M<n>-<AREA>-<nn> <verb + file> — satisfies R-<nnn>, tested by <eval ID>

## Verification
- <eval IDs added to spec/evals.md for this change>

## On merge
Fold ADDED/MODIFIED/REMOVED into the real spec files in the same commit as the last
task, set Status: merged, and move this folder to spec/changes/archive/.
