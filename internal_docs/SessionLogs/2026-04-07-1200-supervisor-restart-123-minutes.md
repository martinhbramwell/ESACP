# Session Minutes — 2026-04-07 12:00 UTC

**Objective:** Fix GH #123 — `bench restart` fails with exit 7 (supervisor group not found)

**Branch:** `fix/123-supervisor-group-name`
**PR:** #125

---

## Decisions

- ✅ Root cause identified: stale honcho or prior supervisor-managed processes hold bench ports (redis 13000/11000, socketio 9000, gunicorn 8000) → `EADDRINUSE` spawn error → `supervisorctl restart` exit 7
- ✅ Initial hypothesis (symlink causing bench name mismatch) disproved — Python's `os.getcwd()` resolves symlinks, so `get_bench_name()` returns `frappe-bench` regardless
- ✅ Fix: run production `stop.py` (already in repo at `platforms/kvm/stop.py`) before each `bench restart` — graceful Redis SHUTDOWN + `fuser -k` fallback
- ✅ `stop.py` deployed to `$BENCH_DIR` early (A3) because `/tmp/rendered/` is owned by SSH user `you`, not readable by `erpadm`
- ✅ Removed `|| true` from `bench restart`, `supervisorctl restart`, and `nginx reload` — errors must surface for zero-defect build log
- ✅ L0 step retained (re-deploys stop.py later — idempotent, harmless)

## Changes

| File | Change |
|---|---|
| `tools/api.py` | A3: deploy+run stop.py before supervisor setup; H2+H4f: run stop.py before bench restart; removed `\|\| true` |
| `platforms/kvm/dev0{1,2,3}-differentiate.sh` | Same three changes in each committed artifact |

## Acceptance Test

- Full Refresh on dev02 (job `e4b6aa3b`) — status: `done`
- A3: stop.py freed all ports, supervisor started cleanly
- H2: stop.py + `bench restart` — exit 0, all groups restarted
- H4f: stop.py + `bench restart` — exit 0, all groups restarted, nginx reload OK
- Zero `exit status 7` errors in log

## Commits

- `e9e2ce3` — fix(kvm): run stop.py before bench restart to prevent EADDRINUSE, fixes #123
- `7aedce8` — fix(kvm): deploy stop.py to bench dir before running as erpadm

## Remaining red flags (from zero-defect triage)

- #116 — ddlViews access denied for erpadm (line 232 in refresh log)
- #117 + #122 — encryption key mismatch / service ordering
- #119 — BKP rsync copies stale backups
- #120 — close (already verified resolved)

## Deferred

- Nothing deferred — single-issue session completed cleanly
