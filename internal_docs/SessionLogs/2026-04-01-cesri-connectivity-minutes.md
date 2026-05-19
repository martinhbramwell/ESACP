# Session Minutes — 2026-04-01 ce_sri Connectivity & Pipeline Fixes

## Objective
Get SRI electronic voucher upload working on dev01 in PRUEBAS mode.

## Completed

- ✅ **Fixed `ce_sri_url` missing from `site_config.json`** — `bench set-config` on dev01
- ✅ **Fixed API secret encryption key mismatch** — regenerated via `bench execute frappe.core.doctype.user.user.generate_keys`; pipeline now clears ALL `__Auth` entries post-restore (H4a)
- ✅ **Fixed P12 signing cert missing + wrong path** — SCP'd cert, patched `SIGNING_CERTIFICATE_PATH`
- ✅ **Fixed Social Login Key decrypt errors** — cleared stale google/facebook `__Auth` entries
- ✅ **Rewrote pipeline to use `install.py`'s `before_install()`** — replaces piecemeal bash (GH #82)
  - H4a: clear `__Auth` + regen API key
  - H4b: place secrets (P12, ce_sri_parms.json, logo)
  - H4c: `bench setup nginx`
  - H4d: `bench execute ce_sri.install.before_install`
  - H4e: `UPDATE_SRI_SERVICE_PARAMETERS.py` generates .env
  - H4f: restart services
- ✅ **Fixed `testNodeJSService()`** — check port not supervisorctl (erpadm has no sudo)
- ✅ **Created `UPDATE_SRI_SERVICE_PARAMETERS.py`** in ce_sri_svc — single script for .env generation from template + ce_sri_parms.json
- ✅ **Updated .env template** — added CERT_FRIENDLY, NICKNAME, BANCO, CUENTA_BANCARIA, IMPUESTO_CODIGO_PORCENTAJE, email mode blocks
- ✅ **Added SOPS/age encryption** for ce_sri_parms.json in ce_sri repo
- ✅ **SRI submit reached PRUEBAS endpoint** — got DEVUELTA error 70 (SRI infrastructure, Easter weekend)

## Commits

| Repo | Commit | Description |
|------|--------|-------------|
| ce_sri | `4b1e164` | testNodeJSService checks supervisor before start/kill |
| ce_sri | `ec3eb2d` | Check port instead of supervisorctl |
| ce_sri | `59c4e62` | Template: add missing .env fields |
| ce_sri | `e440139` | SOPS/age encryption for ce_sri_parms.json |
| ce_sri_svc | `cc53ae6` | UPDATE_SRI_SERVICE_PARAMETERS.py + how-to |
| ESACP | `c43dbfa` | Run install.py post-restore — fixes #82 |
| ESACP | `3877b81` | Use UPDATE_SRI_SERVICE_PARAMETERS.py in pipeline |

## Issues
- GH #82: created and closed (c43dbfa)
- Secrets exposed in this session log: cert pwd, SMTP app pwd, API tokens. Rotate after Easter.

## Deferred
- 🔄 Retry SRI submit after Easter weekend
- 🔄 SOPS encrypted parms still has placeholder secrets — edit in real values
- 🔄 Agenda items #2, #3 from previous session (modules.txt accent fix, fixture import conflict)
- 🔄 Pipeline end-to-end test: destroy + re-provision dev02
- 🔄 GH #79, #68, #50, #37 (carried business)
