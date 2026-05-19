# 2026-05-18 1830 — Session 55 minutes

## Objective

**ESACP#398 Path A** (Candidate A from S55 agenda) — ansible/packer disable of MariaDB `performance_schema` on bench-substrate VMs to unblock the failing v12_0 `delete_duplicate_indexes  # 2022-12-15` re-run-trigger patch, then retry `bench migrate` on dev02 to resume LSKB#15.

## Outcome — ESACP#398 closed via Path X (not Path A); new blocker ce_sri#10 filed

Path A failed empirically post-apply: `performance_schema = OFF` does not remove three MariaDB-10.6-internal compatibility tables (`global_status`, `session_account_connect_attrs`, `session_status`) from `information_schema.tables`. `frappe.db.get_tables()` (`database.py:974-987`) does not filter by `table_schema`, so those rows return alongside site-DB tables, and `SHOW INDEX FROM <pst>` against the site DB fails with 1146 regardless of substrate config. Operator-chosen Path X (pre-seed `tabPatch Log` with the suffixed re-run-trigger patch name) executed cleanly; #398 closed via PR#399 merge `fixes`-keyword auto-close.

### Steps executed

| # | Step | Outcome |
|---|---|---|
| 1 | Pre-flight checklist (sync_check 45/10/2 dev01-only failures, gh counts 42/8/5/2, dev02 substrate retained at v13.58.22 / v13.55.2, SPC code at `5567c47`, S54 evidence `/tmp/lskb15-S54-*` files intact) | ✓ ; one false-alarm (`TRIVIAL_FIXES.md` symlinked from LogiSoluMemory; default `find` doesn't traverse — file intact at 2 monitor-only entries) |
| 2 | Path A edit: `+performance_schema = OFF` in `01_os_prep.sh`'s `99-erpnext.cnf` heredoc (+7 lines); T1 verdict approve-with-conditions, audit-trail enumeration of rejected paths (ansible-post-deploy / third-party-patch) discharged in session response | commit `5946e2d` |
| 3 | Apply equivalent state on dev02 + restart mariadb + verify `[["performance_schema", "OFF"]]` via `bench execute` | ✓ |
| 4 | Retry `bench migrate` on dev02 — **failed on same patch**, different table (`session_account_connect_attrs`); exit code 1; log `/tmp/lskb15-S55-migrate.log` | ⚠ |
| 5 | Root-cause investigation (queries from site user perspective): `SHOW DATABASES` excludes PS ✓ but `information_schema.tables` shows 3 PS tables; site user has only `USAGE *.*` + `ALL on <site_db>.*`, no PS grants. Conclusion: substrate-config cannot solve #398 | ✓ |
| 6 | Revert `5946e2d` (T1 approve) with QA-approved root-cause-explanation message; restore dev02 CNF to pre-#398 state + restart mariadb (confirmed MariaDB-10.6 ships with PS=OFF default already, so the original Packer change was effectively no-op) | commit `fbc1299` |
| 7 | Path X read+plan: tabPatch Log row shape from production's un-suffixed `PATCHLOG00105`; frappe-native helper `frappe.modules.patch_handler.update_patch_log` identified at `patch_handler.py:124-126`; `executed()` does exact-string match `patch_handler.py:129-137` | ✓ |
| 8 | Path X execution: `bench execute update_patch_log --args '["frappe.patches.v12_0.delete_duplicate_indexes  # 2022-12-15"]'` → `PATCHLOG00570` inserted | ✓ |
| 9 | Retry `bench migrate` — **patches phase clear**: `delete_duplicate_indexes  # 2022-12-15` skipped; 7 remaining will-run patches from S54 Path β survey all ran (`remove_share_for_std_users`, `clear_large_email_queues`, `update_schedule_type_in_loans`, `update_asset_value_for_manual_depr_entries`, `update_docs_link`, `correct_asset_value_if_je_with_workflow`, `frankfurter.app` set_value); failed downstream in fixtures-import phase | ✓ for #398 |
| 10 | Document Path X as generic substrate-apply technique: `docs/FrappePatchLogPreseeding.md` (70 lines); T1 approve | commit `0797d47` |
| 11 | PR#399 opened + T2 verdict approve (recommended merge-commit over squash to preserve `fbc1299` root-cause forensics in `git log`) + merge | merge `153b346`; #398 auto-closed `2026-05-19T01:43:10Z` |
| 12 | ce_sri#10 filed for fixtures-import collision (`forma_de_pago_preferida` on Customer; `apps/ce_sri/ce_sri/fixtures/custom_field.json`); LSKB#15 pause-comment posted with updated block chain `ce_sri#10 → LSKB#15 → LSKB#16` | ✓ |

### Path X execution evidence

`PATCHLOG00570` (`creation: 2026-05-18 20:18:39.836588`, `owner: Administrator`, `patch: frappe.patches.v12_0.delete_duplicate_indexes  # 2022-12-15`). Build evidence retained: `dev02:/tmp/lskb15-S55-migrate-pathx.log` (post-Path-X migrate, exit 1 at fixtures-import). Patches-phase clean.

### New blocker — fixtures-import phase

```
frappe/custom/doctype/custom_field/custom_field.py:44, in before_insert
    frappe.throw(...)
frappe.exceptions.ValidationError:
    A field with the name 'forma_de_pago_preferida' already exists in doctype Customer.
```

Class: bespoke-app fixture-vs-production-data collision; not a substrate-config class. Owning app: ce_sri (`apps/ce_sri/ce_sri/fixtures/custom_field.json`). Bucket-3.

## GitHub issue activity

| Issue | Action | Mechanism |
|---|---|---|
| [ESACP#398](https://github.com/martinhbramwell/ESACP/issues/398) | **closed** (`closedAt 2026-05-19T01:43:10Z`) | `fixes #398` in `0797d47` body via PR#399 merge `153b346` |
| [ce_sri#10](https://github.com/martinhbramwell/ce_sri/issues/10) | filed (open) | New fixtures-import collision; full root-cause body + 3 likely-fix-paths |
| LSKB#15 | pause-comment posted; stays open | Updated state retention + retry path; block chain now `ce_sri#10 → LSKB#15 → LSKB#16` |

## Pointer-comments posted

- LSKB#15 — [Path X discharged #398; new pause at fixtures-import → ce_sri#10](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/15#issuecomment-4483718382)

## PR opened + merged

- **[PR#399](https://github.com/martinhbramwell/ESACP/pull/399)** — `fix(#398): document tabPatch Log pre-seeding (revert misdirected packer change + add procedure doc)`; merge-commit mode (per T2 recommendation, preserves `fbc1299` root-cause body in git history); `mergedAt: 2026-05-19T01:43:09Z`; branch retained per `feedback_keep_merged_branches.md`.

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T1 | `a04177d3c16e010f5` — pre-commit `5946e2d` | approve-with-conditions | Single condition: audit-trail enumeration of rejected paths (ansible-post-deploy, third-party-frappe-patch) in session response. Discharged. |
| T1 | `a5cc66cffcb122748` — pre-commit revert `fbc1299` | approve | Clean revert with QA-approved root-cause body; `refs #398` (not `fixes`) — revert alone does not close. |
| T1 | `aac954dfbf5ce877d` — pre-commit `0797d47` (docs/FrappePatchLogPreseeding.md) | approve | One observation noted (line count metadata mismatch: parent said 63, actual 70 — no rule violation in docs/). |
| T2 | `a8104992a9cae53ba` — pre-merge PR#399 | approve | Recommended merge-commit over squash to preserve `fbc1299` root-cause forensics in `git log`. Operator accepted. |
| T1+T3 (combined, this ESACP session-close commit) | _pending — populated after verdict_ | _pending_ | ESACP doc-only direct-to-main per `docs/qa-contract.md` v2.1 §2.1 clause 3 |

## Counts at session end

- ESACP open: **41** (was 42; −#398, no net new on ESACP).
- LSKB open: **8** (unchanged).
- ce_sri open: **6** (was 5; +#10).
- LogiSoluValidations open: 2 (unchanged).
- `sales_partner_commissions/main`: `5567c47` (unchanged through S47–S55; not yet site-installed on dev02).
- Cross-repo `fixes` tally: 18 (unchanged — #398 closed via in-repo `fixes`, not cross-repo).

## TRIVIAL_FIXES.md status

Unchanged. 2 monitor-only entries (LogiSoluMemory Trigger-3 skip pattern S33; `tools/secrets.py` +x bit S47). Pre-flight false-alarm (apparent absence) traced to `find` default not traversing the `memory/` → `LogiSoluMemory/` symlink; file intact.

## Carry-forward operator-reminders (delta)

- **ce_sri#10 (NEW S55)** — fixture-import collision (`forma_de_pago_preferida` on Customer); bucket-3, blocks LSKB#15. Three likely fix paths enumerated in issue body.
- **LSKB#15** — substrate-apply paused at fixtures-import (not patches anymore). Steps 1–9 state retained on dev02; retry path documented in S55 pause-comment.
- **Path-X pattern documented in `docs/FrappePatchLogPreseeding.md`** — generic substrate-apply technique for date-suffixed re-run-trigger patches whose un-suffixed equivalent already ran on source data. "When NOT to use" section spells out the masking-risk cases.
- **MariaDB-10.6 default `performance_schema = OFF`** — discovery during S55: the Packer-baked substrate ships with PS off already, so substrate-config approaches at the PS layer are no-ops. Documented in `fbc1299` revert body.
- **dev02 substrate state** — v13.58.22 / v13.55.2; production data restored; encryption_key aligned; SPC code at `5567c47`; `PATCHLOG00570` row in tabPatch Log; awaiting ce_sri#10 fix to retry migrate from fixtures-import phase.
- **Plan-C meta-pattern (second-instance status)** — S54 first-instance + S55 reinforces with second-class-of-blocker (fixture-import vs substrate-config); both flavors are post-restore-pre-migrate runbook gates, both have low single-digit residual case counts. Confidence in Plan-C as cross-major recovery pattern increases.
- **Build-evidence retained** — `dev02:/tmp/lskb15-S55-migrate.log` (Path-A retry failure), `/tmp/lskb15-S55-migrate-pathx.log` (Path-X retry, fixtures-import failure), `/tmp/lskb15-S55-migrate-pathx-controller-tee.log`. S54 evidence files also retained.
- **LogiSoluMemory Trigger-3 skip pattern** — unchanged (monitor-only).
- **ce_sri local clone in-progress state** — unchanged.
- **Tablet WG sidebar (#383)** — still ripe.

## Trimmed minutes baseline check

This session: ~110 lines as committed. Above S54's ~95-line baseline. Compression-resistance came from: 12-step ladder (Path A attempted + reverted + Path X attempted + succeeded + docs + PR + merge + filing + comment), three commits + merge commit narrative, four QA verdicts table, downstream-blocker filing, three-bucket routing decision. Substantive-class session — not a pure paused-substrate. Trim baseline holds within ~15% for "two-fix-paths-in-one-session-with-PR-merge" class.

## Post-close audit-fix

SESSION END audit (UserPromptSubmit hook re-run pattern per S45–S54) ran all four steps clean. Pure clerical finalization (verdict-cell fill-in for close-batch row of this session-close commit + commit-hash insert + audit-fix qa-log row below); zero substantive discharge required because all session-time pointer-comments + finding-bodies + PR-merge + fixes-keyword-close were already executed within-session.

1. **Forward-tense audit** — minutes/agenda categories of hits all benign: S56 agenda candidates A/B/C/D/E (forward-looking by definition); parked backlog items; carry-forward operator-reminders; self-referential `_pending_` cells in qa-log; "When NOT to use" advisory framing in `FrappePatchLogPreseeding.md`; general-principle reminders. All session-time "I'll X" / "Executing X now" / "Filing X" phrases executed within-session and the audit was performed pre-minutes-write.
2. **GH issue references** — ESACP#398 closed via `fixes #398` in `0797d47` body (mechanism: PR merge → server auto-close; verified `closedAt 2026-05-19T01:43:10Z` non-null). ce_sri#10 filed with full content in issue body (root cause + 3 fix paths + state retained + bucket reasoning). LSKB#15 ([issuecomment-4483718382](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/15#issuecomment-4483718382)) received within-session pause-comment (S50–S54 within-session-discharge discipline sustained for the sixth session running). LSKB#16 referenced in block chain only — no new findings about it.
3. **PRs opened** — PR#399 `mergedAt: 2026-05-19T01:43:09Z` verified pre-session-close; gate satisfied per `feedback_pr_merge_before_session_close.md`.
4. **Unresolved doubts** — three operator-clarification prompts (sub-path A1/A2/A3 enumeration on Path A → operator called decision-theatre, parent decided A2 self / Path X vs Path A pivot when first failure surfaced → operator chose Path X + revert / engineering-internal vs company-owner classification → operator confirmed) all resolved within-session by explicit operator response. Path A misdiagnosis explicitly framed and reverted within-session (no deferred sub-issue).

Self-referential row pattern in qa-log matches Sessions 28/29/35/36/37/38/40/43/44/45/46/47/48/49/50/51/52/53/54. Zero-substantive-gap shape sustained SIX sessions running (S50/S51/S52/S53/S54/S55) — pointer-comment-within-session discipline structurally embedded. First substantive ESACP issue close within-session for this six-session run (#398).
