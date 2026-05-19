# Minutes — Housekeeping: Hooks & Telegram Alerts (2026-04-06)

**Objective:** Fix two recurring UX pain points — compound command permission prompts and identical Telegram alert messages.

**Agenda source:** `2026-04-05-2000-pipeline-error-fixes-next-agenda.md` (deferred — this session addressed housekeeping instead)

---

## Completed

- ✅ **Compound command auto-approve hook** — `~/.claude/hooks/approve_logichem_bash.py`
  - PreToolUse hook in global `~/.claude/settings.json`
  - Inspects `cd` and `git -C` targets; auto-approves only when all paths resolve under `~/projects/Logichem/`
  - Path traversal (`..`) and relative paths rejected safely
  - Memory saved: `feedback_compound_cmd_hook.md`

- ✅ **Context-aware Telegram alerts** — 4 distinct message types:
  - ✅ "All tasks complete" — Claude finished, no question
  - 🔀 "Decision required" + question snippet — Claude asked something
  - 🔐 "Authorization required" + permission detail — tool approval needed
  - 🤖 "Needs attention" — fallback
  - New: `tools/telegram_stop_classifier.py` (Stop hook → classifies reason)
  - New: `tools/telegram_permission_handler.py` (Notification hook → authorization)
  - Modified: `tools/telegram_delayed_alert.sh` (accepts reason, builds message)
  - Notification hook added to `.claude/settings.local.json`

- ✅ **Gitignore** — added `test-results/` to stop Playwright output from cluttering status

## Deferred

- 🔄 Pipeline error fixes (#107, #108, #109, #110) — next session per agenda
- 🔄 UFW boot-ordering (#111) — separate session
- 🔄 Pre-existing uncommitted infra changes (hosts_map, inventory, wireguard keys, dev02-differentiate) — committed as-is from prior sessions

## Notes

- Both hooks take effect on next session restart
- The compound command hook is global (`~/.claude/settings.json`); Telegram hooks are project-scoped (`.claude/settings.local.json`)
