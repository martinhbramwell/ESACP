# Buffer-overflow audit (ESACP#400)

Multi-session audit reassessing whether Plan-B execution has drifted from
Plan-B and Mission-and-Vision planning. See
`memory/project_buffer_overflow_audit_plan.md` for the framing document
and trigger incident.

- **Anchor issue**: [ESACP#400](https://github.com/martinhbramwell/ESACP/issues/400)
- **Window**: S11 (2026-05-06) → present
- **Bucket**: 1 (ESACP-platform) — methodology-stays
- **Report path**: `internal_docs/AuditReports/2026-05-19-buffer-overflow-audit.md`
  (in-tree, internal-only; published `docs/` slot is GitHub Pages per #402)

---

## Step 1 — Overall plan review (S60)

**Date**: 2026-05-19
**Owner**: Session 60
**Status**: Step 1 only — Step 2 (stage list) defers to S61

### Sub-step 1 — Memory-grep gate

Mandatory pre-work grep gate per
`project_buffer_overflow_audit_plan.md`. Three keyword classes swept
across `memory/` and `internal_docs/SessionLogs/`. No "cold spot" risk
detected — all three planning anchors are alive in current memory and
recent minutes.

| Anchor | memory/ files | SessionLogs/ files |
|---|---:|---:|
| Plan B / `idiomatic_refactor` | 17 | 93 |
| three-bucket / `#358` | 15 | 52 |
| `mission_vision` / "Mission and Vision" | 9 | 11 |

Most-referenced memory files for each anchor:

- **Plan B**: `project_erpnext_idiomatic_refactor.md`,
  `project_buffer_overflow_audit_plan.md`,
  `project_phase3_redis_rq_decision.md`,
  `project_phase4_bespoke_app_placement.md`,
  `project_sales_partner_commissions_redesign.md`,
  `project_wip_consolidation_plan.md`,
  `archive/project_plan_b_remaining_roadmap.md`.
- **three-bucket / #358**: `MEMORY.md`, `bucket_definitions.md`,
  `project_bare_bucket_1_association.md`,
  `project_bucket_2_migration_pattern.md`,
  `project_wip_consolidation_plan.md`,
  `feedback_pr_fixes_comma_syntax.md`.
- **Mission and Vision**: `mission_vision.md`, `context_domains.md`,
  `PROTOCOLS.md`, `feedback_consultant_not_peer_engineer.md`,
  `feedback_no_manual_v14_cutover.md`,
  `project_buffer_overflow_audit_plan.md`,
  `project_pages_site_v1.md`.

Conclusion: gate **passes**. Step 1 is safe to proceed.

### Sub-step 2 — Active strategic plan

#### 1. Plan B — `project_erpnext_idiomatic_refactor.md`

- **What it says**. Refactor every customisation in the bespoke fleet
  to ERPNext-native idioms **before** continuing the V14 upgrade
  attempt. Goal: the V13→V14→V15→V16 migration ladder becomes the
  standard `bench backup → bench migrate → regression run` procedure.
  31 in-place core edits classified at Session 10 — 28 are inexperience
  artefacts (18 fixture-equivalent + 10 discardable + 2 debug-print
  litter), 1 is operational (redis/rq pin override), 2 are real edits
  but small. Plan B is 8 phases under parent epic
  [ESACP#353](https://github.com/martinhbramwell/ESACP/issues/353).
  Methodology stays on ESACP (bucket-1); execution sub-issues filed on
  LSKB (bucket-2) as LSKB#2–#10.
- **What it gates**. The V13→V14 cutover. After Phase 8 the system is
  fully ERPNext-idiomatic on V13 and standard `bench migrate` carries
  it forward to V14/V15/V16. Substrate amended S40: local KVM dev VMs
  (CloudStack deferred until V16 end-user-ready per
  `project_cloudstack_deferred_until_v16.md`).
- **Recent amendments** (last-touched per `git log` on the memo):
  - S41 (2026-05-12) — Phase 4 bespoke-app placement = new
    `sales_partner_commissions` app (bucket-2, LSKB tracker). Resolves
    ESACP#386.
  - S40 (2026-05-12) — Phase 4 substrate re-target to local KVM;
    LSKB#6 scope-trim into sub-issue ladder LSKB#13–LSKB#16.
  - S12 (2026-05-07) — no-rework sequencing principle moved all
    behavioural refactors (Phases 4/7/8) ahead of Playwright suite
    authoring.
  - S58 (2026-05-19) — close-out batch + S57 orphan landed; memo
    itself last touched.

#### 2. Three-bucket architecture — [ESACP#358](https://github.com/martinhbramwell/ESACP/issues/358) + [ESACP#359](https://github.com/martinhbramwell/ESACP/issues/359)

- **What it says**. Three institutional buckets for all ERP-maintenance
  work on this tenant:
  - **Bucket 1 — ESACP-platform** (this repo): generic AI-assisted
    ERP-maintenance toolkit.
  - **Bucket 2 — LogiSoluKnowBase**: tenant business logic + Plan B
    execution. Holds `returnable`, `route_planner`, commissions,
    `in_place_core_edit` drift items.
  - **Bucket 3 — `ce_sri` / `ce_sri_svc`**: ERPNext-generic
    operational dependencies.
  - **Bucket 1 associate — `BaRe`**: backup/restore companion;
    modifiable; own tracker.
  - **Sibling artefact — LogiSoluMemory** (#359): Claude Code
    behavioural memory; mounted via symlink at
    `~/.claude/projects/<encoded>/memory`.
- **What it gates**. Where issues live by app; where commits
  reference; the QA verdict layer's catalog-coverage check; the
  bucket-explicit session-start surveys driven by
  `session_buckets.txt`; the `wip/*` prohibition on all tracked repos.
- **Recent activity**. Established at S33 (~2026-05-08); discipline
  mechanisms in continuous use through S59. No amendments outstanding.

#### 3. Mission and Vision — `mission_vision.md`

- **What it says**. ESACP exists so a small family-owned manufacturing
  business can maintain and enhance its heavily-customised ERPNext
  system without depending on any single developer. Required
  properties: self-explanatory, operable by non-technical family
  members, capable of generating graphical tutorials, capable of
  explaining repair operations step-by-step, backed by persistent
  records and MCP connectors. **ERPNext MCP** is the core of the
  mission, not a future nice-to-have; the entire infrastructure layer
  exists to make AI-assisted ERP access reliable. Self-repair answers
  "11pm Friday when the ERP is down and there is no developer to call".
- **What it gates**. Priority of work. Infrastructure that does not
  serve the path to ERPNext MCP integration is lower priority than it
  might appear. UI/doc audience is non-technical family, not
  engineers.
- **Recent activity**. Foundational; 60 days old per memory load
  warning. Predates Plan B declaration. No outstanding amendments.

### Sub-step 3 — Active execution surface

#### Open issues per bucket (2026-05-19, S60 start)

| Bucket | Repo | Open issues |
|---|---|---:|
| 1 | ESACP | 43 |
| 1 associate | BaRe | 2 |
| 2 | LogiSoluKnowBase | 8 |
| 2 | LogiSoluValidations | 2 |
| 3 | ce_sri | 6 |
| 3 | ce_sri_svc | 2 |
| **total** | | **63** |

ESACP at 43 is +1 vs the count expected by the S59 next-agenda (42);
minor drift, not chased here.

LSKB issues are exclusively Plan-B execution rows (Phases 2/4/7/8 +
verifications + chore #18). ce_sri #10 is the trigger-incident issue
that motivated this audit — still open, gated on audit resumption.

#### Audit-window minutes (S11 → S59)

- Audit window opens 2026-05-06 (S11, Plan B declaration).
- Session-minutes files since 2026-05-06: **48**.
- Total session-minutes files in the repo: 147.

#### Active branches

Live umbrella branches:

| Branch | Last commit | Status |
|---|---|---|
| `umbrella/erpnext-idiomatic-refactor` | 2026-05-07 | dormant since S12 |
| `umbrella/ladder-fixture` | 2026-04-24 | orphan — pre-#358 (#361) |
| `umbrella/pages-site-v1` | 2026-05-19 | merged to main S58/S59 |

Recently active feature/fix branches (last 14d) — 12 distinct,
including `fix/398-mariadb-performance-schema-off`,
`fix/392-uv-prerelease-allow`, `fix/388-packer-as-saconsole-dep`,
`docs/404-pages-site-followup`. Local non-main branch total: **112**
(most stale; full inventory not enumerated this step — falls under
`project_wip_consolidation_plan.md`).

### Sub-step 4 — Initial observations (held for Step 2)

Observations gathered during enumeration. Per audit plan they are
captured but **not acted on** at Step 1 — Step 2 stage list partitions
them across stage iterations.

1. **Plan-B execution-surface footprint vs ESACP open issues**. LSKB
   carries 8 Plan-B execution issues; ESACP carries 43 open issues,
   almost none of which are direct Plan-B execution. Suggests
   bucket-placement discipline is broadly holding (Stage 1 candidate
   from the audit-plan stage list).
2. **Plan-B current locus**. LSKB#15 (Phase 4 substrate-apply) and
   LSKB#16 (verification) are the gating execution rows. Both are
   paused pending audit resumption. Phases 7/8 (LSKB#9/#10) are open
   parallel-track and unblocked in principle. Phases 1/2/3/5/6 status
   per memo + minutes not re-verified at Step 1 — falls under Stage 2
   (phase mapping).
3. **Mission-and-Vision activity in recent sessions**. Mentions
   concentrated in two clusters: the three-bucket framing sweep
   (S33-area, 2026-05-08) and the audit-plan and Pages-site work
   (S56-S58). Otherwise sparse — most sessions operate at the
   execution level, not the mission level. Whether shipped work
   advances the self-repairing-platform mission is a Stage 6
   question, not answered here.
4. **`umbrella/ladder-fixture` orphan**. Tracked as ESACP#361, dormant
   since 2026-04-24, pre-dates the #358 umbrella policy. Not a Step-1
   item; flagged for its own session per the operator-reminder list.
5. **ESACP-issue inventory at 43 vs S59 expected 42**. +1 drift
   between agendas, source not identified. Negligible at this stage;
   if it recurs, candidate for Stage 1 (catalog coverage).
6. **Memory document staleness**. `mission_vision.md` is 60 days old
   per memory-load warning; `project_erpnext_idiomatic_refactor.md` is
   6 days old. Mission and Vision pre-dates Plan B — content remains
   foundational but not been re-touched against Plan B's amendments.
   Candidate refresh trigger if Stage 6 surfaces drift.

### Step-1 verdict

Enumeration complete. All three planning anchors are documented,
referenced in current memory, and reflected in active execution
artefacts. The audit can proceed to Step 2 (stage list proposal) in
S61.

No corrective actions ordered at Step 1.

---

## Step 2 — Stage list proposal (S61)

**Date**: 2026-05-19
**Owner**: Session 61
**Status**: Stage scopes drafted; no stage executions this session.
Stage 1 starts S62 at the earliest.

Six stages in memo order 1→6 (operator decision, S60 Sub-step 5). Each
stage block specifies (a) the question it answers, (b) the mandatory
memory-grep gate keyword set, (c) the corpus the stage audits, (d) the
partitioning rule that keeps the stage iteration inside one session's
working context, and (e) the deliverable shape for the stage's report
section.

**Universal preconditions** — apply to every stage:
- **Audit window**: S11 (2026-05-06) → present (per audit plan).
- **Mandatory memory-grep gate**: every stage iteration opens with
  `grep -rl <key> memory/` and `grep -rl <key> internal_docs/SessionLogs/`
  sweeps; gate output is captured into the stage section.
- **Non-compliance entries**: each item is a row with a brief
  corrective-measure note; "no non-compliance found" is a valid
  deliverable.
- **One stage per session** (per audit-plan procedure Step 3).

---

#### Stage 1 — Bucket-placement compliance

**Question**. Are issues, commits, and memory living in the bucket
[ESACP#358](https://github.com/martinhbramwell/ESACP/issues/358)
prescribes?

**Grep gate**.
- `grep -rl bucket_definitions memory/`
- `grep -rl 'bucket-[123]' memory/`
- `grep -rln '#358\|#359' internal_docs/SessionLogs/`
- `grep -rln 'wip/' internal_docs/SessionLogs/`

**Corpus**.
- Memory: `bucket_definitions.md`, `project_bucket_2_migration_pattern.md`,
  `project_wip_consolidation_plan.md`,
  `project_bare_bucket_1_association.md`.
- Issues: all open issues across the six trackers (ESACP 43 / BaRe 2 /
  LSKB 8 / LogiSoluValidations 2 / ce_sri 6 / ce_sri_svc 2 — total 63).
- Commits: every commit on `main` of every tracked repo since S11 that
  carries `fixes #N` — verify the `fixes` target tracker matches the
  bucket the commit's content belongs to.
- Branches: live `wip/*` branches on any tracked repo (expected: none
  post-#358 on ESACP; pre-#358 carry-overs flagged in
  `project_wip_consolidation_plan.md`).

**Partitioning rule**. One pass per bucket (6 passes). Each pass reads
only that bucket's tracker + that bucket's slice of commits. Bucket-1
(ESACP) is the largest pass at 43 issues; still well under the
session-context envelope.

**Deliverable shape**. Per-bucket subsection. Each subsection contains:
(i) the grep-gate output table; (ii) an `issues` table — issue title,
current location, prescribed location, drift Y/N, corrective measure;
(iii) a `commits` table — commit, `fixes` target, prescribed target,
drift Y/N. Final summary: count of drift items; explicit
"discipline-mechanisms #1/#2/#3 holding" verdict, or named gap.

---

#### Stage 2 — Plan-B phase mapping

**Question**. Where in the 8-phase plan
([ESACP#353](https://github.com/martinhbramwell/ESACP/issues/353))
are recent sessions actually operating? Are phase boundaries
respected, or has scope crept across phases?

**Grep gate**.
- `grep -rl 'Plan B\|idiomatic_refactor' memory/`
- `grep -rl 'project_erpnext_idiomatic_refactor' memory/`
- `grep -rln 'Phase [1-8]' internal_docs/SessionLogs/`
- `grep -rln 'LSKB#\|#353' internal_docs/SessionLogs/`

**Corpus**.
- Memory: `project_erpnext_idiomatic_refactor.md`,
  `project_phase3_redis_rq_decision.md`,
  `project_phase4_bespoke_app_placement.md`,
  `project_sales_partner_commissions_redesign.md`,
  `archive/project_plan_b_remaining_roadmap.md`.
- Issues: LSKB #2–#10 (Plan-B execution rows); LSKB #15/#16 (Phase 4
  substrate-apply gating); ESACP#353 (parent epic methodology).
- Minutes: S11→S60 (48 files) — section `Session scope` + `Work done`
  per session, tagged with phase number.

**Partitioning rule**. One pass per phase (8 passes), each pass reads
only the sessions that touched that phase plus the phase's memo
section. Phases with no sessions in-window collapse to a single line
("no activity in window"). Two phases (4 and 7/8) carry most of the
session count; partition further by sub-phase if needed.

**Deliverable shape**. Per-phase subsection: (i) memo summary in one
sentence; (ii) sessions that touched the phase (table — session,
date, work-done snippet); (iii) status (not-started / in-progress /
paused / done); (iv) scope-creep instances — work that should have
landed in a later phase, or work that bypassed a gating phase. Final
summary: phase-by-phase status table; drift items with corrective
measures.

---

#### Stage 3 — Memory hit-rate (relevant vs consulted)

**Question**. Per recent session, which memory files were *relevant
to the work* vs *actually consulted before acting*? This is the
audit's direct response to the S56 trigger — the grep-failure that
treated an issue body as authoritative when memory held the answer.

**Grep gate**. Per-session, derived from the session's primary
work-item:
- For each session N, identify the primary issue/topic T.
- Run `grep -rln <T's-key-terms> memory/` — produces the *relevant*
  memory set.
- Read session N's minutes "Sub-step 1 / Work done" — produces the
  *consulted* memory set.
- Set-difference (relevant minus consulted) = potential miss.

**Corpus**.
- Minutes: S11→S60 (48 files).
- Memory: all `memory/*.md` files (~80+).
- Issues: bodies of issues picked up in each session.

**Partitioning rule**. Full-pass shallow triage — every session gets
a single yes/no/n/a verdict ("did Sub-step 1 grep memory for the
session's topic?") with a one-line evidence note. Drill-into-detail
only on the no's. 48 sessions × shallow triage fits one session;
the no's are then itemised in the deliverable. If no-count exceeds
~10, split the drill-in across multiple sub-stages (operator-confirm
before extending).

**Deliverable shape**. (i) Triage table — session, primary issue,
key memory terms, grep-evidence Y/N/n/a; (ii) the no's table —
session, what memory should have been consulted, what corrective
measure (e.g., new operator-reminder, new pre-commit hook,
elevation to `feedback_*.md`); (iii) explicit confirmation that
the S56 trigger incident is one such no, and its corrective measure
(`feedback_grep_memory_before_issue_body.md`) is already shipped.

---

#### Stage 4 — Acceptance-test compliance

**Question**. Per
[`feedback_acceptance_test_required.md`](../../.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/feedback_acceptance_test_required.md),
have recent issue closes shipped acceptance tests or recorded
acceptance evidence?

**Grep gate**.
- `grep -rl feedback_acceptance_test_required memory/`
- `grep -rln 'acceptance' internal_docs/SessionLogs/`
- `grep -rln 'acceptance' internal_docs/qa-log.md`

**Corpus**.
- Memory: `feedback_acceptance_test_required.md`,
  `internal_docs/qa-contract.md`,
  `feedback_no_downstream_of_merge_acceptance.md`.
- Issues: all closes across all six trackers since S11 (window-bounded
  via `gh issue list --state closed --search 'closed:>2026-05-06'`).
- QA log: `internal_docs/qa-log.md` rows since S11.
- Commits: every `fixes #N` close-commit since S11.

**Partitioning rule**. One pass per bucket (6 passes). For each
bucket: enumerate closes; for each close, record the acceptance
evidence (test name, manual-verification note, or "none"). The 18
cross-repo `fixes` tally bounds the close-count, so per-bucket work
is bounded.

**Deliverable shape**. Per-bucket subsection: (i) closes table —
issue, close commit, acceptance evidence (test path / manual /
none), Y/N compliant; (ii) drift items with corrective measures
(retroactive acceptance, or downgrade to "doc-only close"). Final
summary: compliance rate; pattern of misses if any (e.g., docs-only
closes routinely lack acceptance — acceptable per convention; code
closes that lack acceptance are the real drift).

---

#### Stage 5 — 1:1:1 discipline

**Question**. Have recent sessions actually been 1 issue : 1 branch :
1 session, or has bundling crept beyond the housekeeping-exception
and umbrella-branch carve-outs codified in CLAUDE.md?

**Grep gate**.
- `grep -rl feedback_issue_branch_session_discipline memory/`
- `grep -rl feedback_umbrella_branches memory/`
- `grep -rln '1:1:1\|housekeeping\|umbrella/' internal_docs/SessionLogs/`

**Corpus**.
- Memory: `feedback_issue_branch_session_discipline.md`,
  `feedback_umbrella_branches.md`.
- CLAUDE.md "Session Protocol" section (1:1:1, housekeeping-bundles,
  introspection-sidebar, umbrella-branches policies).
- Minutes: S11→S60 (48 files) — per session, count issues touched /
  branches used / housekeeping-flag / umbrella-flag.

**Partitioning rule**. Per-session shallow scan — each session
produces one row with {issue-count, branch-count, session-type
(substantive / housekeeping / sidebar / umbrella-certification /
umbrella-sub), compliance Y/N}. 48 rows fits one session.

**Deliverable shape**. (i) Per-session compliance table; (ii)
housekeeping-bundle abuse list — bundles that mixed in substantive
changes (should have been pulled to 1:1:1); (iii) umbrella-policy
adoption note — the policy is new in-window, so most "violations"
pre-date the policy and are exempt; (iv) introspection-sidebar
audit — did the trigger (every 5–7 sessions OR 3+ unresolved
carry-forward reminders) get honoured? Final summary: compliance
rate, drift items, corrective measures.

---

#### Stage 6 — Mission-and-Vision alignment

**Question**. Does shipped work in the audit window advance the
self-repairing-platform mission, or has the execution surface
drifted away from
[`mission_vision.md`](../../.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/mission_vision.md)?

**Grep gate**.
- `grep -rl mission_vision memory/`
- `grep -rln 'mission\|vision\|ERPNext MCP\|self-repair' internal_docs/SessionLogs/`

**Corpus**.
- Memory: `mission_vision.md`,
  `feedback_mission_priority_check.md`,
  `feedback_not_perfection_project.md`,
  `project_generic_site_purpose.md`,
  `project_pages_site_v1.md`.
- Issues: all closes since S11 (overlaps with Stage 4 corpus).
- Minutes: S11→S60 — `Work done` section per session; categorise
  shipped items by mission-relevance.

**Partitioning rule**. Stage 4's closes-table is the primary input
to Stage 6 — categorise each shipped item against the mission
properties (ERPNext MCP advance / self-repair advance / tutorial
generation / persistent records / unrelated). If Stage 4 has not
yet executed when Stage 6 lands, Stage 6 falls back to reading
minutes' `Work done` sections directly. Stage 4 → Stage 6
dependency noted; non-blocking.

**Deliverable shape**. (i) Categorisation table — work item,
mission-property advanced (or "none"), brief justification; (ii)
"unrelated" cluster analysis — if a large block of recent work is
mission-unrelated, that itself is the audit finding; (iii) explicit
resolution of S60 observation #6 (M&V staleness): does the audit
window reveal that `mission_vision.md` needs amendment, or that the
mission is still accurately stated and only the execution surface
needs realignment? Final summary: mission-alignment verdict +
corrective measures (memo refresh, ticket re-prioritisation, or "no
drift found").

---

#### Stage dependencies and sequencing notes

- **Stage 6 depends on Stage 4** — Stage 4 produces the closes-table
  Stage 6 categorises. Order memo-1→6 respects this. Stage 6 has a
  fallback path if executed out of order.
- **Stages 1, 2, 5 are independent** — can execute in any order if
  re-sequencing is later proposed.
- **Stage 3 (memory hit-rate) is meta-architectural** — it audits the
  same mechanism this very audit relies on. Useful as a mid-audit
  recalibration.
- **No stage requires writing code in `tools/` or `platforms/`.** All
  stage deliverables are report sections under
  `internal_docs/AuditReports/`. Code corrections, if any, become
  separate sub-issues filed in the appropriate bucket.

---

#### Sanity-check — Step-1 observations mapped to stages (S61)

Each of the six observations captured at Step 1 lands in exactly one
stage. No observation is unhomed; no stage split or list extension is
proposed.

| Obs | Topic (S60) | Home stage |
|---:|---|---|
| 1 | Plan-B execution-surface footprint vs ESACP open issues — bucket-placement discipline broadly holding | **Stage 1** (bucket-placement compliance) |
| 2 | Plan-B current locus — LSKB#15/#16 paused; Phases 1/2/3/5/6 status not re-verified at Step 1 | **Stage 2** (Plan-B phase mapping) |
| 3 | M&V mentions concentrated in two clusters; sparse at execution level | **Stage 6** (M&V alignment) |
| 4 | `umbrella/ladder-fixture` orphan ([ESACP#361](https://github.com/martinhbramwell/ESACP/issues/361)), pre-#358 — own-session candidate | **Stage 5** (1:1:1 / umbrella-branches policy) |
| 5 | ESACP issue count +1 drift vs S59 expected — catalog-coverage candidate if it recurs | **Stage 1** (catalog coverage = discipline mechanism #1) |
| 6 | `mission_vision.md` 60d old; pre-dates Plan B amendments — staleness refresh-trigger candidate | **Stage 6** (M&V refresh trigger) |

Stage 1 carries 2 observations; Stage 6 carries 2; Stages 2 and 5 carry
1 each. Stages 3 and 4 carry none from S60 — neither stage is an
empty-corpus stage, both still have well-defined audit surfaces from
the universal corpus.

---

## Step 3 — Consolidation session spec (S62)

The audit closes with a **consolidation session** scheduled to run
immediately after Stage 6 — the +1 session that follows the six
executable stages. Step 3 is the planning spec for that session,
paralleling the Stage 1–6 spec blocks from Step 2. Drafted S62
(2026-05-20) at operator request after the Stage 1 close-out, to
make the entire audit lifecycle visible in one document.

**Question answered**. What is the single ordered action plan that
discharges ESACP#400's findings, and what is the next move —
resume Epoch 2 (Plan B Phase 4 — LSKB#15) directly, or interleave
corrective measures first?

**Inputs (preconditions)**.
- Audit report Stages 1–6 complete; each section carries its own
  drift table + corrective-measure rows + discipline-mechanism verdict.
- All migrations / new issues / pointer-comments produced during
  Stages 2–6 landed on their respective trackers.
- `memory/project_buffer_overflow_audit_plan.md` not yet updated with
  audit-end retrospective.
- ESACP#400 still open as the audit anchor; six stage-closure comments
  on it (one per stage, S57/S58/S60/S61/S62 pattern continued through
  S6X−1).

**Mandatory grep gate** (universal, matching every stage):
- `grep -n 'Stage [1-6] —' internal_docs/AuditReports/2026-05-19-buffer-overflow-audit.md` — locate the six executed stage sections; confirm each has a `Drift summary` + corrective-measure-row block.
- `grep -rln '#400' internal_docs/SessionLogs/` — recover the full audit-trail of session-log mentions + cross-references.
- `gh issue view 400 --comments` — recover the six stage-closure comments and the pre-#400 setup comments (S57/S58).

**Method** (six sub-steps):

1. **Drift-register consolidation.** Walk Stages 1–6 in order.
   Extract every drift row into a single master register. Per entry:
   `(source stage, drift type, corrective measure, current status [resolved-in-stage / pending], gating-class [blocks-Epoch-2 / parallel-safe / housekeeping])`.

2. **Categorization pass.** Bucket the *pending* items by
   corrective-measure type:
   - Issue migrations (Operations 2/3/4 per `project_bucket_2_migration_pattern.md`)
   - In-place memory/doc edits
   - New issues to file (one per substantive item, not bundled)
   - Process/discipline changes (CLAUDE.md amendments, `feedback_*` additions)
   - Housekeeping (TRIVIAL_FIXES.md adds)

3. **Sequencing pass.** Build a numbered action plan ordered by
   gating-class: blocks-Epoch-2 first; then items unblocking specific
   paused LSKB issues (#15, #16, #18, #21); then parallel-safe; then
   housekeeping. Identify dependencies between items; mark any item
   whose execution must precede another.

4. **M&V realignment check.** Cross-reference the consolidated drift
   findings against `memory/mission_vision.md`. For each pending
   corrective measure, mark whether it advances a mission property
   (low-fault, self-explanatory, AI-introspectable, family-operable)
   or is discipline-only. Discipline-only fixes stay honestly labelled
   — no promotion to "mission-critical" to inflate priority.

5. **Joint review — Go/No-go on Epoch 2 resumption.** Three explicit
   options for operator (`AskUserQuestion`):
   - **A**. Resume Epoch 2 Phase 4 (LSKB#15) immediately after
     consolidation closes; corrective measures interleave by priority.
   - **B**. Run all blocks-Epoch-2 corrective measures first, then
     resume Phase 4.
   - **C**. Hybrid — run only the corrective measures Stage 2 (Plan-B
     phase mapping) identified as actual Phase-4 blockers; defer the
     rest to parallel sessions.

6. **Close-out.**
   - Append `## Consolidation — Drift register + action plan (S6X)`
     section to this audit report (the deliverable).
   - Update `memory/project_buffer_overflow_audit_plan.md` with the
     audit-end retrospective: what the audit found that the planning
     gate missed (the meta-finding — institutional learning).
   - Close **ESACP#400** with pointer comment to the consolidation
     section + the Epoch 2 resumption decision.
   - File any new tracker issues identified by the action plan (one
     per substantive item, not bundled).

**Deliverable shape**.

| Block | Form |
|---|---|
| Master drift register | Table — `(stage, type, measure, status, gating-class, M&V tie)` |
| Action plan | Numbered list, priority-ordered, with dependency arrows |
| Resumption decision | One paragraph recording the operator's A/B/C choice + rationale |
| ESACP#400 closure | Closing comment URL on the issue |
| Meta-finding | One-paragraph addition to `project_buffer_overflow_audit_plan.md` |

**Out of scope** (defer to post-consolidation sessions):
- Executing the corrective measures themselves — each is its own
  1:1:1 session per discipline.
- Epoch 2 Phase 4 execution (LSKB#15 substrate-apply resumption).
- Retrospectives over Epoch 1 — different scope from the
  buffer-overflow audit; not what #400 chartered.

**Estimated wall-clock**. 90–120 min if Stage 2–6 outputs are clean;
up to 180 min if consolidation surfaces unexpected cross-stage
interactions (e.g., Stage 3 memory hit-rate findings overlap with
Stage 5 1:1:1 findings on the same root cause).

**Risks**:
- If Stages 2–6 produce a corrective-measure count >20, the
  categorization pass needs subdivision and the resumption decision
  may split into "decide priority order" + "decide execution shape"
  across two sub-sessions.
- If a stage surfaces a finding that retroactively changes a closed
  stage's verdict, consolidation must reopen that stage — adds 1
  session.
- The "no decision theatre on clerical work" rule still applies —
  most housekeeping items should be batched into a single
  TRIVIAL_FIXES.md update, not enumerated separately at consolidation.

---

## Stage 1 — Bucket-placement compliance (S62)

**Question answered**. Across all six tracked repos
([ESACP#358](https://github.com/martinhbramwell/ESACP/issues/358) prescription),
do open issues, in-window `main` commits, and live branches sit in the
bucket each is supposed to sit in?

**Trigger context**. Memo order 1→6 (operator S60). Audit window
S11 = 2026-05-06 → present. Two S60/S61 observations land here:
**Obs 1** (bucket discipline broadly holding) and
**Obs 5** (ESACP +1 issue drift vs S59 expected — catalog-coverage
candidate if it recurs).

### Sub-step 1 — Mandatory grep gate (universal)

| Grep | Hits | Read |
|---|---:|---|
| `grep -rl bucket_definitions memory/` | 2 | `MEMORY.md` (index) + `session_buckets.txt` (per-controller surveys config). Bucket definitions file itself is canonical. |
| `grep -rl 'bucket-[123]' memory/` | 12 | Wide coverage: `bucket_definitions.md`, `project_bare_bucket_1_association.md`, `project_bucket_2_migration_pattern.md`, `project_wip_consolidation_plan.md`, `project_phase4_bespoke_app_placement.md`, `project_sales_partner_commissions_redesign.md`, `project_logisolu_validations.md`, `project_erpnext_idiomatic_refactor.md`, plus four `feedback_*` memos. Bucket vocabulary is durable, not parked in a single memo. |
| `grep -rln '#358\|#359' internal_docs/SessionLogs/` | 50 | First hit `2026-05-08-1630` (S14); continuous from S14 onward. Bucket framing is the load-bearing context for every post-#358 session. |
| `grep -rln 'wip/' internal_docs/SessionLogs/` | 57 | Spans 2026-03-31 → 2026-05-19. Pre-#358 mentions track wip-discovery (S13); post-#358 mentions track the consolidation plan + the two surviving wip refs in bucket-3. |

### Sub-step 2 — Live branches scan (Discipline #3 corpus)

Branches enumerated on every bucket tracker + Plan-B associated repos
referenced in `project_wip_consolidation_plan.md`:

| Repo | Bucket | Live `wip/*` | Pre-/post-#358 |
|---|---|---|---|
| ESACP | 1 | none | n/a |
| BaRe | 1-associate | none | n/a |
| LSKB | 2 | none | n/a |
| LogiSoluValidations | 2-validations | none | n/a |
| ce_sri | 3 | `wip/2026-03-25` | **pre-#358** — documented in plan |
| ce_sri_svc | 3 | `wip/2026-03-31` | **pre-#358** — documented in plan |
| route_planner (Plan-B Phase 7 eliminate target) | 2 (LSKB-governed) | `wip/2026-03-31`, `phase-1-fixture-equivalent`, `feat/371-wip-consolidation-phase-1` | **pre-#358** — documented in plan; `feat/371-*` is a consolidation sub-branch (compliant) |
| returnable (Plan-B Phase 8 eliminate target) | 2 (LSKB-governed) | repo not enumerable via current `gh` auth (404 on `martinhbramwell/returnable`) | flagged below |

`returnable` 404 is a **secondary finding**, not a Stage 1 drift item:
the canonical reference for tenant-app repo locations is
`hosts_map.yml`/`tenant_business_apps` per #379 hosts-map correction.
`martinhbramwell/returnable` was renamed to `martinhbramwell/BtlMng` per
commit `6910f48` (`#379`). The grep-gate confirms the audit window saw
that rename. Item logged for Stage 5 (1:1:1 discipline) cross-reference,
not Stage 1 drift.

### Sub-step 3 — Per-bucket compliance passes

#### Pass 1 — Bucket 1: ESACP (43 open issues; ~90 in-window `main` commits)

**Issues table** (drift evaluation against bucket-1 scope =
"Generic AI-assisted ERP-maintenance toolkit. Pipelines, Cytoscape
control plane, observability, QA verdict layer, `sync_check`, audit
framework"):

| # | Title (truncated) | Topic class | Bucket fit |
|---:|---|---|---|
| 48 | Registrar credentials backup + family access | infra/DNS/operator | ✅ 1 |
| 65 | Grafana-embedded control plane authn/authz | control plane | ✅ 1 |
| 138 | saconsole phone-home VM auto-registration | saconsole | ✅ 1 |
| 153 | Google OAuth redirect URIs for staging VPS hostnames | infra | ✅ 1 |
| 156 | saconsole on recycled Android tablet (LineageOS) | saconsole | ✅ 1 |
| 157 | WireGuard self-enrollment via staging slave | infra | ✅ 1 |
| 187 | esacp.py extract legacy commands into pipeline wrappers | pipeline | ✅ 1 |
| 219 | cytoscape decompose main.js (2013 lines) | control plane | ✅ 1 |
| 223 | observability metrics history retention post-V16 | observability | ✅ 1 |
| 235 | CLI/API transport parity gap survey | dispatcher audit | ✅ 1 |
| 240 | DNS zone migration iridium.blue → yourpublic.work | infra | ✅ 1 |
| 241 | hosts_map.local.yml overlay for operator overrides | config infra | ✅ 1 |
| 278 | sync_check dev01 carve-out still undocumented | sync_check | ✅ 1 |
| 280 | re-implement chaos harness on KVM | chaos infra | ✅ 1 |
| 302 | verify-stage_*.py provision_mode-aware | pipeline | ✅ 1 |
| 306 | provisionGeneric should install hrms+payments by default | pipeline / generic substrate | ✅ 1 |
| 307 | eval: install hrms+payments on company-specific v13 | tenant decision (label `decision`) | ⚠ **drift candidate** — see below |
| 311 | KVM templates.yml per-role substrate | infra | ✅ 1 |
| 328 | richer attribution for opaque-hash drift classes | audit framework | ✅ 1 |
| 330 | Client/Server Script v14 API-compat (gated on V13→V14 trial) | audit methodology | ✅ 1 |
| 331 | bespoke-app uv pip install crashes on Frappe v14 | pipeline / V14 trial | ✅ 1 |
| 349 | stage-7 error reporter masks failures | pipeline bug | ✅ 1 |
| 350 | stage-2 wireguard-tools apt-fetch tolerated | pipeline bug | ✅ 1 |
| 351 | customisation_audit parameterise → LogiSoluValidations | governance | ✅ 1 |
| 352 | LogiSoluValidations needs own size/QA governance | governance | ✅ 1 |
| 353 | epic: Plan B refactor parent (methodology-stays) | methodology epic | ✅ 1 (methodology home; execution on LSKB per CLAUDE.md) |
| 355 | V16+ Playwright wizard handler | pipeline | ✅ 1 |
| 360 | split mission_vision.md (LogiSolu vs ESACP) | docs / methodology | ✅ 1 |
| 361 | orphan local `umbrella/ladder-fixture` | branch hygiene | ✅ 1 (Stage 5 corpus) |
| 365 | extract session-type policy to session-types.md | docs methodology | ✅ 1 |
| 366 | repo-controlled YAML ontology for disambiguation | methodology | ✅ 1 |
| 368 | parked-backlog regenerate from `gh issue list` | agenda methodology | ✅ 1 |
| 370 | S29 Candidate A mis-scoped vs wip-consolidation prereqs | retrospective | ✅ 1 |
| 374 | git-deploy wrapper on bespoke-app VMs | pipeline infra | ✅ 1 |
| 375 | bespoke-app deploy keys + passphrase SOPS source-of-truth | secrets | ✅ 1 |
| 383 | enroll Windows/Android tablet WG peers | infra | ✅ 1 |
| 387 | Ansible SSH Host alias auto-add | pipeline | ✅ 1 |
| 394 | packer scripts size-band decomposition | pipeline | ✅ 1 |
| 395 | pyyaml 5.4.1 / Cython 3 packer bug | pipeline | ✅ 1 |
| 396 | seed_iso.py hardcodes hasan_mighty.pub | pipeline / no-real-names | ✅ 1 |
| 397 | bespoke-app deploy-key VM-side generation | secrets / pipeline | ✅ 1 |
| 400 | epic: buffer-overflow audit (this audit) | audit framework | ✅ 1 |
| 401 | saconsole 10.10.0.1 unreachable | saconsole infra bug | ✅ 1 |

**ESACP#307 drift detail.** Body explicitly scopes work to
"company-specific fully customized ERPNext v13 instances (master +
replication slave)" — i.e. the tenant's *production* v13. Labelled
`decision`. Per [bucket_definitions](../../[memory link]):

- Bucket-2 (LSKB) is the home for "Operating-tenant business logic +
  Plan B execution".
- Bucket-1 retains methodology and generic-substrate work (#306 is the
  matching bucket-1-fit twin: "provisionGeneric should install hrms +
  payments by default").

Two defensible interpretations:
1. **Bucket-2 drift** — if the decision is "do we install hrms+payments
   on *the tenant's* v13", that is a tenant-business decision; LSKB is
   the home.
2. **Bucket-1 methodology** — if the issue is reframed as "lab-evaluate
   hrms+payments on a v13-with-tenant-customisations clone, decision
   informs but does not execute against production", it stays bucket-1.

Reading #307's body, framing (1) dominates (live HR data, production
instance enumerated). Recommended corrective measure: re-file on LSKB,
close ESACP#307 with pointer comment, per
`project_bucket_2_migration_pattern.md` Operation 2 (migration).

**S62 joint-review outcome**: operator approved migration. Executed
this session:
- Re-filed as **[LSKB#21](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/21)** with body preserved verbatim + migration preamble + cross-link to bucket-1 twin ESACP#306.
- ESACP#307 closed not-planned with pointer comment to LSKB#21.
- Bucket-1 twin ESACP#306 remains here (generic-substrate scope).

**ESACP commits-fixes table** (substantive `fixes #N` only;
session-log close-out commits without `fixes` follow the docs-only
direct-to-main carve-out per `qa-contract` §2.1 condition 2 and do not
require an `issues` reference):

| Commit | `fixes` target | Bucket of target | Drift |
|---|---|---|---|
| d08699e | ESACP#404 (Pages-site nav buttons) | 1 | ✅ |
| 5946e2d / fbeb384 / 153b346 | ESACP#398 (MariaDB perf-schema) | 1 | ✅ |
| e283716 | ESACP#392 (packer uv override) | 1 | ✅ |
| 9ef1aa5 | ESACP#390 (packer FRAPPE_BRANCH) | 1 | ✅ |
| e94e9a5 | ESACP#388 (packer-as-saconsole-dep) | 1 | ✅ |
| 6910f48 | ESACP#378 (hosts_map BtlMng correction) | 1 | ✅ |
| b52de7f | ESACP#358 (three-bucket doc landing) | 1 | ✅ |
| 611c03e | ESACP#367 (qa-contract clarification) | 1 | ✅ |
| 554ad24 | ESACP#382 (qa-contract repo-specific lane) | 1 | ✅ |
| 0137977 | ESACP#380 (qa-contract risk-tier triggers) | 1 | ✅ |
| ed73877 | ESACP#362 (CLAUDE.md trailer template) | 1 | ✅ |
| abcdd02 | ESACP#363 (introspection-sidebar policy) | 1 | ✅ |

All 12 substantive `fixes` targets are bucket-1 issues. **Zero
commit-target drift on ESACP.**

#### Pass 2 — Bucket 1-associate: BaRe (2 open issues; 1 in-window commit)

| # | Title | Bucket fit |
|---:|---|---|
| 10 | docs: README should mention production-machine installability | ✅ 1-associate |
| 8 | chore(bare): cleanup drift vs production + extend `envars.sh` | ✅ 1-associate |

Single in-window commit `8653412 docs: add README declaring bucket-1
association with ESACP-platform` carries `fixes #9` (BaRe intra-repo,
bucket-1-associate target). ✅ No drift.

#### Pass 3 — Bucket 2: LSKB (8 open issues; 1 in-window commit)

| # | Title (truncated) | Bucket fit |
|---:|---|---|
| 1 | Sales Partner Commission Server Scripts misleading event names | ✅ 2 (tenant business) |
| 6 | Plan B Phase 4 — Sales Partner Customer Item Commissions master/detail | ✅ 2 (Plan-B exec) |
| 9 | Plan B Phase 7 — eliminate route_planner | ✅ 2 (Plan-B exec) |
| 10 | Plan B Phase 8 — eliminate returnable | ✅ 2 (Plan-B exec) |
| 11 | Plan B Phase 2 — staged drift promotions | ✅ 2 (Plan-B exec) |
| 15 | Plan B Phase 4 substrate-apply on local KVM | ✅ 2 (Plan-B exec) |
| 16 | verify Plan B Phase 4 commission calc parity | ✅ 2 (Plan-B verify) |
| 18 | sales_partner_commissions user_data_fields cleanup | ✅ 2 (bespoke-app chore) |

In-window commit `a8995e1 feat: seed LogiSoluKnowBase with three-bucket
scaffold` — foundational seed; no precursor issue. Acceptable per
seed-commit pattern. ✅ No drift.

LSKB issues are predominantly closed via cross-repo `fixes` from
`ce_sri` commits (Plan-B execution-on-ce_sri-repo pattern) — see Pass 5.

#### Pass 4 — Bucket 2 (LogiSoluValidations) (2 open issues; 2 in-window commits)

| # | Title | Bucket fit |
|---:|---|---|
| 5 | README cross-references describes BaRe as 'bespoke business-logic app' | ✅ 2-validations |
| 4 | catalogue mis-describes Sales Partner Customer Item Commissions | ✅ 2-validations |

Two in-window commits (`7e655fc` merge + `618811b` revise Spanish
staffer section) — docs sweep, no `fixes` references. Acceptable per
docs-only carve-out. ✅ No drift.

#### Pass 5 — Bucket 3: ce_sri (6 open issues; 3 in-window commits)

| # | Title (truncated) | Bucket fit |
|---:|---|---|
| 1 | fixSupervisor | ✅ 3 (ops dep) |
| 2 | git clone martinhbramwell/ce_sri_svc.git | ✅ 3 (ops dep) |
| 3 | Test viability of mailer key | ✅ 3 (ops dep) |
| 4 | README incomplete after validateEnvironment.sh | ✅ 3 (docs / ops) |
| 5 | dev01 lab egress to SRI Pruebas ECONNRESET vs prod | ✅ 3 (ops / SRI integration) |
| 10 | bench migrate fails on Custom Field collision `forma_de_pago_preferida` | ✅ 3 (ce_sri fixtures); interlocks with LSKB#15 (Plan-B Phase 4); flagged as #400-trigger |

**ce_sri commits-fixes table**:

| Commit | `fixes` target | Bucket of target | Drift |
|---|---|---|---|
| 924ff2e | LSKB#8 (es-EC Translation overrides) | 2 (cross-bucket close) | ✅ — Plan-B execution pattern: tenant work executed on ce_sri repo closes the LSKB tracking issue |
| b22e263 | LSKB#3 (Custom DocPerm v14_patch_script port) | 2 (cross-bucket close) | ✅ — same pattern |
| dd7199e | ce_sri#7 (Phase 1 Custom Fields — intra-repo) | 3 | ✅ |

All commit-fix targets correct under the Plan-B execution routing.
**Zero drift on ce_sri.**

#### Pass 6 — Bucket 3: ce_sri_svc (2 open issues; 0 in-window `main` commits)

| # | Title | Bucket fit |
|---:|---|---|
| 1 | migrate babel-cli@6 → @babel/cli@7 + npm dep updates | ✅ 3 (ops dep) |
| 4 | retry-with-backoff for queryAuthorization + exhaustion contract | ✅ 3 (ops / SRI) |

No in-window `main` commits; one open feature branch
(`fix/sri-node-version-probe-#343`) — naming follows `fix/<topic>-#<n>`,
references ESACP#343 (presumably resolved cross-repo). One additional
non-`wip/*` feature branch (`feat/sri-retry-with-backoff`) is the
in-progress sub-branch for ce_sri_svc#4. Compliant with 1:1:1 +
umbrella discipline. ✅ No drift.

### Sub-step 4 — Drift summary

| Bucket | Open issues (at Stage 1 start) | Drift candidates | Severity | Post-resolution count |
|---|---:|---|---|---:|
| 1 ESACP | 43 | 1 — ESACP#307 (tenant decision → bucket-2) | Soft — operator interpretation | 42 (#307 closed not-planned) |
| 1-associate BaRe | 2 | 0 | — | 2 |
| 2 LSKB | 8 | 0 | — | 9 (+1 — LSKB#21 migration target) |
| 2-LogiSoluValidations | 2 | 0 | — | 2 |
| 3 ce_sri | 6 | 0 | — | 6 |
| 3 ce_sri_svc | 2 | 0 | — | 2 |
| **Total** | **63** | **1** | **<2%** | **63 (net zero)** |

**Commits-fix-target drift across all buckets: 0.**

**Live-branch drift across all buckets:** 0 post-#358 violations. Two
pre-#358 `wip/*` carry-overs on bucket-3 (`ce_sri/wip/2026-03-25`,
`ce_sri_svc/wip/2026-03-31`) plus the Plan-B-associated
`route_planner/wip/2026-03-31` remain as historical refs per
`project_wip_consolidation_plan.md`. Their continued existence is
expected; their continued *use* (any new commits to them) would be a
violation. No new commits to any of the three since the plan landed.

### Sub-step 5 — Discipline-mechanism verdicts

| # | Mechanism | Verdict | Evidence |
|---:|---|---|---|
| 1 | Catalog coverage — every commit references an issue | **HOLDING** | All 12 substantive in-window ESACP commits + all 3 substantive ce_sri commits + 1 BaRe commit reference an issue via `fixes #N`. Session-log / audit-fix commits without `fixes` operate under the qa-contract §2.1 condition-2 docs-only direct-to-main carve-out (codified in S58/S59/S60/S61). Seed/foundational and docs-sweep commits (LSKB, LogiSoluValidations) lack `fixes` legitimately. Obs 5 (ESACP +1 issue drift) closed: the +1 is ESACP#401 (saconsole bug) — a properly-filed issue, not an untracked work item; catalog coverage operating correctly. |
| 2 | Bucket-explicit session-start surveys | **HOLDING** | `session_buckets.txt` lives in `memory/` (LogiSoluMemory symlink), driving per-bucket surveys at session start since `a85cde0 feat(session-start): bucket-explicit per-bucket surveys at session start` (S29). S60/S61/S62 agendas + minutes all execute the survey pattern. **Minor**: `session_buckets.txt` not also at controller root — known S60 carry-forward, housekeeping-sidebar candidate; non-blocking. |
| 3 | `wip/*` prohibition (forward) | **HOLDING** | Zero post-#358 `wip/*` branches across all six bucket trackers + Plan-B-associated repos. Pre-#358 carry-overs (3 known refs) remain frozen with no in-window commits — expected behavior per consolidation plan. |

### Sub-step 6 — Observations closed by Stage 1

| Obs | Outcome | Disposition |
|---:|---|---|
| 1 | **Confirmed.** Bucket discipline broadly holding: 62/63 open issues fit prescribed bucket; 1 soft candidate for operator interpretation; 0 commits-fix-target drift; 0 forward wip/* violations. | Stage 1 verdict = holding; carry ESACP#307 disposition to joint review. |
| 5 | **Closed.** +1 ESACP issue drift S59→S60 explained by ESACP#401 filing (saconsole infra bug); properly catalogued. No catalog-coverage recurrence. | No further action; observation discharged. |

### Stage 1 close

**Drift items requiring corrective measures**:

1. **ESACP#307 → LSKB#21** — **resolved this session** via Operation-2
   migration. ESACP#307 closed not-planned with pointer; LSKB#21
   carries the continuation. Bucket-1 twin ESACP#306 preserved on
   ESACP for generic-substrate work.

**Carry-forward to Stage 5** (1:1:1 / umbrella-branches policy):

- Three pre-#358 `wip/*` carry-overs documented but unresolved
  (`ce_sri/wip/2026-03-25`, `ce_sri_svc/wip/2026-03-31`,
  `route_planner/wip/2026-03-31`). Consolidation per `project_wip_consolidation_plan.md`.
- Local-only orphan `umbrella/ladder-fixture` (ESACP#361). Stage 5 home.

**No Stage 2 execution this session.** Stage 2 (Plan-B phase mapping)
starts S63 at the earliest, per Sub-step 4 of the S62 agenda.

---

## Stage 2 — Plan-B phase mapping (S63)

**Question answered**. Across the 8-phase Plan B
([ESACP#353](https://github.com/martinhbramwell/ESACP/issues/353)),
where are recent sessions actually operating? Are phase boundaries
respected, or has scope crept across phases?

**Trigger context**. Memo order 1→6 (operator S60). Audit window S11 =
2026-05-06 → present (S62 = 2026-05-20). One S60/S61 observation lands
here: **Obs 2** (Plan-B current locus — LSKB#15/#16 paused;
Phases 1/2/3/5/6 status not re-verified at Step 1).

### Sub-step 1 — Mandatory grep gate (universal)

| Grep | Hits | Read |
|---|---:|---|
| `grep -rl 'Plan B\|idiomatic_refactor' memory/` | 15 | Memos: `project_erpnext_idiomatic_refactor.md` (master plan), `project_phase3_redis_rq_decision.md`, `project_phase4_bespoke_app_placement.md`, `project_sales_partner_commissions_redesign.md`, `project_wip_consolidation_plan.md`, `project_buffer_overflow_audit_plan.md`, `project_bucket_2_migration_pattern.md`, `project_cloudstack_deferred_until_v16.md`, `project_logisolu_validations.md`, `project_plan_b_remaining_roadmap.md` (archive), plus 4 feedback memos (`feedback_dev_vms_are_disposable.md`, `feedback_bespoke_apps_single_responsibility.md`, `feedback_check_existing_wip_before_fresh_work.md`, `feedback_consultant_not_peer_engineer.md`) + `MEMORY.md` index. Plan-B vocabulary is durable across 15 memory files, not parked in a single memo. |
| `grep -rl 'project_erpnext_idiomatic_refactor' memory/` | 8 | Direct cross-references: 5 Plan-B project memos + `feedback_dev_vms_are_disposable.md` + `MEMORY.md` + `project_buffer_overflow_audit_plan.md`. Master-plan link is well-fanned. |
| `grep -rln 'Phase [1-8]' internal_docs/SessionLogs/` | 188 | Hits span 2026-03-31 → 2026-05-20. Note: regex matches generic "Phase N" tokens used in pipeline-stage and gen-3 contexts too — Plan-B phase mentions are a subset. Audit-window subset (since 2026-05-06): partitioned per-phase in Sub-step 2 below. |
| `grep -rln 'LSKB#\|#353' internal_docs/SessionLogs/` | 98 | First in-window hit: `2026-05-07-0748-*` (Plan B Phase 4 antecedent discussion). Continuous through 2026-05-20. LSKB# and #353 vocabulary is load-bearing context for every post-S33 session. |

Gate **passes**: all four sweeps return hits in expected ranges; no cold
spot. Notable caveat on grep 3 (the `Phase [1-8]` regex): high hit count
includes non-Plan-B "Phase" tokens — Sub-step 2 partitions properly by
LSKB-issue and phase-specific keywords (`fixture_equivalent`,
`Custom DocPerm`, `discardable_core_edit`, `redis/rq`,
`sales_partner_commissions`, `master/detail`, `catalogue triage`,
`es-EC`, `route_planner`, `returnable`).

### Sub-step 2 — Per-phase compliance pass (8 phases)

**Ground-truth source**. LSKB + ce_sri close-state in window — every
Plan-B execution row tracks via a `refactor(Plan B Phase N):` or
`design/feat(Plan B Phase N):` issue title. Plus pre-bucket-migration
ESACP rows (#356/#357) that landed before #358 migrated execution to
LSKB.

#### Phase 1 — Replace 18 `fixture_equivalent_core_edit` with Custom Fields

**Memo summary** (`project_erpnext_idiomatic_refactor.md`): replace 18
`fixture_equivalent_core_edit` patches with declarative Custom Fields on
dev02; low risk (behaviour-equivalent by audit verdict).

**Sessions that touched the phase**:

| Session date | Issue | Work |
|---|---|---|
| 2026-05-09 | ESACP#356 closed | Pre-bucket-migration: 14 fixture_json Custom Fields replaced on dev02 |
| 2026-05-09 | ESACP#357 closed | Pre-bucket-migration: 3 Custom DocPerm v14_patch_script entries ported (Phase 1B, see below) |
| 2026-05-11 | ce_sri#6 closed | 11 ce_sri-routed Custom Fields consolidated onto main (wip-consolidation companion) |
| 2026-05-11 | LSKB#2 closed | Post-#358 re-filed Phase 1 execution row, closed via the same upstream work |

**Status**: **DONE**.

**Scope-creep**: None. Bucket-migration footprint (ESACP#356 → LSKB#2,
ESACP#357 → LSKB#3) is intentional Operation-2 migration per
`project_bucket_2_migration_pattern.md`, not phase-bypass.

---

#### Phase 1B — Custom DocPerm v14_patch_script entries

**Memo summary**: 3 Custom DocPerm patches → bespoke-app patches (sibling
to Phase 1; appears in catalogue as `human_review` but is mechanically
Phase 1-class).

**Sessions that touched the phase**:

| Session date | Issue | Work |
|---|---|---|
| 2026-05-09 | ESACP#357 closed | 3 Custom DocPerm entries ported (pre-bucket-migration) |
| 2026-05-11 | LSKB#3 closed | Post-#358 re-filed Phase 1B row; ce_sri commit `b22e263 fixes LSKB#3` |

**Status**: **DONE**.

**Scope-creep**: None.

---

#### Phase 2 — Drop 10 `discardable_core_edit` + 2 debug-print human_review entries

**Memo summary**: drop the 10 discardable patches plus the 2 debug-print
litter entries on `frappe/model/delete_doc.py` + `frappe/model/document.py`.
Low risk.

**Sessions that touched the phase**:

| Session date | Issue | Work |
|---|---|---|
| 2026-05-12 | LSKB#4 closed | 10 discardable + 2 debug-print entries dropped on dev02 |
| (open) | LSKB#11 open | Staged drift promotions — `custom_scripts, property_setter, translations` |

**Status**: **PARTIAL** — initial Phase-2 scope (12 entries) done;
follow-on drift-promotion row (LSKB#11) open.

**Scope-creep instance**: LSKB#11 expands Phase 2 from the original
12-item discardable-patch list to include three additional drift
categories (`custom_scripts`, `property_setter`, `translations`).
Verdict: **mid-execution scope-expansion**, cleanly captured as a
separate row (not bundled into LSKB#4 retroactively). Per Phase-2's
general intent ("drift cleanup before substrate-apply") this is an
honest discovery, not a discipline violation. Corrective measure: none
required; LSKB#11 is the canonical home and is properly scoped under
Phase 2 governance.

---

#### Phase 3 — `requirements.txt` redis/rq pin override decision

**Memo summary**: decide keep / match-stock / defer-to-V15+; resolved
2026-05-11 as **match V14 stock** (`redis~=3.5.3` + `rq~=1.8.0` on V13,
`rq frappe-fork` on V14+); applied at substrate rebuild, not as
immediate edit (PRODUCTION_20260404 is read-only).

**Sessions that touched the phase**:

| Session date | Issue | Work |
|---|---|---|
| 2026-05-12 | LSKB#5 closed | Decision documented in `project_phase3_redis_rq_decision.md`; LSKB#5 close-comment points there |

**Status**: **DONE** (decision-only; vendoring carries to substrate
rebuild per `project_phase3_redis_rq_decision.md` "Verification caveat"
section).

**Scope-creep**: None.

---

#### Phase 4 — Sales Partner Customer Item Commissions master/detail

**Memo summary**: master/detail DB-resident redesign + retire `Asignar
Producto a Campo`. Medium risk. Per Premises amended S40 (2026-05-12),
substrate re-targeted to local KVM; LSKB#6 epic scope-trimmed into a
sub-issue ladder (LSKB#12 → LSKB#16). Per Premises amended S41
(2026-05-12), patch + Server Script install hooks live in new dedicated
`sales_partner_commissions` app (bucket-2, LSKB tracker).

**Sessions that touched the phase**:

| Session date | Issue | Work |
|---|---|---|
| 2026-05-09 | ESACP#354 closed | Doc note on Server Script misleading event names (pre-bucket-migration; later re-filed as LSKB#1) |
| 2026-05-12 | ESACP#385 closed | Chronology amendment: Phase 4 substrate CloudStack → local KVM |
| 2026-05-12 | ESACP#386 closed | Bespoke-app placement decision: new `sales_partner_commissions` app |
| 2026-05-12 | LSKB#12 closed | Final master/detail DocType design — `Sales Partner Commission Item` child table |
| 2026-05-13 | LSKB#17 closed | `sales_partner_commissions` repo standup (empty Frappe app skeleton) |
| 2026-05-13 | LSKB#19 closed | Currency re-freeze — `commission_rate` Percent → Currency (S42 escape-clause triggered) |
| 2026-05-13 | LSKB#13 closed | V14 migration patch authored — walks column-explosion into master/detail rows |
| 2026-05-13 | LSKB#14 closed | Server Script rewrites against master/detail shape |
| 2026-05-15 | LSKB#20 closed | Substrate-readiness — dev02 bench-version drift assessment vs PRODUCTION_20260404 |
| (paused) | LSKB#15 open | **PAUSED** — apply Phase 4 changes on local KVM substrate (restore + bench migrate end-to-end) |
| (paused) | LSKB#16 open | **PAUSED** — verify commission calc parity on representative orders (downstream of #15) |
| (open) | LSKB#18 open | `user_data_fields` boilerplate cleanup in `sales_partner_commissions/hooks.py` (chore) |
| (open) | LSKB#1 open | Misleading event names — doc note (re-filed from ESACP#354) |
| (open) | LSKB#6 open | Phase 4 parent epic — remains open until all sub-issues land + substrate-apply verified |

**Status**: **IN-PROGRESS / PAUSED**. Design, repo, migration patch,
Server Script rewrites, currency re-freeze, substrate-readiness all
landed by 2026-05-15 (S48). Substrate-apply (LSKB#15) + parity-verify
(LSKB#16) **paused since** 2026-05-15. Pause origin: S56 (2026-05-18)
surfaced ce_sri#10 fixture collision blocking substrate-apply; ESACP#400
audit chartered S57 specifically to assess whether to resume directly
or interleave corrective measures.

**Scope-creep instances**:

1. **LSKB#15 / LSKB#16 / LSKB#18 / LSKB#19 / LSKB#20 (Phase 4 sub-issue
   ladder)** — per Premises amended S40, LSKB#6 was deliberately
   scope-trimmed into a sub-issue ladder (LSKB#13 migration-patch,
   LSKB#14 Server Scripts, LSKB#15 substrate-apply, LSKB#16
   parity-verify). LSKB#17 (repo standup), LSKB#18 (`user_data_fields`
   chore), LSKB#19 (currency re-freeze from S42 escape clause), LSKB#20
   (substrate-readiness infra) all filed deliberately under Phase-4
   governance. **Verdict**: **planned sub-issue ladder, not
   scope-creep.** Each sub-issue honours 1:1:1 discipline.
2. **ce_sri#10 (Custom Field collision, surfaced S56)** — bucket-3
   fixture bug with Plan-B Phase 4 substrate-apply interlock (blocks
   LSKB#15). Properly bucket-routed (bucket-3 not bucket-2); flagged as
   #400-trigger; ESACP#400 audit chartered to assess. **Verdict**:
   **interlock discovery, not scope-creep.** Phase 4 substrate-apply
   has a legitimate bucket-3 dependency the original chronology did
   not enumerate; honest find.

**Bypass detection**: none. Sub-issues #12 (design) → #17 (repo) → #19
(currency re-freeze) → #13 (migration patch) → #14 (Server Scripts) →
#20 (substrate-readiness) → #15 (substrate-apply, paused) → #16
(parity-verify, paused) executed in correct dependency order per the
amended ladder. Phase 4 design + code landed **before** substrate-apply
— honours the "smaller scaffolds larger" no-rework sequencing principle
(`feedback_no_rework_sequencing.md`).

---

#### Phase 5 — DB-resident customisation catalogue triage (22 TBDs)

**Memo summary**: document the 22 DB-resident customisation TBDs in
`audit/customizations_catalogue.yml`. Low risk; documentation pass.

**Sessions that touched the phase**:

| Session date | Issue | Work |
|---|---|---|
| 2026-05-07 | ESACP#312 closed | Customisation inventory for production v13 — antecedent of LSKB#7 |
| 2026-05-12 | LSKB#7 closed | 22 DB-resident TBDs documented (catalogue triage) |

**Status**: **DONE**.

**Scope-creep**: None.

---

#### Phase 6 — `es-EC → es` language aliasing (eliminate `erpnext/translations/es.csv` core edit)

**Memo summary**: replace the `es.csv` in-place core edit with
ERPNext-native language aliasing. Low risk.

**Sessions that touched the phase**:

| Session date | Issue | Work |
|---|---|---|
| 2026-05-07 | ESACP#339 closed | Language alias map for translation promotion (pre-Plan-B framing; later superseded) |
| 2026-05-12 | LSKB#8 closed | `es-EC → es` aliasing implemented; ce_sri commit `924ff2e fixes LSKB#8` |

**Status**: **DONE**.

**Scope-creep**: None.

---

#### Phase 7 — Eliminate `route_planner` (port additions to DB-resident DocTypes / Custom Fields)

**Memo summary**: smaller of the two app-eliminations (empty `hooks.py`);
surfaces app-elimination strategy learning before Phase 8's harder port.

**Sessions that touched the phase**:

| Session date | Issue | Work |
|---|---|---|
| 2026-05-11 | ESACP#371 closed | Track(wip-consolidation): route_planner Phase 1 pilot — Custom Field consolidation (pre-Plan-B pilot, distinct from elimination) |
| (none in window for the elimination itself) | LSKB#9 open | Not started |

**Status**: **NOT STARTED**.

**Scope-creep**: None. ESACP#371 was a wip-consolidation pilot (Track A
of `project_wip_consolidation_plan.md`), not Phase 7 elimination; the
two are distinct workstreams.

**Bypass**: Phase 7 is parallel-safe with Phase 4 design per Plan-B
chronology amendment S12 (smaller-scaffolds-larger sub-rule). Not
starting Phase 7 while Phase 4 is in-progress is **acceptable** — Plan
B does not require Phase 7 to run in parallel; only permits it.

---

#### Phase 8 — Eliminate `returnable` / `BtlMng` (port `hook_tasks.py` to DB-resident Server Scripts)

**Memo summary**: ~200-line `hook_tasks.py` port + safe_exec sandbox
question for file-I/O logging. Medium risk.

**Sessions that touched the phase**:

| Session date | Issue | Work |
|---|---|---|
| 2026-05-11 | ESACP#377 closed | Track(consolidation): `returnable (BtlMng)` wip-consolidation Phase 2 staged drift promotions (pre-elimination wip-cleanup) |
| 2026-05-11 | ESACP#378 closed | hosts_map / bucket_definitions correction — `martinhbramwell/returnable` → `martinhbramwell/BtlMng` rename |
| (none in window for the elimination itself) | LSKB#10 open | Not started |

**Status**: **NOT STARTED**.

**Scope-creep**: None. ESACP#377/#378 are wip-consolidation + repo-rename
prep; the actual elimination (port `hook_tasks.py` to Server Scripts) has
not started.

**Bypass**: same as Phase 7. Parallel-safe with Phase 4 per memo; not
running yet is acceptable.

### Sub-step 3 — Phase-status summary

| Phase | Status | Execution rows | Gating |
|---|---|---|---|
| 1 | **DONE** | LSKB#2 + ESACP#356 + ce_sri#6 | — |
| 1B | **DONE** | LSKB#3 + ESACP#357 | — |
| 2 | **PARTIAL** | LSKB#4 done; **LSKB#11 open** (staged drift promotions) | LSKB#11 parallel-safe — not gating Phase 4 |
| 3 | **DONE** (decision-only; vendor at substrate rebuild) | LSKB#5 | — |
| 4 | **IN-PROGRESS / PAUSED** | LSKB#12/#17/#19/#13/#14/#20 done; **LSKB#15/#16 paused**; LSKB#18, LSKB#1, LSKB#6 open | **LSKB#15 is the gating execution row**; blocked by ce_sri#10 + the #400 audit verdict |
| 5 | **DONE** | LSKB#7 + ESACP#312 | — |
| 6 | **DONE** | LSKB#8 + ESACP#339 | — |
| 7 | **NOT STARTED** | LSKB#9 | Parallel-safe; awaiting capacity |
| 8 | **NOT STARTED** | LSKB#10 | Parallel-safe; awaiting capacity |

**Drift items + corrective measures**:

| # | Drift type | Phase | Item | Corrective measure |
|---:|---|---|---|---|
| 1 | Scope-expansion (acceptable) | Phase 2 | LSKB#11 expands Phase 2 from 12-item discardable list to include `custom_scripts, property_setter, translations` | **None required.** Honest mid-execution discovery; cleanly captured as separate row not bundled into LSKB#4. Recommend ratifying as Phase-2-extended in `project_erpnext_idiomatic_refactor.md` next memo touch. |
| 2 | Interlock discovery (acceptable) | Phase 4 | ce_sri#10 Custom Field collision blocks LSKB#15 substrate-apply | **#400 audit chartered** for this. Consolidation session (Step 3, S6X) decides resume-direct vs interleave-fixes via Go/No-go on Epoch 2 (options A/B/C in audit-report Step 3). |
| 3 | Pause-class (decision pending) | Phase 4 | LSKB#15 substrate-apply + LSKB#16 verify paused since 2026-05-15 (~5 days at S63) | Resume decision **deferred to #400 consolidation session** (Step 3, S6X). Stage 2 does not pre-decide. |

**No discipline violations found.** Sub-issue ladder for Phase 4 honors
1:1:1 per row. No bundling of phases across single sessions. No bypass
of gating phases. Pre-bucket-migration ESACP rows (#312, #339, #354,
#356, #357, #371, #377, #378, #385, #386) all migrated cleanly or
remain legitimately on ESACP as methodology / chronology / wip-cleanup
work.

### Sub-step 4 — Obs 2 verdict (S60 observation)

**Obs 2 — Plan-B current locus**: LSKB#15/#16 paused; Phases 1/2/3/5/6
status not re-verified at Step 1.

**Stage 2 verdict**:

- **Phases 1, 1B, 3, 5, 6**: all **DONE**, verified via LSKB issue close
  dates (2026-05-11 → 2026-05-12) and supporting commits.
- **Phase 2**: **PARTIAL** — initial 12-item Phase-2 scope done
  (LSKB#4); follow-on drift-promotions row (LSKB#11) open and
  parallel-safe.
- **Phase 4**: **IN-PROGRESS / PAUSED** — most sub-issues done
  (design, repo, migration patch, Server Scripts, currency re-freeze,
  substrate-readiness); substrate-apply (LSKB#15) + parity-verify
  (LSKB#16) paused since 2026-05-15.
- **Phases 7, 8**: **NOT STARTED** — parallel-safe; awaiting capacity.

**Plan-B locus is precisely Phase 4 substrate-apply (LSKB#15).** The
pause is well-understood (ce_sri#10 interlock surfaced S56) and properly
held pending the #400 audit's consolidation-session resumption decision
(Step 3). Obs 2 closed; no fresh corrective measure ordered at Stage 2.

### Stage 2 close

**Drift items requiring corrective measures**: none operational this
session. Three drift entries logged in Sub-step 3 table; entries 1 and
2 are acceptable-by-class; entry 3 is properly deferred to the #400
consolidation session.

**Carry-forward to Stage 6** (M&V alignment): Phase 4 IN-PROGRESS state
is mission-aligned (eliminating schema-as-data anti-patterns advances
the AI-introspectable / family-operable mission per
`mission_vision.md`). Stage 6 will categorise the Phase-4-shipped work
against mission properties.

**Carry-forward to consolidation session** (Step 3, S6X):

- Decide LSKB#15 resume strategy (options A/B/C in audit-report Step 3).
- Ratify LSKB#11 as Phase-2-extended in
  `project_erpnext_idiomatic_refactor.md` next memo touch (low-priority
  memo refresh, not Stage 2's job).

**No Stage 3 execution this session.** Stage 3 (Memory hit-rate) starts
S64 at the earliest, per Sub-step 4 of the S63 agenda.

---

## Stage 3 — Memory hit-rate (S64)

**Question answered**. Per recent session, which memory files were
*relevant to the work* vs *actually consulted before acting*? This is
the audit's direct response to the S56 trigger — the grep-failure that
treated an issue body as authoritative when memory held the answer.

**Trigger context**. Memo order 1→6 (operator S60). Audit window S11
(2026-05-07-0748) → S62 (2026-05-20-0523) = 52 session-minutes files.
No S60/S61 observations land directly here — Stage 3 is the
meta-architectural audit of the very mechanism this audit relies on.
Its inputs are every session's `Stated objective` / `Objective` /
`Session scope` block plus the `How the session went` / `Work done` /
`Outcome` narrative, evaluated against the memory corpus relevant to
each session's primary topic.

### Sub-step 1 — Mandatory grep gate (universal)

| Grep | Hits | Read |
|---|---:|---|
| `grep -rl 'feedback_grep_memory_before_issue_body\|grep memory before' memory/` | 2 | `MEMORY.md` (index entry) + `project_buffer_overflow_audit_plan.md` (the audit-procedure memo). The corrective-measure file itself is the third hit when discovered by name. Adoption surface is canonical and discoverable. |
| `grep -rl 'buffer.overflow\|buffer_overflow' memory/` | 4 | `MEMORY.md`, `project_buffer_overflow_audit_plan.md`, `feedback_grep_memory_before_issue_body.md`, `project_pages_site_v1.md` (Pages-site retrospective references the audit as a self-correction case study). The buffer-overflow framing has crossed beyond the audit into adjacent project memory — institutional uptake, not parked. |
| `grep -rl 'ce_sri#10\|forma_de_pago_preferida' memory/` | 6 | `MEMORY.md`, `project_buffer_overflow_audit_plan.md`, `feedback_grep_memory_before_issue_body.md`, `project_pages_site_v1.md`, `project_zero_defect_build.md`, `project_cesri_modules_fixture_bugs.md`. The last memo is the **canonical S56-miss target** — the memo that would have been surfaced by the grep that didn't run at session start. Its existence at S56 was the audit's empirical proof of the cost. |
| `grep -rln 'memory-grep\|grep -r.*memory/\|grep memory' internal_docs/SessionLogs/2026-05-*-session-minutes.md` | 2 (literal phrase) / 7 (broader audit-framework adoption — `buffer.overflow\|forma_de_pago\|memory.grep.gate`) | Literal "memory-grep" phrase appears in S56 + S61 minutes. Broader audit-framework adoption (audit-procedure references, `forma_de_pago_preferida` analyses, mandatory-grep-gate Sub-step 1 blocks) spans S55→S62 minutes — 7 contiguous post-trigger sessions. Framework adoption pattern is durable. |

Gate **passes**. The corrective-measure memo, the buffer-overflow
framing, and the trigger keyword are all alive and cross-linked in
current memory. Adoption signal is visible in post-S56 minutes via the
formal Sub-step 1 grep-gate blocks now embedded in audit-stage minutes
(S60/S61/S62) and the buffer-overflow audit-plan reference now standard
in stage agendas.

### Sub-step 2 — Per-session triage (S11→S62, 52 rows)

**Ground-truth source**. Per session minutes: `Stated objective` /
`Objective` / `Session scope` block + `How the session went` /
`Work done` / `Outcome` narrative + explicit memory citations
(`feedback_*.md`, `project_*.md`, `mission_vision`, `MEMORY.md`,
`PROTOCOLS.md`, `bucket_definitions`).

**Verdict criterion** (loose-reading interpretation per S64 agenda's
≤5 N expectation):

- **Y** — session minutes visibly cite or apply memory files relevant
  to the primary topic, OR session is post-S56 and applies the formal
  memory-grep gate.
- **N** — post-hoc evidence shows relevant memory existed and went
  unconsulted, causing rework, wasted investigation, or a wrong framing
  that survived into session output. This is the canonical
  buffer-overflow signature.
- **n/a** — session was pure ops with no memory-relevant topic (e.g.,
  sync-check fix with no memory implications). Strictly applied: none
  in window.

| Session | Date | Primary issue/topic | Key memory terms | Grep evidence (one-line) | Verdict |
|---|---|---|---|---|---|
| S11 | 2026-05-07 | PR#1 merge + Spanish staffer revision + architectural discovery (`Sales Partner Customer Item Commissions`) | `project_logisolu_validations`, `project_sales_partner_commissions_redesign`, `feedback_bespoke_apps_single_responsibility`, `feedback_keep_merged_branches` | Minutes cite all four; design pivot grounded in `project_sales_partner_commissions_redesign` | Y |
| S12 | 2026-05-07 | Carry-forward triage; Phase-1 deferred; BaRe/bench-migrate clarification | `project_erpnext_idiomatic_refactor`, `feedback_consultant_not_peer_engineer`, `feedback_no_rework_sequencing` | Memo + feedback rules cited; clarification grounded in `feedback_bare_is_our_code` (S55 retro confirms) | Y |
| **S13** | 2026-05-07 | Phase 1 fixture_json sub-issue + dev02 fixtures externalisation | `project_si_custom_fields_baseline`, `project_wip_consolidation_plan`, `feedback_check_existing_wip_before_fresh_work` (created post-S13) | Minutes confess: "Memory note `project_si_custom_fields_baseline.md` had explicitly recorded `Developer Mode audit — COMPLETE (2026-04-05) — 13/13 field additions externalized` 32 days earlier. Memory was loaded into session context but parent never triangulated it against the agenda." | **N** |
| S14 | 2026-05-08 | Track C governance + real-name audit + architectural-design pivot | `mission_vision`, `feedback_no_real_client_names`, `feedback_bare_is_our_code`, `feedback_bespoke_apps_single_responsibility`, `feedback_check_existing_wip_before_fresh_work`, `feedback_pr_merge_before_session_close`, `project_erpnext_idiomatic_refactor`, `project_logisolu_validations`, `project_wip_consolidation_plan` | Eight memory files cited; real-name audit grounded in `feedback_no_real_client_names`; three-bucket framing originates here | Y |
| S15 | 2026-05-08 | Phase 0 completion — file architectural-decision issues + 8 prior-issue comment updates | `mission_vision`, `feedback_pr_merge_before_session_close` | Filing-only governance; mission_vision cited as framing | Y |
| S16 | 2026-05-08 | Real-name audit on existing memory directory | `feedback_no_real_client_names`, `feedback_pr_merge_before_session_close`, `feedback_bespoke_apps_single_responsibility`, `feedback_enumerate_mechanisms_before_committing`, `project_erpnext_idiomatic_refactor`, `project_sales_partner_commissions_redesign`, `project_wip_consolidation_plan` | Memory directory IS the audit target; consultation is structurally required and visible | Y |
| S17 | 2026-05-08 | LogiSoluMemory repo standup (Phase 1 of #359) | `MEMORY.md`, PROTOCOLS pattern | Repo standup creates the memory substrate; sub-tasks 1–6 aligned with #359 closure-checklist | Y |
| S18 | 2026-05-09 | LogiSoluKnowBase repo standup (Phase 1 of #358) | `feedback_check_tool_actual_cli_before_following_agenda`, `feedback_clean_up_your_own_residue`, `feedback_consultant_not_peer_engineer`, `feedback_decide_and_advise_on_logistics`, `feedback_no_decision_theatre_on_clerical_work` | Five feedback rules cited; CLI-check application visible in `gh repo create` flag verification | Y |
| S19 | 2026-05-09 | BaRe association to ESACP-platform (#358 item 3) | `feedback_bare_production_reference`, `feedback_no_decision_theatre_on_clerical_work`, `project_bare_bucket_1_association` (created in-session), PROTOCOLS | Five sub-tasks executed; bucket-1-associate memo created via the work | Y |
| S20 | 2026-05-09 | First issue migration ESACP#354 → LSKB (Op-2 pattern) | `feedback_production_off_limits`, `feedback_respect_original_scripts`, `MEMORY.md` | Reframed mid-session as periodic introspection sidebar; relevant memory cited in scope-shift discussion | Y |
| S21 | 2026-05-09 | First migration ESACP#354 → LSKB (re-executed) | `feedback_qa_flag_format_only_matters_on_reject` (created in-session), `project_bare_bucket_1_association`, `project_bucket_2_migration_pattern` (codified in-session) | Pattern memo codified directly from the work; corrective-measure rule extracted from session | Y |
| S22 | 2026-05-09 | Second migration ESACP#356 → LSKB | `project_bucket_2_migration_pattern` | Pattern application visible; comment-and-close flow honors codified Op-2 | Y |
| S23 | 2026-05-09 | Third migration ESACP#357 → LSKB | `feedback_no_rework_sequencing`, `project_bucket_2_migration_pattern` | Pattern continues; cross-repo fixes semantics extracted (later codified as `feedback_pr_fixes_comma_syntax`) | Y |
| S24 | 2026-05-10 | Tracker-redirect ESACP#345 → ce_sri_svc (Op-3 first) | `project_bucket_2_migration_pattern` | First Op-3 (tracker-redirect) sub-shape execution; pattern memo extended | Y |
| S25 | 2026-05-10 | Tracker-redirect ESACP#344 → ce_sri_svc#3 PR (Op-3 second) | `feedback_acceptance_test_required`, `project_bucket_2_migration_pattern` | Full-overlap Op-3 sub-shape (comment-and-close on existing PR-anchored work) | Y |
| S26 | 2026-05-10 | Tracker-redirect ESACP#343 → ce_sri (Op-3 third) | `project_bucket_2_migration_pattern` | Partial-overlap Op-3 sub-shape (no in-flight PR; full migration) | Y |
| S27 | 2026-05-10 | Methodology-stays handling — #197 classification | `feedback_pr_merge_before_session_close`, `project_bucket_2_migration_pattern` | Op-4 (methodology-stays) sub-class first execution; classify-and-comment flow | Y |
| S28 | 2026-05-10 | Phase 2 LSKB execution umbrella standup; file LSKB#5–#10 | `feedback_pr_merge_before_session_close`, `feedback_umbrella_branches`, `project_erpnext_idiomatic_refactor` | Umbrella policy applied; LSKB execution rows materialized | Y |
| S29 | 2026-05-10 | Candidate switch B — `platforms/kvm/session_start.py` bucket-explicit surveys | `bucket_definitions`, `feedback_pr_merge_before_session_close`, `feedback_umbrella_branches`, `project_wip_consolidation_plan` | Premise-drift caught at pre-flight; switch to operator-driven Candidate B; bucket-survey infrastructure landed | Y |
| S30 | 2026-05-10 | route_planner wip-consolidation pilot (Track A) | `feedback_acceptance_test_required`, `feedback_keep_merged_branches`, `feedback_pr_fixes_comma_syntax` (codified in-session), `feedback_pr_merge_before_session_close`, `feedback_umbrella_branches`, `project_bucket_2_migration_pattern`, `project_wip_consolidation_plan` | Seven memory files cited; `fixes` comma-syntax rule extracted from session | Y |
| S31 | 2026-05-11 | #372 dev02 deploy-key blocker investigation | `feedback_ssh_askpass_for_bespoke_repos` (extracted from session), `project_bucket_2_migration_pattern`, `project_erpnext_idiomatic_refactor`, `project_wip_consolidation_plan` | Root cause identified (SSH_ASKPASS missing); corrective rule extracted | Y |
| S32 | 2026-05-11 | Session A — finish #358 closure-checklist (3 trackers + memo cleanup) | `feedback_bare_is_our_code`, `feedback_bespoke_apps_single_responsibility`, `feedback_check_existing_wip_before_fresh_work`, `feedback_keep_merged_branches`, `project_erpnext_idiomatic_refactor`, `project_logisolu_validations`, `project_plan_b_remaining_roadmap`, `project_wip_consolidation_plan` | Eight memory files cited; closure-checklist closed | Y |
| S33 | 2026-05-11 | Consolidate `returnable` wip-onto-main via 1:1:1 sub-branch + Track C step 5 dev02 repoint | `bucket_definitions`, `feedback_acceptance_test_required`, `feedback_ssh_askpass_for_bespoke_repos`, `project_wip_consolidation_plan` | Track A consolidation pattern applied; Track C dev02 repoint executed | Y |
| S34 | 2026-05-11 | Consolidate `ce_sri` wip-onto-main via 1:1:1 sub-branch + Track C step 5 dev02 repoint | `feedback_trivial_fixes_buffer` (codified in-session), PROTOCOLS, `project_wip_consolidation_plan` | TRIVIAL_FIXES.md buffer mechanism extracted from session | Y |
| S35 | 2026-05-11 | Plan-B Epoch-1 Session D1 bundle — close LSKB#2 + LSKB#3 | `feedback_bespoke_apps_single_responsibility`, `feedback_decide_and_advise_on_logistics`, `feedback_keep_merged_branches`, `feedback_no_decision_theatre_on_clerical_work` | Bundling rule tested; D1 closed both rows in single session | Y |
| S36 | 2026-05-12 | Plan-B Epoch-1 D2 bundle — close LSKB#4 + LSKB#5 + LSKB#8 | `feedback_consultant_not_peer_engineer`, `feedback_decide_and_advise_on_logistics`, `feedback_dev_vms_are_disposable`, `feedback_pr_fixes_comma_syntax`, `feedback_production_off_limits`, `project_bucket_2_migration_pattern`, `project_phase3_redis_rq_decision` | Seven memory files cited; D2 bundling-rule sharpening applied to D1 | Y |
| S37 | 2026-05-12 | Risk-tier QA verdict layer's trigger contract from S5.5–36 catch-rate data | `internal_docs/qa-contract.md`, `internal_docs/qa-log.md` (institutional artifacts) | Data-driven revision via `bash awk` over qa-log.md; intuition contradicted by data and overridden; ESACP#380 filed | Y |
| S38 | 2026-05-12 | Plan-B Epoch-1 D3 — LSKB#7 22 DB-resident TBDs documentation | `project_plan_b_remaining_roadmap` | LSKB#7 closed-by-comment; disposition rollup grounded in catalogue + memo | Y |
| S39 | 2026-05-12 | Trailing-items housekeeping sweep (#373 cross-repo `fixes` correction + #382 qa-contract.md §2.1 wording) | `feedback_no_downstream_of_merge_acceptance`, `feedback_pr_fixes_comma_syntax`, `project_bucket_2_migration_pattern`, `project_cloudstack_deferred_until_v16`, `project_erpnext_idiomatic_refactor`, `project_platform_strategy` (archived later) | Six memory files cited; housekeeping-bundle exception applied correctly | Y |
| S40 | 2026-05-12 | Plan-B Phase 4 methodology pass — substrate re-target to local KVM + LSKB#6 scope-trim ladder | `feedback_keep_merged_branches`, `project_cloudstack_deferred_until_v16`, `project_erpnext_idiomatic_refactor`, `project_sales_partner_commissions_redesign` | LSKB#13–#16 sub-issue ladder created; substrate decision recorded; CloudStack-deferral memo cited | Y |
| S41 | 2026-05-12 | Resolve ESACP#386 — Plan-B Phase 4 bespoke-app placement decision | `feedback_bespoke_apps_single_responsibility`, `feedback_keep_merged_branches`, `project_erpnext_idiomatic_refactor`, `project_phase4_bespoke_app_placement` (created in-session), `project_sales_partner_commissions_redesign` | Placement memo created; cross-link from CLAUDE.md | Y |
| S42 | 2026-05-12 | LSKB#12 master/detail DocType design freeze + LSKB-standup tracker filing | `feedback_pr_merge_before_session_close`, `feedback_qa_flag_format_only_matters_on_reject`, `project_sales_partner_commissions_redesign` | Design freeze grounded in S40 memo; planning-class scope | Y |
| S43 | 2026-05-12 | LSKB#17 — `sales_partner_commissions` repo standup (Phase 4 ladder code-class prereq) | `feedback_ssh_askpass_for_bespoke_repos` (preamble used), `feedback_bespoke_apps_single_responsibility`, `project_phase4_bespoke_app_placement`, peer-app pattern (route_planner / ce_sri / ce_sri_svc) | Memory citations sparse in minutes but SSH_ASKPASS preamble visibly applied; peer-app pattern followed; bench-emitted output preserved (S42 directive) | Y |
| S44 | 2026-05-13 | LSKB#13 — `sales_partner_commissions` migration-patch authoring (pre-author verification + design re-open) | `feedback_production_off_limits` (PRODUCTION_20260404 read-only), `project_sales_partner_commissions_redesign` | Currency-vs-Percent fieldtype check + Data anomaly identified; design re-frozen via memo amendment | Y |
| S45 | 2026-05-13 | LSKB#13 continued — patch authoring against post-S44 design | `feedback_keep_merged_branches`, S44 design freeze | Patch authored against corrected fieldtype; colocated tests added | Y |
| S46 | 2026-05-13 | LSKB#14 — `sales_partner_commissions` Server Script rewrite (Before-Save + After-Submit) | `feedback_debug_toggles`, `feedback_keep_merged_branches` | Two Server Scripts rewritten against master/detail shape; debug-toggle pattern flagged | Y |
| S47 | 2026-05-13 | LSKB#15 — substrate-apply on dev02 (paused at version-skew F5) | `feedback_dev_vms_are_disposable`, SSH_ASKPASS preamble pattern | Version-skew net-new discovery (production v13.41.3/v13.39.2 vs dev02 v13.58.22/v13.55.2); LSKB#20 + ESACP#387 filed; substrate gap surfaced rather than missed | Y |
| S48 | 2026-05-14 | LSKB#20 Path 1 — rebuild dev02 at production-snapshot versions | `feedback_no_passive_causal_framing` (extracted in-session), `MEMORY.md`, `project_saconsole_as_fleet_capability_record` (extracted in-session) | Passive-causal framing rule extracted from session; saconsole-as-record memo created | Y |
| S49 | 2026-05-14 | ESACP#388 — declare packer as a saconsole dependency (LSKB#20 unblock) | `project_saconsole_as_fleet_capability_record` | Saconsole-dependency declaration applied; pipeline gap closed | Y |
| S50 | 2026-05-14 | LSKB#20 Path 1 execution — packer build + dev02 destroy/rebuild | (no visible memory refs in minutes) | Mechanical execution under operator-pick Path 1; surfaced ESACP#390 (latent packer env-var-stripping flaw, undocumented prior); net-new institutional knowledge | Y |
| S51 | 2026-05-14 | ESACP#390 fix — pass FRAPPE_BRANCH/ERPNEXT_BRANCH via `sudo env` | `feedback_keep_merged_branches`, `feedback_no_downstream_of_merge_acceptance`, `feedback_pr_merge_before_session_close` | Fix authored against S50 finding; packer end-to-end re-run | Y |
| S52 | 2026-05-14 | ESACP#392 fix — uv pip refuses frappe v13.41.3 over yanked-braintree pre-release | `feedback_keep_merged_branches`, `feedback_no_downstream_of_merge_acceptance`, `feedback_no_passive_causal_framing`, `feedback_pr_merge_before_session_close`, `project_saconsole_as_fleet_capability_record` | Five memory files cited; passive-framing rule applied to root-cause analysis | Y |
| S53 | 2026-05-15 | LSKB#20 Plan-C tag pivot — research v13 tag history for buildable substrate target | `feedback_dev_vms_are_disposable`, `feedback_pr_merge_before_session_close`, `feedback_remote_script_pattern` | Plan-C pivot grounded in dev-VMs-disposable rule; remote-script pattern applied to saconsole-driven build | Y |
| S54 | 2026-05-15 | LSKB#15 — substrate-apply on Plan-C-rebuilt dev02 (frappe v13.58.22 / erpnext v13.55.2) | `feedback_dev_vms_are_disposable`, `feedback_pr_merge_before_session_close` | Substrate-apply retried on S53 substrate; further version-handling discoveries | Y |
| S55 | 2026-05-18 | ESACP#398 Path A — disable MariaDB `performance_schema` to unblock `delete_duplicate_indexes` patch | `feedback_keep_merged_branches`, `feedback_pr_merge_before_session_close` | Path A executed; substrate-config gap remediation grounded in ansible + packer change | Y |
| **S56** | 2026-05-19 | ce_sri#10 `forma_de_pago_preferida` — bench migrate fixtures collision | `project_cesri_modules_fixture_bugs` ("Bug 3", 2026-04-04 GH#96), `feedback_bisect_before_hypothesizing`, `feedback_grep_memory_before_issue_body` (extracted from session) | Minutes confess (row 9 of work-table): "Memory grep (the step that should have been step 0): `grep -lr forma_de_pago_preferida memory/` → 10 hits, including `project_cesri_modules_fixture_bugs.md` ('Bug 3', filed 2026-04-04 as GH #96) → every conclusion the investigation re-derived was already in memory, with the institutional fix" | **N** |
| S57 | 2026-05-19 | Introspection sidebar — collaboration-management fractures retrospective | `feedback_bisect_before_hypothesizing`, `feedback_clean_up_your_own_residue`, `feedback_consultant_not_peer_engineer`, `feedback_decide_and_advise_on_logistics`, `feedback_fix_the_design_not_the_escaping`, `feedback_grep_memory_before_issue_body`, `feedback_mission_priority_check`, `feedback_narration_not_action`, `feedback_no_decision_theatre_on_clerical_work`, `feedback_no_invented_commands`, `feedback_no_passive_causal_framing`, `feedback_no_real_client_names`, `feedback_not_perfection_project`, `feedback_plan_before_code`, `feedback_scc_command`, `feedback_tactical_vs_consultant_mode`, `project_pages_site_v1` (created in-session), `MEMORY.md` | 17 feedback files retrospected; the corpus IS the topic; memory consultation maximal | Y |
| S58 | 2026-05-19 | Build GitHub Pages site v1 (ESACP#402) — 5 sub-steps on `umbrella/pages-site-v1` | `feedback_git_mv_restage_after_edit` (extracted in-session), `feedback_narration_not_action`, `feedback_pr_merge_before_session_close`, `project_buffer_overflow_audit_plan`, `project_pages_site_v1`, `MEMORY.md` | Six memory files cited; `git mv` + edit re-stage rule extracted from session | Y |
| S59 | 2026-05-19 | Sidebar — Pages-site v1 follow-up polish (ESACP#404) | `feedback_dev_vms_are_disposable`, `feedback_keep_merged_branches` | Operator-redirected at session start (originally agendaed for #400 Step 1); #400 audit Step 1 re-suspended; sidebar discipline applied | Y |
| S60 | 2026-05-19 | ESACP#400 Step 1 — overall plan review (Sub-steps 1→5) | `mission_vision`, `project_buffer_overflow_audit_plan`, `project_erpnext_idiomatic_refactor`, `bucket_definitions`, `feedback_dev_vms_are_disposable`, `feedback_qa_flag_format_only_matters_on_reject` | **Audit framework's mandatory memory-grep gate visibly applied** — Sub-step 1 grep table captured into report; 3 planning anchors enumerated | Y |
| S61 | 2026-05-19 | ESACP#400 Step 2 — stage list proposal (6 stage blocks drafted) | `mission_vision`, `project_buffer_overflow_audit_plan`, `feedback_dev_vms_are_disposable`, `feedback_qa_flag_format_only_matters_on_reject` | Framework gate applied; observation→stage mapping table grounded in S60 enumeration | Y |
| S62 | 2026-05-20 | ESACP#400 Stage 1 — bucket-placement compliance execution | `bucket_definitions`, `feedback_dev_vms_are_disposable`, `feedback_qa_flag_format_only_matters_on_reject`, `MEMORY.md`, `project_bucket_2_migration_pattern`, `project_wip_consolidation_plan` | Framework gate applied; 6-pass per-bucket compliance audit; ESACP#307 → LSKB#21 migration executed mid-session | Y |

**Triage rollup**:

- **Y**: 50 sessions
- **N**: 2 sessions (S13, S56)
- **n/a**: 0 sessions

Hit rate: 50 / 52 = **96.2%**.

### Sub-step 3 — No's table + corrective measures

| Session | What memory should have been consulted | Corrective measure | Status |
|---|---|---|---|
| **S13** (2026-05-07-2236) | `project_si_custom_fields_baseline.md` (recorded 2026-04-05 — "Developer Mode audit COMPLETE — 13/13 field additions externalized"); existing `wip/*` work on `ce_sri/wip/2026-03-25` + `route_planner/wip/2026-03-31` + `returnable/wip/2026-03-31` containing the Phase-1 externalisation already authored 5 weeks earlier | `feedback_check_existing_wip_before_fresh_work.md` — "Before treating a session's stated task as new work, grep prior commits + memory for prior completion of the same target — bespoke fleet runs from wip/* branches that don't reach main" | **Already shipped** (created post-S13; in current memory) |
| **S56** (2026-05-19-0752) | `project_cesri_modules_fixture_bugs.md` "Bug 3" (filed 2026-04-04, GH #96): same fieldname `forma_de_pago_preferida`, same DocField vs CustomField collision class, same root-cause analysis, **and** the institutional DELETE statement already shipped in BaRe `45b8775` + generic `g2_clear_fixture_custom_fields.py` | `feedback_grep_memory_before_issue_body.md` — "When picking up an issue body that presents a confident diagnosis, first grep memory + recent minutes for the error string / fieldname / table; only treat the body as authoritative if memory is silent" | **Already shipped** (created in S56; in current memory) |

Both N's have **already-shipped corrective measures**. No new
operator-reminder, new pre-commit hook, or further `feedback_*.md`
elevation required at Stage 3 close.

### Sub-step 4 — S56 trigger confirmation

Per the audit-plan spec and the S64 agenda's explicit requirement:

1. **S56 (2026-05-19-0752) is one of the N rows.** Confirmed in
   Sub-step 2 triage table and itemised in Sub-step 3 corrective-measure
   table. The session minutes themselves carry the confession (row 9 of
   the work-table): "Memory grep (the step that should have been step
   0): … every conclusion the investigation re-derived was already in
   memory, with the institutional fix."

2. **Its corrective measure
   (`feedback_grep_memory_before_issue_body.md`) is already shipped.**
   Confirmed via Sub-step 1 mandatory grep gate (`grep -rl
   'feedback_grep_memory_before_issue_body\|grep memory before' memory/`
   → 2 hits including `MEMORY.md` + `project_buffer_overflow_audit_plan.md`).
   The file itself is the third hit when discovered by name. Memory
   index pointer present.

3. **The Stage 3 audit pattern is the audit-framework's check that the
   corrective measure is being honored in subsequent sessions.**
   Confirmed via Sub-step 1 grep 4 (broader-pattern search → 7
   contiguous post-trigger sessions S55→S62 carry buffer-overflow
   framing, `forma_de_pago_preferida` references, or formal Sub-step 1
   memory-grep gates in audit-stage minutes). Adoption is durable and
   institutional, not parked on a single feedback memo.

### Sub-step 5 — Partitioning safeguard

No-count = **2** (S13, S56). Well below the agenda's ≤10 split-trigger
and inside the ≤5 default expectation. **No split required.** Stage 3
delivers in a single session per the agenda's wall-clock estimate.

### Sub-step 6 — Joint review at session end

Stage 3 findings summary:

- **Memory hit-rate is high** (96.2%) across the audit window.
- **Two canonical buffer-overflow incidents** (S13, S56) — both have
  shipped corrective measures already in memory and in MEMORY.md.
- **Post-S56 framework adoption is durable** — 7 contiguous sessions
  (S55→S62) carry buffer-overflow framing or formal Sub-step 1
  memory-grep gates in their minutes; no recurrence of the trigger
  pattern after S56.
- **No new corrective measures ordered** at Stage 3 close.

The audit's response to its own trigger has held: the corrective rule
was extracted, codified, and is being honored. Stage 3 is the framework
verifying itself.

### Stage 3 close

**Drift items requiring corrective measures**: none operational this
session. Two historical N's (S13, S56) carry corrective measures
already shipped pre-Stage-3 (`feedback_check_existing_wip_before_fresh_work.md`
+ `feedback_grep_memory_before_issue_body.md` respectively).

**Carry-forward to consolidation session** (Step 3, S6X):

- None from Stage 3. Both N's are pre-resolved.

**No Stage 4 execution this session.** Stage 4
(Acceptance-test compliance) starts S65 at the earliest, per Sub-step 4
of the S64 agenda.
