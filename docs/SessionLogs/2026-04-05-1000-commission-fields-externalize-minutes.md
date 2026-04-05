# Minutes — 2026-04-05 10:00 — Externalize Commission Fields (#100)

## Objective

Externalize 4 SI commission fields from Developer Mode edits in production's `sales_invoice.json` into Custom Field fixtures, so a clean deploy produces the correct form layout without any local erpnext modifications.

Corresponds to **Session B** from the 2026-04-04-1930 agenda. Issue #100, branch `fix/100-externalize-commission-fields`.

## Completed ✅

### G2 pipeline step added
- Created `tools/vm_scripts/g2_clear_fixture_custom_fields.py` — runs after DB restore, before `bench migrate`
- Deletes ALL fixture-defined Custom Fields from `tabCustom Field` (prevents stale `insert_after` from restored DB)
- Deletes colliding `tabDocField` entries (Developer Mode edits carried in the restored DB)
- Seeds `tabPatch Log` for `delete_duplicate_indexes`
- Re-runs `bench migrate` to reimport fixtures with correct positioning
- Step is generic — handles all fixture Custom Fields across all apps automatically

### dev01 verified end-to-end
- Fresh deploy via Refresh (full pipeline including DB restore + G2 step)
- **18 SI Custom Fields** present: 13 baseline + 4 commission (`sales_partner_supplier`, `comission_entry_created`, `commission_paid`, `break_down`) + `separar`
- Commission section layout matches production
- `apps/erpnext` is **100% stock** — zero local modifications

### Full Developer Mode audit completed
- Compared all 12 production-modified doctype JSONs against stock ERPNext on dev01
- Found **13 Developer Mode field additions across 7 doctypes**
- **12 of 13 covered** by existing fixtures (ce_sri, returnable, route_planner)
- **1 gap**: `Supplier.purchase_taxes_and_charges_template` (Link) — not in any fixture

### Issues and PR
- ✅ PR #101 created (3 commits), merged to main (`37bdc31`)
- ✅ Issue #100 closed automatically via `fixes #100` in commit
- ✅ Issue #102 opened for the Supplier gap — includes full explanation of the G2 approach
- ✅ WG keys synced from verified dev01 redeploy (`316cd45`)

### Commits on branch
1. `bcb8eae` — fix(pipeline): add G2 step to reimport fixture Custom Fields after DB restore
2. `77bf354` — docs(kvm): document G2 step in differentiation pipeline
3. `316cd45` — chore(kvm): sync dev01 WG keys from verified redeploy

## Deferred 🔄

- 🔄 #102: Externalize `Supplier.purchase_taxes_and_charges_template` as Custom Field
- 🔄 #98: Still open — superseded by #100 approach but may need formal closure
- 🔄 ce_sri repo bugs: modules.txt accent + Supplier fixture conflict (need own issue)
- 🔄 erpadm SSH key in differentiate.sh (need own issue)
- 🔄 ce_sri_svc install timing (need own issue)

## Key Decisions

- The G2 step is the permanent solution for fixture/DB-restore conflicts — it clears all fixture Custom Fields then lets `bench migrate` reimport them cleanly
- `apps/erpnext` must remain 100% stock on all dev/staging VMs — all customizations come through fixture imports
- Full audit of production Developer Mode edits is now complete: 12/13 covered, 1 issue queued (#102)

## Action Points

| # | Action | Owner | Target |
|---|--------|-------|--------|
| 1 | Fix #102 — add Supplier tax template to ce_sri fixture | Claude + user | Next session |
| 2 | Close or link #98 — overlaps with completed #100 | User | Next session |
| 3 | Retry SRI PRUEBAS submit on dev01 (Easter downtime cleared?) | Claude + user | 2026-04-07 |

## Notes

- Session terminated abnormally (Ctrl+Z crash, `fg` did not restore). Minutes written in recovery session.
