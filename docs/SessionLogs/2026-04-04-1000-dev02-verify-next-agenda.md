# Agenda — Next session — Full automated re-deploy verification

## Primary Objective

### Destroy dev02 and re-deploy to confirm the pipeline works end-to-end with no manual intervention

BaRe `e0a86db` has the DocField fix + `--skip-failing` safety net. This session confirmed
the fix works manually — next step is proving the full automated pipeline delivers all 18
Sales Invoice Custom Fields on a clean deploy.

## Pre-flight
1. Run `sync_check.sh`
2. Verify toshiba reachable

## Steps

1. **Destroy dev02** from Cytoscape UI
2. **Deploy dev02** from Cytoscape UI — full pipeline
3. **Verify Custom Fields** — all 18 Sales Invoice fields present automatically
4. **Compare dev02 Commission section** against production screenshot
5. **Check ce_sri_svc status** — was it installed correctly? (install.py aborted last time)

## Backlog (priority order)

1. **erpadm SSH key** — add authorized_key deployment to differentiate.sh so `dev02-erp` alias works on fresh provisions
2. **ce_sri repo bugs** — commit fixes for modules.txt accent + Supplier fixture conflict
3. **ce_sri_svc install timing** — ERPNext must be running before install.py; may need a service restart between steps F and G
4. **Latest production backup verification** — SCP today's backup, restore via handleRestore.sh, confirm all fields
5. **Customization inventory** — Phase 1 of the upgrade preparation initiative
6. **Playwright regression suite** — Phase 2 gating each v13 → v16 upgrade step

## Open Issues (16)
#9, #19, #20, #21, #23, #24, #26, #37, #48, #50, #65, #67, #68, #74, #79, #81, #87, #88, #96 (closed)
