# Agenda — 2026-04-03 — Fix #93: Administrator not found after bench restore

## Primary Objective

### Get https://dev02.iridium.blue/ working

## Pre-flight
1. Run `sync_check.sh`
2. Verify dev02 VM state on toshiba (half-provisioned from failed deploy)

## Steps

1. **Investigate root cause of #93**: SSH to dev02, check if Administrator user exists in the DB after restore. Check `bench --site dev02.iridium.blue list-users`. Check if bench migrate creates the user.

2. **Fix**: either adjust the restore sequence, or handle the missing-user case in H4a

3. **Destroy + redeploy dev02** end-to-end via Playwright

4. **Verify**: https://dev02.iridium.blue/ responds, all services green via Inspect

## Deferred
- GH #87: Refresh secrets gap
- GH #90: Topology UI provisioning state
- GH #91: Topology UI live job logs
- dev01 HTTP 502
- SRI PRUEBAS retry (2026-04-07)
