# Agenda carry-forward drift — root cause + roadmap-visualization design (S93)

Secretary notes for the S93 introspection-sidebar discussion. Linked from
`2026-06-02-1335-session-minutes.md`.

## Trigger

S93 opened with the operator setting the objective "start the R6 walkthrough for #483"
— taken verbatim from the S93 agenda, which described "R6 family (#483) — mostly-unbuilt
P1 security/functional fixes … walkthrough first." On loading #483 it was **already
CLOSED** (walkthrough done S80, 5 FIX items deployed + probed S81; deferred child #496
closed S86). The objective was based on a stale agenda.

## Root-cause trace (not a guess — followed the propagation)

Grepped every agenda mentioning R6/#483 and reconstructed three phases:

1. **Tracked correctly (S80–S86).** R6 walkthrough → implementation → R6e.2 deferral (#496)
   all carried accurately across ~6 agendas. State line read "R5 + R6 nginx parity intact"
   — true. Tracker and agenda agreed.
2. **Demotion to footnote (S88, `05-30-1626`).** Once done, R6 dropped off the active list
   and survived only as "R6 family under #483" — a *homed-pointer*, not a to-do.
3. **Recopy + re-inflation (S90→S93).** Each session-close authored the next agenda by
   copying the previous agenda's prose, and the pointer mutated: "under #483" →
   "remaining R6 family" → "mostly-unbuilt P1 … walkthrough first." The inflation step
   reached for the #483 issue **body** (frozen at filing, reads like unbuilt work) instead
   of its **state + disposition comments**.

## The reframe — not "multiple sources of truth"

Operator asked: "Are you depending on multiple sources of truth? Do we need a Kanban?"

Conclusion: there is **one** authority (the GitHub tracker) and it was correct throughout.
The disease is a **denormalized cache** — the agenda's hand-written status prose duplicates
tracker facts and is never invalidated on read. Derived-from-derived with no re-grounding is
a telephone game. Cure is not "pick which truth wins" — it's **stop duplicating; derive the
agenda's status block from the tracker at authoring time.**

On Kanban: we *already have one* (the Projects-classic board — its `projectCards` is why
`gh issue view 483` errored at session start, #434). It prevented nothing, because the drift
was never on the board — it was in the prose. Adding a hand-maintained board just creates a
third copy that also drifts. The needed property is "status section is generated from a live
query," not "a board exists."

## Audit result (all 24 carry-forward refs vs live state)

4 closed refs cited as active: **#483** (R6 phantom — set the objective wrongly),
**#541** (text rebrand cited "underway"; conflated with the still-live un-issued repo-rename
decision), **#505** (closeout), **#548** (memory pointer). Two independent instances of the
same failure mode (#483, #541) in one agenda ⇒ systemic.

## The fix architecture — data model + view

- **#560 (data model):** derive agenda status on-read at session-close (live `gh issue view
  --json state` per ref; CLOSED → prune or stamp `done (#N,Sxx)`, never bare); add an
  `umbrella:480` grouping label so "remaining path" is one query; optional ~30-line
  agenda-lint helper. Behavioral half landed S93 (memory below). Code half = future 1:1:1.
- **#561 (view):** PERT/roadmap visualization in the existing Cytoscape control plane
  (`dagre`/`klay` DAG layout), nodes = umbrella issues, edges = deps, colour = past(closed)/
  current(open-active)/future(open-blocked), **reading live issue state via `api.py`** — the
  same derive-from-tracker source as #560. Operator motivation: "when engaged in a multistep
  process it is not at all easy to know where you are in it." On Beaverdam M&V (self-
  explanatory, step-by-step). Depends on #560's grouping. Future 1:1:1 (touches api.py +
  Cytoscape = substantive code, out of sidebar scope).

Key insight: **#560 is the data model, #561 is the view over it.** The chart can't drift the
way the prose did because it re-queries state.

## Brand-boundary decision (operator, S93)

**Beaverdam** = the **new user-facing product only**. **ESACP** stays — "ERP Systems
Administrator Control Panel" — for the repo, internal identifiers, and the admin platform.
**No repo rename, no sweeping changes.** This resolves (as a definitive NO, not a deferral)
the "repo rename is a Senior+operator call" reminder that had ridden carry-forward since S89
tagged to the now-closed #541. Recorded in memory `project_on_boarding_branch` + a #541 comment.

## Memory written

`feedback_agenda_author_from_state_not_body` — close-time counterpart of
`feedback_grep_memory_before_issue_body` (which fires at pickup/start, not authoring — the
exact moment the drift enters).
