# Session Minutes — Phase 1B Repo/Tooling Sweep

**Date:** 2026-04-21 ~18:30–19:30 EDT
**Branch:** `chore/phase-1b-repo-tooling-sweep` (merged to `main` via `f8ccfad`)
**Issues closed:** #217, #244, #216, #50 (4)
**Issues filed (follow-ups):** #275, #276, #278 (3 — #278 filed during session-close audit)
**PR:** #277 — merged 2026-04-21T23:25:46Z
**Baseline:** plan file `~/.claude/plans/open-issues-purge.md`; session entered at `main @ 24800c6`

## Objective

Execute Phase 1B of the post-matrix open-issues purge plan — repo/tooling
housekeeping sweep closing #217, #244, #216, #50 in a single PR, with the
#216 pipeline-caller audit as the gate. Zero matrix-SUT impact.

## Outcome

All four issues closed by single PR merge; #216 audit cleared so nothing
dropped from the bundle. Two follow-ups filed for side-findings. Open
issues: **25 → 23** (net −2, not −4, because of the two follow-ups).
Plan Phase 1B marked ✅.

## #216 audit — gate result

**CLEAR.** Grep sweep for callers of `phase1` / `gate` / `cmd_phase1` /
`cmd_gate` / `install_specific.py phase1|gate` across the entire tree
(excluding `docs/SessionLogs/`) returned only:

- `install_specific.py` — its own dispatcher
- `vm_scripts/install_specific/__init__.py` — `__all__` + re-exports
- `vm_scripts/install_specific/phase1.py`, `gate.py` — the dead code itself
- `verify_phase9.py` — Phase 9 shape-check (introspection, not a caller)
- `tools/CLAUDE.md` + pre-matrix session logs — documentation

Post-stage-extraction ownership of the same operations:

- `handleBackup` → `stages/wizard_completion/capture_backup.py`
- `handleRestore` → `stages/stage_7_data_restoration/data_restore.sh`,
  `stages/wizard_completion/restore_backup.py`
- `render_bash_aliases` → `tools/renderers/render_bash_aliases.py`
  (invoked by `stage_9_service_activation/{service_activation,generic_activation}.sh`)

## Per-issue work

**#217 (`tools/vm_scripts/` ratchet entry)** — `tools/pre_commit_size_check.py`
`CATEGORY_LIMITS` now includes `"tools/vm_scripts/": 80`. Verified by
importing `get_limit_for` and confirming a path under that prefix returns
80. Previously only enforced manually by `verify_phase9.py`; now mechanically
enforced at commit time alongside `tools/cli/`, `tools/pipeline/`,
`tools/api/`.

**#244 (`.gitignore` archive patterns)** — added `*.tgz` (primary: production
DB backup pattern `YYYYMMDD_HHMMSS-erp_<business>.tgz`) and `*.tar`. `*.zip`
was already covered despite the issue body's wording. Verified:

```
$ git check-ignore -v test.tgz test.tar test.zip test.tar.gz
.gitignore:100:*.tgz    test.tgz
.gitignore:101:*.tar    test.tar
.gitignore:102:*.zip    test.zip
.gitignore:99:*.tar.gz  test.tar.gz
```

**#216 (delete dead `phase1` / `gate`)** — audit cleared. Deleted
`tools/vm_scripts/install_specific/{phase1,gate}.py`. Updated:

- `__init__.py` — dropped imports + `__all__` entries + docstring mentions
- `install_specific.py` — thin entry dispatcher (now 43 lines, ratcheted
  down from 47)
- `verify_phase9.py` — checks for 2 importable `cmd_*` and 2 subcommands
  in `--help` (was 4)
- `tools/CLAUDE.md` — subcommand table, import line, golden-backup note
  rewritten to point at the pipeline stages that actually own those ops

**#50 (`cf-mcp-refresh` canonical copy + install step)** — added
`tools/cf-mcp-refresh` (byte-identical to `~/.local/bin/cf-mcp-refresh`).
Install step added to `docs/BuildOutProcedure.md` section 0 prerequisites:
`install -m 0755 tools/cf-mcp-refresh ~/.local/bin/cf-mcp-refresh`.
Existing runtime path unchanged — `Cld.sh` and `sync_check.sh` continue to
reference `~/.local/bin/cf-mcp-refresh`, now installed from the repo copy.

## Follow-up issues filed

- **#275** — `verify_phase7.py` flags `tools/cli/verify_add_host.py` and
  `tools/cli/verify_provision_generic.py` as unexpected subprocess calls
  when those files are integration-test harnesses. Confirmed pre-existing
  on `main @ 24800c6` via `git stash` + re-run. Proposed fix: teach the
  checker to skip `tools/cli/verify_*.py`. Not a Phase 1B blocker.

- **#276** — `tools/cf-mcp-refresh` contains a bash heredoc feeding Python
  code (CLAUDE.md banned pattern). Preserved verbatim in #50 to keep its
  scope narrow; proper refactor is extracting the token-writing Python into
  a standalone file.

