# Agenda — Next Session

**Objective:** Zero-defect build log — continue triage from 2026-04-07-0240 agenda.

---

## Resolved (remove from triage)

- ~~#120 — session_status patch~~ — confirmed gone in Refresh job `71c3dce8` (g1 seeds before G's migrate now)
- ~~#121 — forma_de_pago_preferida fixture collision~~ — fixed via BaRe `7cfe161` + ESACP `34dc6cb`

## Priority

### 1. GH #123 — supervisor group `frappe-bench-web:` not found (exit 7)
Two occurrences in build log (lines 261, 387). Also redis spawn errors (line 44-45). Likely bench-dir symlink (`frappe-bench` ← `frappe-bench-{NICKNAME}`) causing supervisor group name mismatch. Diagnosis: check `supervisorctl status` output vs generated supervisor.conf group names.

### 2. GH #117 + #122 — Service ordering / encryption key mismatch
#117: Social Login restore uses API with stale encryption key (line 219). #122: `before_install` gets 403 (line 353). Both caused by stale `__Auth` entries encrypted with production's key. H4a clears `__Auth` but runs AFTER handleRestore's Social Login attempt. May share root cause — fix ordering.

### 3. GH #116 — ddlViews access denied for erpadm
Line 209: `ERROR 1045 (28000): Access denied for user 'erpadm'@'localhost'`. Views SQL needs root-level DB access but runs as erpadm.

### 4. GH #119 — BKP rsync copies stale backups
Read BACKUP.txt, rsync only named file + BACKUP.txt. Add progress log line.

### 5. Close #120
Verify it's resolved (confirmed in job `71c3dce8`) and close with commit hash reference.

## Notes

- dev02 Refresh verified — errors #1 and #2 gone, errors #3-#6 still present
- BaRe `handleRestore.sh` now delegates to ESACP cleanup scripts between restore and migrate
