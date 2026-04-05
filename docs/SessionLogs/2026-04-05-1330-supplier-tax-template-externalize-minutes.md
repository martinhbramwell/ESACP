# Minutes — 2026-04-05 13:30 — Externalize Supplier Tax Template (#102)

## Objective

Externalize `Supplier.purchase_taxes_and_charges_template` — the last of 13 Developer Mode field additions — as a Custom Field fixture in ce_sri. Verify via full destroy+deploy of dev03.

Corresponds to **Session B** from the 2026-04-05-1000 agenda. Issue #102, branch `fix/102-supplier-tax-template`.

## Completed ✅

### Fixture added to ce_sri
- Added `Supplier-purchase_taxes_and_charges_template` (Link → Purchase Taxes and Charges Template) to `ce_sri/fixtures/custom_field.json`
- `insert_after: supplier_primary_address` (from production's `supplier.json`)
- Committed `7c99ccc` on `wip/2026-03-25`, pushed to GitHub

### dev03 full lifecycle verified
- Destroyed dev03 completely via Playwright topology UI
- Fresh deploy from template — full pipeline including DB restore + G2 step
- G2 cleared 48 Custom Fields + colliding DocFields, bench migrate reimported all cleanly
- DB query confirmed: field exists in `tabCustom Field` (not `tabDocField`)
- Pipeline completed in ~25 minutes (DB restore ~17 min on toshiba hardware)

### 13/13 Developer Mode audit complete
- All 13 Developer Mode field additions across 7 doctypes are now externalized as Custom Field fixtures
- `apps/erpnext` remains 100% stock on all dev/staging VMs

### Side findings
- Telegram 3-min idle alert works correctly for multiple-choice (AskUserQuestion) wait states — memory updated
- Opened #103: `cd + git` compound command approval friction

## Key Decisions

- Confirmed the field IS non-standard (not in stock ERPNext v13 `supplier.json`) despite appearing on dev VMs — it was carried in as a DocField by the production DB restore
- Understood why #100 (commission fields) caused collisions but #102 didn't: commission fields were half-migrated (in fixture AND DocField), Supplier field was DocField-only (no fixture to collide with)

## Action Points

| # | Action | Owner | Target |
|---|--------|-------|--------|
| 1 | Close or link #98 — overlaps with completed #100 | User | Next session |
| 2 | Fix #103 — cd+git compound command permissions | Claude + user | Next session |
| 3 | Retry SRI PRUEBAS submit on dev01 | Claude + user | 2026-04-07 |
