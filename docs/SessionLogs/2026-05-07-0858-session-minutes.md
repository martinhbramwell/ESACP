# 2026-05-07 0858 — Session 12 minutes (carry-forward triage; Phase-1 deferred)

## Stated objective at session start

Per `2026-05-07-0748-next-agenda.md`: Phase 1 of ESACP #353 — replace 18
`fixture_equivalent_core_edit` patches with Custom Fields on dev02.

## How the session actually went

Operator restated the immediate objective at message 2: triage the six
carry-forward concerns from Session 11 minutes (Polvo de Roca decision,
22 catalogue TBDs, redis/rq override, ESACP #352, Server Script
mislabel, dev01 sync_check #278). Phase 1 deferred. The session became
a planning / triage session rather than the substantive Phase-1
session the agenda anticipated.

Three meta-questions surfaced during triage:

- **(Q1)** Is the triage guidance sufficient to close the reminders?
- **(Q2)** Are many issues rendered moot by Plan B?
- **(Q3)** Is BaRe the correct place for production→post-refactor
  data transformation?

Mid-session operator-driven course corrections:

1. **Item 5 pushback** — operator: "This is the kind of minutiae you
   need to resolve and report, rather than requesting guidance."
   Self-applies `feedback_consultant_not_peer_engineer.md`.

2. **Item 4 reframe via LogiSolu rethink** — operator question "we
   need a repo for Playwright functional and regressions. Valid?"
   walked back the earlier-this-session proposal to close #352 as
   won't-fix. LogiSoluValidations has enduring scope under Plan B
   (SRI integration, post-redesign commissions, ladder acceptance
   gates, surviving DB-resident logic). Retraction posted on #352
   itself.

3. **BaRe / `bench migrate` clarification** — operator asked T/F
   whether refactoring redefines schemas in ways `bench migrate`
   can't resolve. Answer: false. Schema redesigns of this shape
   live as Frappe patches in bespoke apps, registered in
   `patches.txt`, run during `bench migrate`. BaRe stays pure
   backup/restore.

4. **Plan A/B and 6 phases restated in plain language** — operator
   reported context loss; restated cleanup phases 1–6 and Plan B
   chronology in non-technical terms.

5. **Session-realism check** — operator asked whether Phases 1+2+3
   could be done in this session. Answer: no, per 1:1:1 discipline
   each phase is its own sub-branch / session under
   `umbrella/erpnext-idiomatic-refactor` (umbrella criteria met but
   not yet created).

## What landed

### Memory (auto-memory, outside repo)

- `project_erpnext_idiomatic_refactor.md` — Phase 3 row updated:
  V14.101.1 stock check (`redis~=3.5.3`, `rq @ frappe-fork-commit`)
  shows the `redis 4.3.0 / rq 1.10.1` override is **incompatible**
  with V14 stock. Phase 3 reclassified Low → Medium (operational
  decision: keep / match-stock / defer-to-V15+, not auto-droppable).
- `project_erpnext_idiomatic_refactor.md` — new section
  `## Where migration patches live (not BaRe)` anchors the
  cutover-flow boundary: BaRe restores production V13 → `bench migrate`
  runs registered Frappe patches → suite gates → climb V14→V15→V16.

### Issues filed / commented

- **ESACP #354** filed — `doc(commissions): Sales Partner Commission
  Server Scripts have misleading event names`. Reader-trap on
  "After Submit" Server Script (fires Before Submit). Resolution path:
  fixed incidentally by #353 Phase 4. Labelled `documentation`.
- **ESACP #353** commented — V14 stock check finding + Frappe patch
  (not BaRe) boundary. ([comment](https://github.com/martinhbramwell/ESACP/issues/353#issuecomment-4397061168))
- **ESACP #352** commented — Session 12 reconsidered position;
  initial close-as-won't-fix retracted, issue stays open. Re-evaluation
  criterion: first substantive code-change PR on LogiSoluValidations.
  ([comment](https://github.com/martinhbramwell/ESACP/issues/352#issuecomment-4397298540))

### Decisions recorded

- **Item 2 (22 catalogue TBDs)** — confirmed: tracking adequate as
  Phase 5 of #353; no separate action.
- **Item 6 (#278 dev01 carve-out)** — confirmed: leave for next
  housekeeping bundle.
- **BaRe boundary** — transformation patches live in
  `bespoke_app/patches/v14_xxx.py`, never in BaRe.
- **Phase-1 deferral** — Session 13 (next) opens Phase-1 work; this
  session ends as planning.

## What's owed (carrying forward to Session 13)

### Operator decisions still pending

- **Item 1a — Polvo de Roca** — option (a) old way in production
  now / (b) defer to V14 / (c) old way + replicate as migration test
  data on dev02. Recommendation: (c). Decision recorded in
  `memory/project_sales_partner_commissions_redesign.md::Open
  operational decision` once made.
- **Item 1b — Phase 4 sequencing interpretation** —
  (i) Plan B order unchanged, just emphasis vs (ii) Phase 4 jumps
  ahead of cleanup + Playwright suite. (ii) inverts Plan B's safety
  argument and needs explicit retirement.
- **Q2 — 9-issue moot-sweep authorization** — candidates: #312,
  #339, #297, #296, #292, #290, #285, #284. (#352 *removed* from
  this list — retraction above.) All would close with comments
  pointing to #353 / "Plan A retired by Plan B".

### Setup work for Session 13

- File Phase-1 sub-issue under #353 with the explicit list of 18
  `fixture_equivalent_core_edit` entries from
  `audit/_work/delta_report_dev02.json`
- Create `umbrella/erpnext-idiomatic-refactor` off main (criteria met:
  >3 sub-branches expected, cross-cutting fixture files, broad-context
  audit-rerun acceptance)
- Cut Phase-1 sub-branch off umbrella

## QA verdicts this session

| Gate | Verdict | Notes |
|---|---|---|
| Pre-commit (minutes + next agenda; doc-only) | TBD — esacp-qa invocation pending below | No code change; memory edits + issue comments executed in-flight |

## 1:1:1 / housekeeping discipline

Session opened on substantive (Phase 1) but immediately reframed by
operator to triage / planning. Three issues touched (#352 commented,
#353 commented, #354 created). Memory edits + issue comments are
discovery / planning artefacts, not behavioural code change. Within
housekeeping-bundle norms; no working-tree code drift.

## Issues touched

- **ESACP**: #352 commented (rethink), #353 commented (V14 + BaRe),
  #354 opened (Server Script mislabel). #312, #339, #297, #296, #292,
  #290, #285, #284 referenced as moot-sweep candidates but no comments
  posted (operator authorization pending). #278 referenced as housekeeping
  carry-forward; no new finding.
- **LogiSoluValidations**: none touched this session.

## Audit gap closed

Initial draft of close-out missed posting the #352 rethink as a comment
on #352 itself; would have left the retraction strand-stuck in minutes.
Caught by the close-out audit's step 2 (every issue referenced gets
its findings on the issue, not deferred to minutes). Posted prior to
writing these minutes.
