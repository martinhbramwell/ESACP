# Agenda — Next Session (from 2026-04-01 pipeline migration)

## Primary Objective

### 1. Get SRI upload working on dev01

Test the ce_sri electronic voucher (comprobante electrónico) upload flow end-to-end on dev01 in PRUEBAS mode. ce_sri_svc is running with real values (AMBIENTE=1, real cert, real company data).

## Pre-requisites (fix before testing)

### 2. Commit modules.txt accent fix to ce_sri repo

`modules.txt` must say `Comprobante Electronico` (ASCII, no accent). Currently fixed on dev01 only — needs committing to `martinhbramwell/ce_sri` branch `wip/2026-03-25` so future clones work.

### 3. Fix fixture import — conflicting field blocks all subsequent imports

`Supplier-purchase_taxes_and_charges_template` in `custom_field.json` conflicts with a standard ERPNext field. Frappe's import aborts on first error, skipping all remaining fields. Options:
- Remove the conflicting entry from fixture JSON (preferred — it's a standard field, not custom)
- Add a post-migrate script that inserts missing fields individually, skipping conflicts

### 4. Rewrite Section B2 in api.py — real .env files

Replace the `.env.sample` copy approach with:
- Step 10: SCP 4 files (`.env_20260401_TEST_IVA15`, `.env_20260401_PROD_IVA15`, `setTESTMODE.sh`, `setPRODUCTIONMODE.sh`) from controller to VM
- Section B2: parametrise ERP connection (ERP_HOST, ERP_PTCL, ERP_PORT) in both `.env_*` files, then run `setTESTMODE.sh`
- Define canonical controller location for these secrets (currently in `temp/ce_sri/services/ce_sri_svc/`)

### 5. Deploy chkMode.sh + updated spvstr alias via differentiate.sh

Currently only on dev01 manually. Add to Section L (bash_aliases) in the differentiate.sh template.

## Carried Business

### 6. GH #81 — BIND_PORT placeholder (moot once #4 done)
### 7. GH #79 — ce_sri_svc startup banner
### 8. GH #68 — Refresh fast path (skip G/H DB restore)
### 9. GH #50 — cf-mcp-refresh not in repo
### 10. GH #37 — api.py jobs killed on uvicorn restart

## Deferred

- Permissions via bench commands (Phase 5)
- Dashboard chart recreation (Phase 6)
- Custom Translations (Phase 7)
- Extend Playwright coverage
- Update dev02 with all fixes from this session
