# Session Minutes — 2026-04-04 — handleRestore.sh --skip-failing fix

## Objective
Investigate missing commission Custom Fields on dev VMs (sales_partner_supplier, comission_entry_created, commission_paid) visible on production but absent on dev02.

## Completed ✅

- **Root cause identified**: three compounding issues in BaRe/handleRestore.sh
  1. `--skip-failing` (added `ab13be5`, partially reverted `b564c25`) silently swallowed fixture errors
  2. `grep | tail` output filter hid all error messages
  3. Two data issues after production DB restore blocked `bench migrate`:
     - `tabDocField` orphan (`Customer.forma_de_pago_preferida`) from Developer Mode collides with ce_sri fixture → `ValidationError` aborts entire fixture import
     - Frappe v13 `get_file_items()` keeps inline comments from `patches.txt` but `tabPatch Log` stores without → `delete_duplicate_indexes` re-runs and crashes on missing `performance_schema` tables

- **GH #95 opened and closed** — full root cause documented

- **BaRe fix committed** (`45b8775` on main):
  - Removed `--skip-failing` and `grep | tail` filter
  - Added two idempotent SQL data fixes between `bench restore` and `bench migrate`
  - `bench migrate` now runs clean and surfaces errors

- **dev01 verified** — all 18 Sales Invoice Custom Fields present (was 14)

- **Modem issue diagnosed**: toshiba SSH unreachable due to ISP modem AP isolation (TCP connect succeeded but banner exchange timed out). Power-cycling the modem resolved it. WireGuard path (Mighty → saconsole → toshiba virbr0) confirmed as fallback.

## Deferred 🔄

- **dev02 end-to-end test** — destroy + redeploy from UI to verify BaRe fix in full pipeline
- **Latest production backup test** — restore today's backup to confirm no new collisions
- **Customization inventory** — enumerate all differences from stock ERPNext v13
- **Playwright regression suite** — functional + regression tests for v13 → v14 → v15 → v16 upgrade path

## Key Decisions

- handleRestore.sh must be comprehensive and fault-free in all contexts — fixes go INTO BaRe, not as wrapper scripts
- Before upgrading ERPNext: build complete customization inventory + Playwright regression gate
- `gpre_fix_migrate_blockers.py` (ESACP) deleted — fix lives in BaRe where it belongs
