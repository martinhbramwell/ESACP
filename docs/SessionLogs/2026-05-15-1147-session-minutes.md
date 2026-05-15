# 2026-05-15 1147 — Session 54 minutes

## Objective

**LSKB#15 — substrate-apply on dev02 (Candidate A).** Phase 4 ladder — end-to-end substrate-honest verification of LSKB#13 migration patch + LSKB#14 Server Script upsert hook on the S53 Plan-C-rebuilt dev02 (frappe v13.58.22 / erpnext v13.55.2 pinned tags). Bucket-2 substantive (LSKB tracker). D1 manual ssh-config alias, D2 abort+file on non-v14_0 patch failure, D3/D4 standard.

## Outcome — paused at Step 6 (bench migrate); ESACP#397 + #398 filed; Plan-C viability confirmed via Path β survey

Substrate-apply reached `bench migrate` cleanly. The first patch in the chain failed (substrate-config class, not Phase-4 class). Per D2: abort+file. Path β survey then re-quantified the long-feared "intermediate patches conflate verdicts" concern from S47.

### Steps 1–5 (executed cleanly)

| # | Step | Outcome |
|---|---|---|
| 1 | Path-A unblock for ESACP#397 (controller-side keygen + GH register + distribute to dev02 + ssh-config alias) | ✓ smoke-test: `Hi martinhbramwell/sales_partner_commissions! …` |
| 2 | `bench get-app sales_partner_commissions` (SSH_ASKPASS+setsid preamble) | ✓ clone HEAD `5567c474555a16fb9ba2d84e6cf5160ef5f8052f`; `patches/v14_0/` + `server_scripts/` verified |
| 3 | scp 2.4 GB snapshot controller → dev02:/tmp/spc_restore-S54 + md5 verify | ✓ three md5 match |
| 4 | encryption_key alignment to production's `7tnS5lOT_E6nvhktc70L4mGv2WQ0ac1WP0ET1UuGNr0=` | ✓ |
| 5 | `bench restore` (12m43s wall, exit 0; one tolerated `ERROR 1227` on `CREATE VIEW CustomerInvoices` per S47 precedent) | ✓ |

### Step 6 failure — `frappe.patches.v12_0.delete_duplicate_indexes  # 2022-12-15`

```
pymysql.err.ProgrammingError: (1146, "Table '_e27ab2b905ef3a98.global_status' doesn't exist")
```

Root cause chain (5 links): v13.58.22 `patches.txt` carries the patch with date-suffix `# 2022-12-15` (re-run trigger); production tabPatch Log holds the un-suffixed version (ran cleanly at v13.41.3); patch uses `frappe.db.get_tables()` which (per `frappe/database/database.py:974-987`) doesn't filter by `table_schema = DATABASE()`; dev02 MariaDB exposes `performance_schema.global_status` to all users (PUBLIC default); `SHOW INDEX FROM global_status` against current DB → 1146. Filed as [ESACP#398](https://github.com/martinhbramwell/ESACP/issues/398) with Path A (ansible role to disable `performance_schema`).

### Mid-session finding — ESACP#397 (deploy-key VM-side-generation)

Step 1 pre-flight surfaced that `sales_partner_commissions`'s deploy key was originally generated in S42 on dev02 itself (not on controller, inverting the established pattern for `ce_sri` / `route_planner`). dev02 was destroyed in S50 + S53, taking the private key with it. Filed as [ESACP#397](https://github.com/martinhbramwell/ESACP/issues/397) (strict subset of [#375](https://github.com/martinhbramwell/ESACP/issues/375)). Path-A unblock executed: controller-side ED25519 keygen, deleted orphan GH deploy-key 151308091, registered new key (id 151587130), distributed to dev02.

### Path β survey — quantifying Plan-C residual risk

Operator-requested sanity check after Step 6 failure: how many other substrate-config classes lurk in the patch chain?

| Layer | Count |
|---|---|
| v13.58.22 frappe `patches.txt` entries | 193 |
| v13.55.2 erpnext `patches.txt` entries | 381 |
| **Total in chain** | **574** |
| Production tabPatch Log entries (already-applied at v13.41.3) | 567 |
| **Will-run delta** | **8** |

