# Session Minutes — Phase 1A CC-OPS Sweep

**Date:** 2026-04-21 ~17:40–18:00 EDT
**Branch:** `chore/phase-1a-cc-ops-sweep` (merged to `main` via `9184fa2`)
**Issues closed:** #213, #238, #243, #188 (4)
**PR:** #274 — merged 2026-04-21T21:57:48Z
**Baseline:** plan file `~/.claude/plans/open-issues-purge.md`; session entered at `main @ 98177d2`

## Objective

Execute Phase 1A of the post-matrix open-issues purge plan — housekeeping
bundle under the #262 amendment, four CC-OPS issues in one sweep PR, zero
matrix-SUT impact. Also serve as litmus test for the sweep-bundle pattern.

## Outcome

All four issues closed by single PR merge. Open issues: **29 → 25**. Plan
Phase 1A marked ✅. Amendment #262 validated by practice (validation
comment posted to the closed issue). Transport-parity matrix untouched.

## Session narrative

### Pre-work: dirty tree on `main`

Session opened with three uncommitted files on `main` (`ansible/group_vars/all.yml`,
`config/wireguard/keys.sops.yml`, `hosts_map.yml`) — pipeline-emitted state from
Run 07's dev01 pseudo-restore (WG pubkey rotation + `vm_role` reset). Committed
as `fcb5cb0` (`chore(state): record Run 07 pipeline state — dev01 wg key + role reset`)
before branching, so the sweep branch started from a clean tree.

### Per-issue work

**#213 (`session_close_audit` hook relative path)** —
`.claude/settings.json`: command changed to
`${CLAUDE_PROJECT_DIR}/.claude/hooks/session_close_audit.sh`. Matching
allow entry in `.claude/settings.local.json` (gitignored, operator-local)
also updated.

**#238 (size-check baselines persisted on blocked commits)** —
`tools/pre_commit_size_check.py`: swapped execution order so
`save_baselines` + `git add` run only on the success path, not before the
violation-exit branch. Option (a) per pre-work design check.

**#243 (rename `approve_logichem_bash.py`)** — operator-local:
`~/.claude/hooks/approve_logichem_bash.py` →
`~/.claude/hooks/approve_bespoke_bash.py`; `~/.claude/settings.json`
PreToolUse command updated; `feedback_compound_cmd_hook.md` (in CC memory
dir) scrubbed of the legacy token and the carve-out note. No repo diff;
documented in PR body. Takes effect from the next CC session.

**#188 (Claude Code invokes `python <script>`)** — `CLAUDE.md`: new
"Invoke scripts as executables" section between the banned-patterns and
size-limits sections. Pointer to `feedback_invoke_as_executable.md` for
rationale. Option (a) per pre-work design check (form chosen over a
bash-preflight lint).

### PR + merge

- Commit `88a6eab` on `chore/phase-1a-cc-ops-sweep` (GPG-signed, verified).
- PR #274 opened with `fixes #213 #238 #243 #188` + explicit test plan.
- Merged via `gh pr merge 274 --merge` (merge commit, branch kept per
  `feedback_keep_merged_branches.md`). `mergedAt` = 2026-04-21T21:57:48Z.
- Local `main` fast-forwarded to `9184fa2`. Working tree clean.

### Amendment validation

#262 (housekeeping-bundle amendment) was closed 2026-04-20; this session
was the first real execution. Posted a confirmation comment on #262
recording the validation:
<https://github.com/martinhbramwell/ESACP/issues/262#issuecomment-4292130969>

### Plan update

`~/.claude/plans/open-issues-purge.md` Phase 1A row marked ✅ with PR
reference and merge commit.

## State handed to next session(s)

- `main @ 9184fa2`, working tree clean.
- Plan file: Phase 1B row intact — scope `#217, #244, #216, #50`.
  **Gate before 1B:** #216 requires a pipeline-caller audit before deletion.
- Deferred runtime acceptance items (not session blockers):
  - #213 — no more `UserPromptSubmit` "not found" warning should appear
    from next session start.
  - #243 — compound `cd && git` should still auto-approve under the new
    hook name (`approve_bespoke_bash.py`) from next session start.
  - Both tracked on PR #274 test-plan checklist.

## Reminders to user (unresolved concerns)

1. **Phase 1A runtime verification** — the two acceptance items above
   will be observable only at the next CC session start. If either
   regresses, it would reopen #213 or #243.
2. **Dev01 sync-check "unreachable" carve-out** — carried over from the
   2026-04-21-1528 minutes, still not filed as an issue. Dormant while
   dev01 runs.
3. **GPG-agent `default-cache-ttl` missing** — carried from prior
   sessions. User has `allow-loopback-pinentry` + `pinentry-timeout 7200`
   but no `default-cache-ttl 7200`; GPG signing prompted mid-session
   again this run (once). Config unchanged.
4. **Phase 1B gate** — #216 requires a pipeline-caller audit
   (grep-sweep for callers of `phase1` and `gate` subcommands in
   `install_specific`) before the sweep PR can include deletion. If
   a caller surfaces, #216 drops from the 1B bundle.

## File trail

- Pipeline-state commit: `fcb5cb0` on `main`
- Sweep commit: `88a6eab` on `chore/phase-1a-cc-ops-sweep`
- Merge commit: `9184fa2`
- PR: <https://github.com/martinhbramwell/ESACP/pull/274>
- #262 validation comment: <https://github.com/martinhbramwell/ESACP/issues/262#issuecomment-4292130969>
- Plan status edit: `~/.claude/plans/open-issues-purge.md` (Phase 1A ✅)
- This minutes: `internal_docs/SessionLogs/2026-04-21-1801-session-minutes.md`
- Prior-session minutes: `internal_docs/SessionLogs/2026-04-21-1528-session-minutes.md`
  (purge-plan creation)
