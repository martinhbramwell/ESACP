# Minutes — 2026-04-04 19:30 — dev03 Deploy + Workflow Discipline

## Objective

Deploy dev03 end-to-end via Cytoscape UI and verify SI Custom Fields.

## Decisions & Resolutions

### dev03 deployed successfully
- ✅ `hosts_map.yml` updated: `vm_role: dev:unspecified` → `dev:erpnext`
- ✅ Dragged ERPNext template into Development zone in Cytoscape UI
- ✅ Form filled: hostname=dev03, nickname=D3IRBL, WG=10.10.0.14, virbr0=192.168.122.22
- ✅ Full pipeline completed (~25 min): WG peer → seed ISO → clone qcow2 → VM create → Ansible → differentiate → snapshot
- ✅ `sync_check.sh`: 47 passed, 4 warnings, 2 failures (both dev01 — switched off, expected)
- ✅ ERPNext live at https://dev03.iridium.blue — HTTP 200
- ✅ Cloudflare DNS already set: dev03.iridium.blue → 10.10.0.14

### "18 Custom Fields" phantom resolved
- ✅ dev03 has **13** SI Custom Fields — matches production exactly
- ✅ dev02 has **17** — 4 extra fields were added manually during prior debugging sessions
- ✅ Production DB (golden backup `PRODUCTION_20260404`) has exactly **13** SI Custom Fields
- ✅ `ce_sri/fixtures/custom_field.json` delivers 12; `separar` comes from DB restore only
- ✅ The 4 "missing" fields (`sales_partner_supplier`, `comission_entry_created`, `commission_paid`, `break_down`) are **Developer Mode edits** in production's `erpnext/accounts/doctype/sales_invoice/sales_invoice.json` — never were Custom Fields
- ✅ `temp/erpnext_local_changes.patch` and `PRODUCTION_20260404/apps/erpnext/` confirm this
- ✅ Root cause of the 3-5 session debugging loop: comparing against a wrong baseline derived from a manually-patched VM, not from production

### 1:1:1 Workflow discipline established
- ✅ **1 issue = 1 branch = 1 session** — hard rule going forward
- ✅ No accumulating uncommitted changes on main
- ✅ Branch per issue: `{type}/{issue#}-{short-desc}`
- ✅ Merge to main only via PR
- ✅ Memory saved: `feedback_issue_branch_session_discipline.md`

### Committed main is stale
- ✅ Identified: committed main has no dev03 entry and stale WG keys for dev02
- ✅ A build from committed main would produce a broken WG mesh
- ✅ GH #97 opened: bring main up to date with running infrastructure
- ✅ GH #98 opened: externalize 4 commission fields as Custom Fields

### Memory corrected
- ✅ All "18 Custom Fields" references updated to "13 (matches production)"
- ✅ `project_si_custom_fields_baseline.md` created with authoritative field list and sources
- ✅ Golden reference recorded: `~/projects/Logichem/PRODUCTION_20260404/`
- ✅ Production upstream modifications entry corrected — notes 4 un-externalized fields

## Deferred Items

- 🔄 #97: commit dev03 + WG keys to main (next session)
- 🔄 #98: externalize 4 commission fields + `separar` to fixtures
- 🔄 ce_sri repo bugs: modules.txt accent + Supplier fixture conflict (need own issue)
- 🔄 erpadm SSH key in differentiate.sh (need own issue)
- 🔄 ce_sri_svc install timing (need own issue)
- 🔄 CLAUDE.md update for 1:1:1 discipline (part of #97 session)

## Action Points

1. Next session: #97 — branch, commit all uncommitted infrastructure changes, PR to main
2. Then: #98 — branch, add 4 commission fields + separar to fixtures, verify on fresh deploy
3. Open separate issues for ce_sri repo bugs, erpadm SSH key, ce_sri_svc timing before their sessions
