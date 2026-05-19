# Session Minutes — Open-Issues Purge Triage + Safe-Path Plan

**Date:** 2026-04-21 ~14:55–15:25 EDT
**Branch:** n/a — planning session, no branch, no commits beyond plan file + MEMORY.md pointer.
**Issues opened:** none (29 open issues triaged, none newly filed).
**PR:** none.

## Objective

Post-matrix planning session: prepare a safe-path plan for clearing the 29 remaining open issues, using matrix-blast-radius as the primary triage lens.

## Outcome

Plan file landed at `~/.claude/plans/open-issues-purge.md` (external to repo, same pattern as `acceptance-matrix-transport-parity.md` and `synthetic-mapping-pretzel.md`). MEMORY.md updated with pointer. 13-session purge ordering proposed; user has not yet committed to execution.

## Session narrative

### Triage criteria surfaced

User requested two triage lenses beyond the initial scale + subsection grouping:

1. **Matrix re-run impact** — which issues require re-running some or all of the 7-run acceptance matrix, and which subset of runs.
2. **Verify-once, never disturbed** — which issues can be closed without later phases invalidating their verification.

Both lenses were answered in-session, producing two parallel tables.

### Classification outcomes

**Tier A — zero matrix cost, safe-forever (12 issues):**
#213, #238, #243, #188, #217, #244, #216 (audit-gated), #50, #211 (audit-gated), #206, #271 (if unit-tested), #236.

**Tier B — narrow-blast (5 issues):**
- Runs 03 + 06: #181, #250
- Run 01: #220, #225
- Runs 05 + 06 + 07: #219

**Tier C — medium-blast (2 CLI-side issues):**
#187, #235 (likely sub-plan).

**Tier D — broad-blast, full-matrix (3 issues):**
#202 (priority:high), #240 + #241 (bundle).

**Out of purge scope (9 issues):**
- Policy / external: #48, #153, #236 (3 — partly Tier A)
- Parking lot: #65, #138, #156, #157, #223 (5 strategic features / research)

### Plan structure

13 sessions across 7 phases:

| Phase | Sessions | Issues closed | Matrix cost |
|---|---|---|---|
| 1 | 1A + 1B sweeps | 8 | 0 |
| 2 | 2A + 2B + 2C | 3 | 0 |
| 3 | 3A + 3B | 5 (incl. #271) | Run 01 + Runs 03/06 = 3 runs |
| 4 | 4A + 4B | 2 | 6 CLI runs (~2 hr) |
| 5 | 5 (main.js) | 1 | 3 UI runs (~50 min) |
| 6 | 6A + 6B | 3 | 14 runs (~6 hr, split) |
| 7 | 7 (policy) | 2 | 0 |
| **Total** | **13 sessions** | **24 issues** | **~10 hr wall time** |

5 remaining (features + research parking lot) left open, deferred.

Matrix-cost ledger keeps the purge bounded: the alternative ordering (no discipline) can double that by re-running after every small fix.

### Risk-mitigation notes captured in plan

Each SUT-disturbing phase has explicit gates written into the plan file:
- Audit-gates on #216, #211 (confirm dead before delete).
- B03/B06 archival before regeneration (Phase 3A).
- Byte-diff gates for #202 cloud-init template output.
- Per-VM roll-out rather than big-bang replacement (6A).
- LIVE cutover schedule + DNS rollback for 6B.
- Extraction-first-behaviour-change-later split for #219 main.js decomposition.

### MEMORY.md update

Added a new section pointing at the plan file, same pattern as Gen 3 plan reference. No compaction needed; MEMORY.md is well under the load limit post-matrix-closeout.

## State handed to next session(s)

- `main @ dcbfccd` unchanged — planning session made no repo commits.
- Plan file: `~/.claude/plans/open-issues-purge.md`.
- MEMORY.md: pointer added.
- **Recommended next session: Phase 1A — CC-OPS sweep** (#213, #238, #243, #188). One housekeeping PR, zero matrix cost, four issues closed. Acts as litmus test for the sweep-bundle pattern under the #262 amendment.

## Open decisions (captured in plan file; re-flagging here for visibility)

1. **#250 logo-in-DB question** — does the logo-upload fix land inside B03/B06 DB dumps, or only on the filesystem? If inside the dump, Runs 04 + 07 enter Phase 3A re-run scope. Decide at Phase 3A entry.
2. **#235 sub-plan** — CLI/API parity (13 new subcommands) likely needs its own plan file (`~/.claude/plans/cli-api-parity.md`). Decide at Phase 4B entry.
3. **#271 verification** — unit-test (stays Tier A, zero cost) vs spec-integration (moves to Phase 3A piggyback). Decide at Phase 2 entry.
4. **Plan acceptance** — user has not yet committed to the 13-session plan. First move (Phase 1A) pending acknowledgement.

## Reminders to user (unresolved concerns)

1. **Dev01 sync-check "unreachable" carve-out** — carried from Run 07 minutes, still not filed as issue. Dormant while dev01 runs.
2. **GPG-agent `default-cache-ttl`** — user has `allow-loopback-pinentry` + `pinentry-timeout 7200`, missing `default-cache-ttl 7200`. That omission caused two signing retries during the Run 07 session. Config unchanged.
3. **Plan acceptance pending** — Phase 1A entry needs explicit go-ahead before a new session opens a branch.

## File trail

- Plan file: `/home/hasan/.claude/plans/open-issues-purge.md` (new)
- MEMORY.md pointer added to "Open-Issues Purge Plan (post-matrix)" section
- This minutes: `internal_docs/SessionLogs/2026-04-21-1528-session-minutes.md`
- Prior-session minutes: `internal_docs/SessionLogs/2026-04-21-1420-session-minutes.md` (Run 07 GREEN + matrix closeout)
