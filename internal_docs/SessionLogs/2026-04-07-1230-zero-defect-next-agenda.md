# Agenda — Next Session

**Objective:** Zero-defect build log — continue triage from 2026-04-07-1100 agenda.

---

## Resolved (remove from triage)

- ~~#120 — session_status patch~~ — confirmed gone in Refresh job `71c3dce8`
- ~~#121 — forma_de_pago_preferida fixture collision~~ — fixed via BaRe `7cfe161` + ESACP `34dc6cb`
- ~~#123 — supervisor group not found (exit 7)~~ — fixed via stop.py (`e9e2ce3` + `7aedce8`), PR #125

## Priority

### 1. GH #117 + #122 — Service ordering / encryption key mismatch
#117: Social Login restore uses API with stale encryption key (line 232 in job `e4b6aa3b`). #122: `before_install` gets 403. Both caused by stale `__Auth` entries encrypted with production's key. H4a clears `__Auth` but runs AFTER handleRestore's Social Login attempt. May share root cause — fix ordering.

### 2. GH #116 — ddlViews access denied for erpadm
Line 232 of refresh log `e4b6aa3b`: `ERROR 1045 (28000): Access denied for user 'erpadm'@'localhost'`. Views SQL needs root-level DB access but runs as erpadm.

### 3. GH #119 — BKP rsync copies stale backups
Read BACKUP.txt, rsync only named file + BACKUP.txt. Add progress log line.

### 4. Close #120
Verify it's resolved (confirmed in job `71c3dce8`) and close with commit hash reference.

## Notes

- dev02 Refresh verified end-to-end (job `e4b6aa3b`) — #123 errors gone, #116 and #117 still present
- Next issue should be #117+#122 (encryption key / service ordering) — highest impact on zero-defect goal
