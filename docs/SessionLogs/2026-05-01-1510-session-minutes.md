# 2026-05-01 1510 — Session minutes

**Branch:** `feat/promotion-library-phase-2` (cut, merged via PR #334,
deleted from local; main now at `93d4018`).
**Objective:** Implement #327 Phase 2 — promotion library +
`correct_bad_customisations.py`. Locked design from 2026-04-30 1453
session (Q1–Q5).

## Pre-flight

- `bash platforms/kvm/sync_check.sh` → 46 ✅ / 8 ⚠️ / 2 ❌ (dev02 shut
  off, expected per `feedback_one_vm_at_a_time.md`).
- main at `e4eaa2d`. Working tree clean. dev01 reverted to
  `v13-plus-edits` snapshot at session start (per yesterday's unresolved
  question on dev01 fate).

## Mid-session scope discovery — attribution review tool

Locked design assumed `customisation_attribution.yml` had operator
answers for every Phase 4 in_place_core_edit drift. Empirical run
against dev01 (`/tmp/delta_phase2.json`) showed **28 unresolved
promotable drifts** with empty `owning_app_proposed`:
- 17 `in_place_core_edit` `fixture_json` (Phase 4)
- 1 `in_place_core_edit` `app_translations_csv` (es.csv core edit)
- 10 `translation` `app_translations_csv` (Phase 1)

Operator pushed back on a single-default attribution: "I cannot say yes
because I do not know what to look at or how to look at it." Then on
manual handling: "**NOTHING** done by hand!!!! This must all be
automated."

Built `tools/review_attribution.py` (97 → 109 lines) +
`tools/customisation_audit/review_display.py` (47 → 81 lines) — interactive
walkthrough of unresolved drifts with full diff/row context. Added
`k=in_core` marker mapping to `v14_patch_script` (Phase 5 generates
runtime patch — never manual).

Operator iterated three times:
1. Default options too narrow — added `k=in_core` for paired Python
   controller code in core.
2. Mismatched my framing of `in_core` as "manual cutover" — retracted;
   `in_core` writes `promotion_strategy: v14_patch_script` (automated).
3. Asked for module/doctype context — added JSON top-level metadata
   extraction to display.

Operator completed all 28 attributions. Distribution captured in
`config/customisation_attribution.yml`:
- 19 `in_core` (v14_patch_script)
- 4 `returnable` (translations)
- 3 `route_planner` (2 fixture_json + 1 translation)
- 2 `ce_sri` (translations)

Session reframe: `feedback_db_resident_customisations_acceptable.md` rule
applies broadly; 3 `human_review_core_edit` files (#332) reframed from
"operator decisions" to "Phase 5 automation requirement" via `gh issue
edit` — never by hand.

## What ran — Implementation (PR #334)

11 SUT modules + 9 colocated tests + dispatcher + interactive review
tool. Wiring into `discover_in_place_core_edits` via new
`in_place_attribution` module (kept the discover module under its
35-line baseline ratchet).

### Bug surfaced + fixed in same PR (#333)

`tools/customisation_audit/_remote_query.py` runs `mysql -B` (batch
mode) which escapes `\n \t \\ \0 \Z \r` inside cell data. The runner
split on real tabs but didn't un-escape — `tabClient Script.script`
payloads carried literal escape sequences, producing syntactically
broken `.js` fixture files. Caught during Phase 2 acceptance; root cause
fixed in same PR (per global rule). 11 unit tests for unescape coverage.

### Property Setter `name` shim

Phase 4 in_place_core_edit Property Setter drifts had no `name` in
row_data (Frappe auto-generates). promote_fixture_json now derives
`<doc_type>-<property>` (matches Frappe autoname). `discover_property_setter._index_fixtures`
made defensive against missing-name fixture rows.

### Acceptance

| Metric | Before | After | Δ |
|---|---:|---:|---|
| Total drifts | 391 | 371 | −20 |
| `is_promotable()` | 22 | 0 | ✓ |
| `custom_field` | 8 | 0 | promoted |
| `client_script` | 7 | 0 | promoted |
| `translation` | 10 | 3 | 7 promoted; 3 deferred (in_core) |

**22 DB-side promotable rows cleared.** Persisting in post-promote
delta (per locked design intent):
- 22 `v14_patch_script` (Q5 — fixture-only this phase, real-data Phase 5)
- 2 `in_place_core_edit` `fixture_json` (Phase 4 still detects
  source-tree diff for route_planner Address.barrio +
  Address.delivery_route — resolves at V14 cutover)

### PR / commit

- Commit `9dd7747`. PR `#334` opened with full body (acceptance,
  attribution distribution, deferred work).
- Merged 2026-05-01T19:09:13Z → main `93d4018`.
- `#327` auto-closed at 19:09:14Z. `#333` auto-closed at 19:09:15Z.

## Issues touched

| # | Action | State |
|---|---|---|
| #327 | Phase 2 implementation, closed by PR #334 | closed |
| #333 | New bug filed + fixed in same PR | closed |
| #332 | Reframed from "operator decisions" to "Phase 5 automation" | open (deferred) |
| #317 | (Phase 4 — closed yesterday); referenced for hand-off context | closed |

## State at session close

- **main**: `93d4018` (PR #334 merged).
- **dev01**: V13 + edits (per session-start revert from V14).
- **`config/customisation_attribution.yml`**: 28 new operator-curated
  entries, durable across re-runs of `identify_bad_customisations.py`.
- **Bespoke-app worktrees** (ce_sri, returnable, route_planner): 24
  Phase 2 promotion writes **staged but not committed** — operator
  commits each independently per Q4 design (refuse-if-dirty +
  stage+diff+exit; never auto-commit). This is intentional — not residue.
- **Working tree (ESACP)**: clean.

## Memory updates

None this session. The `in_core` semantics + Phase 5 patch generator
intent are captured durably in `customisation_attribution.yml` header
docs, `#332` body, and the PR body.

## Forward-tense audit (session-close)

Every "I'll X" / "we'll X" in this session resolved as either
(a) executed tool call, (b) durable home (issue, PR, commit, memory
file), or (c) flagged unresolved below. None deferred to "noted for
next session."

## Unresolved at close (operator hand)

1. **24 staged Phase 2 promotion writes** in 3 bespoke-app repos. Per
   Q4 design, operator commits each independently. Not residue —
   designed handoff.
2. **22 `v14_patch_script` drifts** persist in post-promote delta.
   Designed: Q5 deferred to Phase 5 (issue #332 + a sibling Phase 5
   ticket TBD). Phase 5 generates the actual runtime patches.
3. **2 `in_place_core_edit` `fixture_json`** drifts (route_planner
   Address.barrio + Address.delivery_route) re-emit on identify because
   Phase 4 reads source-tree diff. Resolves naturally at V14 cutover
   (`bench switch-to-branch version-14` does `git checkout -f` →
   in-place edits wiped → Phase 4 finds 0 diffs; fixtures sync via
   `bench migrate`).
