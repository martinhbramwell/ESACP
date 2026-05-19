# 2026-05-12 1927 — Session 41 minutes

## Objective

**Resolve ESACP #386 — Plan-B Phase 4 bespoke-app placement decision.** Candidate A per Session-40 next-agenda. Self-contained planning-class work: pick from three options for where the V14 migration patch + Server Script install hooks live, capture as a LogiSoluMemory memo, cross-reference from chronology + LSKB#6 + LSKB#12 + ESACP #353. Unblocks the Phase 4 code-class sub-issue ladder (LSKB#13 → #14 → #15 → #16).

## Outcome — Option 1 chosen; placement decision committed + cross-referenced

- **Option 1 chosen**: new dedicated bucket-2 app `sales_partner_commissions` (private repo `martinhbramwell/sales_partner_commissions`, issues filed on LogiSoluKnowBase). DocType definitions remain DB-resident — app holds no DocType fixture exports.
- **Option 2 (catch-all `tenant_bespoke`)** ruled out — would re-materialise the very anti-pattern Plan B is dismantling per `feedback_bespoke_apps_single_responsibility.md`.
- **Option 3 (defer until LSKB#12 finalizes)** ruled out as decision-theatre — no information emerges from LSKB#12 design that bears on placement.
- **Precedent locked**: each code-bearing Plan-B patch gets its own single-responsibility app. No catch-all ever.

## LogiSoluMemory commit

- Branch `housekeeping/s41-phase-4-app-placement` (kept post-merge per `feedback_keep_merged_branches.md`).
- Commit [`39298fe`](https://github.com/martinhbramwell/LogiSoluMemory/commit/39298fe) (GPG-signed, Conventional Commits `docs(plan-b):`, `fixes martinhbramwell/ESACP#386` + Co-Authored-By trailer present).
- Files:
  - `project_phase4_bespoke_app_placement.md` — new decision memo (full reasoning + lifecycle + cross-references)
  - `MEMORY.md` — new Foundational index entry
  - `project_erpnext_idiomatic_refactor.md` — "Premises amended Session 41" subsection
  - `project_sales_partner_commissions_redesign.md` — placement pointer paragraph
- Fast-forward merged to `main`; pushed `66d3a34..39298fe`. Housekeeping branch also pushed.

## ESACP #386 — auto-closed

`ESACP#386` closed at `2026-05-12T22:14:47Z` via cross-repo `fixes martinhbramwell/ESACP#386` in LSM commit `39298fe`. State `CLOSED`. Matches S40 #385 precedent.

## Pointer-comments posted

- ESACP [#353](https://github.com/martinhbramwell/ESACP/issues/353#issuecomment-4435251782) — Session-41 milestone (Plan-B parent epic).
- LSKB [#6](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/6#issuecomment-4435252419) — Phase 4 epic, gating-dependency-resolved + per-sub-issue effects (#12/#13/#14/#15).
- LSKB [#12](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/12#issuecomment-4435252777) — DocType design sub-issue, placement-dependency-resolved + Out-of-scope item cleared.

## QA verdict (combined T1+T3 — pre-commit + pre-push to LSM main)

`esacp-qa` — **approve-with-conditions**. Single condition: confirm the commit body (shown as `<body>` placeholder in the invocation) contains `fixes #386` and the Co-Authored-By trailer. Condition addressed before executing the commit; final body verified to contain both via `git log -1 --show-signature --format=fuller`.

Anti-rubber-stamp evaluation positive: the chosen path (Option 1) is the literal `feedback_bespoke_apps_single_responsibility.md` §"How to apply" prescription ("propose a new dedicated app (e.g. `sales_partner_commissions`)"). The fourth path (BaRe) was correctly identified as not surviving a single read of the rules.

T2 (ff-merge to main) covered by §2.2 carve-out — clean ff, no rebase/cherry-pick, source-branch commit already approved by the combined T1+T3 verdict.

No Trigger 5 (`gh issue close`) invocation needed — #386 closure mechanism was cross-repo auto-close via `fixes`, not `gh issue close`.

## Counts at session end

- ESACP open: **36** (start 37; −1 via #386 auto-close).
- LSKB open: 10 (unchanged).
- ce_sri open: 5 (unchanged).
- LogiSoluValidations open: 2 (unchanged).

## TRIVIAL_FIXES.md status

Unchanged. 1 monitor-only item (LogiSoluMemory Trigger 3 skip).

## Carry-forward operator-reminders (delta)

- **ESACP #386 (bespoke-app placement)** — **resolved** this session. Drop from carry-forward.
- **Phase 4 code-class ladder unblocked**: LSKB#12 (design) can start whenever; LSKB#13 (migration patch) needs `martinhbramwell/sales_partner_commissions` repo standup before coding (tracked at LSKB pickup time per LSKB#6 pointer-comment).
- LogiSoluMemory Trigger 3 skip pattern — unchanged.
- ce_sri local clone in-progress state — unchanged.
- dev02 audit-rerun — still tied to LSKB#15 (substrate apply).
- Tablet WG sidebar (#383) — still ripe for sidebar scheduling.

## Trimmed minutes experiment

This session: ~75 lines, single-target planning-class work. Baseline holds.
