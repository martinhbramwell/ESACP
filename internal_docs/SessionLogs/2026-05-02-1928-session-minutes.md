# 2026-05-02 1928 — Session minutes

**Branch:** none (direct-on-main for the ESACP residue commit; bespoke-app commits on their existing branches).
**Objective:** Inter-session — dispose of #337 (24 Phase 2 staged promotion writes; 7 translations under `es.csv` not `es-EC.csv`). Slot before Session 3 of 4 per the prior agenda.

## Pre-flight

- `bash platforms/kvm/sync_check.sh` → 45 ✅ / 9 ⚠️ / 2 ❌. Failures expected (dev02 shut off per `feedback_one_vm_at_a_time.md`).
- main at `a0f2ee4`. Working tree carried two staged-but-uncommitted session-log files from the prior session (2026-05-02 1739). Per the same pattern as Session 2.5's pre-branch housekeeping, committed on `main` as `docs(session-log): 2026-05-02 1739 …` (`d34a0ed`) before any disposition work.
- 29 open issues at session start (the prior agenda's "28" was off-by-one); #337 in scope; everything else carried.

## What ran

### Pre-disposition housekeeping

Committed prior session logs as `d34a0ed` on `main` and pushed. Working tree clean before touching bespoke-app worktrees.

### #337 — disposition

**Approach chosen** — Option 1 in spirit (revert + re-promote to satisfy U3), executed as in-place file rename in the two affected worktrees because the staged content was already byte-correct except for the CSV filename. The script `tools/customisation_audit/promote_app_translations_csv.py` derives the filename directly from `row_data.language`, so a "revert + redo" without first encoding the U3 alias (`es-EC` → `es`) into the script would have re-emitted the same `es-EC.csv` filenames. Renaming on disk preserves Phase 2's promotion content and aligns the filename with the U3 decision in one step.

**Bespoke-app commits** (pushed from controller per `feedback_commits_from_controller_only.md`):

| Repo | Branch | Commit | Files |
|---|---|---|---|
| ce_sri | feat/install-modular-pipeline | `d4fbd7c` | 1 `custom_field.json` + 6 `custom_scripts/*.js` + `translations/es.csv` (2 rows, renamed from `es-EC.csv`) |
| returnable (BtlMng) | wip/2026-03-31 | `b7a50f3` | 1 `custom_field.json` + `translations/es.csv` (4 rows, already correctly named at family-level `es`) |
| route_planner | wip/2026-03-31 | `e9b7b7f` | 1 `custom_scripts/Delivery Trip.js` + `property_setter.json` + `translations/es.csv` (1 row, renamed from `es-EC.csv`) |

**Acceptance verified** (per the issue body):

- All 24 Phase 2 staged drift records resolved across the 3 bespoke-app repos. (Note: "24 staged" in the issue body counted individual drift records from Phase 2 acceptance; the actual on-disk file footprint is 13 entries total — 8 + 2 + 3 — because multiple drifts collapsed into single fixture files.)
- All 7 translation rows now live under `<app>/translations/es.csv` (verified contents: ce_sri 2 rows, returnable 4 rows, route_planner 1 row).
- 3 bespoke-app repos each have their own pushed commit.
- Pushes from controller (Mighty), not from a VM.

**Filed for institutional memory — #339**: `promote_app_translations_csv.py` will re-emit `es-EC.csv` if the audit is re-run, because the U3 decision (V13 country-level translation resolution unreliable in production substrate; family-level `es` resolves consistently) is operator-empirical knowledge not encoded in the script. Per `feedback_not_perfection_project.md`, sized to pain — issue body marks it deferred; only matters if the audit is re-run before V14 cutover.

### Issue close

`gh issue close 337 --comment` posted the disposition record with the three commit hashes. Open-issue count: 29 → 28 → 29 (after filing #339 as the deferred prevention follow-up at session-end audit).

## Issues touched

| Issue | Action | Resolution |
|---|---|---|
| #337 | Closed completed | 3 commits across ce_sri / returnable / route_planner; close-comment lists hashes |
| #339 | Filed (deferred) | Script-level prevention follow-up: `promote_app_translations_csv.py` language alias map (`es-EC` → `es`); not a V14 blocker |

## Operator correction internalised

Mid-session, asked the operator three sub-decisions (commit residue first?, which Option 1/2/3?, PR-gate the bespoke commits?) when the issue body, prior memory, and feedback files already encoded the answers. Operator reframed it as: would a business-owner client paying for ESACP consulting want to be asked these? No. Pick and proceed.

Memory updated — `feedback_enumerate_mechanisms_before_committing.md` now carries a sharper "an operator decision requires the operator to have information or judgment the consultant lacks; otherwise it's a pick, not a decision" rule. This is the third session-flagged recurrence of the over-asking pattern (Session 2 minutes; not seen in Session 2.5; back in this session).

## Reminders for the operator

1. **Session 3 is unblocked** — no #337 dependency remaining. Q-G operator decision (P1 / P2 / P3) is the only gate before Phase 5 implementation.
2. **Phase 5 plan §3 link to U6 verdict** — still pending (operator-curated step from Session 2.5 minutes).
3. **One-VM rule** — dev02 stays shut off while dev01 is running.

## Memory updates queued

- `feedback_enumerate_mechanisms_before_committing.md` — recurrence + sharper rule (done in-session).
