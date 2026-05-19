# 2026-05-07 0748 — Session 11 minutes (PR #1 merge + strategic refactor direction)

## Stated objective at session start

Per `2026-05-05-1831-next-agenda.md` Path A: review LogiSoluValidations PR
#1 (DB-resident customization discovery sweep), triage catalogue TBD
fields, merge to umbrella when ready. Acceptance: PR #1 `mergedAt`
non-null.

## How the session actually went

Operator refused the Path A framing as too process-heavy. The session
expanded substantially beyond the stated objective into architectural
discovery and strategic-direction recording. Three operator-driven scope
shifts:

1. **Operator went to GitHub to read the README on `main`, found it
   English, said "It is still in English!!!"** — surfaced that PR #1's
   Spanish staffer section was unmerged and the README on `main` was the
   English bootstrap version. The session-start review had flagged PR
   #1's open state as "Path A is gated on review" rather than "the
   Spanish content you want to read is stuck behind your review." Wrong
   framing, corrected.

2. **PR #1 + umbrella merged direct to main** with explicit operator
   sign-off: "Look, there is nothing of value on main. Since the repo
   was started everything of value is on branches, rendered useless
   until you merge them into main." Two merges executed (PR #2:
   discovery-sweep → umbrella; certification merge umbrella → main).
   esacp-qa verdicts at both gates: approve-with-conditions on the first
   (advisory: dev02.iridium.blue hostname leak in catalogue YAML, TBD
   triage override) and approve on the second.

3. **Operator critiqued the just-merged Spanish staffer section in six
   specific points** — condescending intro blockquote, second-person
   feigned familiarity in the Chrome/Mac-Mini paragraph, paragraph
   listing what the staffer doesn't need to know, bullet labels with no
   verb-phrase task, letter prefixes (A/B/C/D/E/F/G/H/A1) confusing,
   empty "Notas — sin notas" stubs adding nothing. PR #3 revised the
   section per all six. Direct-to-main per CLAUDE.md doc-only PR rule.

After the doc work, the session pivoted to architectural discovery
triggered by the Sales Partner Customer Item Commissions DocType
referenced in the staffer README:

4. **Operator showed dev02 form screenshot** revealing the actual
   structure: standalone DocType (`istable=0`, NOT a child table as
   catalogue + README A1 claim), with **dozens of Custom Fields per
   product** organised into Item-Group section breaks. Companion
   DocType `Asignar Producto a Campo` maps Item code → Custom Field
   name. Schema-as-data: every new product is a DDL change.

5. **Operator articulated the V14-window redesign**: master/detail,
   entirely DB-resident. Parent: sales_partner+customer. Child table:
   item+commission_rate. Drop `Asignar Producto a Campo` (job done by
   parent/item columns). Rewrite Server Scripts. One-shot migration
   patch. DB-resident chosen over new-Frappe-app on operator-self-service
   grounds (mission point: family adds new product line by clicking
   +Add Row, no developer deploy).

6. **Operator corrected my "BaRe fixture / route_planner consumer"
   sloppiness** — bespoke apps are single-responsibility (BaRe =
   backup/restore, route_planner = delivery routing, ce_sri = SRI,
   returnable = containers). Saved as
   `feedback_bespoke_apps_single_responsibility.md`.

7. **Operator asked: can returnable + route_planner also be DB-resident,
   or must they be apps?** — research answered: route_planner trivially
   yes (empty `hooks.py`, no behavioural wiring); returnable yes with
   real porting work (200+ lines of `hook_tasks.py`, file-I/O logging
   blocked by `safe_exec` sandbox). Plus a reference table of which
   `hooks.py` mechanisms have DB-resident equivalents (DocType Event
   Server Script, Scheduler Event Server Script, etc.).

