# Agenda — Next Session (from 2026-03-31 rebuild-prereqs)

## Pre-flight

### 0. Verify LAN switch
- Confirm toshiba reachable at new LAN IP
- `~/.ssh/config` (toshy HostName) and `/etc/wireguard/wg0.conf` (Endpoint) updated
- `sudo wg syncconf wg0 <(wg-quick strip wg0)` — WireGuard reconnected
- `bash platforms/kvm/sync_check.sh` — all green

### 1. Push unpushed commits
- ESACP: `6b64e66`, `3d2fcbd`
- BaRe: `07323d0`

## Primary Objective

### 2. Full dev01 rebuild from template — end-to-end fixture verification
- Destroy dev01 via Cytoscape UI (Playwright: `npx playwright test --grep "Destroy"`)
- Deploy fresh dev01 from template
- Verify ce_sri fixtures applied automatically by `bench migrate` after DB restore
- Verify Section B2: AMBIENTE=1 and ERP_HOST=dev01.iridium.blue in active .env
- Browser-verify `forma_de_pago_especificada` on Sales Invoice form
- **Success criteria**: field present + AMBIENTE=1, no manual intervention

## Pre-requisites (all met)

- ✅ Playwright installed + Inspect test passes
- ✅ GH #75 — Patch log UPDATE in handleRestore.sh
- ✅ Returnable TypeError — not reproducible (monitor during rebuild)
- ✅ App rsync in Refresh flow
- ✅ GH #76 — AMBIENTE enforcement (Section B2)

## Deferred

### 3. Permissions via bench commands (Phase 5)
HR Manager on User/Employee, create on Party Type roles.

### 4. Dashboard chart recreation (Phase 6)
Profit & Loss, Asset, CRM, Selling dashboards — via ERPNext UI on dev01.

### 5. Custom Translations (Phase 7)
2 Spanish translations via Custom Translation DocType.

### 6. Extend Playwright coverage
Add fixture verification test: after deploy, SSH to VM and check `tabCustom Field` for `forma_de_pago_especificada`.

## Carried Business

### 7. GH #68 — Refresh fast path (skip G/H DB restore)
### 8. GH #50 — cf-mcp-refresh not in repo
### 9. GH #37 — api.py jobs killed on uvicorn restart
### 10. Bi-directional voice (carried)
