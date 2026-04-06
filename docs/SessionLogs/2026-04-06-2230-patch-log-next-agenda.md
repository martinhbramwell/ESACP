# Agenda — Next Session

**Objective:** Continue pipeline error fixes from 2026-04-06-1700 agenda.

---

## Priority

### 1. Full rebuild verification for #107
Run Destroy+Deploy on dev02 to confirm `g1_seed_patch_log.py` works end-to-end from a clean state. Merge PR if passes, close #107.

### 2. GH #117 — Social Login restore runs before H4a clears stale __Auth
Encryption key mismatch causes API failure during handleRestore. Fix ordering.

### 3. GH #116 — DB views restoration fails silently (access denied)
Views restoration runs mysql without credentials. Supply MariaDB root password.

### 4. GH #113 — Topology UI doesn't show VM up/down state
Enhancement — separate session.

## Notes

- `.env` placeholder values observed during Refresh — investigate whether `ce_sri_parms.sops.json` has real SMTP secrets or if they need adding
- G's internal errors (handleRestore.sh) are third-party BaRe code — non-fatal but noisy
