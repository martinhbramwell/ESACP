# Session Minutes — Matrix Run 06 UI pseudo-wizard — HALTED at wizard replay (#267 filed)

**Date:** 2026-04-21 ~09:15–10:33 EDT
**Branch:** `accept/06-ui-pseudo-wizard` (scaffold pushed at `b1a20f2`; no PR — halted)
**Issues opened:** #267 (blocker), #268 (latent)
**Issues commented:** #256 (cross-reference to #267)
**Issues closed:** none

## Objective

Execute Acceptance Matrix Run 06 — UI transport, pseudo-company wizard variant — producing backup B06 with canary-facts parity to B03 (Run 03 partner).

## Outcome — HALTED

Run 06 attempt 1 failed at wizard replay. dev01 destroyed cleanly; no B06 artefact produced. Two GitHub issues filed; scaffold branch preserved for attempt 2 once #267 is resolved in a dedicated session.

## Session narrative

### Opening — clean start from Run 05 residue

Working tree held Run 05 live-state drift (same pattern seen previously): new `wg_pubkey_dev01`, `vm_role: dev:unspecified` (UI-forced — #235), and SOPS ciphertext rotation. Discussed origin of each type of drift with the user; selected Option A — `git restore` the three files, branch Run 06 from clean `main @ e3808a1`.

### Scaffold commit

Authored:
- `internal_docs/SessionLogs/acceptance-matrix/params/06-ui-pseudo-wizard.yml` — params file, parity-twinned to Run 03 (same wizard recording `pseudo-co-wizard.spec.js`, same company facts).
- `prototypes/cytoscape/tests/accept-06-ui-pseudo-wizard.spec.js` — UI-transport spec. Drag `tpl-erpnext-generic` into Dev zone, select wizard_mode=replay, waitForJob, canary verbatim from accept-03 Step 5, B06 artefact check mirroring B03.

Design decisions confirmed with user before commit:
1. Reuse `pseudo-co-wizard.spec.js` verbatim (Run 03 partner).
2. `vm_role: dev:unspecified` is the UI-forced contract — acceptance does not assert vm_role.
3. B06 artefact is the new `.tgz` in `platforms/kvm/golden_backups/` (same carve-out as B03, predates the agenda's `.sql.gz` prescription).
4. Canary = Run 03 verbatim (Company REST + `get_count=1`).
5. Step 7 `sync_check` assertion — #247 regression guard.

Committed + GPG-signed as `b1a20f2` `test(accept-06): scaffold UI pseudo-wizard spec + params`; pushed to `accept/06-ui-pseudo-wizard`.

### Live execution — attempt 1

User confirmed both servers up: `./doCytoscape.sh` → uvicorn :8088 (HTTP 200), `./doVite.sh` → Vite :5173 (HTTP 200). Headless mode selected.

Spec launched in background as `byecu2382`. Progress captured via two scheduled wake-ups:

| T+ | Observation |
|---|---|
| 0:00 | Spec start. |
| 0:30 | Step 0 self-check OK. Step 1 destroy-as-precondition complete (golden_backups baseline: 3). Step 2 drag-deploy submitted; provision job `9c821e47` running (budget 3000s). |
| 10:36 | Job status transitioned to `error`. Pipeline stages 1-9 complete; wizard replay timed out at Industry-page Manufacturing checkbox. |
| 29:00 | Wake-up #2 — discovered terminal failure via `/api/jobs/9c821e47`. `waitForJob()` had continued polling because it only recognises `'done'` and `'failed'` — not `'error'` (→ #268). Test would have run ~20 more minutes before hitting its own 3000s budget. |

### Failure diagnosis

Job log at `13:36:18 UTC` enters wizard replay. Subsequent Playwright `TimeoutError` at `pw-replay-1776778578319.cjs:43:63` (`locator.check: Timeout 30000ms exceeded`) on `getByRole('checkbox', { name: 'Manufacturing' })`. Interception sequence:

1. Retries 1-3 (20-100ms): `<div class="modal-backdrop fade show">` intercepts — backdrop-only, no full modal yet.
2. Retries 4+ (~60 retries × 500ms): full `<div tabindex="-1" aria-modal="true" class="modal fade show">` intercepts.

The recording's guard (lines 35-42, added in PR #257 for issue #256) runs once before the `.check()` call and looks for `.modal.fade.show`. At the moment the guard fires, the modal hasn't materialised yet — so the guard passes. The modal then appears during Playwright's built-in click retry, which doesn't dismiss modals. The guard pattern addresses the pre-click race but not the during-click race.

Run 03 passes on the same recording because Run 03 hasn't hit this particular timing window yet — it is a latent flake there, not an absent one.

### Halt protocol executed

1. **Killed background spec** (`byecu2382`) + orphan chromium — 0 processes remaining.
2. **Destroyed dev01** via `./tools/esacp.py destroy dev01` — 8-step teardown clean: live WG peer removed, 2 snapshots deleted, virsh destroy+undefine, `hosts_map.yml` / `group_vars/all.yml` / `keys.sops.yml` scrubbed, inventory regenerated, hub wg0.conf reapplied.
3. **Filed #267** (blocker): wizard-replay Manufacturing-checkbox modal race, full evidence + fix candidates (force-click / DOM click / retry loop) + acceptance criteria.
4. **Filed #268** (latent): `helpers.js:waitForJob()` does not recognise `status='error'` as terminal; burns test budget after job death.
5. **Cross-referenced #256** with comment linking #267 — the fix landed there (`c8e289d` / PR #257) proved incomplete.
6. **Restored post-destroy residue** (`ansible/group_vars/all.yml`, `ansible/inventory/kvm.yml`, `config/wireguard/keys.sops.yml`, `hosts_map.yml`) — working tree clean on `accept/06-ui-pseudo-wizard`.

### Sync-check state

Post-destroy spot-check: wg0 healthy, hub has 4 WG peers (correct — dev01 removed from 5). Full sync_check not re-run this session; state matches pre-Run-06.

## State handed to next session

- Branch `accept/06-ui-pseudo-wizard @ b1a20f2` pushed; no PR. Scaffold (params + spec) is correct as-is; attempt 2 reuses it verbatim after #267 fix lands on a separate branch.
- dev01 absent from toshiba; hub peer count 4; inventory reflects 4 spokes.
- #267 blocks Run 06 attempt 2. Fix must land on its own branch per 1:1:1 discipline — not on `accept/06-ui-pseudo-wizard`.
- #268 latent across all acceptance specs using `waitForJob`; lower priority; should land before next run that could hit error-path.

## Reminders to user

- **Untracked files in project root**: `doCytoscape.sh`, `doVite.sh` appeared as untracked during the session (user-created helpers; mtime Apr 21 09:21 / 09:23). Not part of Run 06 scope. Decide whether to commit, gitignore, or leave untracked.
- **Order-of-operations for next session**: pick #267 first (blocker). Attempt 2 of Run 06 only after #267 merges. Consider folding #268 into the same fix branch if scope stays small, or file as a follow-on.
- **Run 03 latent regression**: after #267 fix lands, re-running Run 03's spec against the updated recording is a cheap parity check — the fix should be transparent to Run 03's passing path.
- **Watch-list for Run 06 attempt 2**: #250 (company-logo [SKIP]) was listed as watch-list for this run but never reached — wizard crashed before provisioning completed. Carry to attempt 2.

## File trail

- Scaffold commit: `b1a20f2` on `accept/06-ui-pseudo-wizard`
- Issue #267: https://github.com/martinhbramwell/ESACP/issues/267
- Issue #268: https://github.com/martinhbramwell/ESACP/issues/268
- #256 cross-ref comment: https://github.com/martinhbramwell/ESACP/issues/256#issuecomment-4289370104
- Failed job log: captured in `/api/jobs/9c821e47` (ephemeral — pipeline job store); key excerpt reproduced in #267 body.