- **#278** — `sync_check.sh` misclassifies a dormant dev01 as
  "unreachable" instead of the "dormant (expected off)" treatment given
  to other dev VMs. Carried as an unresolved reminder across three
  consecutive sessions' minutes without being filed. Filed during the
  session-close audit so it no longer relies on minute-to-minute memory.

## PR + merge

- Commit `dbba514` on `chore/phase-1b-repo-tooling-sweep` (GPG-signed,
  verified). First two commit attempts timed out waiting for GPG pinentry
  — standing reminder from the 2026-04-21-1801 minutes (GPG-agent
  `default-cache-ttl` missing) manifested as a double timeout.
- PR #277 opened with `fixes #217 #244 #216 #50` in the title.
- Merged via `gh pr merge 277 --merge` (branch kept per
  `feedback_keep_merged_branches.md`). `mergedAt` = 2026-04-21T23:25:46Z.
- Local `main` fast-forwarded to `f8ccfad`. Working tree clean.

### Auto-close misfire

GitHub auto-closed only **#217**. The `fixes #A #B #C #D` no-comma syntax
links only the first referenced issue. #50, #216, #244 were closed
manually with comments citing the merge commit. House-style guidance for
future sweep PRs (`fixes #A, fixes #B, …`) is now persisted in:

- `memory/feedback_pr_fixes_comma_syntax.md` (project feedback memory)
- Comment on #262 (housekeeping-bundle amendment) folding the trap into
  the amendment's standing guidance: <https://github.com/martinhbramwell/ESACP/issues/262#issuecomment-4292603856>

## Plan update

`~/.claude/plans/open-issues-purge.md` Phase 1B row marked ✅. Note that
the listed exit count (25 → 23) differs from the plan's original
prediction (25 → 21) by +2 because of the two follow-up issues filed
during the session — within the spirit of the plan ("Audit-before-delete"
explicitly allows scope changes when an audit surfaces a finding).

## State handed to next session(s)

- `main @ f8ccfad`, working tree clean.
- **Phase 1B runtime verification** (passive, observable at next session):
  - From the next CC session start, a new operator setting up a fresh
    controller would follow the `docs/BuildOutProcedure.md` section 0
    `install -m 0755 tools/cf-mcp-refresh …` step. Current controller
    is unaffected — `~/.local/bin/cf-mcp-refresh` is still the live copy.
  - `sync_check.sh` should still pass (the ratchet change is commit-time
    only; phase1/gate deletions are invisible to runtime — pipeline never
    called them).
- Plan next hop: **Phase 2A** (`#206` — snapshot_vm subprocess → pipeline
  primitive). Verification: unit test + manual snapshot smoke. No matrix
  re-run. Expected delta: 24 → 23.

## Reminders to user (unresolved concerns)

1. **GPG-agent `default-cache-ttl` missing** — third consecutive session
   where pinentry timeout has cost time. Still no `default-cache-ttl 7200`
   in `~/.gnupg/gpg-agent.conf`. This session: two back-to-back timeouts
   before the third attempt succeeded (user responded to pinentry). Cost
   ≈5 minutes. Operator action — the fix belongs in `~/.gnupg/gpg-agent.conf`,
   not anywhere in this repo.

2. **Phase 1A runtime-verification check** — the two acceptance items from
   the 2026-04-21-1801 minutes (#213 UserPromptSubmit warning, #243
   compound `cd && git` auto-approval) were passively observed clean this
   session start (no regressions). **Resolved — dropped from carried
   concerns.**

### Session-close audit resolutions

Items that were surfacing as forward-tense narration in this minutes file
have been moved to durable homes:

- `fixes #A #B` auto-close trap → `memory/feedback_pr_fixes_comma_syntax.md`
  + comment on #262.
- MEMORY.md issue count drift → updated in place (29 → 24, including the
  three follow-ups filed this arc).
- Dev01 sync-check carve-out → filed as **#278**.

## File trail

- Phase 1B commit: `dbba514` on `chore/phase-1b-repo-tooling-sweep`
- Merge commit: `f8ccfad`
- PR: <https://github.com/martinhbramwell/ESACP/pull/277>
- Follow-up issues: #275, #276, #278
- #262 auto-close-trap comment: <https://github.com/martinhbramwell/ESACP/issues/262#issuecomment-4292603856>
- New feedback memory: `memory/feedback_pr_fixes_comma_syntax.md`
- MEMORY.md edits: open-issues line (29 → 24) + new feedback pointer
- Plan status edit: `~/.claude/plans/open-issues-purge.md` (Phase 1B ✅)
- This minutes: `docs/SessionLogs/2026-04-21-1830-session-minutes.md`
- Prior-session minutes: `docs/SessionLogs/2026-04-21-1801-session-minutes.md`
  (Phase 1A CC-OPS sweep)