8. **Operator articulated the deeper strategic question** — would
   refactoring everything correctly into ERPNext make the V13→V14→V15→V16
   ladder become standard? Verdict: substantially true, ~85–90% of the
   V14-upgrade headache is inexperience-driven and eliminable. 28 of 31
   `in_place_core_edit` patches are clearly avoidable artefacts (18
   should-have-been-Custom-Fields, 10 discardable, 2 debug-print litter,
   1 dependency-pin override that's a real deployment question). Saved
   as `project_erpnext_idiomatic_refactor.md`.

9. **Operator contemplated Plan B** — refactor first, then stand up the
   migration substrate, then capture activity, then climb. Operator
   clarifications applied: time pressure not a concern, staffer-recording
   premise retired (operator can replicate workflows faster than
   explaining them), substrate is CloudStack VM (Stage 2.x architectural
   pattern) not third-party VPS, no privacy concern (production already
   on third-party VPS).

10. **Plan B chosen.** Memory updated: Plan A retired, chronology
    captured (Phases 1,2,3,6 → Phase 5 → CloudStack VM stand-up → suite
    authoring → Phase 4 under cover → climb ladder → cut over
    production). Untangled the planning stack — three memory files
    cross-checked for consistency, MEMORY.md index updated.

## What landed

### LogiSoluValidations
- PR #1 merged → umbrella → main (discovery-sweep landing on main)
- PR #2 merged (umbrella → main certification merge)
- PR #3 merged (revised Spanish staffer section direct to main per six
  operator critiques)
- All branches in parity with main (umbrella behind 1, discovery-sweep
  behind 2 — kept per `feedback_keep_merged_branches.md`)

### ESACP memory
- New: `project_sales_partner_commissions_redesign.md` — actual structure
  + V14-window redesign direction (master/detail DB-resident)
- New: `feedback_bespoke_apps_single_responsibility.md` — BaRe = backup/
  restore, ce_sri = SRI, returnable = containers, route_planner =
  routing; do not bolt unrelated logic into them
- New: `project_erpnext_idiomatic_refactor.md` — Plan B chosen, 6-phase
  cleanup chronology, premises confirmed, Plan A retired
- New: `reference_db_resident_hooks_table.md` — lookup table for
  "can app X be DB-residentized?" decisions, plus per-app verdicts
- Updated: `project_logisolu_validations.md` — authoring shift (tests
  written directly by operator + AI on CloudStack VM substrate, staffer
  recording retired)
- Updated: `MEMORY.md` index — four new pointers, two updated entries,
  "7-phase" → "6-phase" correction

### Issues filed at session close
- **LogiSoluValidations #4** — catalogue YAML + README Section A1
  mis-describe commissions DocType as "Custom child table" (`istable=0`
  — verified against `delta_report_dev02.json` row_data and live form)
- **LogiSoluValidations #5** — README Cross-references describes BaRe
  as "bespoke business-logic app"; should be "backup/restore CLI
  utility"
- **ESACP #353** — parent epic for the strategic refactor; 6-phase
  checklist; Plan B chronology; sub-issues per phase to be filed as
  each phase begins (1:1:1 discipline)

## What's owed (carrying forward to Session 12)

- Fix the bugs filed as LogiSolu #4 and #5 (issue capture is done; PR is
  the deferred work)
- File Phase 1 sub-issue under ESACP #353 when Session 12 starts
  (Phase 1 = replace 18 `fixture_equivalent_core_edit` patches with
  Custom Fields on dev02)

## QA verdicts this session

| Gate | Verdict | Notes |
|---|---|---|
| Pre-merge PR #1 → umbrella | approve-with-conditions | dev02.iridium.blue hostname in catalogue (advisory); TBD triage operator-overridden |
| Pre-merge umbrella → main | approve | hostname not a real-name-rule violation; mission alignment direct |
| Pre-commit/push/merge PR #3 | approve | doc-only README revision, all six fixes verified in diff |

## 1:1:1 / housekeeping discipline

Session opened on Path A (PR #1 review) — substantive, single-issue.
Three merges (PR #1, #2, #3) all in LogiSoluValidations; PR #3 was an
unplanned scope expansion but classifies as housekeeping (doc-only,
no behavioural change). The architectural discussion + memory updates
are planning, not code. Within housekeeping-bundle norms.

## Issues touched

- **ESACP**: #353 opened (parent epic for strategic refactor); existing
  #312/#330/#339/#344/#345/#349/#350/#351/#352 referenced in #353 body
  as cross-references but no comments owed (no new findings on those
  specific issues this session)
- **LogiSoluValidations**: PRs #1, #2, #3 all merged (`mergedAt`
  non-null verified at session close); issues #4 and #5 opened (doc
  bugs on `main` content)
