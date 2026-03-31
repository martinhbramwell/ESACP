# Agenda — Next Session (from 2026-03-31)

## Primary Objective

### 1. Full dev01 rebuild from template — end-to-end fixture verification
- Destroy dev01 via Cytoscape UI
- Deploy fresh dev01 from template
- Verify ce_sri fixtures applied automatically by `bench migrate` after DB restore
- Browser-verify `forma_de_pago_especificada` on Sales Invoice form
- **Success criteria**: field present with no manual intervention

## Pre-requisites (fix before rebuild)

### 2. Install Playwright + verify tests work
```bash
cd prototypes/cytoscape
npm install -D @playwright/test
npx playwright install chromium
npx playwright test --grep "inspect"  # read-only, safest first
```
Then use Playwright for the Destroy + Deploy cycle in item 1 — one `npx playwright test --grep "lifecycle"` replaces dozens of browser automation tool calls.

### 3. GH #75 — Seed patch log with inline-comment format in differentiate.sh
After `bench restore`, before `bench migrate`:
```sql
UPDATE `tabPatch Log` SET patch='frappe.patches.v12_0.delete_duplicate_indexes  # 2022-12-15'
WHERE patch='frappe.patches.v12_0.delete_duplicate_indexes';
```
Without this, `bench migrate` fails on every fresh restore.

### 3. Returnable app TypeError blocking `bench migrate`
`TypeError: expected str, bytes or os.PathLike object, not NoneType` in `frappe.get_module().__file__`.
Blocks fixture import phase. Must be fixed or the returnable app excluded from migrate scope.

### 4. Add app rsync to Refresh flow in api.py
Currently Refresh only re-runs `differentiate.sh` — does NOT rsync updated app code from controller. Fixture updates require manual rsync. Fix: add rsync step before `sudo bash differentiate.sh` in `_run_refresh()`.

## Deferred from this session

### 5. Permissions via bench commands (Phase 5)
HR Manager on User/Employee, create on Party Type roles.

### 6. Dashboard chart recreation (Phase 6)
Profit & Loss, Asset, CRM, Selling dashboards — via ERPNext UI on dev01.

### 7. Custom Translations (Phase 7)
2 Spanish translations via Custom Translation DocType.

### 9. Extend Playwright coverage
Add fixture verification test: after deploy completes, SSH to new VM and check `tabCustom Field` for `forma_de_pago_especificada`.

## Carried Business

### 9. GH #68 — Refresh fast path (skip G/H DB restore)
### 10. GH #50 — cf-mcp-refresh not in repo
### 11. GH #37 — api.py jobs killed on uvicorn restart
### 12. Bi-directional voice (carried)

## Notes
- ce_sri_prod repo now tracks `wip/2026-03-25` from GitHub — fixture commit `ecd4284`
- dev02 has fixtures applied (manual bench console) — dev01 rebuild will be the clean pipeline test
- AMBIENTE=1 (Pruebas) mandatory on all dev/staging VMs — see `feedback_cesri_pruebas_mode.md`
- Items 2-5 must be resolved before item 1 will succeed unattended
- Playwright tests should drive the Destroy/Deploy/Inspect cycle — cheaper and more reliable than browser extension automation
