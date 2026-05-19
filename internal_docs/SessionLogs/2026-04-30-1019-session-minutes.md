# 2026-04-30 1019 — Session minutes

## Objective

Two phases, operator-directed:

1. **First move (mandatory per 2026-04-29-1435 next-agenda)**: merge PR #323; confirm #318 auto-closes; sync main.
2. **Substantive work (operator pivoted from Option A to Option C)**: land #319 (`feat(audit): auto_rules pattern matching in customisation_attribution.yml`).

## State at session start

- main tip: `a0a9e5b` (1435-session docs commit on top of #321 merge)
- 24 open issues
- PR #323 OPEN, `mergedAt: null` — gating #318 closure
- dev01: real-prod-data substrate UP (HTTPS 200)
- dev02: V14-baseline shut off
- sync_check: 46 ✅ / 8 ⚠️ / 2 ❌ — both ❌ are dev02 dormant, expected per `feedback_one_vm_at_a_time.md`

## Part 1 — PR #323 merge (#318 close-out)

Merge executed via `gh pr merge 323 --merge`:

- Merge commit `03f8acb` on main
- PR #323 `mergedAt: 2026-04-29T14:46:48Z`
- #318 auto-closed at 14:46:49Z via `fixes #318` keyword
- main fast-forwarded `a0a9e5b → 03f8acb`

## Part 2 — #319 design + implementation

### Design phase

Operator chose Path A (Phase 2 directly) initially, then redirected to #319 for richer Phase-2 substrate. Five design questions presented, all five confirmed:

1. **Integration shape**: new `resolve()` wrapper in `attribution.py` (not modifying `lookup()`). Preserves "operator-resolved by name" contract; one-line change per discover module.
2. **Multiple patterns per class**: separate rules instead of list-valued matchers (only 2 print_format prefixes — verbose-but-readable wins).
3. **TODO precedence**: TODO entries do NOT block auto-rule (current `lookup()` returns None for TODO; `resolve()` falls through to auto_rules naturally).
4. **Acceptance gate**: 0 non-`custom_docperm` manual rows post-merge (stricter than the issue body's "~3" — that was pre-#320).
5. **#322 coordination**: #319 is read-only for the YAML; proceeding independently. Cross-link comment posted on #322 (issue-comment-4353237041).

### Branch + commits

- Branch `feat/auto-rules-attribution-319` cut from main (`03f8acb`)
- Commit `f706fcd`, GPG-signed, conventional, `fixes #319`, Co-Authored-By trailer
- Pushed; PR opened: **https://github.com/martinhbramwell/ESACP/pull/324**

### Edits

| File | Change |
|---|---|
| `tools/customisation_audit/auto_rules.py` | NEW — 57 lines. Matchers (`dt_in`, `name_pattern`, `view`, `standard`), AND semantics, malformed-skip |
| `tools/customisation_audit/test_auto_rules.py` | NEW — 89 lines. 9 tests covering matcher dispatch, AND, malformed, precedence, empty-section |
| `tools/customisation_audit/attribution.py` | +10 lines: `resolve()` composer (per-name → auto_rule fallback) + import |
| `tools/customisation_audit/test_attribution.py` | +24 lines: 4 tests for `resolve()` |
| `tools/customisation_audit/discover_*.py` × 7 | one-line each: `attribution.lookup(...)` → `attribution.resolve(..., row)` |
| `config/customisation_attribution.yml` | +40 lines: `auto_rules:` section (4 rules) + header documentation |

Total: 12 files, 231 insertions / 11 deletions.

### Verification — dev01 substrate

Pre-#319 reference: `/tmp/delta_report_318_post.json` (post-#318 baseline).
Post-#319 acceptance: `/tmp/delta_report_319_post.json` (and `_b.json` round-trip check).

| Metric | Pre-#319 | Post-#319 | Δ |
|---|---|---|---|
| total drifts | 360 | 360 | 0 |
| by_class | (8 classes) | (8 classes, identical) | 0 |
| by_strategy.manual | 219 | **203** | **−16** |
| by_strategy.fixture_json | 1 | **8** | **+7** |
| by_strategy.fixtures_custom_scripts | 1 | **7** | **+6** |
| by_strategy.v14_patch_script | 0 | **3** | **+3** |
| by_strategy.app_translations_csv | 10 | 10 | 0 |
| by_strategy.none | 129 | 129 | 0 |

Remaining 203 manual rows are all `custom_docperm` (out of scope per plan §7 Phase 2 design Q3 — depends on Phase 2 schema redesign for richer parent+role+permlevel attribution).

Round-trip stable: re-run produced byte-identical JSON modulo `generated_at`. All 19 colocated audit tests green. Pre-commit size check exit 0.

## State at session close

- main tip: `03f8acb` (PR #323 merge), unchanged by part-2 work
- Branch `feat/auto-rules-attribution-319` @ `f706fcd`, pushed to origin
- **PR #324 OPEN, `mergedAt: null`** — fix complete on branch; #319 NOT marked DONE per `feedback_pr_merge_before_session_close.md`
- 24 open issues (no net change: #318 closed via PR #323; nothing yet closed for #319)
- dev01: substrate UP (HTTPS 200), `ERPNext v13 Restored Baseline` snapshot retained — usable next session without re-provisioning
- dev02: still shut off

## Issue ledger delta

| Issue | Status change |
|---|---|
| #318 | OPEN → **CLOSED** at 2026-04-29T14:46:49Z via PR #323 merge |
| #319 | OPEN → fix-implemented, PR #324 awaiting merge. **NOT yet closed.** Closes on merge of PR #324. |
| #322 | unchanged — cross-link comment added documenting #319's read-only-YAML stance (issue-comment-4353237041) |
| All others | unchanged |

## Status surface — V13→V14 migration ladder (operator-requested mid-session refresh)

The four-script chain status, restated for the record:

| # | Script | Status |
|---|---|---|
| 1 | `./tools/identify_bad_customisations.py` (find flaws) | ✅ exists; #319 enhances attribution coverage 12 → 28 rows automatable |
| 2 | `./tools/correct_bad_customisations.py` (correct flaws) | ❌ NOT YET — Phase 2 |
| 3 | `./tools/upgrade_to_v14.py` | ❌ NOT YET — Phase 5 |
| 4 | `./tools/migrate_production_to_v14.py` | ❌ NOT YET — Phase 6 |

dev02 V13→V14 manual proof of concept stands (2026-04-27, bench-clean substrate). Real-prod-data dry-run not yet attempted; awaits scripts 2 + 3 + 4.

## Forward-tense audit (run before writing these minutes)

| Phrase | Resolution |
|---|---|
| "Merging PR #323 now" | Executed: merge `03f8acb`, #318 closed |
| "Cutting branch and implementing" | Executed: `feat/auto-rules-attribution-319` |
| "Implementing now" | Executed: `auto_rules.py` + tests + 7 discover updates + YAML |
| "Committing, pushing, opening PR" | Executed: commit `f706fcd`, PR #324 |
| "first move next session is verify-and-close PR #324" | Captured in next-agenda (durable home) |
| "Next natural session: Phase 2 (`correct_bad_customisations.py`)" | Captured in next-agenda |
| "#319 is read-only for the YAML; #322 independent" | Posted as comment on #322 (issue-comment-4353237041) — durable home |
| "holding 'done' for #319 until mergedAt is non-null" | Honoured — these minutes do NOT mark #319 DONE |

No unresolved forward-tense promises.

## Memory updates

None this session. The Path-A-vs-Path-B sequencing tradeoff (#319-first-vs-Phase-2-first) is captured on the issue ledger and the operator chose by inspection; no abstraction worth a memory file.
