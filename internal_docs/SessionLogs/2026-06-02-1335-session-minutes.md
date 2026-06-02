# 2026-06-02 1335 — Session 93 minutes

## Stated objective

**Introspection sidebar** — triggered by discovering the S93 agenda's objective ("start the
R6 walkthrough for #483") was based on a stale carry-forward. Pivoted (operator-approved) from
the phantom R6 task to: trace the root cause of agenda↔tracker drift, audit all carry-forward
refs, file the fix, and prune the staleness.

Mechanically a sidebar: this session edits MEMORY.md indexing **and** attrits carry-forward
operator-reminders (CLAUDE.md diff-based sidebar trigger).

## Pre-flight

- `sync_check`: **49 pass / 8 warn / 0 fail** — all warnings expected (dormant dev03/target5,
  manual Chrome-tab verify).
- Open issues at start: ESACP **71**, LSKB **12** — matched agenda forecast.
- TRIVIAL_FIXES.md: 1 monitor-only entry (S33 LSMem T3 skip); nothing to clear.

## What happened

### The phantom objective

Operator set "R6 walkthrough for #483." On load, **#483 was already CLOSED** — walkthrough
conducted S80, five FIX items (R6a/b/c/e.1/e.3) deployed to dev01+dev02 and probed green S81,
deferred child #496 closed S86. There was nothing to walk through. Surfaced the anomaly rather
than fabricate a walkthrough.

### Root-cause trace

Operator asked "how did this happen?" Followed the actual propagation across agendas (not a
guess): R6 was tracked **correctly** S80–S86; then on completion it demoted to a one-line
homed-pointer ("R6 family under #483", S88); then successive session-close recopies re-inflated
that pointer — pulling detail from the #483 **body** (frozen, reads unbuilt) rather than its
**state** — into "mostly-unbuilt P1 … walkthrough first." Full trace in the linked notes file.

### The reframe + Kanban question

Operator: "multiple sources of truth? do we need a Kanban?" Diagnosis relayed: **one**
authority (tracker, correct throughout); the agenda is an un-invalidated **denormalized cache**
of it. We *already have* a Kanban (Projects-classic, the cause of the `gh issue view 483`
`projectCards` error, #434) and it prevented nothing — the drift is in the prose, not the board.
Fix is derive-on-read, not more board. Operator agreed the direction.

### Audit — all carry-forward refs vs live state

18 ESACP + 6 LSKB refs checked. **4 stale closed refs** cited as active: #483 (R6 phantom),
#541 (rebrand "underway"; conflated with un-issued repo-rename), #505 (closeout), #548 (memory
pointer). Two independent instances (#483, #541) ⇒ systemic, per "same error twice → fix all
sites."

### Filed + written

- **#560** — data-model fix: derive agenda status on-read at authoring + `umbrella:480`
  grouping label + agenda-lint helper. (Code half = future 1:1:1; behavioral half landed today.)
- **#561** — PERT/roadmap visualization in the Cytoscape control plane (dagre DAG, live
  tracker-derived). The **view** over #560's data model. Depends on #560. Future 1:1:1.
- Cross-linked #560↔#561; annotated #480 umbrella with the trace + actual remaining path.
- Memory `feedback_agenda_author_from_state_not_body` (+ MEMORY.md index) — author carry-forward
  from tracker STATE, not body/prose; close-time counterpart of `feedback_grep_memory_before_issue_body`.

### Brand-boundary decision (operator)

**Beaverdam = new user-facing product only; ESACP stays** ("ERP Systems Administrator Control
Panel") — repo, internals, admin platform unchanged. **No repo rename.** Resolves the S89-era
"repo rename is Senior+operator call" reminder as a definitive **NO**. Recorded in memory
`project_on_boarding_branch` + a #541 comment.

## Decisions

1. Fix direction: **derive-on-read + `umbrella:*` grouping label; no new hand-maintained Kanban.**
2. PERT roadmap (#561) = the visual layer over the same live-tracker data (#560).
3. **No repo rename** — ESACP name stays; Beaverdam is the new product brand only.
4. R6/#483 is **done**; removed from the #480 remaining path.

## Carry-forward prune applied (lands in S94 agenda)

| Stale ref | Disposition |
|---|---|
| #483 / R6 | removed — done S81/S86; remaining #480 path = #456, R1/R3 pipeline-integration, fresh-substrate clean-run |
| #541 | stamped done (closed); repo-rename caveat **resolved NO**, dropped |
| #505 | replaced with standing fact (on_boarding = Junior jurisdiction), untied from closed ref |
| #548 | restated as homed in `feedback_prune_dead_end_options.md` |

## Acceptance

Sidebar deliverables complete: root cause traced + named; all refs audited; #560/#561 filed
and cross-linked; memory written + indexed; brand boundary decided + recorded; carry-forward
reconciled. No code touched (doc/process only, per sidebar scope).

## Artifacts

- Notes: `notes/2026-06-02-1335-agenda-drift-rootcause-and-roadmap.md`
- Issues: #560, #561 (filed); #480, #541 (annotated)
- Memory (LogiSoluMemory): `feedback_agenda_author_from_state_not_body.md` (new),
  `MEMORY.md` (index), `project_on_boarding_branch.md` (brand boundary)
