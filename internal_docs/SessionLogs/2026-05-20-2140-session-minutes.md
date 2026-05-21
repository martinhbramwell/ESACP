# 2026-05-20 2140 — Session 68 minutes

## Session scope

**Agendaed**: create the `on_boarding` branch off `main` and stock it
with the starting kit a fresh Claude Code session on a separate Windows
11 controller will need to develop new-user onboarding functionality
under a zero-knowledge assumption. Per `2026-05-20-2034-next-agenda.md`
(S68).

**Stated objective at session start**: file an ESACP issue for the
branch work, create `on_boarding` off `main` (exact spelling,
underscore), stock with ~4–6 starting-kit files (tenant-free mission/
orientation doc, pointer index into ESACP's technical surface, scope
statement, instructions to the fresh Claude, kit-index README), apply
the tenant-detail scrub gate, close via 1:1:1 PR → merge.

## Pre-flight

- `bash platforms/kvm/sync_check.sh` — 46 ✅ / 9 ⚠️ / 2 ❌. Both ❌ are
  `dev01` (VM shut off + WG unreachable) — matches agenda's expected
  `~46 / ~9 / 2`. dev01 disposable lab substrate per
  `feedback_dev_vms_are_disposable.md`. dev03 + target5 dormant
  (expected off).
- `gh issue list --repo martinhbramwell/ESACP --state open` — **42**
  (matches agenda preflight).
- Sibling-tracker counts: LSKB 9 / ce_sri 6 / ce_sri_svc 2 /
  LogiSoluValidations 2 / BaRe 2 — all match.
- `TRIVIAL_FIXES.md` — 3 entries (S33 monitor + S47 `secrets.py +x`
  + S58 `sync_check.sh:2 Mighty`). None in S68 scope; deferred.

## How the session went

Single objective, scaffolding-class session. Three distinct phases.

### Phase 1 — Issue + branch + kit scoping

Operator approved the stated objective verbatim. Operator immediately
raised a scope-expansion query: should the fresh Win-11 Claude inherit
a subset of the project's AI guard-rails (1:1:1, session management,
no minutiae) and were any of these already in the ESACP directory?
Audit of the repo's existing guard-rail surface produced a pointer
table mapping universal sections of root `CLAUDE.md` + `internal_docs/
qa-contract.md` + `.claude/agents/esacp-qa.md` + subdirectory
`CLAUDE.md` files (universal) against tenant-specific sections
(institutional history of the current tenant). Memory-resident process
rules (no invented commands, plan-before-code, acceptance-test-required,
PR-merged-before-session-close, etc.) identified as not inheritable
unless lifted to the branch.

Operator decision: **inline the global conduct rules** into the kit
(reliability > clean boundary).

ESACP#406 filed; `on_boarding` branch created off `main` (clean,
single commit ahead expected).

### Phase 2 — Kit drafting + three operator interventions

Initial kit drafted as 4 files (instead of separate MISSION + SCOPE +
POINTERS + GUARDRAILS + README — folded MISSION + SCOPE into a single
ORIENTATION.md):

- `ORIENTATION.md` — what ESACP is, target audience, 4-stage user
  journey, in/out scope
- `POINTERS.md` — map into ESACP's repo-resident technical surface
- `AI_GUARDRAILS.md` — inlined globals + project-agnostic process
  rules + repo-resident pointers
- `README.md` — kit index + first-session checklist

Three operator interventions during drafting:

1. **Audience-framing correction**. Draft inherited the current
   operating tenant's posture ("heavily customised ERPNext +
   maintainer-dependent") as the universal frame. Operator corrected:
   target audience is **data-scattered small businesses needing to
   consolidate around ERPNext but unable to justify a dedicated ERP
   consultant**. Maintainer-dependent case re-framed as one of two
   named variants. Sole skew location: `ORIENTATION.md` two sections.
   Corrected.

2. **Concrete categories with examples**. Abstract "point tools,
   manual ledgers" framing was unhelpful for the audience. Operator
   pointed to specific products small businesses actually use (Zoho,
   Shopify, Sage Accounting, Square, TurboTax) and requested at least
   4 categories with several examples each. Expanded to 6 categories
   × 4–6 named examples (accounting / online sales / POS+payments /
   CRM / payroll+HR / tax) plus spreadsheets-as-glue.

