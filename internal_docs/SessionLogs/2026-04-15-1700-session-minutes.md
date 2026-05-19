# Session Minutes — 2026-04-15 17:00

**Objective:** Fix #180 — Generic provision snapshot naming

**Branch:** `fix/180-snapshot-naming` (merged to main via PR #183)

---

## Completed

### Step 1: Fix snapshot naming (#180)
- Root cause: `provision_generic.py` named its final snapshot "ERPNext v13 Generic — Wizard Ready" — the verify logic and Cytoscape UI check for `"Baseline"` substring to determine provisioned status
- Fix: renamed to "ERPNext v13 Generic Baseline" (one-line change)
- Verified: `verify.py:88` uses `"Baseline" in r.stdout` — new name matches
- Verified: `/api/hosts` shows target5 `provisioned=True`

### Step 2: PR and merge
- PR #183 created and merged to main
- Issue #180 closed automatically (commit `f5422e4`, merge `889a286`)

## Open Issues (10)

| Priority | Issue | Title |
|---|---|---|
| Bug | #178 | SSH config for saconsole — unroutable hostname |
| Bug | #179 | Ansible hub_key undefined at parse time |
| Enhancement | #181 | Parameterise Playwright recordings |
| Infra | #50 | cf-mcp-refresh not in repo/docs |
| Infra | #153 | Register Google OAuth redirect URIs for staging |
| Infra | #138 | saconsole phone-home agent |
| Decision | #48 | Registrar credentials backup |
| Decision | #65 | Auth architecture for control plane |
| Nice-to-have | #156 | saconsole on recycled Android tablet |
| Nice-to-have | #157 | WireGuard self-enrollment via staging slave |

## Not Done
- Nothing deferred — objective fully completed
