# Minutes — Patch Log Seed Ordering (#107)

**Date**: 2026-04-06 20:30–22:30 UTC-4
**Objective**: Fix #107 — `delete_duplicate_indexes` patch crashes `bench migrate` during differentiation

---

## Decisions

- #108 already resolved (commit `a8780a9`, closed today) — confirmed and moved on
- Created `tools/vm_scripts/g1_seed_patch_log.py` to seed `tabPatch Log` before any `bench migrate`
- Removed duplicate seeding from `g2_clear_fixture_custom_fields.py`
- Seeding must happen **twice** in the pipeline:
  - **E1** (before F): protects `installApps.sh`'s migrate (relevant on Refresh when DB already has production data)
  - **G1** (after G, before G2): re-seeds because `bench restore` wipes the entire DB

## Key Learnings

1. First attempt placed G1 before G — wrong because `bench restore` drops and recreates the DB, wiping the seed
2. Second attempt placed G1 after G — Refresh crashed at F because F's migrate also hits the patch (DB already has production data from previous run)
3. Final fix: dual seeding at E1 and G1

## Test Results

- **Refresh on dev02**: PASSED — F's migrate and G2's migrate both clean
- G's migrate (inside handleRestore.sh, third-party BaRe) still logs non-fatal `delete_duplicate_indexes` and `forma_de_pago_preferida` errors — expected, not our code

## Artifacts

- Commit: `f888c7c` on branch `fix/107-patch-log-seed-ordering`
- Branch pushed, issue commented as provisionally resolved

## Deferred

- Full Destroy+Deploy rebuild needed to fully verify #107
- `.env` placeholder values (`MAILERUID=SMTP_EMAIL_ACCOUNT`) observed in Refresh output — separate concern
- Issues #117 (Social Login ordering), #116 (DB views access denied) — per agenda, next sessions
- G's internal errors (handleRestore.sh) are third-party — cannot fix without modifying BaRe

## Action Points

- [ ] Full rebuild (Destroy+Deploy) on dev02 to confirm #107 end-to-end
- [ ] Merge PR for `fix/107-patch-log-seed-ordering` after rebuild passes
- [ ] Close #107 with final commit hash after merge
