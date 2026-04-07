# Minutes — Refresh Secrets SCP Fix (#87)

**Date**: 2026-04-07 00:30–02:40 UTC-4
**Objective**: Fix #87 — Refresh doesn't re-SCP SOPS-decrypted secrets, `.env` gets placeholder values
**Branch**: `fix/107-patch-log-seed-ordering` (continued from prior session)

---

## Decisions

- Extracted `_scp_cesri_secrets()` helper from Deploy Step 10 inline code in `tools/api.py`
- Helper called from **both** Deploy and Refresh — SOPS decrypt happens on controller (age key not on VM)
- Fixed pre-existing `controller_pubkey_path` NameError in Deploy Step 10 (variable was used without being defined in scope)
- Bumped BKP rsync timeout from 300s → 600s (510MB over ProxyJump double-hop)

## Acceptance Tests

1. **Deploy path**: Destroy+Deploy on dev02 — `[OK] 3 ce_sri secret files → /tmp/`, `.env` confirmed with real SMTP credentials ✅
2. **Refresh path**: Deleted `ce_sri_parms.json` on VM, ran Refresh — secrets re-delivered, `.env` regenerated with real values ✅

## Issues Opened

- **#119** — BKP rsync copies stale backups + no progress feedback (510MB, two backups where only one is current)
- **#120** — frappe v12 `delete_duplicate_indexes` patch fails on restored v13 DB (session_status table missing)
- **#121** — route_planner fixture sync collision (`forma_de_pago_preferida` already exists in Customer)
- **#122** — H4d ce_sri `before_install` fails — bench not running yet (connection refused in Deploy, 403 in Refresh)
- **#123** — `bench restart` fails — supervisor group `frappe-bench-web:` not found (exit 7, Refresh only)

## Issues Closed

- **#87** — Refresh secrets SCP fix — commit `43b1e4a`, merged to main as `fb3e10c`

## Observations

- Deploy has 3 build-log errors (#120, #121, #122)
- Refresh has 6 build-log errors (#120, #121, #117 encryption key + cascade 403, #123 supervisor ×2)
- Zero-defect build log not yet achieved — 5 new issues filed to track remaining errors
- `controller_pubkey_path` bug was latent — only surfaced when Deploy actually ran Step 10 (previous deploys may have succeeded due to variable leaking from a prior function call in the same process)

## Artifacts

- Commit: `43b1e4a` on branch `fix/107-patch-log-seed-ordering`
- Merge: `fb3e10c` on main
- Branch pushed and merged

## Action Points

- [ ] Next session: triage #119–#123 for zero-defect build log
- [ ] #117 + #122 may share a root cause (service ordering in differentiation pipeline)
- [ ] #123 likely related to bench-dir symlink + supervisor group naming
- [ ] #119 is quick win — read BACKUP.txt, copy only named file
