# Agenda — 2026-04-04 — Clean rebuild: destroy dev01 + dev02, full uninterrupted UI build

## Primary Objective

### Destroy both dev VMs and rebuild from UI — prove uninterrupted end-to-end pipeline

## Pre-flight
1. Run `sync_check.sh`
2. Verify uvicorn running with latest api.py (`--reload`)
3. Verify Cytoscape UI + API responding

## Steps

1. **Fix #83 and #84 in ce_sri repo FIRST** — commit to `wip/2026-03-25` branch:
   - #83: `modules.txt` accent `ó` → ModuleNotFoundError on `bench migrate`
   - #84: fixture JSON includes standard ERPNext field → aborts Custom Field import, 12 fields skipped
   - These block clean deploys — must be fixed before rebuilding

2. **Fix #94: move H3 after H4a** — H4a does `DELETE FROM __Auth` which wipes the password H3 just set. Move H3 to run after H4a (or have H4a preserve password rows).

3. **Destroy dev01 + dev02** via Playwright topology UI

4. **Deploy dev01** via UI — watch full pipeline, do not interrupt

5. **Deploy dev02** via UI — watch full pipeline, do not interrupt

6. **Verify both**: health check, HTTPS, Commission custom fields present, admin login works

## Deferred
- GH #87: Refresh secrets gap
- GH #90/#91: Topology UI provisioning state + live logs
- GH #68: Refresh fast path
- SRI PRUEBAS retry (2026-04-07)
