# Session Minutes — Phase 2C Umbrella-Branch Policy (#236)

**Date:** 2026-04-22 ~07:55–08:00 EDT
**Branch:** `internal_docs/236-umbrella-branch-policy` (merged to `main` via `7482318`)
**Issues closed:** #236 (1)
**Issues opened:** none
**PR:** #282 — merged 2026-04-22T11:55:17Z
**Baseline:** plan file `~/.claude/plans/open-issues-purge.md`; session entered at `main @ c612fbb`

## Objective

Close #236 by adopting the umbrella-branch model: sub-branches of a long-
lived `umbrella/<topic>` merge to the umbrella, and the umbrella merges
to `main` only via a deliberate certification session. Single-issue and
doc-only work continues to go direct to main.

## Outcome

Policy landed in `CLAUDE.md` under the Session Protocol block (9 lines
added). Six open questions in #236 resolved in the PR body and in the
new feedback memory. Open-issue count **22 → 21** as planned.

## Six open questions — resolutions

| # | Question | Resolution |
|---|---|---|
| 1 | Trigger for umbrella → main merge | **Deliberate certification session** — broad-context acceptance green, `sync_check` green against umbrella tip, explicit user sign-off. Not "last sub-branch merged." |
| 2 | Rebase cadence | **On demand** — before cutting a new sub-branch, when a direct-to-main PR touches files also touched on umbrella, before the certification session. No fixed schedule. |
| 3 | "Merged" semantics | **Merged-to-target-branch.** Sub-branch → umbrella; umbrella → main. Both `mergedAt` timestamps required before the multi-session effort is "done." |
| 4 | Retroactive application | **None.** Prior matrix / Gen 3 work stays as-landed. Rule applies only to multi-session work started after merge. |
| 5 | CI / `sync_check` impact | **No change this phase.** Branch topology is out of scope for `sync_check`. Revisit only if merges are later gated on umbrella-tip state. |
| 6 | Naming convention | `umbrella/<short-topic>` (e.g. `umbrella/v16-upgrade`, `umbrella/matrix-run-08`). Single prefix so `git branch --list 'umbrella/*'` enumerates live umbrellas. |

**Triggers for use (any of):** >3 sub-branches expected; cross-cutting
files touched by multiple issues; a broad-context acceptance exists that
cannot run per-sub-branch (matrix runs, full-pipeline e2e); explicit user
call at planning time.

## Files changed (in-repo)

| File | Change |
|---|---|
| `CLAUDE.md` | +9 lines — new "Umbrella branches" subsection under Session Protocol, between the Housekeeping-bundles exception and the Bug-workflow block |

## Memory updates (outside repo, applied immediately)

| File | Change |
|---|---|
| `memory/feedback_umbrella_branches.md` | **NEW** — feedback-type memory: rule + why + how to apply (triggers, naming, rebase cadence, merged-to-target semantics, certification-session criteria, retroactive-application stance, CI stance) |
| `memory/feedback_pr_merge_before_session_close.md` | Clarified "merged" = merged-to-target-branch (sub-branch → umbrella; umbrella → main) |
| `memory/feedback_issue_branch_session_discipline.md` | Appended cross-reference to `feedback_umbrella_branches.md` for multi-session / broad-context cases |
| `memory/MEMORY.md` | Added index pointer under Critical Rules; updated open-issues line 22 → 21 + Phase 2C entry |

## Acceptance verification

- ✅ `git diff --stat` — 1 file, +9 lines (CLAUDE.md only, as scoped).
- ✅ `grep -n "Umbrella branches" CLAUDE.md` — one hit under Session Protocol.
- ✅ `gh pr view 282 --json state,mergedAt` → `MERGED`, `mergedAt=2026-04-22T11:55:17Z`.
- ✅ `gh issue view 236 --json state,closedAt` → `CLOSED`, `closedAt=2026-04-22T11:55:18Z`.
- ✅ `gh issue list --state open --json number | jq length` → `21`.
- ✅ `git log -1 --oneline main` → `7482318 Merge pull request #282`.
- No SUT smoke required (policy doc).

## PR + merge

- Commit `4e94525` on `internal_docs/236-umbrella-branch-policy` (GPG-signed,
  verified). Pinentry succeeded first attempt.
- PR #282 opened with `fixes #236` in the body.
- Merged via `gh pr merge 282 --merge` (branch kept per
  `feedback_keep_merged_branches.md`). `mergedAt` = 2026-04-22T11:55:17Z.
- Merge commit: `7482318`. #236 auto-closed 2026-04-22T11:55:18Z.

## Plan update

`~/.claude/plans/open-issues-purge.md` Phase 2C row marked ✅ with merge
hash `7482318` and count 22 → 21. Plan next hop: **Phase 3A** — Wizard +
logo bundle (#181, #250, #271 piggyback), matrix-touching, Runs 03 + 06
re-run with B03/B06 regeneration.

## State handed to next session(s)

- `main @ 7482318`, working tree clean.
- Open issues: **21** — #48, #65, #138, #153, #156, #157, #181, #187,
  #202, #219, #220, #223, #225, #235, #240, #241, #250, #271, #276,
  #278, #280.
- Plan next hop: **Phase 3A** (#181, #250, #271). First matrix-touching
  phase after the Zero-Cost and Process clusters — risk mitigations in
  the plan table include back-up of B03/B06 before regeneration and a
  decision on whether #250's logo lands in the DB dump.

## Reminders to user (unresolved concerns)

1. **Phase 3A is matrix-touching.** Back up `platforms/kvm/golden_backups/B03.tar.*`
   and `B06.tar.*` to `platforms/kvm/golden_backups/archive/` **before**
   starting, not during.
2. **#250 design decision still needed:** does the company logo end up
   in the DB dump? If yes, Runs 04 + 07 enter the re-run scope for
   Phase 3A and the session grows. Worth resolving before opening the
   3A branch.
3. **Umbrella model is now policy but has no live umbrella.** First
   work that meets the trigger criteria (likely the ERPNext v13 → v16
   upgrade, or a future matrix-rewrite sweep) will be the first live
   test of the policy. Watch for refinements needed on first use.

## File trail

- Phase 2C commit: `4e94525` on `internal_docs/236-umbrella-branch-policy`
- Merge commit: `7482318`
- PR: <https://github.com/martinhbramwell/ESACP/pull/282>
- Closed issue: <https://github.com/martinhbramwell/ESACP/issues/236>
- Plan status edit: `~/.claude/plans/open-issues-purge.md` (Phase 2C ✅)
- MEMORY.md edits: open-issues line (22 → 21 + Phase 2C entry); new
  "Umbrella branches" pointer under Critical Rules
- New memory file: `memory/feedback_umbrella_branches.md`
- Updated memory files: `memory/feedback_pr_merge_before_session_close.md`,
  `memory/feedback_issue_branch_session_discipline.md`
- This minutes: `internal_docs/SessionLogs/2026-04-22-0801-session-minutes.md`
- Prior-session minutes: `internal_docs/SessionLogs/2026-04-22-0700-session-minutes.md`
  (Phase 2B #211 orphan orchestration audit)
