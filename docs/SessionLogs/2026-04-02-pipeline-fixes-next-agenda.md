# Agenda — Next Session (from 2026-04-02 pipeline fixes)

## Primary Objective

### 1. Clean Destroy + Deploy of dev02 — zero manual steps

All api.py fixes are committed. Do a full Destroy → Deploy cycle for dev02 and verify:
- All 9 supervisor services RUNNING
- Custom Fields imported (should be 39 now, not 0)
- ce_sri_svc .env present with real values
- `bench list-apps` shows ce_sri, route_planner, returnable
- https://dev02.iridium.blue loads

## Pre-requisites

### 2. Fix #87 — Refresh must re-SCP secrets

`_run_refresh()` needs to mirror Step 10's SCP of deploy keys, ce_sri secrets (P12, parms.json, logo), and BKP. Without this, Refresh leaves ce_sri_svc broken.

### 3. Investigate `bench list-apps` empty

Apps are git-cloned to `apps/` but not registered as installed Frappe apps. Check `installApps.sh` (Section F) and `handleRestore.sh` (Section G) — `bench install-app ce_sri` may not be running.

### 4. Regenerate dev01-differentiate.sh

dev01's saved artifact is from an older api.py version — missing `_CESRI_SVC` fix and bash_aliases move. Either Refresh (which regenerates nothing) or a manual regeneration is needed.

## Carried Business

### 5. GH #79 — ce_sri_svc startup banner
### 6. GH #68 — Refresh fast path (skip G/H DB restore)
### 7. GH #50 — cf-mcp-refresh not in repo
### 8. GH #37 — api.py jobs killed on uvicorn restart

## Deferred

- SRI PRUEBAS retry — moved to 2026-04-07 agenda
- Permissions via bench commands (Phase 5)
- Dashboard chart recreation (Phase 6)
- Custom Translations (Phase 7)
- Extend Playwright coverage
