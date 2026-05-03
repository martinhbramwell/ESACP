# 2026-05-03 0732 — Session 3 minutes

**Branch:** `feat/upgrade-to-v14-and-patch-generator-phase-5` (cut from `main` `3c9001f`).
**Objective:** Phase 5 P1 — synthetic Frappe app `legacy_error_fixes` + 15 generated patches + V14 upgrade orchestrator. Q-G operator decision: P1 (full automation).
**Outcome:** PR #340 opened covering Plan §8 steps 1-6; **mergedAt null at session close — Session 3 not yet DONE per `feedback_pr_merge_before_session_close.md`.** Step 7 (E2E V14 upgrade run) and `fixes #331` close deferred to Session 3.5.

## Pre-flight

- `bash platforms/kvm/sync_check.sh` → 45 ✅ / 9 ⚠️ / 2 ❌. Both ❌ expected (dev02 shut off per `feedback_one_vm_at_a_time.md`).
- `gh issue list` → 29 open at session start, no new since 2026-05-02 1928.
- Working tree carried 2 staged session-log files from prior session; committed on `main` as `3c9001f` (`docs(session-log): 2026-05-02 1928 …`) before cutting branch (Session 2.5 / 2.6 housekeeping pattern).
- §3 U6 verdict link in Phase 5 plan still pending operator action — P1 doesn't need it (verifier was for P2/P3 dedup behaviour); proceeded.

## What ran (Plan §8 P1 steps)

### Step 1 — Synthetic Frappe app scaffold
`/home/hasan/projects/Logichem/legacy_error_fixes/` — separate git repo (commit `3bf34c9`). 12-file Frappe app skeleton modelled on `route_planner`. Empty `patches.txt`, `patches/v14_0/__init__.py` ready for generation. **GitHub remote NOT created** — operator action carried to Session 3.5 (deployment mechanism for E2E).

### Step 2 — 5 shape compose modules + tests
Under `tools/customisation_audit/`:
- `_v14_compose_custom_field.py` — fields[X] in-core edits → Custom Field with `(dt, fieldname)` guard
- `_v14_compose_custom_docperm.py` — opaque-hash perms → `(parent, role, permlevel)` guard
- `_v14_compose_translation.py` — DB-resident Translations → `(language, source_text)` guard
- `_v14_compose_print_format.py` — DB-resident Print Formats → `name` guard (matches on `class == "print_format"`, not doctype, since discover_print_format puts the parent doctype in the `doctype` field)
- `_v14_compose_property_setter.py` — generic fallback
- 5 colocated tests (`test__v14_compose_*.py`)

### Step 3 — Shape dispatcher in `promote_v14_patch_script`
`compose()` becomes a registry-based dispatcher. `target()` adds `in_core` / empty owner → `legacy_error_fixes` redirect via new `resolve_v14_patch_app()`. `patch_module_name()` disambiguates with the suffix-after-`#` (multiple drifts per JSON file no longer collapse — five sales_invoice fields[X] edits formerly produced one filename).

### Step 4 — Q5 deferral lifted
`promotion_dispatch.is_promotable()` accepts `v14_patch_script` with in_core/empty owners (route to legacy_error_fixes); skips synthetic doctypes like `(translation_csv)` explicitly.

### Step 5 — Real-data verify
`./tools/identify_bad_customisations.py --substrate dev01 -o /tmp/delta-pre-v14.json` → 374 total drifts, 22 v14_patch_script. After `is_promotable` filter (skip 1 `(translation_csv)`), 21 v14_patch_script promotions land. **18 patches in `legacy_error_fixes`** (12 Custom Field + 3 Custom DocPerm + 3 Translation no-ops) **+ 3 in `ce_sri`** (Print Formats). Matches Phase 5 plan §3 expected counts (15 substantive + noise). All patches AST-valid.

Three issues uncovered + fixed during this step:
- JSON serializes `drift_class` as `class` (`delta_report.py:18`) → matchers now check both via new `promote_common.drift_class()` helper.
- Print Format drifts have `doctype` set to the *parent* DocType (Sales Order, Quotation, …), not "Print Format" → matcher keys on `drift_class == "print_format"`.
- Filename collisions when multiple drifts target one JSON file → `patch_module_name` now appends suffix-after-`#`.

