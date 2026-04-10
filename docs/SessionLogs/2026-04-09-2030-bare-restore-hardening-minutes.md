# Session Minutes — 2026-04-09 20:30 — BaRe Restore Hardening

## Objective
Fix #116 — DB views restoration fails silently in BaRe handleRestore.sh

## Attendees
- <controller> operator
- Claude Opus 4.6 (1M context)

## Decisions

### 1. Production BaRe is the golden reference
- `~/projects/Logichem/PRODUCTION_20260404/BaRe/handleRestore.sh` is battle-tested
- The git repo's first commit (`4d94925`, 2026-03-25) was NOT a faithful import — it included `sed` DB name substitution, `--insecure` curl, `--skip-failing` migrate, and Social Login Key cleanup that don't exist in production
- Future BaRe changes must be diffed against the production copy first

### 2. Production handles cross-site restores
- `repackageWithCorrectedSiteName()` renames files + patches site_config for different hostnames
- Production does NOT substitute DB names in ddlViews.sql (same DB name across master/slave)
- The `sed` substitution in git was added for lab (different DB names) — genuinely needed there

### 3. Two showstopper bugs fixed
- `--skip-failing` on `bench migrate` — silently drops Custom Field fixture imports (lab-added code, not in production)
- `2>/dev/null || true` on Social Login Key DELETE — hides credential failures (lab-added code, not in production)

### 4. Production restart toggle is intentional
- `1==0` on restart block is deliberate operator control for manual failover checks
- Not a debug leftover — production user wants to verify state before restarting

### 5. DSIT path (`../sites/` vs `./sites/`) is a non-issue for lab
- `restoreSocialLoginConfig()` is never reached in lab pipeline (`DEFER_SOCIAL_LOGIN=1`)
- Production's `../sites/` is correct for its calling convention

## Actions Completed
- ✅ BaRe commit `6750d9b`: remove `--skip-failing` + error masking
- ✅ BaRe PR #5 merged to main
- ✅ dev03 Refresh triggered and completed end-to-end (all sections A–L)
- ✅ #116 closed with acceptance test comment
- ✅ Memory updated: `feedback_bare_production_reference.md`, `project_pipeline_acceptance_status.md`, `MEMORY.md`

## Pipeline Status
**COMPLETE — zero known blockers.** All sections acceptance-tested.

## Deferred Items
- 🔄 BaRe git repo divergence from production — lab-specific additions are interleaved with original code. Consider separating lab orchestration into ESACP pipeline (future cleanup, not blocking)
- 🔄 Previous session log `2026-04-08-2230-install-refactor-minutes.md` still untracked
