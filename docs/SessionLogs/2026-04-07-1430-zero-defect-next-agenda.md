# Agenda — Next Session

**Objective:** Zero-defect build log — fix service ordering in differentiation pipeline.

---

## Resolved (remove from triage)

- ~~#119 — BKP rsync stale backups~~ — fixed in `b22ba49` (PR #126), confirmed in Refresh job `0dc4d213`
- ~~#120 — session_status Patch Log seeding~~ — confirmed resolved, closed with job ref
- ~~#123 — supervisor group name~~ — fixed in prior session, confirmed still clean

## Priority

### 1. GH #117 + #122 — Service ordering / encryption key mismatch
Root cause confirmed in Refresh job `0dc4d213`:
- **#117**: handleRestore Social Login (line 233) tries API with stale `__Auth` entries encrypted with production's key. H4a clears `__Auth` but runs ~2 minutes later. Fix: move H4a (clear stale secrets) to run BEFORE handleRestore's Social Login step.
- **#122**: H4d `before_install` (line 360) gets `Connection refused` on port 8000. H2b warns "gunicorn did not respond within 60s". Fix: ensure gunicorn is serving before H4d runs.

### 2. GH #116 — ddlViews access denied for erpadm
Line 224: `ERROR 1045 (28000): Access denied for user 'erpadm'@'localhost' (using password: NO)`. The views SQL restoration step requires root-level DB access. Fix: run ddlViews with `--mariadb-root-password` or via a root-privileged script.

### 3. Full Refresh acceptance test
After #116/#117/#122 are fixed, run another Playwright Refresh on dev02 and confirm zero errors in the job log.

## Notes

- Refresh job `0dc4d213` log has 434 lines — full pipeline completed successfully aside from the three known errors above
- All three remaining errors are in the post-restore phase (H-series steps) — the restore itself is clean