### Step 6 — Upgrade orchestrator + 10 stages + tests
- `tools/upgrade_to_v14.py` (53 lines) — argparse + hosts_map.yml lookup + `build_config(use_wg=True)` + `run_upgrade_v14`.
- `tools/pipeline/upgrade_v14/` — 10 stage units (each ≤47 lines), `verify.py`, `_test_helpers.py`, 6 colocated tests (each ≤47 lines per the `tools/pipeline/**/*.py` 80-line cap; first attempt as one 195-line file was caught by `pre_commit_size_check.py` and split).
- One naming gotcha resolved: `from .switch_branches import switch_branches` shadowed the submodule attribute with the function; renamed function to `switch_to_v14`.

**Test totals at close:** 45/45 pass (39 customisation_audit + 6 upgrade_v14).

### Step 7 — E2E V14 upgrade run on dev01
**Deferred to Session 3.5** per Option 3 (operator-chosen mid-session). Code review can catch design bugs before the multi-hour V14 run; Session 3.5 becomes a focused E2E session.

### Step 8 — PR #340
Opened: https://github.com/martinhbramwell/ESACP/pull/340 — `feat(v14-prep): Phase 5 P1 — patch generator + upgrade orchestrator`.
- `fixes #332` (debug residue, V14 `git checkout -f` wipes harmlessly per plan §2).
- **`fixes #331` deliberately omitted** — Stage 4 codifies the workaround but close defers to the Session 3.5 PR after E2E proves it.
- mergedAt: null at session close.

## Side-effect cleanup (audit-driven)

Re-running `correct_bad_customisations.py` produced dirty leftovers in 2 bespoke-app worktrees:
- `ce_sri`: 3 Print Format patches (kept; committed `fb5a460` + pushed) + 1 `es-EC.csv` translation (#339 bug; reverted)
- `route_planner`: 1 `es-EC.csv` translation (#339 bug; reverted)
- `ce_sri` pre-existing dirt (`BKP/BACKUP.txt`, `LogichemLogo.png`) — operator-side, untouched

## Issues touched

| Issue | Action | Resolution |
|---|---|---|
| #332 | Comment posted (`issuecomment-4366061337`) | `fixes` reference in PR #340; closes on merge |
| #331 | Comment posted (`issuecomment-4366061396`) | Workaround codified in Stage 4; **close deferred to Session 3.5 PR** after E2E |
| #339 | Comment posted (`issuecomment-4366061471`) | Recurrence confirmed: 1 dirty leftover per audit run; bug-fix priority unchanged |
| #340 | Opened | mergedAt null; carries `fixes #332` only |

## Operator-correction internalised

Mid-session, asked operator to choose between Option 1 (push through 6→7→8), Option 2 (split Steps 1-5 into Session 3 PR; defer 6-7), Option 3 (build 6, defer 7). Operator chose Option 3. The choice was a real boundary-crossing — multi-hour V14 upgrade with non-trivial gotcha risk on dev01 — so this was a legitimate operator decision per `feedback_enumerate_mechanisms_before_committing.md`, not the over-asking pattern flagged in Session 2.6.

## Carried into Session 3.5

1. **PR #340 review + merge** (sync_check at next session start should report mergedAt non-null before any "Session 3 done" claim).
2. **`legacy_error_fixes` GitHub remote** — operator creates `martinhbramwell/legacy_error_fixes`; controller adds remote + pushes `main`. Stage 5 `bench get-app` will then resolve via `LEGACY_APP_REPO` env or default URL.
3. **End-to-end V14 upgrade run on dev01** — `./tools/upgrade_to_v14.py --substrate dev01`. Acceptance per Phase 5 plan §5: HTTPS 200, `bench version` reports v14, sample Salary Slip with es-translated labels, round-trip identify yields 0 promotable + 0 in_place_core_edit drifts.
4. **#331 close** in the Session 3.5 PR (post-E2E proof).
5. **#339** still deferred unless audit re-run becomes routine.

## Memory updates queued

None pending — feedback files referenced (no new feedback patterns surfaced).
