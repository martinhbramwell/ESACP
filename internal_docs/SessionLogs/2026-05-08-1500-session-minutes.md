# 2026-05-08 1500 — Session 14 minutes

## Stated objective at session start

Per `2026-05-07-2236-next-agenda.md`: Track C governance + Track A/B
issue filing — file the structural ESACP issues that govern future
bespoke-app consolidation work, so Sessions 15+ have a deterministic
execution surface. Six sub-tasks: (1) bespoke-app commit-policy issue,
(2) `esacp-qa` wip-rejection issue, (3) three per-app consolidation
epics (route_planner / returnable / ce_sri), (4) comment on #197, (5)
SOPS-encryption issue for `ce_sri_parms.json`, (6) Session 15 agenda.

## How the session actually went

The session pivoted entirely from filing-mode to architectural-design-mode
through operator-driven Socratic questioning. Sub-task 1 (bespoke-app
commit policy issue) was drafted twice and then retired without filing.
None of the original six sub-tasks completed in their original form. The
output of this session is **the long-term plan + close-out artifacts**;
implementation moves to Session 15 as Phase 0 completion.

The pivot path:

1. **Sub-task 1 first draft** — wrote `policy(bespoke): commits must trace
   to ESACP issues; no direct commits to wip/* branches`. Operator's
   first probe: "When may git branches be used?" Surfaced that the rule
   should enumerate *allowed* branch patterns, not just forbid wip/*.
   Revised the draft.
2. **Operator's second probe**: scope question — does the rule apply to
   ESACP itself, or just bespoke apps? Operator surfaced that we need a
   clear distinction between operating-company development work and
   ESACP development work. Identified two distinct governance scopes
   (bespoke-app development vs ESACP-platform development). Revised the
   draft to articulate two tracks.
3. **Operator's third probe**: "Does the new rule against wip branches
   solve a problem or suppress a symptom?" — caught that wip/* prohibition
   was symptom-suppression. The load-bearing rule is the positive triad
   (traceability, reviewable arrival, QA verdict); wip/* prohibition is a
   *consequence*. Operator's fourth probe in same turn: real-name leakage
   audit — the parent had been mirroring the operator's conversational
   use of the company name into the issue body, in violation of
   `feedback_no_real_client_names.md`. Revised the draft again, replacing
   the real name with "operating-company-specific" / "bespoke" throughout.
4. **Operator's fifth probe** on the revised draft: the framing
   ("ESACP is the institutional memory for both the platform and the
   bespoke applications") cemented a conflation that needed unwinding.
   Plan B work, returnable, route_planner, sales-partner-commissions —
   these are operating-company-specific and not pertinent to ESACP's
   future as a generic platform. "Have we left the distinction vague for
   too long to retroactively recreate the distinction successfully?"
5. **Architectural diagnosis**: ESACP currently does two things at once
   — generic AI-assisted ERP-maintenance platform AND issue tracker for
   the operating company's bespoke-app work. Triaged the 32 open issues
   into three camps: ~17 pure platform, ~9 pure bespoke, ~6 mixed.
6. **Tracker semantics established**: defined precisely what "tracker"
   means (GitHub Issues feature on one repo: numbered ticket sequence,
   shared label namespace, `fixes #N` auto-close scope, cross-reference
   surface, search surface). Surfaced the cross-repo `fixes` automation
   break — a real wrinkle for any multi-repo institutional-memory model.
7. **Multi-tenant pressure-test**: operator asked whether the
   shared-tracker-with-N-area-labels model would scale to N tenants
   (`area:bespoke01`, `area:bespoke02`, etc.). Identified three failure
   modes: confidentiality, cross-repo `fixes` × N, label namespace
   blowup. Concluded: **separate trackers per tenant is the only
   structurally sound multi-tenant model**, and option 2 (labels on
   shared tracker) is a structural dead end. **Walked back the
   option-2 lean** to recommend option 1 (separate trackers) even at
   N=1.
8. **Operator's reframing**: introduced the **three-bucket model** —
   ESACP-platform (with BaRe joining it) / operating-company-specific
   bespoke (with `LogiSolu...?` placeholder name) / ERPNext-generic deps
   (ce_sri / ce_sri_svc with own repos, loosely linked to LogiSolu, no
   community-product aspiration). Asked the parent to react without
   generating files.
9. **Naming clearances**: "LogiSolu" cleared for public-repo / public-
   issue use. ce_sri / ce_sri_svc keep current GitHub location.
10. **Discovery-problem audit**: operator asked whether Claude needed a
    private memory git repo. Walked through what the parent's session-
    start protocol actually surveys (one repo, one tracker, local git
    only) and what it does not (other repos' branches, issues, commits).
    Established the **three discipline mechanisms** required to close the
    Session-13-style discovery gap: catalog coverage, bucket-explicit
    session-start surveys, wip/* prohibition. Two-out-of-three is
    insufficient.
11. **Bucket-3 over-articulation pressure-test**: operator surfaced the
    "category-of-one" concern — promoting ce_sri/ce_sri_svc to a named
    architectural bucket might over-articulate. Walked through the
    discovery-problem implication: "loose linking" alone reintroduces
    the original Session 13 failure mode. **Three-bucket framing it is**
    — the third bucket exists to make the discovery surface explicit and
    enumerable, not for sibling-ambition.
12. **Memory-as-repo**: operator floated the idea of a private git repo
    for Claude's memory. Confirmed value (durability, cross-machine
    portability, multi-tenant scaling fit, auditability, structural
    cleanliness). Added `LogiSoluMemory` as a fourth artifact alongside
    the three buckets — Claude's private behavioral memory for this
    tenant. Operator decided: siblings (architectural-decision issue +
    memory-repo issue), not folded.
13. **Long-term plan agreed**: drafted breadth-only plan covering Phases
    0–5 + Tracks A–H. Operator amended: CloudStack dropped (extra
    complexity, low value-added); KVM-on-toshy substrate sufficient
    through V16 cutover; sequential V-ladder cycling confirmed.

## Architectural decisions (filed in Session 15 as ESACP issues)

### Three-bucket architecture + LogiSoluMemory sibling

- **Bucket 1: ESACP-platform** — `martinhbramwell/ESACP`. Generic
  AI-assisted ERP maintenance toolkit any SME could adopt. Includes
  pipelines, cytoscape control plane, observability, QA verdict layer,
  sync_check, the audit framework. **BaRe joins this bucket** (was
  bespoke; backup/restore is universal infrastructure).
- **Bucket 2: LogiSoluKnowBase** — operating company's specific
  business-logic institutional memory + transitional code during
  normalization. Holds tickets for `returnable`, `route_planner`, the
  sales-partner-commissions work, the 31 `in_place_core_edit` drift
  items, LogiSoluValidations governance. Naming convention
  `<Tenant>KnowBase` scales to future tenants.
- **Bucket 3: ERPNext-generic operational dependencies** — ce_sri,
  ce_sri_svc. Currently a category-of-one. Stays at
  `martinhbramwell/ce_sri` and `martinhbramwell/ce_sri_svc`, loosely
  linked to LogiSolu, no community-product aspiration. Existence as a
  named bucket is for **discovery-surface determinism**, not
  sibling-ambition.
- **LogiSoluMemory (sibling decision)** — private git repo holding
  Claude's behavioral memory for this tenant. Naming convention
  `<Tenant>Memory`. **Real-name audit** on the existing memory directory
  is a Phase 1 prerequisite before any first push.

### Three discipline mechanisms (load-bearing together)

1. **Catalog coverage** — every commit on any tracked repo references an
   issue. `esacp-qa` hard-blocks otherwise.
2. **Bucket-explicit session-start surveys** — every session names the
   bucket(s) it touches; session-start surveys each bucket's tracker(s)
   + recent commits + open branches. Lands in memory files (not
   CLAUDE.md only, per operator decision).
3. **wip/\* prohibition** — no future uncatalogued sprawl on any tracked
   repo.

### Naming + privacy posture

- `LogiSolu` cleared for public repo / public issue use.
- `LogiSoluKnowBase` and `LogiSoluMemory` → **private** repos
  (`martinhbramwell/`). GitHub free-tier supports unlimited private
  repos; no charge.
- `ce_sri` / `ce_sri_svc` keep current GitHub location.
- Multi-tenant `<Tenant>KnowBase` org placement → mental placeholder
  for now; future tenants stand up their own GitHub orgs.

## Mission/Vision split

Two M&Vs, both active, mutually informing:

- **LogiSolu M&V** (operating company): family-resilient, AI-maintained
  ERPNext, all bespoke logic normalized into the database, V-current
  upgrade posture, observability + self-repair. Concrete, immediate.
- **ESACP M&V** (platform): generic SME-facing toolkit for migrating
  scattered information projects into integrated ERPNext, with a **safe
  parallel-test substrate for upgrades**. Aspirational, refined slowly.
  **LogiSolu scouts ahead** for the optimal ESACP M&V — every concrete
  LogiSolu lesson becomes ESACP-product evidence.

## Long-term plan (breadth)

### Work tracks

| Track | Purpose | Lives mostly in |
|---|---|---|
| **A — Realignment** | Stand up `LogiSoluKnowBase` + `LogiSoluMemory`. Migrate issues to right trackers. Move BaRe to ESACP-platform. Rewrite memory under three-bucket. Extend session_start protocol. Real-name audit pre-first-push. | ESACP repo + new repos |
| **B — Plan B Execution** | The 31 `in_place_core_edit` drift items resolved into ERPNext-idiomatic patterns. Phases 1–8 of #353 under the new umbrella on LogiSoluKnowBase. `returnable` and `route_planner` get eliminated as separate apps (Phases 7–8). Sales-partner commissions redesign. | LogiSoluKnowBase, bespoke-app repos |
| **C — V-Ladder Climb** | V13 → V14 → V15 → V16 trial migrations + production cutover. Standing upstream-current posture afterward. | LogiSoluKnowBase + parallel-test substrate |
| **D — Platform Engineering** | ESACP feature work: chaos harness (#280), cytoscape decomposition (#219), version watchdog, transport parity follow-ons, audit framework, observability evolution. | ESACP repo |
| **E — Parallel-Test Substrate** (capability spanning C+D) | The "safe space" mission element. KVM/libvirt VMs on toshy + pipeline + BaRe + LogiSoluValidations + version watchdog + chaos harness, integrated as a coherent upgrade-and-test capability. | ESACP + LogiSoluKnowBase |
| **H — M&V Evolution** | Slow track: split `mission_vision.md` into LogiSolu-M&V and ESACP-M&V. Codify ESACP M&V incrementally from observed LogiSolu reality. | Memory + ESACP repo |
| **F — Multi-tenant Readiness** (conditional, parked) | Generic CLAUDE.md template, onboarding runbook. Triggers only on real second tenant. | Deferred |
| **G — Knowledge Transfer** (parked) | Graphical tutorials, family runbooks. Operator deferred. | Deferred |

### Phases (sequence with active tracks)

- **Phase 0 — Architectural Decisions (Session 14, this session)**:
  long-term plan agreed. Two architectural-decision issues to be filed
  in Session 15. *Active: minimal A, H.*
- **Phase 1 — Realignment (~7–10 sessions)**: stand up new repos.
  Migrate issues. Move BaRe. Rewrite memory + CLAUDE.md. Real-name
  audit. Extend session_start.py. *Active: A, H. No B/C/D/E to avoid
  rework.*
- **Phase 2 — Plan B Execution (~15–25 sessions)**: Plan B Phases 1–8
  under new umbrella on LogiSoluKnowBase. **LogiSoluValidations
  authoring precedes Phases 7+8 — hard sequencing constraint** (the
  apps being eliminated need regression coverage before elimination).
  `returnable`, `route_planner` eliminated. Sales-partner commissions
  redesign. *Active: B, partial C (substrate use), partial E
  (regression authoring).*
- **Phase 3 — V-Ladder Climb (~10–20 sessions)**: V13 → V14 trial +
  cutover, then V15, then V16. First demonstration of the parallel-test
  substrate as an end-to-end capability — Track E becomes evidentially
  real. **Sequential cycling** on toshy (one trial VM at a time, dev
  VMs cycled in/out). *Active: C, E, ongoing B follow-ups, ongoing D.*
- **Phase 4 — Operating Company Stabilizes; Platform Continues
  (indefinite)**: LogiSolu enters upstream-current maintenance posture.
  Stages 3 + 4 (Ubuntu Server controller, macOS controller) executed
  this phase. Tracks F + G evaluated for activation. *Active: D, H,
  conditional F+G.*
- **Phase 5 — Indefinite Platform Evolution**: standing platform-
  maintenance + ESACP M&V refinement. Tenant-onboarding (F) triggers
  only on real second tenant. *Active: D, H, conditional F+G.*

### Stage 2.x / 3 / 4 sequencing

- **CloudStack backend dropped** — extra complexity, low value-added.
  Stage 2.x retires from "CloudStack backend, chaos on KVM, version
  watchdog" to "chaos on KVM, version watchdog" (folds into Track D).
- **Stages 3 + 4** → **Phase 4** (controller-machine portability work,
  lower urgency than substrate; non-blocking for V-ladder).

### What this plan deliberately does NOT include

- A timeline. Sessions count is rough; calendar dates depend on cadence
  + interruptions.
- Detail inside each track. Interior-goal work for next conversation.
- Multi-tenant onboarding execution (Track F, conditional/parked).
- Knowledge-transfer authoring (Track G, parked).
- Audit framework parameterisation (#351) sequencing — parked.
- ce_sri / ce_sri_svc maintenance posture details (anticipate continuous
  development; specifics deferred).

## Operator decisions captured this session (close-out reminders)

| # | Operator decision | Captured as |
|---|---|---|
| 1 | Real-name audit on existing memory directory — APPROVED | Phase 1 prerequisite (memory grep + scrub before `LogiSoluMemory` repo init) |
| 2 | `feedback_no_real_client_names.md` recurrence — defer to Phase 1 | No standalone action; Phase 1 memory rewrite covers |
| 3 | LogiSoluValidations precedes Plan B Phases 7+8 | **Hard sequencing constraint** in long-term plan (Phase 2 ordering locked) |
| 4 | Bucket-explicit session-start protocol → memory files | Phase 1 work item: new memory file + `MEMORY.md` index pointer + `platforms/kvm/session_start.py` extension |
| 5 | `umbrella/erpnext-idiomatic-refactor` + `phase-1-fixture-equivalent` repoint or cherry-pick — operator delegates choice, asks for report | Phase 1 work item: parent chooses at execution time (Session 15+); decision + rationale reported in that session's minutes |
| 6 | 16GB toshy ceiling acknowledged | No action; flagged as Phase 3 trigger condition |

## What was NOT done this session

- **No issues filed** — the original six sub-tasks all retired through
  the architectural reframe. Two architectural-decision issues
  (three-bucket + LogiSoluMemory) remain to be filed in Session 15.
- **No PRs opened** — `feedback_pr_merge_before_session_close.md`
  vacuously satisfied.
- **No code changes** — purely deliberative session, output is the plan
  + close-out artifacts.
- **No memory-file rewrites** — the architectural reframe affects ~6
  memory files (`project_wip_consolidation_plan.md`,
  `project_erpnext_idiomatic_refactor.md`,
  `feedback_bespoke_apps_single_responsibility.md`,
  `feedback_bare_is_our_code.md`,
  `feedback_check_existing_wip_before_fresh_work.md`,
  `project_logisolu_validations.md`) plus `MEMORY.md` index. All
  rewrites belong in Phase 1; this session adds only a single index
  pointer to these minutes.

## Real-name discipline this session

Parent slipped into mirroring the operator's conversational use of the
real company name into Sub-task 1's revised issue draft (the unfiled
draft used the real name as a category-label paraphrase across the
issue body — section headings, track names, scope clauses).
Operator caught it in the second probe; parent committed to using
"operating company" / "LogiSolu" / "bespoke" going forward. Verified
by post-commitment scan: held discipline for the remainder of the
session. The drift-and-recovery is captured here as evidence; the
recurrence-section addition to `feedback_no_real_client_names.md` is
deferred to Phase 1 memory rewrite (per operator decision #2 above).

## Issue comments posted this session (8 issues)

Per close-out audit Step 2: every GH issue with a new finding from
this session received a comment pointing to these minutes. Comment
template referenced the forthcoming Session 15 architectural-decision
issue. Per-issue specifics captured below.

| Issue | Reshape under three-bucket framing |
|---|---|
| #353 | Methodology stays on ESACP, execution migrates to LogiSoluKnowBase. Phases 7+8 eliminate `returnable` / `route_planner` apps via DB-residency. |
| #356 | Pure LogiSoluKnowBase work; ticket migrates to LogiSoluKnowBase tracker in Phase 1. |
| #357 | Pure LogiSoluKnowBase work; ticket migrates to LogiSoluKnowBase tracker in Phase 1. |
| #197 | Stays on ESACP (mixed bucket: platform code, bespoke motivation); cross-referenced from LogiSoluKnowBase ce_sri-consolidation work in Phase 2. |
| #343 | Migrates to `martinhbramwell/ce_sri/issues` in Phase 1. |
| #344 | Migrates to `martinhbramwell/ce_sri_svc/issues` in Phase 1. |
| #345 | Migrates to `martinhbramwell/ce_sri_svc/issues` in Phase 1. |
| #354 | Pure LogiSoluKnowBase work; migrates in Phase 1. |

## Session 15 Phase 0 work

- **File two architectural-decision issues** on ESACP:
  1. Three-bucket architecture + naming convention + discipline
     mechanisms + migration roadmap.
  2. `LogiSoluMemory` private memory repo (sibling decision).
- **Optional Track H seedling**: M&V split scaffolding decision.
- **Estimated wall-clock**: 1–2 hours.

## Files at session-end

- `docs/SessionLogs/2026-05-08-1500-session-minutes.md` (this file)
- `docs/SessionLogs/2026-05-08-1500-next-agenda.md` (Session 15 brief)
- `docs/qa-log.md` (Session 14 verdict appended)
- `MEMORY.md` (single index pointer added to these minutes)

## QA verdicts batched

See `docs/qa-log.md` row for 2026-05-08 — Session 14 close-out doc
sweep. Verdict batched at session-close per the contract.
