# Session Minutes — Matrix Run 06 (UI pseudo-company wizard) GREEN

**Date:** 2026-04-21 ~11:40–12:55 EDT
**Branch:** `accept/06-ui-pseudo-wizard` (scaffold from 2026-04-21-1033 session, forward-merged with main this session)
**Issue opened:** #271 (latent `accept-NN` destroy-guard bug, deferred)
**PR:** #272 — merged `2026-04-21T17:12:28Z` via GPG-signed merge commit `29aec7a`

## Objective

Execute Matrix Run 06 attempt 2 — UI-transport pseudo-company wizard, validated end-to-end by Playwright, to runtime-verify the #268 (`3499447`) + #267 (`af05f80`) fixes merged in the prior two sessions, and advance UI-transport acceptance to 2/3.

## Outcome

**GREEN — 1 passed (10.6m)** on attempt 3, not attempt 2. Attempt 2 halted at 29s on a latent spec-guard bug; attempt 3 succeeded after restoring dev01 to the agenda's documented entry state.

- Provision job `00e76f76` finished after 557s (9m 17s)
- UI convergence: 1s
- B06 artefact: `platforms/kvm/golden_backups/20260421_114520-dev01_iridium_blue.tgz`
- B03/B06 parity confirmed: **14 Pseudo-Co hits** in each, identical canary facts (`Pseudo-Co`, `PSC`, `CAD`, Company.count=1)
- Final sync_check: 43 ✅ / 14 ⚠️ / 0 ❌

## Session narrative

### Session open — context load

