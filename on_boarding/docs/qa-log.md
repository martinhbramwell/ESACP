# QA Verdict Log — `on_boarding` branch

Junior-side companion to [`internal_docs/qa-log.md`](../../internal_docs/qa-log.md)
(the broader-project Claude's institutional log). Records `esacp-qa`
verdicts produced by Junior on this branch. Scoped narrowly to the
`on_boarding` branch and its sub-branches.

Why separate from `internal_docs/qa-log.md`: the directory convention
([memory `feedback_docs_directories.md`](#)) reserves `internal_docs/`
for the broader-project Claude. Junior's outputs go under
`on_boarding/docs/`. Two Claudes on two controllers writing into one
file invites coordination drift; the operator integrates across both
logs.

## Brevity protocol

Records verdicts **with signal**, not every verdict — same protocol as
the parent's qa-log. Specifically:

1. At session close (after PRs merged into `on_boarding`), review every
   `Agent(subagent_type: "esacp-qa", …)` invocation in the session.
2. Skip routine `approve` verdicts that surfaced no surprise.
3. Append rows for `approve-with-conditions`, `reject`, agent-failure
   fallbacks, trigger-skip incidents, and any `approve` that flagged
   something useful (e.g. a "surprising-good-catch").
4. If the session's verdict count is high, add one summary row first
   (`N routine approves, M with conditions, all satisfied`) and then
   individual rows for the notable ones.
5. Commit alongside the session's closeout work, not as a separate
   commit.

The point of this log is not exhaustive bookkeeping. It is the
evidence base for whether the QA layer is producing useful signal —
the same rationale the parent's log carries.

## Column legend

| Column | Meaning |
|---|---|
| **Date** | YYYY-MM-DD (session date, not entry date) |
| **Trigger** | 1=commit, 2=merge, 3=push, 4=destroy, 5=issue-close |
| **Action** | Verbatim or summarised — `git commit -m "docs(on_boarding): …"`, `gh pr merge 414 …` etc. |
| **Verdict** | `approve` \| `approve-with-conditions` \| `reject` |
| **Outcome** | `proceeded`, `revised`, `overridden-by-operator`, `aborted`, `agent-unreachable-fail-open`, `agent-unreachable-fail-closed`, `verdict-skipped` |
| **Why-logged** | Short tag: `session-summary`, `conditions-flagged`, `surprising-good-catch`, `false-positive`, `false-negative`, `override`, `skip`, `fallback` |
| **Notes** | One paragraph max. Reasoning excerpt or operator-override rationale. Link the commit hash, PR number, or invocation ID where relevant. |

## Entries

| Date | Trigger | Action | Verdict | Outcome | Why-logged | Notes |
|---|---|---|---|---|---|---|
| 2026-05-21 | 1, 2, 3 | Session 1 — bootstrap on_boarding cadence (PRs [#414](https://github.com/martinhbramwell/ESACP/pull/414), [#417](https://github.com/martinhbramwell/ESACP/pull/417)). 8 verdicts: 5 routine `approve`, 3 `approve-with-conditions`. | mixed | proceeded | session-summary | See individual rows below for the notable verdicts. PRs #414 (commits `9f15b59`, `41a875a`) and #417 (commit `2f8c321`). Issues #412, #415, #416, #419, #420. |
| 2026-05-21 | 2 | T2 on PR [#414](https://github.com/martinhbramwell/ESACP/pull/414) merge into `on_boarding` | approve | proceeded | surprising-good-catch | Agent flagged that `session-discipline.md` (the file being merged) references `on_boarding/docs/SESSIONS.md` which did not yet exist — a forward-reference inconsistency, not a blocker. The flag drove the subsequent seed work in PR [#417](https://github.com/martinhbramwell/ESACP/pull/417). Demonstrates real value of T2 verdicts even when target is non-`main` and the verdict is advisory under qa-contract §2.2. |
| 2026-05-21 | 1 | T1 on commit `41a875a` (path relocation: `on_boarding/SESSION_DISCIPLINE.md` → `on_boarding/docs/session-discipline.md`) | approve-with-conditions | proceeded → both conditions satisfied within session | conditions-flagged | Two cosmetic conditions: (1) confirm Co-Authored-By trailer is in the actual commit message — the invocation's quoted block omitted it; trailer was present at commit time. (2) Update PR [#414](https://github.com/martinhbramwell/ESACP/pull/414) title/body to reflect the new file path — deferred to immediately post-commit, satisfied via REST API once `gh pr edit` was found broken. Neither was structural. |
| 2026-05-21 | 3 | T3 on push of `41a875a` (fast-forward fixup push to existing remote branch) | approve-with-conditions | proceeded → condition satisfied within session | conditions-flagged | Restated the outstanding T1 condition (PR title/body update). Mild redundancy with the T1 row above — same condition surfaced twice across triggers when the fixup commit-and-push sequence wasn't co-located. Pattern worth noting: when T1 carries a condition deferrable to post-push, T3 will tend to restate it. Not harmful; tolerable. |
| 2026-05-21 | 1 | T1 on commit `2f8c321` (seed `on_boarding/docs/SESSIONS.md` + README cross-reference) | approve | proceeded | surprising-good-catch | Routine `approve` — but the agent explicitly verified that the seed closes the forward-reference flagged by the T2 verdict on PR [#414](https://github.com/martinhbramwell/ESACP/pull/414). Worth logging as the resolution-side of that loop. Without the prior T2 catch, the SESSIONS.md file might have remained missing through several sessions. |
| 2026-05-21 | 1, 2, 3, 5 | Session 2 (cont.) — triage #415 + Stage-2 hybrid shape decision (PR [#429](https://github.com/martinhbramwell/ESACP/pull/429)). 6 verdicts across T1/T2/T3/T5: 2 routine `approve` (T3 pushes), 2 `approve-with-conditions` (both T1), 2 notable `approve` (T2 + T5). | mixed | proceeded | session-summary | See individual rows below for the notable verdicts. PR #429 commits `686e5a1` (triage doc) and `c04caff` (PR-number backfill). Issues #415, #419, #423, #429. |
| 2026-05-21 | 1 | T1 on commit `686e5a1` (triage doc + SESSIONS row, PR [#429](https://github.com/martinhbramwell/ESACP/pull/429)) | approve-with-conditions | proceeded → condition satisfied within session via commit `c04caff` | conditions-flagged | Single carry-forward condition: backfill the `PR #TBD` placeholder in the new SESSIONS row once the PR existed. Mechanical, no structural issue. Same pattern as Session 1's commit-then-backfill loop on PR [#414](https://github.com/martinhbramwell/ESACP/pull/414) (see row 3 of this log) — recurring pattern worth noting: SESSIONS rows that reference their own PR number always introduce a backfill round-trip. Candidate for future automation. |
| 2026-05-21 | 1 | T1 on commit `c04caff` (SESSIONS PR-number backfill) | approve-with-conditions | proceeded → condition satisfied | surprising-good-catch | Agent caught that the parent's invocation claimed the file was "staged" when `git diff --staged` was empty (file was Edit'd but not `git add`'d yet). Condition was a one-command fix (`git add ...`), but the catch is real signal: parent-side optimistic reporting of state vs. actual git index state is a recurring failure mode worth this log entry. |
| 2026-05-22 | 2 | T2 on merge of PR [#429](https://github.com/martinhbramwell/ESACP/pull/429) (`docs/stage-2-triage` → `on_boarding`) | approve | proceeded | surprising-good-catch | The verdict surfaced the **carve-out clarification** that T2 hard-block applies only to literal `main` and `umbrella/*` prefix targets — `on_boarding` qualifies as institutionally the kit trunk but not by literal prefix, so T2 is *advisory* (not hard-block) for sub-branch → `on_boarding` merges. All §2.2 carve-out conditions held (prior T1+T3 passed; no rebase/amend; no surprise commits). Captured durably as memory `project_on_boarding_trunk_vs_default.md`. Without this verdict's clarification, future closeouts on this branch would invoke T2 as a hard-block and either over-block trivial doc merges or under-invoke when actually needed. |
| 2026-05-22 | 5 | T5 on `gh issue close 419 --comment ...` (Session-2 agenda close) | approve | proceeded | surprising-good-catch | First T5 on this branch. The verdict surfaced that GitHub's `fixes #N` auto-close fires **only on merges to the repo default branch** (`main`) — sub-branch → `on_boarding` merges do not auto-close, so every Session-N agenda issue requires manual T5 close with a pointer comment until `on_boarding` itself merges to `main`. Same memory file as the T2 row above (`project_on_boarding_trunk_vs_default.md`). Two consequences of one root cause, both surfaced in the same session. |
