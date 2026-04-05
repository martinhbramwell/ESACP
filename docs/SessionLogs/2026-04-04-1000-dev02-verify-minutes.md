# Minutes — 2026-04-04 10:00 — dev02 End-to-End Verification

## Objective
Destroy dev02 and re-provision from Cytoscape UI to verify BaRe fix (commit `45b8775`) delivers all 18 Sales Invoice Custom Fields without manual intervention.

## Pre-flight
- ✅ sync_check.sh: 47 passed, 0 failed, 3 warnings (non-blocking)
- ✅ toshiba reachable, all VMs running, WireGuard mesh healthy

## Pipeline Execution
- ✅ Destroy dev02 — Playwright test passed
- ✅ Deploy dev02 — Playwright triggered provision, full pipeline ~16 min
- ✅ ERPNext live at https://dev02.iridium.blue (HTTP 200)

## Verification — FAILED initially
- Only 13 of 18 Sales Invoice Custom Fields found
- Missing: `sales_partner_supplier`, `comission_entry_created`, `commission_paid`, `break_down`, `forma_de_pago_especificada`

## Root Cause (GH #96)
- `Customer.forma_de_pago_preferida` exists as orphaned standard `tabDocField` (from production Developer Mode edits)
- When ce_sri fixture import hits this collision, Frappe throws `ValidationError` and aborts entire remaining fixture list
- Fields appearing after the collision point are silently dropped
- The `delete_duplicate_indexes` patch also still re-executing (patch log INSERT IGNORE may not match existing row format)
- `handleRestore.sh` grep pipe (line 357) was still swallowing error messages

## Fix Applied
- Manually deleted orphaned DocField on dev02
- Re-ran `bench migrate --skip-failing` — all 18 SI Custom Fields confirmed present
- BaRe `e0a86db`: re-added `--skip-failing 2>&1` (45b8775 had removed it)
- GH #96 opened and closed

## Additional Findings
- `erpadm` SSH key not deployed on fresh dev02 — `dev02-erp` alias fails; use `you` + `sudo -u erpadm` as workaround
- dev03 leftover from Playwright lifecycle test — destroyed and cleaned up
- `ce_sri_svc` install aborted during pipeline (ERPNext not yet reachable at port 443 when install.py runs)

## Deferred Items
- 🔄 Full automated re-deploy to confirm pipeline works end-to-end without manual intervention
- 🔄 Compare dev02 Commission section against production screenshot
- 🔄 Restore latest production backup on dev VM
- 🔄 Customization inventory + Playwright regression suite (Phase 1 + 2)
- 🔄 erpadm SSH key deployment needs to be added to differentiate.sh
- 🔄 ce_sri_svc install timing issue — needs ERPNext running before install.py
- 🔄 Bugs 1+2 in ce_sri repo still need committing
