# Session Minutes — Matrix Run 07 GREEN + Matrix Close-out

**Date:** 2026-04-21 ~13:00–14:20 EDT
**Branch:** `accept/07-ui-pseudo-restore` (`9277f0a`) → merged into main (`5350641`)
**Issues opened:** none
**PR:** #273 — merged `2026-04-21T18:19:15Z` via GPG-signed merge commit `5350641`

## Objective

Execute Matrix Run 07 — UI-transport pseudo-company restore from B06, parity partner to Run 04. Close the 7-run matrix: branch, PR, merge, then write `docs/SessionLogs/acceptance-matrix/MATRIX-CLOSEOUT.md` and update `MEMORY.md`.

## Outcome

**GREEN — 1 passed (12.0m)** on attempt 1. Matrix 7/7 complete. Close-out written, MEMORY.md compacted + flagged foundation-solid.

- Provision job `e8544650` finished after 638s (10m 38s)
- UI convergence: 1s
- Canary matches Run 04 byte-for-byte: `Pseudo-Co` / `PSC` / `CAD` / `Canada` + `Company.count=1`
- Golden-backups delta = 0 (restore did not capture a new backup — parity with Run 04 Step 6)
- B06 still present post-restore (restore did not consume its source)
- Final sync_check: 45 ✅ / 12 ⚠️ / 0 ❌

## Session narrative

### Session open — context load

Loaded MEMORY.md + latest minutes (`2026-04-21-1256-session-minutes.md`, Run 06 GREEN). `sync_check.sh` at open: **45 ✅ / 12 ⚠️ / 0 ❌** — clean open, no carry-over failures; dev01 running from Run 06 exit state (Pseudo-Co wizard-restored). 29 open issues; no issue-fix in scope — Run 07 is matrix-plan work.

PR verification per `feedback_pr_merge_before_session_close`: #272 `mergedAt=2026-04-21T17:12:28Z` — real.

User acknowledged objective.

### Prereq check — entry state matches agenda

- dev01 present in `/api/hosts`: `provisioned=True, vm_state=running, vm_role=dev:unspecified` — Run 06 exit state.
- B06 present: `platforms/kvm/golden_backups/20260421_114520-dev01_iridium_blue.tgz` (1358769 bytes).
- Vite :5173 and Cytoscape API :8088 both 200.

No destroy-guard concern from #271: dev01 is fully provisioned, so the Destroy button renders and the spec's `if (existing)` branch will correctly fire.

### Authoring

Wrote `params/07-ui-pseudo-restore.yml` + `tests/accept-07-ui-pseudo-restore.spec.js`. Structure:

- Step 0 self-check: 0a sops decrypt, 0b sync_check parseability (#247 guard), 0c API, 0d Vite, 0e toshiba SSH, 0f B06 file exists.
- Step 1 destroy-as-precondition: verbatim from accept-06 (UI right-click → Destroy → waitForJob → `/api/hosts` absence assertion → `page.reload()` to rehydrate stale Cytoscape graph per #249).
- Step 2 drag-deploy: `tpl-erpnext-generic` → fill form → `wizard_mode=existing` radio → wait for `#wizard-existing-select` to un-hide → select B06 from `#f-wizard-backup` dropdown → submit.
- Step 3 job wait: `waitForJob(jobId, wait_budget_seconds * 1000)`.
- Step 4 topology convergence: same shape as accept-04/05/06.
- Step 5 canary: verbatim from accept-04 Step 5 (Pseudo-Co + abbr + currency + country + `get_count == 1`).
- Step 6 backup delta: verbatim from accept-04 Step 6 (delta == 0, B06 still present).
- Step 7 sync_check: ERPNext dev01 row asserted ✅.

`node --check` clean; committed nothing until the run was green.

### Attempt 1 — GREEN end-to-end

Launched spec. Progression:

| Step | Duration | Outcome |
|---|---|---|
| 0 — self-check | instant | ✓ all 6 probes pass |
| 1 — destroy dev01 (provisioned, Destroy button visible) | ~1m | ✓ UI right-click → Destroy → confirm → job completes → ABSENT from /api/hosts → `page.reload()` |
| 2 — drag tpl-erpnext-generic → Dev zone | instant | ✓ dialog opens, form populated with params, wizard_mode=existing + B06 selected |
| 3 — provision job (`e8544650`) | **638s** (10m 38s) | ✓ `waitForJob` returned cleanly |
| 4 — UI convergence | **1s** | ✓ `/api/hosts` shows dev01 provisioned+running, Cytoscape node present |
| 5 — Pseudo-Co canary | ~3s | ✓ Administrator login, REST `Company/Pseudo-Co` (abbr=PSC, CAD, Canada), Company.count=1 |
| 6 — backup delta | instant | ✓ delta == 0, B06 still present |
| 7 — sync_check | ~5s | ✓ `✅ ERPNext dev01 (https://dev01.iridium.blue)` present |

Total elapsed: 12.0m (`1 passed (12.0m)`, exit 0).

### Commit → PR → merge

Commit contents (avoiding runtime drift, consistent with Run 02–06 PRs):
- `docs/SessionLogs/acceptance-matrix/params/07-ui-pseudo-restore.yml`
- `prototypes/cytoscape/tests/accept-07-ui-pseudo-restore.spec.js`

**Not committed** (runtime drift identical to prior matrix PRs):
- `ansible/group_vars/all.yml` (+1/-1)
- `config/wireguard/keys.sops.yml` (+24/-24)
- `hosts_map.yml` (+1/-1)

Commit `9277f0a` required two GPG pinentry retries — default agent TTL / pinentry timeout was too short; user was told how to extend via `~/.gnupg/gpg-agent.conf` (`default-cache-ttl 7200`, `max-cache-ttl 7200`, `pinentry-timeout 7200`). No config changed this session.

PR #273 opened on branch `accept/07-ui-pseudo-restore`. Merged locally via `git merge --no-ff -S` → merge commit `5350641` (GPG good signature `DA9704E8`), pushed to origin. `gh pr view 273 --json mergedAt` → `2026-04-21T18:19:15Z`, state MERGED.

**PR-body discrepancy (post-merge):** #273's body states the matrix closeout + MEMORY.md compaction "will land as the next follow-on PR". They actually landed as direct commit `515b26d` to main (docs-only, consistent with Run 04/05/06 minutes-on-main pattern). Discrepancy is documentary only — work is complete; amending the merged PR body was judged not worth the churn.

### Matrix close-out

Wrote `docs/SessionLogs/acceptance-matrix/MATRIX-CLOSEOUT.md` — 7-run result table, three parity-pair verdicts (02↔05 full, 03↔06 wizard, 04↔07 restore), issue ledger (matrix-time + remaining-open), transport-parity verdict ("functionally indistinguishable endpoints"), and a handoff note for downstream ERPNext-focused work.

### MEMORY.md compaction + update

Addressed reminders #3 and #4 from Run 06 minutes:
- The "Acceptance Matrix — Transport Parity" paragraph was 500+ chars per run. Replaced the run-by-run prose with a single-sentence matrix-complete marker that references `MATRIX-CLOSEOUT.md` for detail. Historical session logs retain the full narrative — MEMORY.md now points at them rather than duplicating.
- "GitHub Issues" line: removed #267 and #268 (closed 2026-04-21), added #271 to open-issues list.
- Stage Status: flagged Stage 2.3 matrix acceptance complete.

## State handed to next session(s)

- `main @ 5350641` — matrix fully merged.
- dev01 running with restored Pseudo-Co ERPNext (Run 07 exit state: skeletal ERPNext, `Company.count=1`).
- No schema/pipeline changes from the matrix closeout — all lifts were test-layer, docs, or memory.
- **Acceptance: CLI 4/4 + UI 3/3 = 7/7. Transport-parity foundation-solid.**

## Reminders to user (unresolved concerns)

1. **Untracked `doCytoscape.sh` / `doVite.sh`** — still unresolved since 2026-04-21-1033. Decide commit vs `.gitignore` vs leave. Interacts with #244 (`*.tgz` in `.gitignore`).
2. **Dev01 sync-check "unreachable" carve-out** — not filed as an issue. Dormant for this exit state (dev01 is running) but returns on any test run that ends with dev01 destroyed.
3. **#271 fix** — when tackled, audit accept-02..05 for the same destroy-guard gap.
4. **GPG-agent TTL** — `pinentry-timeout` + `default-cache-ttl` default values caused two signing retries this session. User asked about extending to 2hr; config knobs provided (`default-cache-ttl 7200`, `max-cache-ttl 7200`, `pinentry-timeout 7200` in `~/.gnupg/gpg-agent.conf` + `gpgconf --reload gpg-agent`); no change applied this session.
5. **PR #273 body discrepancy** — body states closeout "will land as the next follow-on PR"; actually landed as direct commit `515b26d` to main (docs-only precedent from Runs 04/05/06). Noted; not amended.

## File trail

- Branch: `accept/07-ui-pseudo-restore` at `9277f0a` (spec+params)
- Merge commit: `5350641` on main
- PR: #273 — merged 2026-04-21T18:19:15Z
- Spec: `prototypes/cytoscape/tests/accept-07-ui-pseudo-restore.spec.js`
- Params: `docs/SessionLogs/acceptance-matrix/params/07-ui-pseudo-restore.yml`
- Agenda (unchanged): `docs/SessionLogs/acceptance-matrix/07-ui-vm-pseudo-company-restore-from-wizard-backup.md`
- Closeout: `docs/SessionLogs/acceptance-matrix/MATRIX-CLOSEOUT.md`
- This minutes: `docs/SessionLogs/2026-04-21-1420-session-minutes.md`
- Prior-session minutes: `docs/SessionLogs/2026-04-21-1256-session-minutes.md` (Run 06 GREEN)
