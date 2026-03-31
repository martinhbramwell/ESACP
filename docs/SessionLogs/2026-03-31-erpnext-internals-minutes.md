# Session Minutes — 2026-03-31 ERPNext Internals

## Objective
Investigate missing `forma_de_pago_especificada` field on dev01 Sales Invoice; discover and plan externalization of all production upstream modifications.

## Context (carried from interrupted session)
Previous session (rate-limited) had already:
- Identified 3 differences between dev01 and production Procfiles (ce_sri_svc, redis_socketio, 3-queue workers)
- Confirmed `forma_de_pago_especificada` is NOT in `ce_sri/fixtures/custom_field.json`
- Confirmed `tabSingles` error was transient
- Established Frappe v13 two-tier model (DB customizations vs file-based fixtures)
- Identified AMBIENTE switch (.env) for SRI production vs test endpoints

## Major Discovery: Production Upstream Modifications

**23 files modified directly in upstream `frappe` and `erpnext` repos on production** — uncommitted local edits made via Developer Mode over ~2 years.

### Patches captured
- `temp/erpnext_local_changes.patch` — 18 files, 1992 lines
- `temp/frappe_local_changes.patch` — 5 files, 146 lines

### Root Cause
Developer Mode was ON in production. Frappe's DocType editor writes directly to the owning app's JSON file (not to `tabCustom Field`). So fields added via the UI landed in `erpnext/` and `frappe/` source files instead of being externalized as database customizations in `ce_sri`.

### Categorized Changes

**Business-critical fields (17 fields across 8 DocTypes):**
- Sales Invoice: `forma_de_pago_especificada`, `sales_partner_supplier`, `comission_entry_created`, `commission_paid`, `break_down`
- Customer: `forma_de_pago_preferida`
- Delivery Note: `saldo_del_cliente`
- Sales Order: `customer_special_note`, `data_90`
- Purchase Order Item: `tipo_comprobante`, `comprobante_interno`
- Supplier: `purchase_taxes_and_charges_template`
- Address (frappe): `delivery_route`, `barrio`
- Sales Partner: `supplier`

**Property overrides:** hidden fields (commission_rate, amount_eligible_for_commission, tax_withholding_category), collapsible sections, label changes, Tax Rule autoname→Prompt

**Permissions:** HR Manager on User and Employee, create on Party Type roles

**Disposable:** debug `print()` in delete_doc.py/document.py, redis/rq version bumps, JSON reformatting noise, dashboard user-preference saves

### Key Insight: Dev01 is Clean
Dev01 runs stock `frappe v13.58.22` / `erpnext v13.55.2` with **zero local patches**. Developer Mode is OFF. Two orphaned `tabDocField` rows exist from the production DB restore (`forma_de_pago_preferida`, `purchase_taxes_and_charges_template`) — fragile, would be dropped on `bench migrate`.

## Plan: Externalize into ce_sri Fixtures (GH #74)

Full plan at `~/.claude/plans/snazzy-hatching-swing.md`. Summary:

1. **Phase 0**: `bench migrate` to clean orphaned tabDocField rows
2. **Phase 1**: Update ce_sri `hooks.py` — add `"Property Setter"` to fixtures
3. **Phase 2**: Create 17 Custom Fields via Customize Form UI on dev01
4. **Phase 3**: Create Property Setters via Customize Form UI
5. **Phase 4**: `bench export-fixtures --app ce_sri`
6. **Phase 5**: Add permissions via bench commands
7. **Phase 6**: Recreate dashboard configuration via UI
8. **Phase 7**: Add 2 Spanish translations via Custom Translation DocType
9. **Phase 8**: Commit fixtures to ce_sri repo
10. **Phase 9**: Verify round-trip (migrate + browser check)

