# Agenda — Next Session (from 2026-04-01 ce_sri connectivity)

## Primary Objective

### 1. Retry SRI PRUEBAS submit on dev01
Error 70 was likely Easter weekend SRI downtime. Retest invoice 001-004-000000074.

## Pre-requisites (carried from previous agenda)

### 2. Commit modules.txt accent fix to ce_sri repo
`modules.txt` must say `Comprobante Electronico` (ASCII, no accent). Fixed on dev01 only — needs committing to `martinhbramwell/ce_sri` branch `wip/2026-03-25`.

### 3. Fix fixture import — conflicting field blocks all subsequent imports
`Supplier-purchase_taxes_and_charges_template` in `custom_field.json` conflicts with standard ERPNext field.

### 4. Populate SOPS-encrypted ce_sri_parms.json with real secrets
Run `sops example_srvr_files/ce_sri_parms.sops.json` to replace placeholders with real values (cert pwd, SMTP pwd, bank account, email). Then re-encrypt and commit.

### 5. Rotate exposed secrets
Cert password, SMTP app password, and API tokens were exposed in the 2026-04-01 session log. Rotate them.

### 6. Pipeline end-to-end test
Destroy + re-provision dev02 using the updated pipeline. Verify SRI submit works with zero manual steps.

## Carried Business

### 7. GH #79 — ce_sri_svc startup banner
### 8. GH #68 — Refresh fast path (skip G/H DB restore)
### 9. GH #50 — cf-mcp-refresh not in repo
### 10. GH #37 — api.py jobs killed on uvicorn restart

## Deferred
- Permissions via bench commands (Phase 5)
- Dashboard chart recreation (Phase 6)
- Custom Translations (Phase 7)
- Extend Playwright coverage
