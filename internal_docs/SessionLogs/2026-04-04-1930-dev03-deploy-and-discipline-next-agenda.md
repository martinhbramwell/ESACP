# Agenda — Upcoming Sessions (1:1:1 Discipline)

Each session works exactly one issue on its own branch. PR to main at session end.

---

## Session A — #97: Bring main up to date with running infrastructure

**Branch:** `chore/97-sync-main-with-running-infra`

### Pre-flight
1. Run `sync_check.sh`
2. Verify dev02 and dev03 WG connectivity

### Steps
1. Create branch from main
2. Stage and commit all 5 uncommitted files:
   - `hosts_map.yml` (dev03 entry + dev:erpnext)
   - `ansible/group_vars/all.yml` (dev03 pubkey + updated dev02 pubkey)
   - `ansible/inventory/kvm.yml` (dev03 added)
   - `config/wireguard/keys.sops.yml` (dev03 keys + re-encrypted)
   - `platforms/kvm/dev03-differentiate.sh` (rendered style)
3. Update CLAUDE.md: add dev03 to architecture table, add 1:1:1 workflow rules
4. Verify: `sync_check.sh` still passes
5. PR to main with `fixes #97`
6. Merge, confirm clean working tree on main

### Acceptance
- `git status` on main is clean
- `sync_check.sh` passes for dev02 + dev03

---

## Session B — #98: Externalize 4 commission fields as Custom Fields

**Branch:** `fix/98-externalize-commission-fields`

### Pre-flight
1. Read `project_si_custom_fields_baseline.md` for field definitions
2. Read golden `PRODUCTION_20260404/apps/erpnext/.../sales_invoice.json` for insert_after positioning

### Steps
1. Create branch from main
2. Add 4 fields to `returnable/fixtures/custom_field.json` (in the returnable repo, branch `wip/2026-03-31`):
   - `sales_partner_supplier`, `comission_entry_created`, `commission_paid`, `break_down`
   - With correct `insert_after` values matching production form layout
3. Add `separar` to `ce_sri/fixtures/custom_field.json` (in ce_sri repo, branch `wip/2026-03-25`)
4. Deploy a fresh dev VM (destroy + redeploy dev03 via UI)
5. Verify: 17 SI Custom Fields present (13 + 4 new) + separar
6. Compare Commission section layout against production screenshot
7. PR to each repo, merge

### Acceptance
- Clean deploy produces 17 SI Custom Fields automatically
- Commission section matches production layout

---

## Session C — ce_sri repo bugs (need issue first)

**Open issue before session for:** modules.txt accent + Supplier fixture conflict (currently fixed manually on VMs, not committed to repo). These block any fresh provision that doesn't apply manual workarounds.

---

## Session D — erpadm SSH key deployment (need issue first)

**Open issue before session for:** add `hasan_mighty.pub` as authorized_key for erpadm during differentiate.sh, so `dev0X-erp` SSH aliases work on fresh provisions without fallback.

---

## Session E — ce_sri_svc install timing (need issue first)

**Open issue before session for:** ERPNext must be running before `install.py`; may need service restart between differentiate steps F and G.

---

## Backlog (not yet scheduled)

- #68: split Refresh into fast path (skip G/H DB restore)
- #50: cf-mcp-refresh into repo + setup docs
- Customization inventory (upgrade prep phase 1)
- Playwright regression suite (upgrade prep phase 2)
- Latest production backup verification
