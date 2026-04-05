# Agenda — Next Sessions (1:1:1 Discipline)

Each session works exactly one issue on its own branch. PR to main at session end.

---

## Session A — dev03 WireGuard spoke unreachable (need issue first)

**Priority: HIGH** — dev03 deployed but unreachable via WireGuard mesh.

### Problem
Deploy pipeline Step 9 (Ansible WG spoke) failed because dev03 was not in inventory at that point — the destroy removed it from `hosts_map.yml`/inventory/keys, and the deploy didn't re-add it before the spoke step. The pipeline continued, so ERPNext is running but the VM has no WG tunnel.

### Steps
1. Open issue
2. Diagnose: is dev03 missing from `hosts_map.yml` / `inventory/kvm.yml` / `keys.sops.yml`?
3. Re-add dev03 to all three, regenerate inventory
4. Run Ansible WG spoke for dev03 (or Refresh via topology UI)
5. Verify: `ping 10.10.0.14` from Mighty

### Acceptance
- dev03 reachable via WG mesh (`ping 10.10.0.14`)
- `sync_check.sh` passes all dev03 checks

---

## Session B — #103: Allow cd + git compound commands without approval prompt

**Branch:** `fix/103-cd-git-permissions`

### Steps
1. Add permissions rule in `.claude/settings.local.json` for `cd && git` compound commands
2. Test with `cd /home/hasan/projects/Logichem/ce_sri && git status`
3. Verify no prompt appears for known project directories

### Acceptance
- Compound `cd && git` commands run without approval prompt for repos under `/home/hasan/projects/Logichem/`

---

## Session B — Close or link #98

**#98** (externalize 4 commission fields) overlaps with completed **#100**. Decide: close as duplicate, or keep for any remaining scope.

---

## Session C — Retry SRI PRUEBAS on dev01

Error 70 was likely Easter weekend SRI downtime. Retest invoice 001-004-000000074.

---

## Session D — Terminal friction: Ctrl+Z recovery + Telegram alerts (need issue first)

Two parts of one problem — Claude Code terminal session resilience:

1. **Ctrl+Z muscle memory**: standard text-editor undo fires SIGTSTP, suspends Claude Code, and `fg` often fails to restore.
2. **Telegram alerts**: permission-prompt (action authorization) wait state still unverified for 3-min alert.

### Acceptance
- Ctrl+Z no longer kills a session (prevented or recoverable)
- Telegram alerts verified for all wait states

---

## Session E — ce_sri repo bugs (need issue first)

Open issue for: `modules.txt` accent + Supplier fixture conflict. These block fresh provisions that don't apply manual workarounds.

---

## Session F — erpadm SSH key deployment (need issue first)

Add `hasan_mighty.pub` as authorized_key for erpadm during `differentiate.sh`.

---

## Backlog (not yet scheduled)

- #68: split Refresh into fast path (skip G/H DB restore)
- #50: cf-mcp-refresh into repo + setup docs
- ce_sri_svc install timing (need own issue)
- Customization inventory (upgrade prep phase 1)
- Playwright regression suite (upgrade prep phase 2)
- Latest production backup verification
