# Agenda — Next session — Post-rebuild: Refresh test + deferred issues

## Primary Objective

### Test Refresh on both dev VMs — prove idempotent re-run after clean rebuild

## Pre-flight
1. Run `sync_check.sh`
2. Verify uvicorn running with latest api.py (`--reload`)
3. Verify both VMs healthy (health endpoint green, HTTPS 200)

## Steps

1. **Refresh dev01** via `POST /api/refresh/dev01` — confirm idempotent re-run succeeds
   - Validates: git pull (no changes expected), full pipeline re-run, services green after

2. **Refresh dev02** via `POST /api/refresh/dev02` — same validation

3. **GH #87: Refresh secrets gap** — Refresh doesn't re-SCP secrets (P12 cert, ce_sri_parms.json). If Refresh overwrites `.env` or parms, ce_sri_svc breaks.
   - Decision needed: should Refresh re-SCP secrets from controller, or skip H4b/H4e on Refresh?

4. **GH #90/#91: Topology UI provisioning state + live logs** — nodes show "Unprovisioned" during active provisioning; clicking a provisioning node should show live job logs.

## Deferred
- GH #68: Refresh fast path (skip G/H DB restore)
- GH #50: cf-mcp-refresh not in repo
- SRI PRUEBAS retry (2026-04-07)
- GH #9: hardcoded usernames/machine names in scripts
- h4e_patch_parms.py backslash continuation collapse in f-string template (cosmetic)
