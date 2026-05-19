# Agenda — Next session — End-to-end verification of handleRestore.sh fix

## Primary Objective

### Destroy dev02 and re-provision from the Cytoscape UI

Full end-to-end test of the BaRe fix (commit `45b8775`): Destroy → Deploy → verify
all 18 Sales Invoice Custom Fields are present without manual intervention.

## Pre-flight
1. Run `sync_check.sh`
2. Verify toshiba reachable (modem may need power-cycle — AP isolation seen 2026-04-04)
3. Confirm dev01 healthy (already verified this session)

## Steps

1. **Destroy dev02** from Cytoscape UI
2. **Deploy dev02** from Cytoscape UI — full pipeline including handleRestore.sh
3. **Verify Custom Fields** — all 18 Sales Invoice fields present, especially:
   - `sales_partner_supplier`, `comission_entry_created`, `commission_paid`, `break_down`
4. **Compare dev02 Commission section** against production screenshot (should now match)
5. **Verify with latest production backup** — SCP today's backup to dev02, restore via
   handleRestore.sh standalone, confirm all fields survive

## Near-term: Production backup verification

Restore the **latest** production backup (not the one baked into the template) onto a
dev VM and confirm handleRestore.sh handles it cleanly. This catches any new Developer
Mode edits made on production since the last backup was captured.

## New initiative: Customization inventory + Playwright regression suite

### Phase 1 — Customization inventory
Build a complete list of every difference between this ERPNext and stock v13:
- 39 Custom Fields (ce_sri fixtures)
- 194 Property Setters (ce_sri fixtures)
- Custom DocTypes (ce_sri, returnable, route_planner)
- Client scripts, server scripts, custom print formats
- Naming series overrides
- Workflow customizations
- Bespoke apps: ce_sri, ce_sri_svc, returnable (BtlMng), route_planner
- Production upstream patches (captured in temp/*.patch — 23 files, now externalized)

### Phase 2 — Playwright regression tests
Write a Playwright test suite that validates each customization survives migration:
- Functional tests: field presence, field behavior, workflow triggers
- Regression tests: run after each version upgrade (v13 → v14 → v15 → v16)
- SRI e-invoice flow (PRUEBAS mode)
- Commission fields + Sales Partner Supplier link
- forma_de_pago on Customer + Sales Invoice
- Route planner integration
- Returnable bottle management
- Custom print formats render correctly

This suite becomes the gate for each upgrade step.

## Open Issues (15)
(unchanged from previous agenda — see 2026-04-04-rebuild-dev01-dev02-next-agenda.md)
