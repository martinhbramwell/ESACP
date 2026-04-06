# Agenda — Next Sessions (1:1:1 Discipline)

Each session works exactly one issue on its own branch. PR to main at session end.

---

## Session A — Merge PR #106, close #105

PR #106 (`fix/105-dev03-wireguard-spoke`) adds sync_check section 9b (WG hub peer drift detection). Merge, close #105 with hash.

---

## Session B — Pipeline: erpadm SSH key + saconsole hub reorder (need issue)

Two pipeline gaps found during #105 investigation:
1. `erpadm` SSH authorized_keys never deployed — `ssh erpadm@<vm>` from Mighty fails for all VMs
2. Document that manual/ad-hoc deploys must include saconsole WG hub update

### Steps
1. Open issue
2. Add erpadm key deployment to differentiate.sh template in api.py (section A2e or similar)
3. Verify on dev03: `ssh dev03-erp` works after re-running differentiate

---

## Session C — Pipeline: differentiate.sh template vs committed artifacts (need issue)

Per-host `platforms/kvm/{hostname}-differentiate.sh` files are rendered copies of a single template. They accumulate, go stale when template logic changes, and blur the line between source and artifact.

### Steps
1. Open issue
2. Refactor: keep template in repo, render at provision/refresh time, do not commit per-host copies
3. Delete existing committed differentiate scripts
4. Verify Refresh still works (re-renders from template)

---

## Session D — #103: Allow cd + git compound commands without approval prompt

**Branch:** `fix/103-cd-git-permissions`

---

## Session E — Close or link #98

**#98** (externalize 4 commission fields) overlaps with completed **#100**. Decide: close as duplicate, or keep for any remaining scope.

---

## Session F — Retry SRI PRUEBAS on dev01

Error 70 was likely Easter weekend SRI downtime. Retest invoice 001-004-000000074.

---

## Backlog (not yet scheduled)

- #68: split Refresh into fast path (skip G/H DB restore)
- #50: cf-mcp-refresh into repo + setup docs
- Terminal friction: Ctrl+Z recovery + Telegram alerts
- ce_sri repo bugs (modules.txt accent + Supplier fixture)
- Customization inventory (upgrade prep phase 1)
- Playwright regression suite (upgrade prep phase 2)
- Latest production backup verification
