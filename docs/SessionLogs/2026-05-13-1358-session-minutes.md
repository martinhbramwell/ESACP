# 2026-05-13 1358 — Session 46 minutes

## Objective

**LSKB#14 — `sales_partner_commissions` Server Script rewrite (Candidate A).** Phase 4 ladder next code-class artefact, authoring the Before-Save + After-Submit replacements against the post-LSKB#13 master/detail shape. Substantive-code-class session (bucket-2 / LSKB tracker).

## Outcome — LSKB#14 scripts authored, PR merged, issue closed

- **Branch**: `feat/lskb-14-server-script-rewrite` off `main` on `martinhbramwell/sales_partner_commissions`.
- **Module decomposed into 7 focused files** under `sales_partner_commissions/server_scripts/`:
  - `_calc.py` (53 lines) — Frappe-free pure helpers: `build_item_rate_map`, `compute_breakdown`.
  - `_upsert.py` (40 lines) — Frappe-aware Server Script upsert (idempotent diff-check).
  - `register.py` (51 lines) — orchestrator, loaded by `after_install` + `after_migrate` hooks.
  - `before_save_body.py` (58 lines) — script body text for "Sales Partner Commission - Before Save" (Sales Invoice / Before Save).
  - `before_submit_helpers_body.py` (57 lines) + `before_submit_main_body.py` (67 lines) — fragments concatenated by `register.py` into the body for "Sales Partner Commission - After Submit" (Sales Invoice / Before Submit; name misalignment preserved per agenda Candidate A constraint + LSKB#1 doc-bug tracker).
  - `__init__.py` (empty).
- **Colocated unit tests** — `test_build_item_rate_map.py` (55 lines) + `test_compute_breakdown.py` (61 lines), 11 tests, all passing alongside the 8 from LSKB#13 patch dir (19/19 total). Test split mirrors LSKB#13 4-module pattern.
- **`hooks.py`** wires `after_install` + `after_migrate` to `sales_partner_commissions.server_scripts.register.run`; upsert no-ops when stored `Server Script.script` matches assembled text.
- **Pre-author verification**: extracted the two existing Server Script row texts from `PRODUCTION_20260404` SQL dump (2637 + 5626 chars) to anchor the rewrite. Verified Print Format insert has zero references to `break_down`, `total_commission`, `Sales Partner Customer Item Commissions`, or `sales_partner_supplier` — D4 print-format-regen N/A.
- **Commit `fd8353f`** → squash-merged as commit [`5567c47`](https://github.com/martinhbramwell/sales_partner_commissions/commit/5567c474555a16fb9ba2d84e6cf5160ef5f8052f) via [PR #2](https://github.com/martinhbramwell/sales_partner_commissions/pull/2). Feature branch preserved per `feedback_keep_merged_branches.md`.
- **LSKB#14 auto-closed at `2026-05-13T17:57:56Z`** (2 seconds after merge at `2026-05-13T17:57:54Z`) via cross-repo `fixes martinhbramwell/LogiSoluKnowBase#14` in commit body.
- **Operator decisions (from approved plan)**: D1 drop dead `if 1 == 0` debug block per `feedback_debug_toggles.md`; D2 hook-based carrier (vs fixtures-JSON); D3 inline calc in bodies (Frappe `safe_exec` prohibits app-module imports; `_calc.py` is the unit-tested reference); D4 print-format-regen verified N/A; script-name preservation (LSKB#1 handles doc-bug).

## GitHub issue activity

| Issue | Action | Why |
|---|---|---|
| LSKB#14 | auto-closed via `fixes` at PR merge | Phase 4 ladder Server Script rewrite complete |

## Pointer-comments posted

- ESACP [#353](https://github.com/martinhbramwell/ESACP/issues/353#issuecomment-4443880051) — Plan-B parent epic; Session-46 ledger entry + cross-repo `fixes` tally update (15th).
- LSKB [#6](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/6#issuecomment-4443881058) — Phase 4 epic; ladder progression table.

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T1+T3 (combined, `feat/lskb-14-server-script-rewrite` commit `fd8353f`) | `ad5732d199d19c54f` | approve | Clean approve, no conditions |
| T2 (PR#2 squash-merge to `sales_partner_commissions/main`) | `a0b01573483324c7f` | approve | §2.2 carve-out conditions all hold (same-commit prior T1+T3 approve, no rebase, squash) |
| T1+T3 (this session-close commit) | _pending — populated after verdict_ | _pending_ | ESACP doc-only direct-to-main per v2.1 §2.1 clause 3 |

## Cross-repo `fixes` tally

**15th** cross-repo `fixes`-keyword auto-close in the running tally: #358, #377, #378, ce_sri#6, LSKB#3, LSKB#8, #380, #373, #385, #386, LSKB#12, LSKB#17, LSKB#19, LSKB#13, **LSKB#14**. Direction: `sales_partner_commissions` → LSKB (third such; first two were S43 LSKB#17 and S45 LSKB#13). Mechanism unaffected by originating repo.

## Counts at session end

- ESACP open: **36** (unchanged).
- LSKB open: **8** (LSKB#14 closed; was 9).
- ce_sri open: 5 (unchanged).
- LogiSoluValidations open: 2 (unchanged).
- `sales_partner_commissions`: 1 commit added to main (`5567c47`); 1 PR opened + merged (#2).

## TRIVIAL_FIXES.md status

Unchanged. 1 monitor-only item (LogiSoluMemory Trigger 3 skip pattern, S33).

## Carry-forward operator-reminders (delta)

- **LSKB#14** — closed S46. **Drop from carry-forward.**
- **LSKB#15 (substrate apply)** — unchanged; substrate gate for both LSKB#13 (closed S45) and LSKB#14 (closed S46); v14-lifecycle observations from S45 already on the issue.
- **LSKB#16 (parity verification)** — unchanged; after LSKB#15.
- **LSKB#18 (`user_data_fields` cleanup)** — unchanged; chore-class micro-fix on the new repo.
- LogiSoluMemory Trigger 3 skip pattern — unchanged.
- ce_sri local clone in-progress state — unchanged.
- Tablet WG sidebar (#383) — still ripe.
- **QA file-size lesson (S46 application)** — S45's mid-session file-split lesson applied successfully from the outset: every new file came in under 80 lines without a QA-mandated decomposition. Test file naturally hit 103 lines pre-split → decomposed into 2 sibling test files (per S45 precedent) before staging.

## Trimmed minutes experiment

This session: ~80 lines as committed (substantive-code-class with full QA-iteration narrative: 2 substantive QA invocations + PR + merge + ladder-state pointer-comments). Sits right at the S40–S45 ~73–80 line baseline despite substantive-code-execution shape — compression came from tabular QA-verdict + counts rather than narrative expansion. Trim baseline holds.
