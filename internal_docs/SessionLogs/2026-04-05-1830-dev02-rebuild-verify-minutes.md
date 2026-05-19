# Minutes — dev02 Full Rebuild + Supplier Field Verification

**Date**: 2026-04-05 18:30–19:30 UTC  
**Objective**: Verify that the `insert_after: tax_id` fixture fix (ce_sri `a5c776e`) survives a clean pipeline rebuild of dev02.

---

## Actions Taken

1. ✅ **Sync check** — 51/51 passed at session start
2. ✅ **Destroy dev02** via Playwright (`npx playwright test --grep "Destroy"`) — job completed
3. ✅ **Verify purge** — VM removed from virsh, disk images deleted, WG peer removed from saconsole hub (3 peers)
4. ✅ **Deploy dev02** via Playwright (`npx playwright test --grep "provisions"`) — pipeline completed in ~16 min
5. ✅ **ERPNext live** — HTTP 200 at https://dev02.iridium.blue
6. ✅ **Supplier field verified** — `purchase_taxes_and_charges_template` with `insert_after: tax_id` present
7. ✅ **18 SI Custom Fields** — matches production baseline
8. ✅ **49 total Custom Fields** across all doctypes
9. ✅ **Final sync check** — 51/51 passed (before toshiba reboot)

## Build Log Errors Reviewed

User reviewed the full differentiation log and identified errors requiring explanation:

### Differentiation Pipeline Errors

| # | Error | Root Cause | Issue |
|---|---|---|---|
| 1 | `session_status` table doesn't exist during `bench migrate` | Patch Log seeding in G2 runs after first migrate in G | #107 |
| 2 | `forma_de_pago_preferida already exists in Customer` | G2 deletes Custom Fields by fixture `name` only; production DB may use different auto-generated name | #108 |
| 3 | `Connection refused` on port 8000 during ce_sri install | No readiness poll between `bench restart` (H2) and API check (H4d) | #109 |

### Claude Code Session Errors

| # | Error | Root Cause |
|---|---|---|
| 1 | `Permission denied (publickey)` for erpadm | Fresh provision lacks erpadm authorized_keys → #110 |
| 2 | Bash syntax error in nested SSH command | Violated "remote script pattern" rule — inlined Python over SSH |
| 3 | `IncorrectSitePath` running frappe.init | `sudo -u erpadm` resets cwd; resolved via `bench execute` |
| 4 | `sync_check.sh: No such file or directory` + SSH stalls | Lost cwd after Playwright step; multiple background SSH tasks exhausted connections |

### Investigation Finding — Diff #2 Root Cause

`forma_de_pago_preferida` belongs to **ce_sri** (confirmed in fixture JSON), NOT route_planner. The "Updating DocTypes for route_planner" in the error trace is just a progress bar from an earlier doctype sync — the actual crash is in `sync_fixtures()`. G2's `DELETE FROM tabCustom Field WHERE name IN (...)` uses the fixture `name` value, but the production DB may store the same field with a different auto-generated name. Fix: also delete by `(dt, fieldname)`.

## Incidents

- **toshiba CPU saturation**: 4 VMs × 4GB on 16GB host caused CPU saturation during rebuild. Toshiba became unresponsive.
- **UFW boot-ordering bug**: After toshiba reboot, inbound SSH blocked despite sshd running. Fix: `sudo ufw disable && sudo ufw enable`. Tracked as #111.
- **toshiba has 16GB RAM, not 32GB**: 4 VMs at 4GB each = 100% physical RAM allocated. Policy going forward: only saconsole + 1 dev VM at a time.

## Issues Opened

- [#107](https://github.com/martinhbramwell/ESACP/issues/107) — Patch Log seeding too late (bug)
- [#108](https://github.com/martinhbramwell/ESACP/issues/108) — G2 Custom Field cleanup misses renamed fields (bug)
- [#109](https://github.com/martinhbramwell/ESACP/issues/109) — API check before gunicorn ready (bug)
- [#110](https://github.com/martinhbramwell/ESACP/issues/110) — Deploy erpadm SSH authorized_keys (enhancement)
- [#111](https://github.com/martinhbramwell/ESACP/issues/111) — UFW blocks SSH after toshiba reboot (bug)

## Decisions

- **1 VM at a time** on toshiba (saconsole + 1 dev VM). Shut down idle VMs before rebuilds.
- **User wants 100% error-free builds** — all three pipeline errors must be fixed, not tolerated.
- dev01 and dev03 shut down at session end; dev02 + saconsole running.

## Deferred

- All five issues (#107–#111) deferred to dedicated 1:1:1 sessions per next agenda.
