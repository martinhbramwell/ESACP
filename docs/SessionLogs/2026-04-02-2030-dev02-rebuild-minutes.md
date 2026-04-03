# Minutes — 2026-04-02 20:30 — dev02 Rebuild + Jinja2 Discovery

## Objective
Destroy and recreate dev02 end-to-end with zero failures.

## Completed
- ✅ DNS migration committed: `192.168.40.16` → `toshy.iridium.blue` (6 repo files)
- ✅ Re-provision logic added to `/api/provision/erpnext` — existing unprovisioned hosts cleaned up and rebuilt (Step 0)
- ✅ UI fix: skip duplicate node on re-provision (`main.js`)
- ✅ dev02 VM created and differentiation pipeline ran through Step G (DB restore OK)
- ✅ GH #89 opened: Jinja2 template refactor for differentiate.sh generator

## Failed / Blocked
- ❌ dev02 differentiation failed at H4a — three distinct f-string escaping bugs:
  1. Heredoc backtick `\`__Auth\`` mangled by `bench console` stdin chain
  2. `["Administrator"]` quoting collision in `bash -c "..."`
  3. `{"filters": ...}` parsed as Python f-string expression
  4. `apikey.sh` missing double quotes (`KEYS=k:s` instead of `KEYS="k:s"`)
- ❌ Each fix exposed the next bug — tunnel-vision iterating instead of redesigning
- ❌ Chrome browser closed mid-session; not detected — should have run sync_check

## Decisions
- **Jinja2 refactor** (GH #89) is the right fix — eliminates the entire class of escaping bugs
- Codebase reset to known-good: `dev02-differentiate.sh` reverted, api.py H4a template reverted, only re-provision logic kept
- saconsole was running the whole time — Ansible WG updates to saconsole failed during destroy/rebuild cycles (exit code 4, UNREACHABLE). Root cause not diagnosed — sync_check was not run when the failures occurred. dev02/dev03 WG peers likely missing from saconsole's wg0.conf because the Ansible updates never succeeded. Needs investigation next session.

## Learnings Recorded
- `feedback_stop_and_redesign.md` — two occurrences of same bug class = stop, redesign
- `feedback_check_working_environment.md` — surprise issue → run sync_check FIRST
- `feedback_check_latest_agenda.md` — agenda filenames must include datetime (YYYY-MM-DD-HHMM)