3. **Integration-promise caveat**. The categorized product list
   carried an implicit turnkey-connector claim. Operator surfaced
   three preconditions (API surface / EULA permission / ESACP+Claude-
   Code capability) and asked for either a caveat or a confidence-
   graded table. Added both: a caveat subsection in `ORIENTATION.md`
   plus an indicative-readiness table classifying named products by
   API+EULA readiness. Companion rule added to `AI_GUARDRAILS.md`
   under "Project-agnostic process rules" so the fresh Claude
   inherits the same discipline when producing onboarding material.

Operator confirmed retention of `martinhbramwell/ESACP` (6 refs across
the kit) as canonical institutional URL — the fresh Claude needs it to
file issues; precedent matches parent `CLAUDE.md` + the Pages-site
usage.

### Phase 3 — Stage + QA + commit + push + PR + merge

Tenant-detail scrub clean against the agenda's Sub-step 3 pattern list
(LogiSolu family + dev01/dev02/dev03/target5/saconsole/toshiba/mighty
+ bespoke-app names + Spanish field names + iridium.blue). Only
`martinhbramwell/ESACP` retained per Phase 2 operator decision.

T1+T3 combined QA invocation produced approve with one advisory:
trim the 88-character commit-message header to ≤72. Applied (71
chars). GPG-signed commit `c48ad41`, pushed to `origin/on_boarding`.

PR#407 opened. T2 QA invocation produced approve, no conditions. QA
agent specifically evaluated whether the long-lived `on_boarding`
branch triggers umbrella-branch certification protocol and concluded
it does not: this commit is a single discrete S68 deliverable, not a
multi-stage refactor with cross-cutting integration risk. The branch
continues after merge for S69+ work by the fresh Win-11 Claude.

PR#407 merged via merge-commit (preserves GPG sig); `mergedAt =
2026-05-21T01:42:53Z`. ESACP#406 auto-closed at `2026-05-21T01:42:54Z`
via `fixes #406` in commit body. `on_boarding` branch persists on
origin (commit `c48ad41`) per `project_on_boarding_branch.md` plan.

## Sub-task execution

### Sub-task 1 — ESACP#406 filed

`feat(on_boarding): create branch + starting kit for zero-knowledge
Win-11 Claude developing user-onboarding material`. Audience-neutral
issue body (the audience-skew was in the kit drafts, not in the
issue body, so no body edit needed post-correction).

### Sub-task 2 — `on_boarding` branch + kit

4 files / 719 lines under `on_boarding/`. Commit `c48ad41` GPG-signed.
PR#407 → merge commit `8a6d01e` on `main`. Branch persists per
`project_on_boarding_branch.md`.

### Sub-task 3 — Session close artefacts

This file + S69 next-agenda + qa-log Session-68 close-batch row.

## QA verdicts this session

- **T1+T3 (pre-commit + pre-push, §2.1 combined)** on `c48ad41` —
  `approve` with one advisory (header trim, applied → 71 chars). Per
  `feedback_session_end_audit_brevity.md` brevity rule, mechanical
  advisory on otherwise-clean approve does not warrant a qa-log row.
- **T2 (pre-merge)** on PR#407 — `approve`, no conditions. Notable
  reasoning recorded inline in QA verdict: umbrella-branch protocol
  evaluated and explicitly ruled out (single discrete deliverable, not
  multi-stage refactor). Routine approve; no qa-log row per brevity
  rule.

(Two verdict invocations; close-batch row in qa-log is the third and
only logged row, per S58/S65/S66/S67 precedent.)

## Acceptance

Per the S68 agenda Sub-step 5 "joint review with operator at session
end":

- ESACP#406 filed + auto-closed at merge ✓.
- `on_boarding` branch exists on origin with starting-kit commit ✓.
- Kit contents (4 files / 719 lines) match scoping bullets in agenda
  Sub-step 2 ✓.
