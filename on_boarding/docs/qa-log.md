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
