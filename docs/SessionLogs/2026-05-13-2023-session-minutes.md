# 2026-05-13 2023 — Session 47 minutes

## Objective

**LSKB#15 — substrate-apply on dev02 (Candidate A).** Phase 4 ladder — end-to-end substrate-honest verification of LSKB#13 migration patch + LSKB#14 Server Script upsert hook on dev02 against `PRODUCTION_20260404` data. Substrate-touching infra session (bucket-2 / LSKB tracker).

## Outcome — paused at version-skew discovery; LSKB#20 filed; LSKB#15 stays open

Substrate-apply sequence reached `bench restore` cleanly. Pre-`bench migrate` baseline capture surfaced a Plan B Phase 1 ↔ Phase 4 sequencing block that disqualifies isolated Phase 4 acceptance on the current substrate.

### What ran cleanly on dev02

- **F1** — Stale orphan clone of `sales_partner_commissions` (commit `474666c master`, no remote) removed via `bench remove-app --no-backup --force`.
- **Substrate-config gap remediation** — `~erpadm/.ssh/config` was missing the `Host sales_partner_commissions.gh` alias for the deploy key dropped 2026-05-12. Appended the 5-line block matching the established `ce_sri.gh` / `ce_sri_svc.gh` / `route_planner.gh` pattern; deploy-key auth confirmed (`Hi martinhbramwell/sales_partner_commissions! You've successfully authenticated`). Filed [ESACP#387](https://github.com/martinhbramwell/ESACP/issues/387) for the upstream ansible-pipeline gap.
- **Fresh `bench get-app`** via SSH_ASKPASS+setsid preamble against `git@sales_partner_commissions.gh:martinhbramwell/sales_partner_commissions.git --branch main` → clone at [`5567c47`](https://github.com/martinhbramwell/sales_partner_commissions/commit/5567c474555a16fb9ba2d84e6cf5160ef5f8052f); all 4 `patches/v14_0/` modules + 2 colocated tests + 7 `server_scripts/` modules + 2 colocated tests verified present; `patches.txt` references `sales_partner_commissions.patches.v14_0.migrate_commissions_to_child_table`.
- **scp 2.4 GB snapshot** (SQL 2.1 G + files.tar 331 M + private-files.tar 5.3 M) controller → dev02 `/tmp/spc_restore/`; md5 verified identical both sides.
- **encryption_key alignment** — dev02 site_config `encryption_key` updated to production's `7tnS5lOT_E6nvhktc70L4mGv2WQ0ac1WP0ET1UuGNr0=` via `bench set-config` so post-restore encrypted-field decryption works.
- **`bench restore`** with `--db-root-password erpnext_build --admin-password sasa --force` — exit 0. One non-fatal `ERROR 1227` on `CREATE VIEW CustomerInvoices` because the production dump's `DEFINER=root@localhost` requires SUPER/SET USER privs the site DB user lacks; view is reporting-only and out of LSKB#15 scope.

### Why the substrate-apply paused before `bench migrate`

**F5 — version skew.** Production snapshot was taken at **frappe 13.41.3 / erpnext 13.39.2**; dev02 bench is at **13.58.22 / 13.55.2** (~17 frappe minor / ~16 erpnext minor delta). Restored `tabPatch Log` carries 569 rows (341 erpnext / 113 frappe / 15 misc). Running `bench migrate` now would execute ~80–150 intermediate version-bump patches **before** the `sales_partner_commissions.patches.v14_0.*` chain that LSKB#15 actually verifies. That conflates three test results into one verdict (v13-minor-bump migration cleanliness on production data = Phase 1 scope; v14_0 patches + `after_migrate` upsert = Phase 4 scope) and any failure in the first family blocks reaching the second without producing a verdict that belongs to LSKB#15.

**F6** — production master DocType `Sales Partner Customer Item Commissions` lives in module `"Logichem"` (literal customer-name in-place-core-edit drift). Pre-existing; LSKB#15 doesn't touch it; noted only.

### Filed

- [**LSKB#20**](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20) — Phase 1 sub-issue: `dev02 bench-version drift from PRODUCTION_20260404 snapshot blocks isolated Phase 4 substrate-apply`. Three resolution paths spelled out (provision dev02 to match snapshot / bring production up to dev02 version / per-Phase substrate VM). Operator selection lives in that issue.
- [**ESACP#387**](https://github.com/martinhbramwell/ESACP/issues/387) — pipeline gap: ansible should auto-add `Host <app>.gh` SSH config block when provisioning bespoke-app deploy keys on target VMs.

## GitHub issue activity

| Issue | Action | Why |
|---|---|---|
| LSKB#20 | filed (open) | Phase 1 substrate-version-alignment prerequisite |
| ESACP#387 | filed (open) | Pipeline ssh-config-gap discovered on dev02 |
| LSKB#15 | pause-comment posted ([issuecomment-4446250031](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/15#issuecomment-4446250031)); **stays open** | Blocked on LSKB#20; v14_0 + Server Scripts unchanged on `sales_partner_commissions/main@5567c47` |

## Pointer-comments posted

- LSKB [#15](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/15#issuecomment-4446250031) — substrate-apply pause rationale + LSKB#20 cross-link + v14_0 artefacts unchanged.

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T1+T3 (LSM `TRIVIAL_FIXES.md` close commit) | _pending — populated after verdict_ | _pending_ | LogiSoluMemory direct-to-main per v2.1 §2.1 clause 3 (LSM single-branch convention) |
| T1+T3 (this ESACP session-close commit) | _pending — populated after verdict_ | _pending_ | ESACP doc-only direct-to-main per v2.1 §2.1 clause 3 |

## Counts at session end

- ESACP open: **37** (was 36; +#387).
- LSKB open: **9** (was 8; +#20; #15 unchanged).
- ce_sri open: 5 (unchanged).
- LogiSoluValidations open: 2 (unchanged).
- `sales_partner_commissions/main` tip: `5567c47` (unchanged).

## TRIVIAL_FIXES.md status

One new monitor-only entry added — **F4** — `tools/secrets.py` lost its `+x` bit (currently `-rw-rw-r--`). Library module, not a CLI, so contract bend is mild; restore with `chmod +x` next housekeeping pass.

## Carry-forward operator-reminders (delta)

- **LSKB#15** — substrate-apply now blocked on LSKB#20; v14-lifecycle + transaction-management checklists remain accurate; sales_partner_commissions/main@5567c47 unchanged and ready to re-apply once Phase 1 alignment resolves.
- **LSKB#20** (NEW) — Phase 1 substrate-version-alignment prerequisite. Operator-decision lives in the issue (3 resolution paths spelled out).
- **ESACP#387** (NEW) — ansible-pipeline ssh-config-gap; modest scope; pickable as a standalone bucket-1 session.
- **LSKB#16 (parity verification)** — unchanged; after LSKB#15 (which is after LSKB#20).
- **LSKB#18 (`user_data_fields` cleanup)** — unchanged; chore-class micro-fix on `sales_partner_commissions`, pickable independently.
- **`tools/secrets.py` +x bit (F4)** — TRIVIAL_FIXES.md monitor-only; restore on next housekeeping pass.
- **dev02 substrate state** — left as-is post-restore (production-data, encryption_key aligned, Administrator=sasa, /tmp/spc_restore staging files retained). Disposable per `feedback_dev_vms_are_disposable.md`; next LSKB#15 attempt (post-#20) may re-use or rebuild as appropriate.
- LogiSoluMemory Trigger 3 skip pattern — unchanged.
- ce_sri local clone in-progress state — unchanged.
- Tablet WG sidebar (#383) — still ripe.

## Trimmed minutes experiment

This session: ~81 lines as committed. Sits right at the S40–S46 ~73–80 line baseline despite the substrate-investigation shape (substrate discovery + remediation + filing two issues + pause-rationale + version-skew quantification). Compression came from tabular issue-activity + counts + reminders rather than narrative expansion. Trim baseline holds for paused-substrate-class as cleanly as for substantive-code-class.

## Post-close audit-fix

SESSION END audit (UserPromptSubmit hook re-run) caught **two gaps** in the close-out batch (`97de323`):

1. **LSKB#20 mis-categorized as "Plan B Phase 1"** — the title prefix `infra(Plan B Phase 1):` and the body's `Parent: LSKB#5` cite were both wrong. LSKB#5 was Plan B Phase 3 (closed) and LSKB#2 (Phase 1 — fixture_json Custom Fields) is also closed. The substrate-version-drift issue is **substrate-readiness** work, not part of any specific closed Plan B Phase. Discharged this session by `gh issue edit 20 --title "infra(substrate-readiness): …" --body "…"` (parent re-pointed to ESACP#353 Plan B epic; added categorization note explaining why the issue is bucket-2 but not bound to a closed phase number).
2. **Missing pointer-comments on Plan B parent epics** — S45/S46 precedent posts a Session-N ledger entry on ESACP#353 (Plan B parent) + Phase-N ladder progression on LSKB#6 (Phase 4 epic) at each session-close. S47 minutes recorded only the LSKB#15 pause-comment; the parent-epic pointers were missing. Discharged this session by posting:
   - ESACP [#353](https://github.com/martinhbramwell/ESACP/issues/353#issuecomment-4446348072) — Session-47 ledger entry; substrate-apply pause rationale; LSKB#20 + ESACP#387 announcement; cross-repo `fixes` tally stays at 15.
   - LSKB [#6](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/6#issuecomment-4446349051) — Phase 4 ladder pause; full ladder-state table (LSKB#12/#19/#13/#14 closed; #15 blocked on #20; #16 blocked on #15).

Other audit categories all clean: step 1 (forward-tense — no unresolved "will" claims in minutes); step 3 (no PRs opened this session, so no `mergedAt` gate); step 4 (no carried-forward doubts — all session-time decisions D1–D8 resolved within-session). 2-gap audit-fix is heavier than the S45/S46 1-gap precedent (single LSKB#15 pointer-discharge); the additional gap (Plan-B-parent ledger entries) reflects S47's two-tier filing structure (one new issue per bucket — LSKB#20 + ESACP#387) that S45/S46's single-PR-per-session shape didn't trigger.
