# Session Minutes — 2026-04-17 17:02

**Type:** Planning session (no production code changes).
**Objective at start:** Scope Stage 2.x — produce an agreed plan for one of: CloudStack backend / Chaos on KVM / Version watchdog.
**Actual objective pursued (user redirected):** Define an 8-run UI↔CLI acceptance matrix that proves Gen 3 pipeline parity, as the foundation for resuming ERPNext-focused work.

## What happened

### 1. Session-start review

- Read MEMORY.md; read `docs/SessionLogs/2026-04-17-1649-next-agenda.md`.
- Ran `bash platforms/kvm/sync_check.sh`: 44 ✅ / 10 ⚠️ / 3 ❌. The 3 failures (WG-ping to `dev02`, `dev03`, `target5`) are expected per the agenda — unprovisioned VMs. No regression.
- Listed 16 open issues via `gh issue list`.
- Proposed Stage 2.x planning objective.

### 2. User-driven scope pivot

User asked to enumerate acceptance runs needed to trust saconsole + VM destroy/rebuild across UI and CLI. Agreed on **8 runs**: 4 per transport, ordered saconsole → full-Logichem → pseudo-wizard → pseudo-restore, UI first then CLI.

### 3. Cross-cutting invariants captured

After dialogue the following invariants were pinned for the matrix:

1. Single-command launch (1 destroy + 1 build, no mid-run input).
2. Parametric pre-configuration (all variant differences in a param file before the command fires).
3. Playwright is the sign-off.
4. Topology convergence is observed by Playwright for CLI runs (05–08); intrinsic for UI runs.
5. SUT frozen during runs. Test code itself is **not** length-limited (a user-refined point of the rule); any new non-test code created during acceptance stays ≤~100 lines. Code under test must not be altered — findings halt the run and become their own 1:1:1 session.

### 4. SUT oversize-file survey + exemption decision

Measured all files in the destroy/build call graph. ~34 files exceed 100 lines. Of those, only three are blatantly oversized and in-scope for the 8 runs:

- `prototypes/cytoscape/src/main.js` (2013) — in every run.
- `platforms/kvm/bootstrap_hub.sh` (406) — in runs 01 and 05.
- `platforms/kvm/prepare_hypervisor.sh` (370) — confirmed **not** in any run's call graph (one-time hypervisor prep).

User chose to park `main.js` and `bootstrap_hub.sh` with explicit exemptions so the acceptance matrix can proceed. Filed:

- **#219** `refactor(cytoscape): decompose main.js (2013 lines) into per-concern modules`
- **#220** `refactor(kvm): decompose bootstrap_hub.sh (406 lines) into phase scripts`

Both tagged `refactor`, scheduled after the matrix closes.

### 5. Planning deliverables

- Plan file: `~/.claude/plans/acceptance-matrix-transport-parity.md` (local home, not under the repo).
- Agenda files (8, under the repo): `docs/SessionLogs/acceptance-matrix/NN-*.md`.
- Memory entries (local home):
  - `memory/project_acceptance_matrix.md` — project context for future sessions.
  - `memory/feedback_sut_frozen_tests_unlimited.md` — the SUT-frozen / test-code-unlimited rule.
  - `memory/MEMORY.md` — new matrix index line added; open-issues line updated with #219, #220.

### 6. Git / PR

- Discovered previous session's PR **#218** still open on branch `docs/2026-04-17-1649-phase9-minutes`. Did not touch that branch.
- Branched fresh from `main` as `docs/acceptance-matrix-plan`.
- Committed the 8 agendas as a single signed commit `28c7d3a`.
- Pushed; opened **PR #221**: `docs: acceptance matrix plan — 8 agendas for UI/CLI transport-parity runs`.
- PR #221 state at the time of writing these minutes: **OPEN, MERGEABLE, `mergedAt: null`** — session not yet closed per `feedback_pr_merge_before_session_close.md`.

## What was NOT done

- The original Stage 2.x scoping (CloudStack / Chaos / Watchdog) — superseded by the matrix planning; remains available as the follow-on conversation after the matrix closes.
- No production code changes. No SUT file was altered.
- No Playwright test files were created yet — they are written per-run in each acceptance session, not up front.
- Minutes do not claim the session is DONE. That word is gated on #221's merge.

## Open issues touched this session

- **Created:** #219, #220.
- **Referenced:** #218 (prior session's PR, unmerged — left alone).

## State handed to next session

- 8 agendas committed and on PR #221 pending merge.
- Once #221 merges, the next 1:1:1 session picks up Acceptance Run 01 per `docs/SessionLogs/acceptance-matrix/01-ui-saconsole-destroy-rebuild.md`.
- Previous session's PR #218 remains open and will be resolved on its own track.