- Tenant-detail scrub clean per agenda Sub-step 3 patterns ✓.
- PR#407 merged with `mergedAt` non-null ✓ (per
  `feedback_pr_merge_before_session_close.md`).
- `on_boarding` branch preserved on origin for S69+ handoff ✓.

S69+ handoff posture: fresh Win-11 Claude `git switch on_boarding`
finds the starting kit oriented to its zero-knowledge stance, with
inlined conduct + process rules, repo-resident-pointer index, and
explicit audience scope (data-scattered small businesses + 4-stage
user journey + integration-readiness caveat).

## Post-close audit (UserPromptSubmit hook)

Ran clean. All four steps: (1) forward-tense — all in-session
intentions executed and discharged to durable homes (kit files
merged; #406 auto-closed; PR#407 merged; QA verdicts archived in
agent transcripts; advisory header-trim applied). (2) GH issue
references — only #406 referenced; auto-closed via `fixes #406` (the
merge IS the closure; no separate comment needed per
`feedback_no_downstream_of_merge_acceptance.md`). (3) PRs opened —
PR#407 `mergedAt: 2026-05-21T01:42:53Z` verified. (4) Unresolved
doubts — none; all three operator interventions resolved (audience-
framing applied, categorized examples applied, integration caveat +
companion rule applied) and the canonical-URL question explicitly
decided.

## Operator decisions to honor (carried forward)

(Inherits all S67 close decisions + adds S68 outcomes.)

- `LogiSolu` intentional public alias.
- **PRODUCTION_20260404 read-only.**
- **dev01 / dev02 disposable.**
- **CloudStack postponed until V16 is end-user-ready.**
- Trivial-fixes buffer scan at session start.
- `internal_docs/qa-contract.md` v2.1 active.
- **Plan-B Phase 4 substrate is local KVM dev VMs.**
- **Plan-B Phase 4 bespoke-app placement is
  `sales_partner_commissions`.**
- **No passive-causal framing.**
- **Decide-and-advise on logistical micro-decisions.**
- **Memory-grep before treating issue body as authoritative.**
- **No tenant detail on published `docs/` pages OR on `on_boarding/`
  branch.**
- **Pages-classic mode** — `main:/docs` is the live source.
- **Audit Stages 1+2+3+4+5+6 complete S62–S67** — Step 3
  consolidation deferred to S69+.
- **`git mv` + edit ⇒ re-stage before commit** (S58 memory).
- **LSKB#11 ratification deferred** (S63 operator decision).
- **Stage 4 — 100% compliance verdict** (S65 operator decision).
- **Stage 5 — 96.4% compliance verdict (S66 operator)**.
- **Stage 6 — no drift verdict (S67 operator)**; CM-6-A footer
  folded into consolidation session.
- **`on_boarding` branch landed S68** — 4-file starting kit committed
  + merged to main; branch persists on origin for S69+ fresh-Win-11-
  Claude handoff.
- **Audience-framing for ESACP-as-platform**: data-scattered small
  businesses unable to justify a dedicated ERP consultant; the
  maintainer-dependent-customisation case (current tenant) is one of
  two named variants, not the universal frame.
- **Integration-promise discipline**: third-party-product names in
  onboarding material describe a *target landscape*, not a validated
  integration matrix; three preconditions (API surface / EULA /
  ESACP+Claude-Code capability) verified per product before any
  integration claim.
- **Global conduct rules inlined into `on_boarding/AI_GUARDRAILS.md`**
  (reliability > clean boundary) — fresh Win-11 Claude does not need
  its own `~/.claude/CLAUDE.md` to inherit the rules.
- **`martinhbramwell/ESACP` retained on `on_boarding/`** as canonical
  institutional URL (operator decision); generic `<owner>/ESACP`
  abstraction rejected as self-contradictory for a fresh Claude that
  needs the real coordinate to file issues.
- **on_boarding branch governance**: PRs from S69+ sub-branches merge
  *into* `on_boarding`; `on_boarding` → `main` happens only at
  operator-decided milestones (next one open-ended). Not an umbrella
  branch in the strict sense; QA T2 verdict on PR#407 explicitly
  evaluated and ruled this out.
