# Session discipline — `on_boarding` branch

Read this once at the start of your first session on this branch, and
again whenever you're about to commit, merge, push, or close an issue.
It is the *cadence* layer. [`AI_GUARDRAILS.md`](../AI_GUARDRAILS.md) is the
*conduct* layer. If they ever appear to conflict, conduct wins.

## Why this file exists

The parent project's root `CLAUDE.md` carries a session discipline
calibrated for tenant-side infrastructure work: KVM hypervisors,
WireGuard meshes, ERPNext targets, multi-session refactors. Each of
those rules earned its place by costing a session when it was absent.

This branch is lighter. The work is documentation, walkthroughs, and
small scripts that streamline a new operator's path through the four
stages in [`ORIENTATION.md`](../ORIENTATION.md). The blast radius of a
mistake is "a paragraph reads badly" — easy to revert via `git`.

So the parent project's full ceremony would be theatre here. This file
keeps the rules that are load-bearing at any blast radius, relaxes the
ones that aren't, and adds the few that are specific to writing
onboarding material for a zero-knowledge audience.

## Quick start (every session on this branch)

1. **Verify state.**
   ```bash
   git branch --show-current   # expect: on_boarding, or a sub-branch off it
   git status                  # expect: clean
   ```
2. **30-second skim of the previous session.** `git log --oneline -5`
   plus the most recent merged PR's description. Enough to know where
   you're picking up.
3. **State the session's one objective** in a sentence. One objective
   per session.
4. **Open or pick up the issue(s)** for that objective on
   `martinhbramwell/ESACP`. File the issue before writing the work, not
   after.
