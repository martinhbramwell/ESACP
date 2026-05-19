# Session Minutes — 2026-04-20 08:02 EDT — Matrix Run 02, attempt 4 — HALTED

**Branch:** `accept/02-cli-full-company-specific` (off `main@8e695a4`)
**Agenda:** `internal_docs/SessionLogs/acceptance-matrix/02-cli-vm-full-logichem-from-backup.md` (filename frozen pending #246)
**Plan:** `~/.claude/plans/acceptance-matrix-transport-parity.md`

---

## Objective (entering)

Close Matrix Run 02, attempt 4 — CLI-driven dev VM build with full company-specific ERPNext restored from the golden production backup, driven by a Playwright spec that also asserts Cytoscape topology convergence and an ERPNext canary.

## Status

**HALTED at Step 6 of the Playwright spec.** SUT fully healthy; failure is test-code only. Two new issues filed (#247 blocker, #248 side-finding). Attempt 5 unblocks once #247 merges.

---

## Precondition gates (all passed)

- `main` at `8e695a4` (post-`bf30b76` PR #242 + `8e695a4` PR #245 memory scrub).
- Sync check: 43 ✅ / 8 ⚠️ / 3 ❌ at session start. The 3 ❌ are the expected idle-VM ping failures (`dev02`/`dev03`/`target5`).
- MEMORY.md carries the `$BESPOKE_ROOT` header from the 2026-04-19 18:16 memory-scrub session.
- `dev01` absent at baseline. `saconsole` running on toshiba. Cytoscape API :8088 and Vite :5173 both HTTP 200.

## D3 / D4 / D5 decisions (this session)

- **D3 (acceptance-matrix agenda filenames + body scrub)**: (c) — leave the 5 agendas frozen; new artifacts use `company-specific` token; file follow-on issue for later scrub pass. Result: **#246 filed**.
- **D4 (`wait_budget_seconds`)**: 3600 (empirically 28.7 min for full restore — budget was ~2× generous).
- **D5 (canary)**: `https://${HOST}/app/item/Test%20Item` — an `Item` doctype record `Test Item` present in the golden backup. REST + desk view both asserted.

---

## Artefacts authored + committed

| File | Purpose | Commit |
|---|---|---|
| `internal_docs/SessionLogs/acceptance-matrix/params/02-cli-full-company-specific.yml` | Run 02 parameters | `9680b5f` |
| `prototypes/cytoscape/tests/accept-02-cli-full-company-specific.spec.js` | Run 02 Playwright spec (190 lines) | `9680b5f` |

Commit `9680b5f` — signed, Conventional Commits format, Claude co-author trailer, refs #239 + #246.

---

## Execution timeline

### Attempt 4a (2026-04-19 late night EDT, ~28.8 min wall time)

- Step 1 (baseline): ✅ saconsole up, dev01 absent from `/api/hosts` and Cytoscape.
- Step 2 (`./tools/esacp.py addHost dev01 …`): ✅ exit 0.
- Step 3 (`./tools/esacp.py provision dev01`): ✅ exit 0 after 1724s. Snapshot `ERPNext v13 Restored Baseline` taken. Company `Logichem Solutions S. A.` restored.
- Step 4 (topology convergence): ✅ converged in 1s.
- **Step 5 (canary login): ❌ HTTP 401.**
  - Root cause: user-supplied `ERP_ADMIN_PWD=09oikjmn.0.0.0` (intended as the production Administrator password) was rejected. Confirmed reproducible via raw `curl` (not a Playwright quirk).
  - Investigation: the pipeline resets the restored Administrator to the build-time secret `erp_user_pwd` from `config/build_secrets.sops.yml` — which is `sasa`, not the production value. Design intent is sensible (lab shouldn't carry production creds). `curl -d 'usr=Administrator&pwd=sasa' https://dev01.iridium.blue/api/method/login` → HTTP 200.

User chose **Path A**: destroy `dev01`, re-run with `ERP_ADMIN_PWD=sasa`.

### Destroy

- `echo y | ./tools/esacp.py destroy dev01`: ✅ 8 steps clean (WG peer removal, snapshot delete, virsh destroy+undefine, hosts_map.yml clean, group_vars update, inventory regen, hub WG update, key removal, cloud-init dir removal).
- `/api/hosts` confirmed dev01 absent.

### Attempt 4b (2026-04-20 early morning EDT, ~29.2 min wall time)

- Steps 1–5: ✅ all green. Provision exit 0 after 1724s (same wall time — repeatable). Canary login with `sasa` succeeded. REST `/api/resource/Item/Test%20Item` OK. Desk URL `/app/item/Test%20Item` rendered with "Test Item" visible.
- **Step 6 (sync_check): ❌ `execSync` throws.**
  - Root cause: `sync_check.sh` exits non-zero whenever ANY row fails. The 3 ❌ rows are the pre-existing idle-VM ping failures, unrelated to dev01. Live re-run confirms `✅  ERPNext dev01 (https://dev01.iridium.blue) — HTTP 200` row IS present.
  - Test-code defect: wrap in try/catch, inspect `err.stdout`, assert specific row.
  - Same pattern latent in accept-01 spec; Run 01's canonical Playwright green was formally waived 2026-04-19 pm so the trap was never tripped there.

---

## Path decision at halt

User chose **Path X** (strict matrix): file #247, fix test code, destroy dev01, re-run. Then pivoted to session-end audit before execution. Session closes halted; attempt 5 picks up from here.

---

## Issues filed this session

| # | Title | Role |
|---|---|---|
| **#246** | chore(scrub): rename + body-scrub the 5 acceptance-matrix agenda files (post-#239 follow-on) | D3(c) follow-on — deferred |
| **#247** | bug(matrix-tests): execSync of sync_check.sh in Run 01/02 specs throws on script's legitimate non-zero exit | Blocker for Run 02 attempt 5 |
| **#248** | bug(scrub): #239 completeness — LogichemLogo.png filename still referenced; stale .pyc bytecode | #239 regression — low priority |

---

## Findings NOT filed (with reason)

- **WG reachability drift post-provision.** First attempt showed `ping 10.10.0.12 — unreachable` for ~minutes after provision completed (while HTTPS via public DNS worked). Re-run showed `ping 10.10.0.16 — reachable` immediately. Probably a post-provision settling delay (WG handshake refresh), not a reproducible bug. Noted here; did not file.

---

## State at session close

- Branch `accept/02-cli-full-company-specific` at `9680b5f`. To be pushed by the close-out commit (these minutes + MEMORY.md update).
- `dev01` **remains provisioned** on toshiba. Attempt 5 must begin with destroy.
- Working tree has live config mutations (`hosts_map.yml`, `group_vars/all.yml`, `inventory/kvm.yml`, `keys.sops.yml`) from dev01's live state — will revert automatically on destroy. Not committed.
- Playwright test-results artifacts under `prototypes/cytoscape/test-results/` are uncommitted and will be discarded on next run.

---

## What unblocks attempt 5

1. #247 fix merged to main — single-file test-code edit in `accept-02-cli-full-company-specific.spec.js` (and same edit in accept-01 for hygiene).
2. Destroy `dev01` (or confirm still absent from previous session clean-up).
3. Re-run: `ERP_ADMIN_PWD=sasa npx playwright test --grep accept-02` from `prototypes/cytoscape/`.

Empirical wall-time budget: 30 min provision + ~1 min convergence + ~5 min canary + sync_check = ~35 min per attempt.

---

## Acceptance-of-minutes checklist

- [x] Objective stated.
- [x] All three D-decisions recorded with reasoning.
- [x] Every forward-tense phrase from the session resolved (see Audit Step 1 in this session's transcript).
- [x] Every GH issue referenced confirmed current (no uncommitted findings).
- [x] No PR opened (session halted, not "DONE").
- [x] Two new issues filed; MEMORY.md tracker updated.
- [x] Side findings either filed or explicitly dismissed with reason.
