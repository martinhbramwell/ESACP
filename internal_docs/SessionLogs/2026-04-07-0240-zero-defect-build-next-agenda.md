# Agenda — Next Session

**Objective:** Zero-defect build log — triage and fix remaining Deploy/Refresh errors.

---

## Priority

### 1. GH #123 — supervisor group `frappe-bench-web:` not found (exit 7)
Refresh-only. Likely bench-dir symlink (`frappe-bench` ← `frappe-bench-{NICKNAME}`) causing supervisor group name mismatch. Quick diagnosis: check `supervisorctl status` output vs generated supervisor.conf group names.

### 2. GH #117 + #122 — Service ordering in differentiation
Both involve API calls before services are ready. #117: Social Login restore hits stale encryption key. #122: `before_install` gets connection refused (Deploy) or 403 (Refresh). May share a root cause — H4a/H4d ordering relative to bench start.

### 3. GH #120 — frappe v12 patch `delete_duplicate_indexes`
Seed it as already-applied in `g1_seed_patch_log.py`, same pattern as #107.

### 4. GH #121 — route_planner fixture collision (`forma_de_pago_preferida`)
Delete conflicting Custom Fields before migrate, same pattern as #118.

### 5. GH #119 — BKP rsync copies stale backups
Read BACKUP.txt, rsync only named file + BACKUP.txt. Add progress log line.

## Notes

- dev02 is currently deployed and functional (https://dev02.iridium.blue) — snapshot taken
- Branch `fix/107-patch-log-seed-ordering` merged to main — start new branches from main
- Deploy errors: 3 (#120, #121, #122). Refresh errors: 6 (#120, #121, #117+cascade, #123×2)
