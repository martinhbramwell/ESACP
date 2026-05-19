# Agenda — Next Sessions (1:1:1 Discipline)

Each session works exactly one issue on its own branch. PR to main at session end.

---

## Session A — Terminal friction: Ctrl+Z recovery + Telegram alerts (need issue first)

Two parts of one problem — Claude Code terminal session resilience:

1. **Ctrl+Z muscle memory**: standard text-editor undo fires SIGTSTP, suspends Claude Code, and `fg` often fails to restore. A long complex session is lost. Need either: a way to disable/remap Ctrl+Z within Claude Code, a wrapper that traps SIGTSTP, or a reliable recovery path (`claude --continue`).

2. **Telegram alerts not meeting intent**: the Stop hook exists but doesn't cover the user's actual need (details TBD at session start — the current implementation is not what was asked for).

### Acceptance
- Ctrl+Z no longer kills a session (prevented or recoverable)
- Telegram alerts work as the user intends

---

## Session B — #102: Externalize Supplier.purchase_taxes_and_charges_template

**Branch:** `fix/102-supplier-tax-template`

### Steps
1. Read golden `PRODUCTION_20260404/apps/erpnext/.../supplier.json` for `insert_after` position
2. Add field to `ce_sri/fixtures/custom_field.json` (branch `wip/2026-03-25`)
3. Push ce_sri, Refresh a dev VM, verify field appears on Supplier form
4. PR to ESACP if pipeline changes needed

### Acceptance
- Supplier form shows `purchase_taxes_and_charges_template` field from fixture (not Developer Mode)
- 13/13 Developer Mode field additions fully externalized

---

## Session C — Close or link #98

**#98** (externalize 4 commission fields) overlaps with completed **#100**. Decide: close as duplicate, or keep for any remaining scope.

---

## Session D — Retry SRI PRUEBAS on dev01

Error 70 was likely Easter weekend SRI downtime. Retest invoice 001-004-000000074.

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
