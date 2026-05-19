# 2026-04-29 1315 — Session minutes

## Objective (set at session start, accepted by operator)

Walk through the 231 unmapped customisations from Phase 1's delta report, identify automation patterns vs operator-required mappings, file the resulting issue stack, and resolve the cross-app edge cases (category 3) on a 1:1:1 branch.

## What happened

### Pre-flight

- Loaded MEMORY.md + 0735 next-agenda.
- `bash platforms/kvm/sync_check.sh` → 46 ✅ / 8 ⚠️ / 2 ❌. Both ❌ are dev02 (`shut off` + WG ping unreachable). Expected per `feedback_one_vm_at_a_time.md` carve-out — dev01 is the live substrate. #278 still open (sync_check carve-out for live dev VM remains undocumented; out of scope today).
- 25 open issues at session start.
- Branch state clean on `main` @ `f2b2d9f`.

### Attribution walkthrough — analysis phase

Examined `/tmp/delta_report_dev01.json` (Phase 1 acceptance run) directly rather than re-running. Decomposed 231 unmapped rows into a **trichotomy**:

| Category | Rows | Class breakdown | Operator action |
|---|---:|---|---|
| **No consequences** | 9 | server_script (5) + custom_doctype (4) | Audit D-3 / D-5 enumerate_only — no promotion path by design. Phase 1 mis-categorization (emit `manual` instead of `none`) — fix filed as #318. |
| **Automatable by single rule** | ~218 | custom_docperm (203) + most of custom_field/client_script/print_format (~15) | Pattern-uniform per class. `auto_rules:` infrastructure feature filed as #319. custom_docperm bulk attribution still pending Phase 2 schema redesign (per plan §7 Phase 2 design Q3). |
| **Operator must map** | 3 | Customer-compras + Bought Returnable / Delivery Trip-Form / IRS 1099 Form | Cross-app domain calls. This session's branch (#320). |

Operator pushback **corrected** my initial framing that "resolving all three categories solidifies 0-fault V14". None of the 231 rows blocks V14 — all live in DB tables that survive `bench switch-to-branch` + `bench migrate` (verified empirically on dev02 V13→V14 run 2026-04-27). The actual 0-fault-V14 critical path is **Phase 4** (in-place core-tree edits classifier) — filed as #317 with the production `user.json` HR Manager block as worked example.

### Issues filed (5)

- **#317** — `feat(audit): Phase 4 — in-place core-tree edits classifier (V14 safety)`. Concretises Phase 4 placeholder from `~/.claude/plans/customisation-discovery-promotion.md` §7. Worked example: production user.json HR Manager permission-tree augmentation (audit §5.9 — class 5.11, gets wiped by `git checkout version-14`).
- **#318** — `fix(audit): enumerate_only classes should emit promotion_strategy=none, not manual`. ~5 LoC fix; drops unmapped count 231 → 222 (or 228 → 219 if landed after #320). Comment posted noting `discover_custom_doctype.py` + `discover_server_script.py` currently don't call `attribution.lookup()` at all — minimal vs wider scope option.
- **#319** — `feat(audit): auto_rules pattern matching in customisation_attribution.yml`. Schema sketch + acceptance criteria. Drops unmapped to ~3 + custom_docperm 203. Comment posted cross-linking #322 — auto_rules and #322 must share write mechanism.
- **#320** — `feat(audit): operator-resolved attribution for cross-app edge cases (category 3)`. This session's branch issue. **CLOSED** via PR #321 merge.
- **#322** — `bug(audit): --write-stubs strips comments from customisation_attribution.yml`. Latent bug in `yaml.safe_dump()` rewrite path. Filed at operator instruction after PR body flagged it.

### Operator decisions on category 3

| Edge case | Decision | Encoded in YAML as |
|---|---|---|
| Customer-compras + Bought Returnable | `returnable` app | `custom_field.Customer-compras: {owning_app: returnable, promotion_strategy: fixture_json}` (Bought Returnable itself is enumerate_only D-3, no YAML entry; conceptual owner recorded in PR body + commit message) |
| Delivery Trip-Form | `route_planner` app | `client_script.Delivery Trip-Form: {owning_app: route_planner, promotion_strategy: fixtures_custom_scripts}` |
| IRS 1099 Form | not ours, no action | `print_format.IRS 1099 Form: {owning_app: not_ours, promotion_strategy: none}` (introduced new sentinel `not_ours` + documented `none` in YAML comment block) |

### Acceptance test (#320)

- YAML loads cleanly via `yaml.safe_load()`.
- `./tools/identify_bad_customisations.py --substrate dev01` re-ran without error.
- Unmapped count: 231 → 228 (drop of 3 ✓).
- All three attributions propagated to `delta_report.drifts[*].owning_app_proposed + promotion_strategy`.
- Strategy distribution gained `fixture_json` (1) + `fixtures_custom_scripts` (1); one row moved `manual` → `none`.

### Branch + PR

- Branch: `feat/category-3-edge-case-attribution-320` cut off main @ `f2b2d9f`.
- Commit: `b853622` (GPG-signed, pinentry passphrase entered by operator after the known `feedback_gpg_agent_cache_ttl.md` hang).
- PR: #321 (https://github.com/martinhbramwell/ESACP/pull/321).
- Merge: `18fd6b85` at 2026-04-29T13:15:10Z. `mergedAt` non-null ✓.
- #320 auto-closed at 13:15:12Z via `fixes #320`.
- Local main fast-forwarded; merged branch retained per `feedback_keep_merged_branches.md`.

### Schema extension (lasting effect)

`config/customisation_attribution.yml` comment block now documents:
- `owning_app: ce_sri | returnable | route_planner | not_ours` (added `not_ours`)
- `promotion_strategy: fixture_json | fixtures_custom_scripts | v14_patch_script | manual | none` (added `none` — was canonical per plan §6 but undocumented in-file)

Survives in repo until #322's fix lands or someone runs `--write-stubs`, whichever comes first.

## Memory rules invoked

- `feedback_pr_merge_before_session_close.md` — verified `mergedAt` non-null before declaring DONE.
- `feedback_keep_merged_branches.md` — branch retained.
- `feedback_no_real_client_names.md` — bespoke app names (ce_sri, returnable, route_planner) are app names not client names; `not_ours` sentinel for the IRS form preserves anonymity.
- `feedback_gpg_agent_cache_ttl.md` — pinentry hang on commit, operator-side concern, did not derail.
- `feedback_plan_before_code.md` — #319's schema sketch labeled as starting point.
- `feedback_tactical_vs_consultant_mode.md` — production user.json claim flagged in #317 as audit-cited, not independently verified.

## Open at session close

- 24 open issues, including the 4 new feat/fix/bug filed this session and #317 (V14-safety critical path).
- dev01 still up as live substrate (V13 + Pseudo-Co + four-field canary intact, HTTPS 200).
- dev02 V14-baseline still parked + bench-clean.

## Unverified claim (flag for Phase 4)

The production user.json HR Manager 31-line block (audit §5.9) is **audit-narrative**, not verified by direct file read this session. Phase 4 (#317) verifies at runtime. Operator may want to spot-check by reading `$BESPOKE_ROOT/PRODUCTION_20260404/apps/frappe/frappe/core/doctype/user/user.json` against upstream v13 at any point before Phase 4 starts.