Loaded MEMORY.md + latest minutes (`2026-04-21-1121-session-minutes.md`, #267 fix GREEN). `sync_check.sh` at open: 41 passed / 14 warnings / **2 failed** — both the expected post-destroy carry-over from Run 06 attempt 1 (dev01 unreachable + hub has 4 WG peers instead of 5). Flagged openly, not silently worked around. 28 open issues; no issue-fix in scope — Run 06 is matrix-plan work.

PR verification per `feedback_pr_merge_before_session_close`: #269 `mergedAt=2026-04-21T14:58:22Z`, #270 `mergedAt=2026-04-21T15:22:54Z`. Both fixes real.

User acknowledged objective.

### Prereq — forward-merge main into accept/06

Branch `accept/06-ui-pseudo-wizard @ ddc3de2` was cut from main at `e3808a1` (pre-#267/#268). A valid attempt 2 requires both fixes in the branch. Divergence: 6 commits ahead on main, 4 files touched, **zero overlap with branch files** → clean merge guaranteed.

Presented user with merge vs rebase; user chose merge (non-destructive, preserves halt-minutes historical record).

Executed: `git merge main --no-ff -S` → merge commit `16ff71d` (GPG good signature `DA9704E8`), pushed to origin. Post-merge verification:
- Wizard recording now contains `getByRole(...Manufacturing...)` + `cb.checked = true` (DOM-mutation fix #267) — 2 matches.
- Helpers.js line 41: `if (job.status === 'error') throw new Error(...)` — #268 fix present.

### Attempt 2 — HALTED at 29s

Launched spec. Self-check green (6-step harness validation: sops decrypt, sync_check, API :8088, Vite :5173, toshiba SSH, wizard recording file). Step 1 destroy fired because dev01 was in `/api/hosts` — then timed out:

```
TimeoutError: locator.waitFor: Timeout 5000ms exceeded.
  - waiting for locator('#info-panel button').filter({ hasText: 'Destroy' }) to be visible
  at clickInfoButton (helpers.js:24)
  at accept-06-ui-pseudo-wizard.spec.js:162:13
```

**Root cause**: dev01's state at session open was `provisioned: false, vm_state: None` (pre-registered only — attempt 1's destroy removed the VM but the hostmap entry had been re-registered by hand between sessions, with `vm_role: dev:pseudo_wizard` for this run). The Cytoscape info-panel guards the **Destroy** button to only appear when `provisioned: true`; the spec's Step 1 guard checks only `if (existing)` which conflates "in hosts_map" with "destroyable". A structural spec bug, not a SUT bug.

Per CLAUDE.md "Confirm before acting" + `feedback_narration_not_action`: halted, presented user with two paths:
- **A. Restore agenda entry state** via `provisionGeneric dev01 --wizard-mode existing --wizard-arg 20260420_142102-dev01_iridium_blue.tgz` (same command Run 04/05 used to seed from B02), then rerun.
- **B. Fix the spec's `provisioned` guard in-flight** (permitted under `feedback_sut_frozen_tests_unlimited.md`), skip destroy when pre-registered-only.

User chose **A**.

### Latent issue filed — #271

Filed before acting on option A (per "bug found → open issue immediately"):

> **#271 bug(accept-NN specs): destroy-branch lacks provisioned guard — flakes on pre-registered-only entry state**
> - Scope: accept-06 confirmed affected; accept-02..05 need audit
> - Fix shape proposed: `if (existing && existing.provisioned)` guard; fall-through log for pre-registered-only case
> - Deferred: Run 06 attempt 3 sidesteps via option A, doesn't exercise the gap

### Option A execution — dev01 restoration

Ran `./tools/esacp.py provisionGeneric dev01 --wizard-mode existing --wizard-arg 20260420_142102-dev01_iridium_blue.tgz` (background, monitored). Stages 1–9 + handleRestore completed:

| Phase | Outcome |
|---|---|
| Stages 1–9 | All green (VM start, network, connectivity, content delivery, TLS, base platform, data init, app config, service activation) |
| handleRestore.sh | **Elapsed 0h 2m 9s** |
| `/api/hosts` post-restore | `provisioned=True, vm_state=running, vm_role=dev:pseudo_wizard` |

Agenda entry state achieved: running dev01 with Pseudo-Co canary from B02.

### Attempt 3 — GREEN

Re-launched spec. Progression:

| Step | Duration | Outcome |
|---|---|---|
| 0 — self-check | instant | ✓ all 6 probes pass |
| 1 — destroy dev01 (provisioned, Destroy button visible) | ~1m | ✓ UI right-click → Destroy → confirm → job completes → ABSENT from /api/hosts → `page.reload()` (rehydrates stale Cytoscape graph per #249) |
| 2 — drag tpl-erpnext-generic → Dev zone | instant | ✓ dialog opens, form populated with params, wizard_mode=replay + `pseudo-co-wizard.spec.js` selected |
| 3 — provision job | **557s** (9m 17s) | ✓ `waitForJob('00e76f76', 3000_000)` returned cleanly — this is the first runtime validation of PR #270's DOM-mutation fix and PR #269's error-terminal fix in acceptance context |
| 4 — UI convergence | **1s** | ✓ `/api/hosts` shows dev01 provisioned+running, Cytoscape node present |
| 5 — Pseudo-Co canary | ~3s | ✓ Administrator login, REST `Company/Pseudo-Co` (abbr=PSC, CAD, Canada), Company.count=1 |
| 6 — B06 artefact | ~2s | ✓ **1 new .tgz**: `20260421_114520-dev01_iridium_blue.tgz` — SQL contains `Pseudo-Co` (14 hits, identical to B03) |
| 7 — sync_check ERPNext dev01 row | ~5s | ✓ `✅ ERPNext dev01 (https://dev01.iridium.blue)` present |

Total elapsed: 10.6m (`1 passed (10.6m)`, exit 0).

### B03/B06 parity verification

Post-green, ran independent canary comparison:

```
B03 Pseudo-Co hits: 14
B06 Pseudo-Co hits: 14
```

Spot-check of B06 Chart of Accounts confirms `'Pseudo-Co','PSC'`, `'CAD'`, `'Canada'` — byte-level parity with B03's wizard-backup facts. Run 06 is the UI-transport mirror of Run 03's CLI success: **same recording, same canary, same hit count**.

### Commit → PR → merge

Commit contents (avoiding Run-04/05 commit pattern):
- `platforms/kvm/golden_backups/20260421_114520-dev01_iridium_blue.tgz` (B06)
- `internal_docs/SessionLogs/2026-04-21-1256-session-minutes.md` (this file)

**Not committed** (runtime drift identical to prior matrix PRs):
- `ansible/group_vars/all.yml` (+1/-1)
- `config/wireguard/keys.sops.yml` (+24/-24)
- `hosts_map.yml` (+1/-1)

PR #272 merged `2026-04-21T17:12:28Z` via merge commit `29aec7a` on main.

## State handed to Run 07

- `main @ 29aec7a` — B06 available for Run 07 consumption.
- dev01 running with skeletal Pseudo-Co ERPNext from the wizard. Run 07 destroys first and restores from B06.
- No schema/pipeline changes in this PR — all lifts were test-layer or artefacts.
- **Acceptance progress: CLI 4/4 + UI 2/3 = 6/7**. Only Run 07 (UI restore-from-B06, parity partner to Run 04) remains.

## Reminders to user (unresolved concerns)

1. **Untracked `doCytoscape.sh` / `doVite.sh`** — flagged since 2026-04-21-1033, still unresolved. Not touched this session. Decide commit vs. `.gitignore` vs. leave. Interacts with #244 (`*.tgz` in `.gitignore`).
2. **Dev01 sync-check "unreachable" carve-out** — still not filed as an issue (reminder carried from 2026-04-21-1121-minutes #2). After Run 07, dev01 is destroyed as the final exit state — the red row returns. Decide carve-out vs transient-VM concept vs leave.
3. **MEMORY.md over load limit** — this session's open still showed `25.8KB vs 24.4KB limit`. Compaction still needed. Current bloated paragraphs: "Acceptance Matrix — Transport Parity" (each run appends ~500 chars) and "GitHub Issues" index line.
4. **MEMORY.md open-issues line** — still lists #267, #268 as open; both closed 2026-04-21. Will also newly need #271 added, and should not list it as resolved until the fix PR lands. Partial-update is a no-op-magnet — bundle with reminder #3's compaction pass.
5. **#271 audit of accept-02..05** — #271's fix should audit those specs for the same destroy-guard gap. Flagged in the issue body; will surface as Run 07 branch-cut decision (whether to fix the guard pre-emptively in accept-07 before using a similar destroy prelude).
6. **Run 06 attempt 1 halt-minutes commit** — committed by the prior session (`ddc3de2`) on `accept/06-ui-pseudo-wizard` and is now part of this PR via the merge chain. That's a documentation record of a failed attempt inside an acceptance branch — accurate but unusual. No action required; note for minutes reviewer.

## File trail

- Merge-main-into-branch: `16ff71d` on `accept/06-ui-pseudo-wizard`
- B06 artefact: `platforms/kvm/golden_backups/20260421_114520-dev01_iridium_blue.tgz` (1358769 bytes)
- This minutes: `internal_docs/SessionLogs/2026-04-21-1256-session-minutes.md`
- Agenda (unchanged): `internal_docs/SessionLogs/acceptance-matrix/06-ui-vm-pseudo-company-wizard-creates-backup.md`
- Params (unchanged): `internal_docs/SessionLogs/acceptance-matrix/params/06-ui-pseudo-wizard.yml`
- Spec (unchanged from scaffold): `prototypes/cytoscape/tests/accept-06-ui-pseudo-wizard.spec.js`
- PR #272 — merge commit `29aec7a`, merged 2026-04-21T17:12:28Z
- Issue #271 (deferred, out of scope): https://github.com/martinhbramwell/ESACP/issues/271
- Prior-session minutes: `internal_docs/SessionLogs/2026-04-21-1121-session-minutes.md` (#267 fix), `2026-04-21-1100-session-minutes.md` (#268 fix), `2026-04-21-1033-session-minutes.md` (Run 06 attempt 1 halt)