## Completed ✅
- Captured full production patches (erpnext + frappe)
- Categorized all 23 modified files by risk and disposition
- Identified collision risk (tabDocField vs tabCustom Field duplication)
- Opened GH #74
- Plan written and approved
- **Phase 0**: `bench migrate` on dev01 — succeeded (patch log fix: inline comment mismatch); orphaned tabDocField rows manually deleted (migrate doesn't clean rows that were never in JSON)
- **Phase 1**: hooks.py updated — `fixtures = ["Custom Field", "Property Setter"]` with filtered fieldname list (excludes returnable app fields)
- **Phase 2**: 15 Custom Fields created via `bench console` Python script (all OK, zero errors)
- **Phase 3**: 9 Property Setters created via `bench console` Python script (all OK)
- **Phase 4**: `bench export-fixtures --app ce_sri` — 40 Custom Fields + 194 Property Setters exported to JSON
- **Phase 9 (partial)**: `bench migrate` round-trip verified — fields survive, frappe/erpnext repos remain clean
- **Commit**: `ecd4284` on `wip/2026-03-25` branch of ce_sri — pushed to GitHub
- **dev02 provisioning**: launched from Cytoscape UI — full pipeline complete ✅
- **dev02 Refresh**: triggered to pick up updated ce_sri_prod — complete ✅
- **dev02 manual fixture apply**: 12 created, 3 already existed — `forma_de_pago_especificada` verified in DB ✅
- **ce_sri_prod reset**: `git reset --hard github/wip/2026-03-25` — now tracks fixture branch
- **Playwright scripts**: `tests/topology-ops.spec.js` + `playwright.config.js` written for Deploy/Refresh/Destroy/Inspect/Lifecycle
- **Memory saved**: ce_sri_svc MUST be Pruebas mode (AMBIENTE=1) on all non-production VMs

## Discoveries During Execution
- **Refresh does NOT rsync app code** — only re-runs differentiate.sh with whatever's on disk. Need to add app rsync to Refresh flow.
- **`bench migrate` fails on returnable app** — `TypeError: expected str, bytes or os.PathLike object, not NoneType` during DocType update. Blocks fixture import. Separate investigation needed.
- **Patch log inline-comment mismatch** — production backup has `delete_duplicate_indexes` but Frappe v13.58.22 expects `delete_duplicate_indexes  # 2022-12-15`. Must seed after every DB restore. Filed as #75.
- **`export-fixtures --app` exports ALL custom fields** unless hooks.py has a filter — returnable fields leaked into ce_sri fixture until we added a fieldname whitelist.
- **ce_sri_prod vs ce_sri repos**: differentiation pipeline rsyncs from `ce_sri_prod` (uses `ce_sri.gh` SSH alias, unreachable from Mighty). Fixed by adding `github` remote and resetting to fixture branch.

## In Progress 🔧
- (none — all current work complete for this session)

## Not Started 🔄
- Procfile additions (ce_sri_svc, redis_socketio, 3-queue workers) — separate issue
- ce_sri_svc .env configuration for dev VMs (AMBIENTE=1, ERP_HOST=dev0N.iridium.blue) — separate issue
- Fix returnable app TypeError blocking `bench migrate` — separate issue
- Add app rsync to Refresh flow in api.py — enhancement to #68
- Dashboard chart recreation (Phase 6) — deferred
- Custom Translations (Phase 7) — deferred
- Permissions via bench commands (Phase 5) — deferred
- Fix differentiate.sh to seed patch log with inline-comment format (#75)
- Playwright: install dependencies, test run, expose `_openDialogForZone` or use context-menu approach

## Key Decisions
- All business fields → ce_sri Custom Fields + fixtures (not upstream JSON patches)
- Property overrides → ce_sri Property Setter fixtures
- `data_90` included (may be used by Client Script)
- `saldo_del_cliente` default set to blank (runtime-populated, not -543.21)
- Dashboard changes preserved via UI recreation (deferred)
- Spanish translations via Custom Translation DocType (deferred)
- Debug leftovers, JSON reformatting, dep bumps — disposable, not externalized
- **ce_sri_svc ALWAYS Pruebas mode (AMBIENTE=1) on dev/staging** — AMBIENTE=2 fires legally binding invoices
- **ce_sri_prod repo now tracks wip/2026-03-25** from GitHub — old installer scripts abandoned
- **Pre-canned scripts (Playwright, bench console) preferred** — cheaper in credits, more reliable than browser automation

## New Issues Opened
- **#74** — Externalize production customizations from upstream JSON into ce_sri fixtures
- **#75** — Differentiation: seed tabPatch Log with inline-comment format for delete_duplicate_indexes

## Commits This Session
- **ce_sri `ecd4284`** (wip/2026-03-25) — feat: externalize production customizations as fixtures

## Next Session Agenda
1. Fix differentiate.sh to seed patch log (#75) — quick fix, high value
2. Fix returnable app TypeError in `bench migrate` — investigate root cause
3. Add app rsync to Refresh flow in api.py — so fixture updates propagate without manual rsync
4. Browser-verify `forma_de_pago_especificada` on dev01 + dev02 Sales Invoice forms
5. Install Playwright + test run of topology-ops.spec.js
6. Dashboard + translations (Phases 6-7) if time permits