5. **Cut a sub-branch** off `on_boarding` (see [Branch flow](#branch-flow))
   and work there. Do not commit onto `on_boarding` directly.
6. **At each QA trigger (T1–T5)** invoke the `esacp-qa` agent. See
   [QA verdict layer](#qa-verdict-layer).

## What stays load-bearing

These survive the lighter context. They are cheap in isolation and
load-bearing in aggregate.

| Rule | Why it survives |
|---|---|
| **Conventional Commits, GPG-signed, with `Co-Authored-By:` trailer** | The cost is a one-line commit message and a signing key the controller already needs. The benefit is a `main` history the next zero-knowledge Claude can actually read. See root `CLAUDE.md` §"Commit Conventions". |
| **GitHub Issues as institutional memory** | This conversation will be gone tomorrow. The issue will be searchable forever. Future operators reconstruct intent from issues, not from chat. |
| **No real names / no tenant identifiers** | The branch is published; the audience is every future operator. Stricter than the parent project — even pseudonymised tenant references are out. |
| **No masking of errors** | A doc that hides a broken command is worse than a doc that says "broken on `<OS>`, contributions welcome." Silent excepts, `\|\| true`, and `--skip-failing` flags stay banned. |
| **Acceptance test before issue close** (adapted form) | Every documented command was run on a real fresh box, OR the doc explicitly says "untested on `<OS>`, contributions welcome." "Looks right" is not acceptance. |
| **PR `mergedAt` non-null = done** | A merged PR is the contract. "Opened", "CI green", "approved" are not. |
| **QA verdict layer (T1–T5)** mandatory | See [QA verdict layer](#qa-verdict-layer). |
| **Confirm before acting on risky ops** | Push, merge, destructive, third-party uploads. Threshold unchanged. |
| **No decision theatre on clerical work** | Doc work has more clerical micro-decisions than infra work. Decide and tell the operator in one sentence; don't stage a multi-option question over a filename. |

## What relaxes vs. the parent project

These are quieter on this branch and the parent rule would be overhead.

| Parent-project rule | This branch | Why it relaxes |
|---|---|---|
| **1:1:1** (one issue = one branch = one session) | **1:1:N**, N≈5–10, with a **thematic spine** — all N issues serve one named session objective (e.g. "draft Stage 1 first-encounter content"). Random bundling is forbidden; each issue is still filed individually. | Doc work's natural unit is the page or section. N=1 burns ceremony without buying safety. |
| **`platforms/kvm/sync_check.sh` at session start** | Step 1 of the Quick-start above (branch + `git status` + 5-commit skim). | `sync_check.sh` tests tenant fleet state. This branch has no fleet. |
| **File an issue at the moment of bug discovery**, before fixing | **Inline-fix-then-bundle** for typos / dead links / wording fixes inside the section you're editing. One rollup issue at session end for everything that wasn't inside your section. | Filing nine issues for nine typos noticed in nine minutes is theatre. |
| **Umbrella branches** for multi-session refactors | **Drop.** All work is sub-branches off `on_boarding`, which is itself the umbrella over `main`. | Double-stacking adds nothing. |
| **Plan → operator approval → new session → implement** for non-trivial code | **Plan as 3–5 bullets in chat, approved in the same turn, implement same session** unless the operator says otherwise. | Doc-work surprises are small and survivable. |
| **Bisect before hypothesizing** | Keep the *spirit* (narrow before guessing), drop the *ceremony*. For docs, "bisect" usually means re-reading the section. | No CI to bisect against. |
| **Introspection sidebar** every 5–7 sessions | **On request only.** | Less context to drift. |

## Branch-specific additions

These don't exist in the parent rules and would be wrong to add there.
They are calibrated to the audience and substrate of this branch.

| Addition | Why |
|---|---|
| **Name the persona each doc serves.** Frontmatter or first line declares the [`ORIENTATION.md`](../ORIENTATION.md) variant (Variant 1 greenfield consolidation, Variant 2 maintainer-dependent customisation) and an archetype (e.g. "Win-11 controller + QuickBooks operator, mobile-first, never opened a terminal"). | Without an explicit persona declaration, every doc drifts toward the *author's* mental model — which is us, not them. |
| **Every documented command is run on the target OS before publish.** A Windows-controller doc that was only ever exercised on Linux is a defect, not a draft. | Caught in spirit by "acceptance test before close"; surfaced explicitly because the OS matrix here (Windows, macOS, Linux) is wider than usual. |
| **Memory-dir-not-available doctrine.** No onboarding material may depend on `~/.claude/projects/<encoded>/memory/`. The current operator's memory dir is symlinked from a private tenant repo; end-users won't have it. | [`POINTERS.md`](../POINTERS.md) already states this; repeating because it is the easiest rule to accidentally violate when drafting examples. |
| **One-line session log.** Append one row to `on_boarding/internal_docs/SESSIONS.md` at session close: date, objective, sub-branch / PR #, issues closed. | The parent project uses `internal_docs/SessionLogs/` agendas + minutes. Overkill here. One line lets the next Junior pick up. |
| **Next-session agenda is a GitHub issue, not a markdown file.** File one issue on `martinhbramwell/ESACP` capturing the next session's objective, context, considered framings, and acceptance. The issue *is* the agenda — searchable, linkable, action-tracked via open/closed state. Reference it in the current session's `SESSIONS.md` row as `agenda → #N`. | The parent project uses `internal_docs/SessionLogs/*-next-agenda.md`. Issue-as-agenda is more discoverable for a zero-knowledge audience: a fresh Junior can `gh issue list --state open` without knowing the filename convention. |
| **Junior-side QA log lives at `on_boarding/internal_docs/qa-log.md`.** Append notable verdicts there per the file's brevity protocol; do *not* write to `internal_docs/qa-log.md` (broader-project Claude's territory per `feedback_docs_directories.md`). | Two Claudes on two controllers writing into the same log invites coordination drift. Operator integrates across both logs at the institutional level. |

## Practical mechanics

### Branch flow

- Sub-branches off `on_boarding`, named by Conventional-Commit type:
  `docs/<topic>`, `chore/<topic>`, `feat/<topic>`, `fix/<topic>`.
- PRs target `on_boarding`, not `main`.
- `on_boarding` merges to `main` **only on the operator's explicit
  sign-off**, never as a side-effect of completing a sub-branch.

### Issue bundling (1:1:N)

- N is a fuzzy 5–10, not a hard ceiling. Two related issues bundle
  fine; twelve unrelated ones do not.
- All N issues must share one thematic spine, named in the session
  objective.
- Each issue is filed individually on `martinhbramwell/ESACP`.
- The PR title names the theme: `docs(on_boarding): Stage 1
  first-encounter content`.
- The PR body lists `fixes #A, #B, #C` so merge auto-closes the set.
- The commit messages also reference issues with `fixes #N` — the
  cross-repo auto-close only fires from the commit body, not the PR
  description.

### Acceptance test for docs

A documentation issue closes when **at least one** of these is true:

1. The doc's commands were executed on a real fresh box of the target
   OS, by the author or operator, and the output matched the doc.
2. The doc explicitly carries an `> Untested on <OS>, contributions
   welcome.` notice on the affected section.

"Reads well" is not acceptance.

### Persona declaration

Every operator-facing doc starts with a one-block frontmatter:

```markdown
> **Audience:** Variant 1 greenfield (small business not yet on any ERP) ·
> **Archetype:** Win-11 controller, QuickBooks user, mobile-first, never
> opened a terminal · **Stage:** 1 — first encounter.
```

When a doc serves multiple personas, declare each one.

### One-line session log

Append at session close — last action of the session. (If the session
also closes an issue via `gh issue close`, append before the T5
verdict; most sessions don't, since issues typically auto-close on the
eventual `on_boarding` → `main` merge.)

```markdown
| 2026-05-21 | Draft session-discipline doc | docs/session-discipline → #PRNUM | closes #412 |
```

`on_boarding/internal_docs/SESSIONS.md` lives next to this file. Header row only; no
prose between entries.

### Closeout-PR backfill workflow

Session closeout PRs carry a circular-reference problem: the closeout
commit's SESSIONS row and qa-log summary row need to cite the closeout
PR's own number, which doesn't exist until the PR is opened. The
established workflow handles this in two distinct precedents that
**must not be conflated**:

**Precedent 1 — T1+T3 skip on the closeout commit itself.** The closeout
commit (which writes the SESSIONS row + qa-log entries) leaves `PR #TBD`
placeholders in the cells that would have cited its own PR. T1 and T3 on
*this commit specifically* are skipped, because the inputs (the PR
number) don't exist at commit time. T2 on the closeout PR's merge and
T5 on any issues that PR closes still apply normally. Reference:
Session-3 `7a66f4d`, Session-5 `c155c62`.

**Precedent 2 — the backfill commit is its own sub-branch + PR.** Once
the closeout PR has merged and its number is known, a *separate* commit
substitutes `PR #TBD` → `#NNN` in the two cells. This backfill commit
goes through the full sub-branch + T1 + commit + T3 + push + PR + T2 +
merge cycle. It does **not** inherit the T1+T3 skip from precedent 1.
By backfill time, the PR number is the entire content of the change —
there is no longer any reason to skip QA gates. Reference: Session-5
backfill = PR [#471](https://github.com/martinhbramwell/ESACP/pull/471).

The skips are different because precedent 1's skip is structural (inputs
don't exist) while precedent 2's would be merely procedural-shortcut
(inputs do exist; we'd just be skipping for convenience). Session 6
(2026-05-24) introduced commit `87e1043` directly to `on_boarding`,
mistakenly applying precedent 1's skip to a precedent-2 commit. The
content was correct but the discipline drifted; this section codifies
the distinction so future Junior catches the shape before committing.

**Mechanical check before committing**: if the diff touches only
`PR #TBD → #NNN` substitutions in `SESSIONS.md` and/or `qa-log.md`, and
you are about to commit directly to `on_boarding` (no sub-branch), STOP.
Cut a `docs/session-N-pr-backfill` sub-branch first and route the change
through a PR.

## QA verdict layer

T1 commits · T2 merges · T3 pushes · T4 destructive ops · T5 issue
closes. All five mandatory on this branch, no carve-outs for doc-only
diffs. The agent is at [`.claude/agents/esacp-qa.md`](../../.claude/agents/esacp-qa.md)
and the contract at [`internal_docs/qa-contract.md`](../../internal_docs/qa-contract.md).

The agent self-adjusts to the surface — a `.md`-only commit under
`on_boarding/` clears far faster than a `tools/pipeline/` commit. The
cost of keeping T1 mandatory is small; the cost of *forgetting* the
rule when the branch's scope creeps into scripts would not be.

Junior records notable verdicts in [`qa-log.md`](qa-log.md) per that
file's brevity protocol. The broader-project Claude's institutional
log at [`internal_docs/qa-log.md`](../../internal_docs/qa-log.md) is
out of scope for Junior — read it for context, don't write to it.

## Precedence

If a rule here ever appears to conflict with the parent project's
global conduct (no real names, no masking errors, no third-party code
modification, the QA verdict contract), **the parent rule wins**. This
file relaxes *cadence*, never *conduct*.

If a rule here ever appears to conflict with the rest of the kit
([`README.md`](../README.md), [`ORIENTATION.md`](../ORIENTATION.md),
[`POINTERS.md`](../POINTERS.md), [`AI_GUARDRAILS.md`](../AI_GUARDRAILS.md)),
the kit wins and this file is the bug — file an issue.
