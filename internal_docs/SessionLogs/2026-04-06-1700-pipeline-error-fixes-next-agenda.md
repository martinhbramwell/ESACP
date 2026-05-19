# Agenda — Pipeline Error Fixes (continued)

**Objective:** Continue fixing differentiation pipeline errors. Each issue is a 1:1:1 session.

---

## Issues to Address (priority order)

### 1. GH #108 — G2 Custom Field cleanup misses renamed fields
**Why first:** Most impactful — causes `bench migrate` to crash during fixture import. Silent data integrity risk.
**Fix:** Add fieldname-based DELETE alongside existing name-based delete in `g2_clear_fixture_custom_fields.py`.
**Verify:** Rebuild dev02, confirm zero `ValidationError` in migrate output.

### 2. GH #107 — Patch Log seeding runs after first bench migrate
**Why second:** Causes noisy `ProgrammingError` in Step G output. Benign but violates zero-error policy.
**Fix:** New `g1_seed_patch_log.py` + Step G1 in differentiate template (between G-pre and G).
**Verify:** Rebuild, confirm no `ProgrammingError` in Step G output.

### 3. GH #117 — Social Login restore runs before H4a clears stale __Auth
**Why third:** Encryption key mismatch causes API failure during handleRestore. Ordering issue.
**Fix:** Move Social Login step to run after H4a, or remove from handleRestore and handle post-H4a.

### 4. GH #116 — DB views restoration fails silently (access denied)
**Why fourth:** Views restoration runs mysql without credentials. Silent failure.
**Fix:** Supply MariaDB root password to views restoration command; fail visibly on error.

### 5. GH #113 — Topology UI doesn't show VM up/down state
**Separate session:** Enhancement — poll `/api/health/{host}` or `virsh domstate` and style nodes.

## Notes

- Backup updated to `20260404_162416-erp_logichem_solutions.tgz` — next provision/rebuild uses fresh data
- `config/ce_sri_parms.sops.json` now has real secrets — .env generation should produce correct values on next rebuild
- Refresh endpoint now works end-to-end — use it to verify fixes without full destroy+deploy