Of the 8: **1** uses cross-schema introspection (the failing `delete_duplicate_indexes`); **7** are standard frappe/erpnext data-mutation patches (UPDATE on Loan / Asset / Email Queue tables, single doc saves, set_value). Paranoid grep across all 8 for `get_tables` / `information_schema` / `performance_schema` / `SHOW INDEX|TABLES`: zero hits except the known-failing one. **Plan-C remains viable**; Plan-D not needed. S47 "80–150 intermediate patches" estimate was off by an order of magnitude.

## GitHub issue activity

| Issue | Action | Why |
|---|---|---|
| [ESACP#397](https://github.com/martinhbramwell/ESACP/issues/397) | filed (open) | Deploy-key VM-side anti-pattern surfaced + Path-A unblock |
| [ESACP#398](https://github.com/martinhbramwell/ESACP/issues/398) | filed (open) | `bench migrate` substrate-config bug (performance_schema visibility) |
| LSKB#15 | pause-comment posted; **stays open** | Step 6 failed; blocked on ESACP#398 |

## Pointer-comments posted

- LSKB#15 — [substrate-apply Step 6 pause + ESACP#398 cross-link + state retained](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/15#issuecomment-4460942174)
- ESACP#353 (Plan-B parent epic) — [Session-54 ledger entry + Path β survey result](https://github.com/martinhbramwell/ESACP/issues/353#issuecomment-4461216837)
- LSKB#6 (Phase-4 epic) — [Phase-4 ladder pause + block chain update](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/6#issuecomment-4461217835)

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T1+T3 (combined, this ESACP session-close commit) | _pending — populated after verdict_ | _pending_ | ESACP doc-only direct-to-main per `docs/qa-contract.md` v2.1 §2.1 clause 3 |

## Counts at session end

- ESACP open: **42** (was 40; +#397 +#398).
- LSKB open: **8** (unchanged).
- ce_sri open: 5 (unchanged).
- LogiSoluValidations open: 2 (unchanged).
- `sales_partner_commissions/main`: `5567c47` (unchanged through S47–S54).

## TRIVIAL_FIXES.md status

Unchanged. 2 monitor-only entries (LogiSoluMemory Trigger 3 skip pattern S33; `tools/secrets.py` +x bit S47).

## Carry-forward operator-reminders (delta)

- **LSKB#15** — substrate-apply now blocked on ESACP#398. Steps 1–5 state retained on dev02 (production data restored, encryption_key aligned, `sales_partner_commissions` installed at `5567c47`). Disposable per `feedback_dev_vms_are_disposable.md`.
- **ESACP#397** (NEW) — deploy-key VM-side anti-pattern; strict subset of #375. Path-A unblock executed; institutional fix at #375.
- **ESACP#398** (NEW) — substrate-config bug; Path A (ansible role disabling `performance_schema`) recommended. Should be applied to all bench-substrate VMs.
- **Path β survey caveat #1** — patches `clear_large_email_queues` / `update_schedule_type_in_loans` / `update_asset_value_for_manual_depr_entries` / `update_docs_link` / `correct_asset_value_if_je_with_workflow` carry minor data-mutation risk against production data shape (post-ESACP#398 fix). Likely no-ops or simple UPDATEs but not zero-risk.
- **Path β survey caveat #2** — survey scope: grepped `get_tables` / `information_schema` / `performance_schema` / `SHOW INDEX|TABLES`. Other substrate-config classes (SQL mode, charset, sql_safe_updates) wouldn't be detected. Confidence high, not absolute.
- **Plan-C meta-pattern** — second-instance trigger remains absent; S54 reinforces first-instance evidence (intermediate-patches concern much smaller than feared).
- **dev02 substrate state** — production data restored; sales_partner_commissions installed; encryption_key aligned. Awaiting ESACP#398 fix to retry Step 6.
- **Build-evidence retained** — dev02:`/tmp/lskb15-S54-restore.log`, `/tmp/lskb15-S54-migrate.log`, `/tmp/check_patch_log.sql`. Rotation handles cleanup.
- **LogiSoluMemory Trigger 3 skip pattern** — unchanged (monitor-only).
- **ce_sri local clone in-progress state** — unchanged.
- **Tablet WG sidebar (#383)** — still ripe.

## Trimmed minutes experiment

This session: ~95 lines as committed. Slightly over the S40–S47 ~73–82 line baseline. Compression-resistance came from: substrate-apply 6-step ledger + mid-session ESACP#397 finding-and-discharge + Path β survey result table + paranoid double-check evidence. Trim baseline holds within ~15% for paused-substrate-with-finding-and-survey-class.

## Post-close audit-fix

_To be populated by the post-close audit hook re-run._
