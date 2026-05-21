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

---

## Stage 4 — Acceptance-test compliance (S65)

**Question answered**. Per
[`feedback_acceptance_test_required.md`](../../.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/feedback_acceptance_test_required.md),
have recent issue closes (S11 = 2026-05-06 → present) shipped acceptance
tests or recorded acceptance evidence?

**Trigger context**. Memo order 1→6 (operator S60). Audit window S11
(2026-05-06) → S64 (2026-05-20). No S60/S61 observations land here —
Stage 4 audits the close-discipline mechanism, complementary to Stage 1
(bucket-placement) and Stage 5 (1:1:1 / umbrella). Its inputs are all
issue closes across all six trackers in window.

### Sub-step 1 — Mandatory grep gate (universal)

| Grep | Hits | Read |
|---|---:|---|
| `grep -rl feedback_acceptance_test_required memory/` | 3 | `project_buffer_overflow_audit_plan.md` (audit-procedure memo), `feedback_no_downstream_of_merge_acceptance.md` (sibling rule extracted from S30 #371), `MEMORY.md` (index entry). The rule memo itself is the fourth hit by name. Cross-reference fan-out is healthy. |
| `grep -rln 'acceptance' internal_docs/SessionLogs/` | 208 (files) | Acceptance vocabulary is ubiquitous in session minutes across the window — every substantive close-out commit carries acceptance language, every audit-stage minutes block discusses acceptance evidence. Durable, not parked. |
| `grep -cn 'acceptance' internal_docs/qa-log.md` | 43 (lines) | qa-log entries routinely cite acceptance status in their verdict bodies; 43 lines is dense for a single-purpose log. Verdict-layer alignment with `feedback_acceptance_test_required` is institutional. |

Gate **passes**: rule memo is cross-linked from at least two siblings +
`MEMORY.md`; acceptance vocabulary is ubiquitous in minutes + qa-log.
No cold spot.

### Sub-step 2 — Per-bucket closes pass (6 buckets)

**Ground-truth source**. `gh issue list --state closed --search
'closed:>2026-05-06'` per repo, cross-checked against close commits
(`git log --grep="fixes #\|fixes martinhbramwell"`) and individual
issue close-comments (`gh issue view --comments`). State reason from
`gh api repos/<repo>/issues/<n> --jq '.state_reason'`.

**Evidence vocabulary** (per agenda):
- **manual** — verification narrative in commit body or close-comment
  (includes empirical-test transcripts, build logs, end-to-end UI
  verifications, etc.)
- **docs-lands** — docs/decision/methodology class; acceptance is "doc
  lands at canonical location" (CLAUDE.md, memo, qa-contract, etc.)
- **migration** — `not_planned` Op 2/3/4 close; acceptance is
  "pointer comment posted + target tracker carries continuation"
- **supersession** — `not_planned` Plan-A-retired-by-Plan-B close;
  acceptance is "framework supersession explained + reopen anchor
  named"
- **test** — explicit Pytest / Playwright / shell-script path shipped
  in the closing PR
- **none** — no acceptance evidence recorded

A **Compliant Y** verdict requires the close to carry evidence in at
least one of these categories AND the evidence-class to match the
close's substance class (e.g., a code-class close cannot claim
"docs-lands" — that would be drift).

#### Pass 1 — Bucket 1: ESACP (37 closes in window)

**Migration / supersession closes** (13 — all `state_reason: not_planned`):

| Issue | Title (truncated) | Target | Class | Evidence | Y/N |
|---:|---|---|---|---|---:|
| #284 | Industry→Company race | superseded; reopen anchor [#355](https://github.com/martinhbramwell/ESACP/issues/355) | wizard-replay (Plan-A retired) | supersession | Y |
| #285 | B06 cold-system regen | superseded; reopen anchor #355 | wizard-replay (Plan-A retired) | supersession | Y |
| #290 | Español/Mexico locale fail | superseded; reopen anchor #355 | wizard-replay (Plan-A retired) | supersession | Y |
| #292 | Playwright en/Canada fixture | superseded; reopen anchor #355 | wizard-replay (Plan-A retired) | supersession | Y |
| #296 | HTTP 499 race | superseded; reopen anchor #355 | wizard-replay (Plan-A retired) | supersession | Y |
| #297 | welcome-modal multi-Next race | superseded; reopen anchor #355 | wizard-replay (Plan-A retired) | supersession | Y |
| #354 | Server Script event-name doc | [LSKB#1](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/1) | Op-2 (S21) | migration | Y |
| #356 | Phase 1 fixture_json | [LSKB#2](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/2) | Op-2 (S22) | migration | Y |
| #357 | Phase 1B Custom DocPerm | [LSKB#3](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/3) | Op-2 (S23) | migration | Y |
| #345 | ce_sri_svc retry-with-backoff exhaustion | [ce_sri_svc#3](https://github.com/martinhbramwell/ce_sri_svc/issues/3) | Op-3 (S24) | migration | Y |
| #344 | ce_sri_svc retry-with-backoff transient | ce_sri_svc | Op-3 (S25) | migration | Y |
| #343 | dev01 lab egress ECONNRESET | [ce_sri#5](https://github.com/martinhbramwell/ce_sri/issues/5) | Op-3 (S26) | migration | Y |
| #307 | hrms+payments eval on company-specific v13 | [LSKB#21](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/21) | Op-2 (S62, this audit Stage 1) | migration | Y |

**Code / infra closes** (11 — `state_reason: completed`):

| Issue | Close commit / PR | Class | Evidence (location) | Y/N |
|---:|---|---|---|---:|
| #369 | `a85cde0` + LSM `b9e39fb` (S29) | feat — bucket surveys | manual (close-comment: "Acceptance verified end-to-end: session_start.py with logisolu_memory bucket active produced Bucket Surveys section showing both commits in the live survey output") | Y |
| #371 | route_planner PR #1 `ea62def` (S30) | track — wip-consolidation pilot | manual (close-comment + S30 minutes; criterion-5 partial with explicit deferral to #372 chain; 4 of 5 criteria green at close) | Y |
| #372 | LSM PR #2 `261312f` (S31) | bug — dev02 deploy-key | manual (close-comment carries 5-criterion mapping; criterion 2 empirically verified with shell transcript exit-0) | Y |
| #373 | LSM `1d3fce8` cross-repo `fixes` (S39) | chore(memory) — fixes-keyword correction | manual (close-comment: "Dogfood result: the very commit that corrects the 'cross-repo fixes doesn't auto-close' memory was itself auto-closed via cross-repo fixes") | Y |
| #377 | BtlMng PR #1 `8bd44620` cross-repo `fixes` (S33) | chore — BtlMng wip-consolidation Phase 2 | manual (S33 minutes record consolidation onto master; cross-repo `fixes` auto-close confirmed) | Y |
| #378 | `6910f48 fixes #378` (S33) | chore(hosts) — BtlMng rename correction | manual (commit body: latent fix, discovered S33 during #377 pre-flight; `bucket_survey.py` reference verified) | Y |
| #388 | `e94e9a5 fixes #388` (S49) | infra(saconsole) — packer dep declaration | manual (close-comment carries design direction post-S48; saconsole rebuild verifies `command -v packer`) | Y |
| #390 | PR #391 `9ef1aa5 fixes #390` (S51) | bug(packer) — env-var stripping | manual (commit body documents root cause + fix; build re-ran with correct tags) | Y |
| #392 | PR #393 `e283716 fixes #392` (S52) | bug(packer) — uv override for yanked deps | manual (commit body carries explicit `## Acceptance` section: braintree resolver-stage barrier cleared (verified); tag-gating verified) | Y |
| #398 | PR #399 `0797d471 fixes #398` (S55) | bug(substrate) — MariaDB perf-schema | manual (commit body documents Plan-C path, mechanism, revert via `fbc1299` + `tabPatch Log` pre-seeding doc as durable record) | Y |
| #404 | PR #405 `d08699e fixes #404` (S59) | feat(pages) — slideshow nav + QR-code | manual (S59 minutes record claude-in-chrome MCP end-to-end verification of slideshow nav buttons + QR slide render) | Y |

**Docs / decision / methodology closes** (13 — `state_reason: completed`):

| Issue | Close commit / mechanism | Class | Evidence | Y/N |
|---:|---|---|---|---:|
| #312 | manual close (S12) | docs — customisation inventory | docs-lands (close-comment: deliverables now at LogiSoluValidations + #353; both satisfied) | Y |
| #339 | manual close (S12) | feat(audit) — language alias map | docs-lands (close-comment: superseded by #353 Phase 6 ownership) | Y |
| #358 | `b52de7f fixes #358` (S32) | decision — three-bucket architecture | docs-lands (CLAUDE.md Three-Bucket Architecture section landed verbatim from this issue) | Y |
| #359 | manual close (S17) | decision — LogiSoluMemory private repo | docs-lands (close-comment: standup checklist 4/5 items green; item 5 split with #358) | Y |
| #362 | `ed73877` (S20) | docs — CLAUDE.md trailer Opus 4.6→4.7 | docs-lands (commit lands CLAUDE.md fix + 8 qa-log row backfill) | Y |
| #363 | `abcdd02` (S20) | docs — introspection-sidebar session-type | docs-lands (CLAUDE.md policy section added) | Y |
| #364 | manual close (S32) | chore(audit-hook) — pre-close audit-grep timing | docs-lands — **soft observation 1** (close-comment self-flags as "provisional pattern-break"; behavioral mitigation chosen over structural hook-timing fix; comment text "does not retire the issue" coexists with state=closed) | Y (with caveat) |
| #367 | `611c03e` (S20) | chore(qa-contract) — §5 malformed-verdict semantics | docs-lands (qa-contract.md §5 clarified) | Y |
| #373 | (listed above under Code/infra — `chore(memory)`; cross-classification) | — | — | — |
| #380 | PR #381 `0137977 fixes #380` (S37) | chore(qa) — risk-tier triggers | docs-lands (qa-contract.md risk-tier amendments landed from Sessions-5.5-36 calibration data) | Y |
| #382 | PR #384 `554ad24 fixes #382` (S39) | chore(qa) — §2.1 condition 2 broaden | docs-lands (close-comment: PR landed three-clause proposal verbatim + one tightening; QA verdicts logged in qa-log.md S39 rows) | Y |
| #385 | manual close (S40) | docs(chronology) — Phase 4 substrate re-target | docs-lands (`project_erpnext_idiomatic_refactor.md` S40 amendment) | Y |
| #386 | manual close (S41) | arch — Phase 4 bespoke-app placement decision | docs-lands (`project_phase4_bespoke_app_placement.md` created; CLAUDE.md cross-link) | Y |
| #402 | PR #403 squash-merge (S58) | feat(pages) — Pages site v1 | manual (close-comment: full acceptance satisfied — Pages-enable API success; three live URLs HTTP-200 verified via claude-in-chrome MCP) | Y |

**ESACP bucket summary**: 37/37 closes have documented acceptance
evidence in their close-class. Cross-classified #373 counted once (under
Code/infra `chore(memory)` since the audit's Stage 1 list includes it as
the `fixes`-keyword correction).

**Soft observation 1 (#364)**: closed completed despite close-comment's
own caveat "does not retire the issue" — structural hook-timing fix was
deferred; behavioral mitigation was treated as sufficient. The close is
transparent (caveat in comment) but the issue's stated direction
(structural fix) was not the deliverable. Disposition: see
Sub-step 3.

#### Pass 2 — Bucket 1-associate: BaRe (1 close in window)

| Issue | Close commit | Class | Evidence | Y/N |
|---:|---|---|---|---:|
| #9 | `8653412 docs: add README declaring bucket-1 association` (fixes #9) | docs(README) | docs-lands (README cross-reference landed; BaRe-as-bucket-1-associate is now discoverable on its own tracker) | Y |

**BaRe bucket summary**: 1/1 compliant.

#### Pass 3 — Bucket 2: LSKB (12 closes in window)

| Issue | Close mechanism | Class | Evidence | Y/N |
|---:|---|---|---|---:|
| #2 | manual close (S35) | Plan-B Phase 1 — 14 fixture_json Custom Fields | manual (close-comment table with 14-entry routing breakdown: 11 → ce_sri PR #7 `dd7199e`, 2 → route_planner PR #1 `ea62def`, 1 discarded; ce_sri + route_planner PRs verified merged) | Y |
| #3 | ce_sri PR #8 `b22e263 fixes LSKB#3` cross-repo (S35) | Plan-B Phase 1B — 3 Custom DocPerm patches | manual (close-comment notes ESACP#372 prerequisite was load-bearing; ce_sri PR #8 carries the port) | Y |
| #4 | manual close (S36) | Plan-B Phase 2 — 12 patches | docs-lands — **soft observation 2** (close-comment explicitly reframes acceptance from execution → classification: "Phase 2 is being closed at classification-complete, not execution-complete. Physical removal of these 12 patches from the vendored Frappe tree is deferred to the CloudStack Epoch-2 substrate standup"; LSKB#11 carries staged drift promotions) | Y (with caveat) |
| #5 | manual close (S36) | Plan-B Phase 3 — redis/rq decision | docs-lands (`project_phase3_redis_rq_decision.md` carries full rationale + escalation path) | Y |
| #7 | manual close (S38) | Plan-B Phase 5 — 22 DB-resident TBDs catalogue | docs-lands (close-comment with full 22-entry triage table; per-entry disposition keep/move/port/patch/drop documented) | Y |
| #8 | ce_sri `924ff2e fixes LSKB#8` cross-repo (S36) | Plan-B Phase 6 — es-EC aliasing | manual (ce_sri commit body documents language aliasing implementation; cross-repo `fixes` auto-close) | Y |
| #12 | manual close (S42) | Plan-B Phase 4 design | docs-lands (close-comment: placement gating dependency #386 resolved; design freeze recorded; JSON exports produced as record-of-truth) | Y |
| #13 | sales_partner_commissions repo cross-repo `fixes` (S45) | Plan-B Phase 4 migration patch | manual (close-comment: design re-freeze unblocking narrative; patch authoring grounded in S44 PRODUCTION_20260404 SQL-dump verification; colocated tests per `feedback_tests_with_code`) | Y |
| #14 | sales_partner_commissions repo cross-repo `fixes` (S46) | Plan-B Phase 4 Server Script rewrites | manual (Stage 2 audit verified ladder closure: "Server Script rewrites against master/detail shape landed by 2026-05-15"; commit body on sales_partner_commissions carries acceptance) | Y |
| #17 | sales_partner_commissions cross-repo `fixes` (S43) | chore — repo standup | manual (repo standup verified: empty Frappe app skeleton exists at `martinhbramwell/sales_partner_commissions`) | Y |
| #19 | LSM `bd31a50 fixes LSKB#19` cross-repo (S44) | Plan-B Phase 4 currency re-freeze | docs-lands (memo amendment: `project_sales_partner_commissions_redesign.md` re-frozen with Currency fieldtype + Data anomaly handling) | Y |
| #20 | manual close (S53) | infra — substrate-readiness | manual (close-comment: 5-row "Pin discipline chain — verified end-to-end" table; build/destroy/provision logs retained at saconsole:`/tmp/build-LSKB20-S53.log`) | Y |

**LSKB bucket summary**: 12/12 compliant. Soft observation on #4 carried.

#### Pass 4 — Bucket 2 (LogiSoluValidations) (0 closes in window)

No closes in window. Both open issues (#4, #5) are docs-class and
non-blocking per Stage 1 verdict.

#### Pass 5 — Bucket 3: ce_sri (1 close in window)

| Issue | Close mechanism | Class | Evidence | Y/N |
|---:|---|---|---|---:|
| #6 | ce_sri PR #7 `dd7199e` (S34) — same PR also `fixes ce_sri#7` intra-repo | Plan-B Phase 1 — 11 ce_sri-routed Custom Fields onto main | manual (LSKB#2 close-comment table cross-references this PR as the carrier for the 11 ce_sri-routed entries; wip-consolidation Phase 1 verified) | Y |

**ce_sri bucket summary**: 1/1 compliant.

#### Pass 6 — Bucket 3: ce_sri_svc (0 closes in window)

No closes in window. Both open issues (#1, #4) are unrelated to current
session focus.

### Sub-step 3 — Drift items + corrective measures

**No hard drift items.** All 51 closes across the six buckets carry
documented acceptance evidence appropriate to their close-class.

**Soft observations** (2 — transparent acceptance reframing, not
discipline violation):

| # | Issue | What was reframed | Transparency | Corrective measure |
|---:|---|---|---|---|
| 1 | ESACP#364 | Acceptance went from "structural hook-timing fix" (issue body) to "behavioral mitigation: in-session pre-close audit grep" (close-comment) | Close-comment self-flags "provisional pattern-break", "does not retire the issue" | **None required** — close-comment is transparent. Post-close history (Sessions 33–64 use the formal Sub-step 1 grep-gate pattern in audit-stage minutes) shows the behavioral mitigation became institutional, so the structural fix is no longer load-bearing. Recommend: ratify the close as "behaviorally retired, not structurally retired" in the next CLAUDE.md or `feedback_*.md` touch that mentions audit-hook timing. |
| 2 | LSKB#4 | Acceptance went from "12 patches removed from vendored Frappe + bench migrate green" (issue body) to "classification-complete, per-entry strategy field describes removal mechanism" (close-comment) | Close-comment self-flags: "Phase 2 is being closed at classification-complete, not execution-complete" + LSKB#11 named as continuation row | **None required** — close-comment is transparent. Per Stage 2 verdict, LSKB#11 (open) carries staged drift promotions as Phase-2-extended; execution-acceptance moves to the CloudStack Epoch-2 substrate standup naturally. Already on the consolidation-session backlog as "ratify LSKB#11 as Phase-2-extended in `project_erpnext_idiomatic_refactor.md` next memo touch" (Stage 2 carry-forward). |

Both soft observations are **acceptable-by-class** acceptance
reframings. Neither is a discipline violation: in both cases, the
close-comment explicitly names the reframing, the deferred substance,
and the continuation tracker (where applicable). This satisfies the
spirit of `feedback_acceptance_test_required` (honest acceptance
recording) even if the literal text ("a successful acceptance test that
proves the fix works") would, strict-read, require execution-level
verification at close-time.

**Pattern check** — neither soft case is repeat-class:
- #364 is the only audit-hook timing close in window
- LSKB#4 is the only Phase-2-drop close in window

So neither warrants institutional-rule elevation. The transparency
discipline (close-comments naming the reframing) is the live correction
mechanism; no `feedback_*.md` extension needed.

### Sub-step 4 — Compliance rate + pattern analysis

**Compliance rate**: 51 / 51 = **100%** (strict-Y with 2 soft caveats
on acceptance-reframing transparency, neither a discipline violation).

**Compliance by close class**:

| Class | Count | Y | N | Compliance pattern |
|---|---:|---:|---:|---|
| Migration (Op 2/3/4) | 7 | 7 | 0 | Uniform — pointer comment + target tracker pickup |
| Supersession (Plan-A retired) | 6 | 6 | 0 | Uniform — framework supersession note + reopen anchor (#355) |
| Code / infra (`fixes` keyword or manual) | 18 | 18 | 0 | Uniform — verification narrative in commit body or close-comment |
| Docs / decision / methodology | 19 | 19 | 0 | Uniform — doc lands at canonical location |
| Test path (explicit) | 1 | 1 | 0 | LSKB#13 (colocated migration-patch tests); #404 (Pages site UI via MCP) — sparse but visible |
| **Total** | **51** | **51** | **0** | **100%** |

(Counts cross-classified at most-substantive class. Some closes carry
multiple evidence types; primary evidence selected.)

**Pattern of misses**: none. No close was filed without acceptance
evidence appropriate to its class.

**Patterns observed (institutional)**:

1. **Migration class** universally honors the pointer-comment +
   target-tracker mechanism codified in
   `project_bucket_2_migration_pattern.md`. Op 2/3/4 sub-shapes all
   produce identifiable evidence at close.
2. **Supersession class** (S12 Plan-A→Plan-B moot-sweep) uses a
   uniform template: framework explanation + named reopen anchor
   (#355). No drift across 6 closes.
3. **Code-class** closes routinely carry explicit `## Acceptance`
   sections in their commit bodies (#392, #390, #398) or detailed
   acceptance-criteria mappings in close-comments (#372, #369, #371).
   This is the strongest evidence pattern.
4. **Docs/decision-class** closes use "doc lands" as the acceptance
   convention. The convention is consistently applied; no close-comment
   misstates the substance class.
5. **Cross-repo `fixes`** (post-S30 discovery, auto-close works) is now
   used routinely — 8 of 18 code-class closes leveraged it. None
   produced a `feedback_no_downstream_of_merge_acceptance` violation in
   window (the rule extracted from S30 #371 has held).
6. **Soft reframing** (2 cases: #364, LSKB#4) is transparent and
   tracker-deferred. The audit's view: this is the rule working as
   intended, not failing — acceptance evidence is honest about what
   was actually verified.

### Sub-step 5 — Partitioning safeguard

Non-compliant count = **0** (well under the agenda's ≤10 split-trigger
and ≤5 default expectation). **No partitioning required.** Stage 4
delivers in a single session per the agenda's wall-clock estimate.

### Sub-step 6 — Joint review at session end

**Stage 4 findings summary**:

- **100% compliance** across all six trackers (51 / 51 closes have
  documented acceptance evidence appropriate to their close-class).
- **Zero hard drift items.** No close was filed without recorded
  acceptance evidence.
- **Two soft observations** (#364 audit-hook timing, LSKB#4 Phase-2
  drop) — both are transparent acceptance-reframings, both
  tracker-deferred to continuation rows (Sessions-33+ in-session
  audit-grep pattern; LSKB#11 staged drift promotions). Neither is a
  discipline violation; neither needs corrective action.
- **No new `feedback_*.md`, no CLAUDE.md amendment, and no new tracker
  issues filed.** The acceptance-test discipline is institutionally
  load-bearing and operating.

The `feedback_acceptance_test_required` rule (with its companion
`feedback_no_downstream_of_merge_acceptance`) is being honored at the
substantive level. The 2 soft cases preserve transparency — the rule's
spirit — even where the literal text would, strict-read, require
execution-level acceptance at close-time.

### Stage 4 close

**Drift items requiring corrective measures**: none operational this
session. Two soft observations (Sub-step 3 table) are
acceptable-by-class acceptance reframings with transparent
close-comments and tracker-deferred continuations.

**Carry-forward to consolidation session** (Step 3, S6X):

- None new from Stage 4. The Stage 2 carry-forward (ratify LSKB#11 as
  Phase-2-extended) covers soft observation 2; no additional item needed
  for soft observation 1 (#364's behavioral mitigation is already
  institutional).

**Carry-forward to Stage 6** (M&V alignment):

- The 51-close corpus is the primary input to Stage 6 — Sub-step 2's
  per-bucket tables provide the categorisation surface for Stage 6's
  mission-property-advanced verdict.

**No Stage 5 execution this session.** Stage 5 (1:1:1 discipline)
starts S66 at the earliest, per Sub-step 6 of the S65 agenda.

---

## Stage 5 — 1:1:1 discipline (S66)

**Question answered**. Across the S11→S65 audit window (55 sessions,
2026-05-07 → 2026-05-20), have sessions actually been 1 issue : 1
branch : 1 session for substantive work, or has bundling crept beyond
the housekeeping-exception and umbrella-branch carve-outs codified in
CLAUDE.md?

**Trigger context**. Memo order 1→6 (operator S60). Stage 5 carries one
S60/S61 observation: **Obs 4** (`umbrella/ladder-fixture` orphan,
ESACP#361). Sub-step 6 cross-references Stage 1's wip/* enumeration.

### Sub-step 1 — Mandatory grep gate

| Grep | Hits | Read |
|---|---:|---|
| `grep -rl feedback_issue_branch_session_discipline /home/hasan/.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/` | 3 | `MEMORY.md` (index), `feedback_issue_branch_session_discipline.md` (canonical 1:1:1 rule + 2026-04-20 housekeeping amendment #262), `feedback_pr_merge_before_session_close.md` (related "merged" semantics referenced by umbrella-cert). |
| `grep -rl feedback_umbrella_branches /home/hasan/.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/` | 2 | `MEMORY.md` (index), `feedback_umbrella_branches.md` (canonical umbrella-branch policy, #236 adopted 2026-04-22). |
| `grep -rln '1:1:1\|housekeeping\|umbrella/' internal_docs/SessionLogs/` | 169 hits across files | Wide coverage across S11→S65 minutes + agendas; vocabulary durable across the audit window. Universal corpus for Sub-step 2. |

**Corpus**. Memory: the two `feedback_*` memos above + CLAUDE.md
"Session Protocol" section (1:1:1 / housekeeping-bundle /
introspection-sidebar / umbrella-branch policies). Minutes: 55
session-minutes files for S11→S65 in
`internal_docs/SessionLogs/2026-05-{07,08,…,20}-*-session-minutes.md`.
Mapping confirmed S11 = `2026-05-07-0748`, S65 = `2026-05-20-1149`.

**Policy adoption dates vs audit window**. Both policies pre-date the
audit window:

- 1:1:1 discipline + housekeeping-bundle amendment: ESACP#262 adopted
  **2026-04-20** (16 days before S11).
- Umbrella-branch policy: ESACP#236 adopted **2026-04-22** (14 days
  before S11).

Consequence: **every session in the audit window is post-policy.** No
"new-in-window" exemption applies (Sub-step 4 below revisits this).

### Sub-step 2 — Per-session shallow scan (S11→S65)

| S# | Date | Primary issue(s) | Branch | Session-type | Compliance | Note |
|---:|---|---|---|---|---|---|
| 11 | 2026-05-07 | LSV PR#1 + PR#2 umbrella-cert + PR#3 doc revise | `main` + `umbrella/erpnext-idiomatic-refactor` cert | umbrella-cert (scope-expanded) | **N** | Cert merge + scope-expanded into discovery work in same session; `feedback_umbrella_branches.md` requires cert to be a distinct session |
| 12 | 2026-05-07 | #353 triage | `main` (planning) | substantive | Y | planning-only |
| 13 | 2026-05-07 | #356, #357 (Phase-1 sub-issue filing) | `phase-1-fixture-equivalent` (sub-branch of `umbrella/erpnext-idiomatic-refactor`) | umbrella-sub | Y | |
| 14 | 2026-05-08 | #358, #359 architectural discovery | `main` (planning) | substantive | Y | planning-only; filed issues for S15 |
| 15 | 2026-05-08 | #358, #359, #360 filing | `main` | housekeeping | Y | filing-only governance bundle |
| 16 | 2026-05-08 | #359 memory-scrub audit | `main` | housekeeping | Y | doc-scrub audit only |
| 17 | 2026-05-08 | #359 LogiSoluMemory standup | `main` (LSM init) | substantive | Y | new repo init; no precursor issue |
| 18 | 2026-05-09 | #358 LSKB standup | `main` (LSKB init) | substantive | Y | new repo init; no precursor issue |
| 19 | 2026-05-09 | #358 BaRe association | `main` | housekeeping | Y | doc-only sweep across BaRe/LSM/ESACP |
| 20 | 2026-05-09 | #362, #363, LSM#1, #364, #365, #366 | `main` | sidebar | Y | introspection sidebar; carry-forward cleanup + governance fixes |
| 21 | 2026-05-09 | #354 migration | `main` | housekeeping | Y | migration-comment + close |
| 22 | 2026-05-09 | #356 migration | `main` | housekeeping | Y | migration-comment + close |
| 23 | 2026-05-09 | #357 migration | `main` | housekeeping | Y | migration-comment + close |
| 24 | 2026-05-10 | #345 migration + #368 filing | `main` | housekeeping | Y | migration + substrate-fix issue filed |
| 25 | 2026-05-10 | #344 migration | `main` | housekeeping | Y | migration-comment + close |
| 26 | 2026-05-10 | #343 migration | `main` | housekeeping | Y | migration-comment + close |
| 27 | 2026-05-10 | #197, #353 methodology-stays | `main` | housekeeping | Y | documentary commentary on both |
| 28 | 2026-05-10 | LSKB#4–#10 filed + LSKB umbrella standup | `umbrella/erpnext-idiomatic-refactor` (LSKB) | substantive | Y | umbrella + 7-issue filing |
| 29 | 2026-05-10 | #369, #370 (bucket-survey extension) | `main` | substantive | **N** | Substantive code (`bucket_survey.py` 88 lines + `session_start.py` extension) direct-to-main; esacp-qa rejected 1:1:1 violation + 71–100 line band; operator override documented in minutes |
| 30 | 2026-05-10 | #371, #372, #373 (route_planner consolidation) | `feat/371-wip-consolidation-phase-1` (route_planner) | substantive | Y | route_planner side; ESACP issues filed for surprises |
| 31 | 2026-05-11 | #372 investigation | `main` | substantive (investigation) | Y | investigation + memory file; minimal commit |
| 32 | 2026-05-11 | #358 closure (Plan-B Epoch-1) | `internal_docs/358-memory-three-bucket-framing` (LSM) | housekeeping | Y | memory rewrites for #358 closure |
| 33 | 2026-05-11 | LSKB#10 + #378 (BtlMng consolidation) | `feat/378-bucket-survey-btlmng` + `feat/377-wip-consolidation-phase-2` (BtlMng) | substantive | Y | bucket-3 BtlMng work; ESACP fix bundled (#378) |
| 34 | 2026-05-11 | LSKB#2 (ce_sri Phase-1 consolidation), LSKB#11 | `feat/6-wip-consolidation-phase-1` (ce_sri) | substantive | Y | ce_sri side; TRIVIAL_FIXES.md adopted |
| 35 | 2026-05-11 | LSKB#2 close + LSKB#3 (3 DocPerm patches) | `feat/lskb-3-hr-docperm-patches` (ce_sri) | substantive | Y | D1 bundle: 1 substantive PR + 1 close-by-comment; bundling-test |
| 36 | 2026-05-12 | LSKB#4, LSKB#5, LSKB#8 | `feat/lskb-8-es-ec-translation-aliases` (ce_sri) | substantive | Y | D2 bundle: 1 code PR + 2 close-by-comment; operator-approved bundle test |
| 37 | 2026-05-12 | #380 (QA contract v2) | `feat/380-qa-contract-v2` | substantive | Y | qa-contract v2 work; clean 1:1:1 |
| 38 | 2026-05-12 | LSKB#7 close-by-comment | `main` | housekeeping | Y | D3 documentation-class close-by-comment |
| 39 | 2026-05-12 | #382, #373, #383 filed | `chore/s39-housekeeping-sweep` | housekeeping | Y | cross-repo housekeeping sweep |
| 40 | 2026-05-12 | #385, #386, LSKB#6 trim, LSKB#12–16 filed | `housekeeping/s40-phase-4-scope-trim` (LSM) | housekeeping | Y | methodology + tracker grooming |
| 41 | 2026-05-12 | #386 (Phase-4 app placement) | `housekeeping/s41-phase-4-app-placement` (LSM) | housekeeping | Y | decision memo only |
| 42 | 2026-05-12 | LSKB#12, LSKB#17 filed | `main` (LSM direct) | housekeeping | Y | doc-only design freeze |
| 43 | 2026-05-12 | LSKB#17, LSKB#18 (SPC repo standup) | `main` (new `sales_partner_commissions` repo) | substantive | Y | new repo + scaffold; clean |
| 44 | 2026-05-13 | LSKB#19 (design re-open) | `main` (LSM direct) | housekeeping | Y | doc-only memo amendment |
| 45 | 2026-05-13 | LSKB#13 migration patch | `feat/lskb-13-migration-patch` (SPC) | substantive | Y | code PR; clean 1:1:1 |
| 46 | 2026-05-13 | LSKB#14 Server Script rewrite | `feat/lskb-14-server-script-rewrite` (SPC) | substantive | Y | code PR; clean 1:1:1 |
| 47 | 2026-05-13 | LSKB#15, #387, LSKB#20 filed | `main` | substantive (investigation) | Y | substrate-apply paused; pause-comment + new tracker issues |
| 48 | 2026-05-14 | LSKB#20, #388 filed | `main` | substantive (investigation) | Y | pre-flight pause; bucket-1 gap filed |
| 49 | 2026-05-14 | #388 (packer-as-saconsole-dep) | `feat/388-*` (via PR#389) | substantive | Y | ansible-role landed via PR; clean 1:1:1 |
| 50 | 2026-05-14 | LSKB#20, #390 filed | `main` | substantive (investigation) | Y | packer build run; new bucket-1 issue filed |
| 51 | 2026-05-14 | #390 (packer env-vars fix) | `fix-390-packer-env-vars` | substantive | Y | clean 1:1:1; new downstream issue filed |
| 52 | 2026-05-14 | #392 (uv.toml override), #394, #395 filed | `fix/392-*` (via PR#393) | substantive | Y | clean 1:1:1; downstream issues filed |
| 53 | 2026-05-15 | LSKB#20 (Plan-C tag pivot), #396 | `main` | substantive (investigation) | Y | LSKB#20 closed; runs packer build, no ESACP code change |
| 54 | 2026-05-15 | LSKB#15, #397, #398 filed | `main` | substantive (investigation) | Y | substrate-apply paused; pause-comment + new tracker issues |
| 55 | 2026-05-18 | #398 (Path A then Path X), ce_sri#10 filed | `fix/398-*` (via PR#399) | substantive | Y | clean 1:1:1; new bucket-3 issue filed |
| 56 | 2026-05-19 | ce_sri#10 abandoned, #400 filed | `main` | substantive (investigation) | Y | pivot to audit-tracker filing |
| 57 | 2026-05-19 | #401, #402 filed | `main` | sidebar | Y | introspection sidebar; doc artefacts + 2 issues filed |
| 58 | 2026-05-19 | #402 (Pages site) | `umbrella/pages-site-v1` | substantive | Y | 1:1:1 work; `umbrella/*` naming used for a single-session feature branch — naming-policy note in Sub-step 4, not a 1:1:1 violation |
| 59 | 2026-05-19 | #404 (Pages-site follow-up) | `docs/404-pages-site-followup` | substantive | Y | sidebar-flavoured polish but compliant 1:1:1 |
| 60 | 2026-05-19 | #400 Stage 1 (audit Step 1) | `main` | audit-stage | Y | audit-stage execution (docs-only carve-out) |
| 61 | 2026-05-19 | #400 Step 2 (stage list) | `main` | audit-stage | Y | audit-stage execution |
| 62 | 2026-05-20 | #400 Stage 1 execution | `main` | audit-stage | Y | audit-stage execution |
| 63 | 2026-05-20 | #400 Stage 2 execution | `main` | audit-stage | Y | audit-stage execution |
| 64 | 2026-05-20 | #400 Stage 3 execution | `main` | audit-stage | Y | audit-stage execution |
| 65 | 2026-05-20 | #400 Stage 4 execution | `main` | audit-stage | Y | audit-stage execution |

**Compliance count**: 53 Y / 2 N across 55 sessions. **Compliance rate
= 96.4 %.** Non-compliant count (2) is well below the Sub-step 7
partitioning threshold (~10), so Stage 5 fits one session and proceeds
to Sub-steps 3–8 without splitting.

**Session-type distribution** (observation, not policy criterion):

| Type | Count | Sessions |
|---|---:|---|
| substantive (1:1:1) | 26 | 12, 14, 17, 18, 28, 29, 30, 31, 33, 34, 35, 36, 37, 43, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 58, 59 |
| housekeeping bundle | 17 | 15, 16, 19, 21, 22, 23, 24, 25, 26, 27, 32, 38, 39, 40, 41, 42, 44 |
| introspection sidebar | 2 | 20, 57 |
| umbrella-cert | 1 | 11 |
| umbrella-sub | 1 | 13 |
| audit-stage | 6 | 60, 61, 62, 63, 64, 65 |
| (planning-only counted under substantive) | — | 12, 14 |

Total 53 + audit-stage 6 = 59 row-types vs 55 sessions — two sessions
(13, 58) carry mixed-type flavour and are listed in the single most
salient bucket above. Distribution sums to 55 for accounting.

### Sub-step 3 — Housekeeping-bundle abuse list

| Session | What was bundled | Should have been split how |
|---|---|---|

**Empty.** No housekeeping bundle in the 17 housekeeping sessions
mixed in a substantive code change. Bundles either filed/closed
governance issues (S15, S20, S38, S39, S40), groomed methodology memos
(S40–S44), or processed migration close-by-comments (S21–S27).
None touched `tools/pipeline/`, dispatchers, SUT scripts, Ansible plays,
SOPS-backed runtime config, or pipeline tests.

The two non-compliant rows (S11, S29) are **not** mis-classified
housekeeping bundles — they are openly substantive sessions whose
violation mode is different (S11 = umbrella-cert + scope-expand; S29 =
substantive direct-to-main with QA override). Sub-step 3 is empty by
construction.

### Sub-step 4 — Umbrella-policy adoption note

**Premise correction**. The S66 agenda's Sub-step 4 text states
"`feedback_umbrella_branches.md` is new in-window. Most pre-policy
'violations' are exempt." Verified: the policy was adopted **2026-04-22**
(#236), 14 days **before** S11. **No pre-policy exemption applies to any
session in the audit window.** The agenda's "new in-window" framing
appears to refer to umbrella usage growing across the window (from one
live umbrella at S11 to three at S65), not to the policy's adoption
date. Reading-record corrected.

**Live umbrellas at S65** (3):

| Umbrella | Created | Last activity | Pre-/post-policy | Status |
|---|---|---|---|---|
| `umbrella/erpnext-idiomatic-refactor` | pre-S11 (Plan-B substrate) | S28 (LSKB sub-issue filing) + S11 cert | post-policy | Live; partially certified to main S11 |
| `umbrella/ladder-fixture` | pre-#358 | dormant | **pre-#358 carry-forward** | Orphan, ESACP#361 (Stage 1 carry); Sub-step 6 below |
| `umbrella/pages-site-v1` | S58 | S58 (merged to main same session) | post-policy | Naming-policy slip (see below); merged + no longer live as cert target |

**Post-policy umbrella usage findings**:

1. **S11 cert + scope-expansion (Compliance: N).** Per
   `feedback_umbrella_branches.md`: "Certification session: a distinct
   session dedicated to merging umbrella → main … No new sub-branches
   opened here". S11 (a) certified
   `umbrella/erpnext-idiomatic-refactor` (PR#2 → main) AND (b)
   scope-expanded into PR#1 (LSV review) + PR#3 (doc revise) + an
   architectural-discovery pivot in the same session. The cert was not
   a dedicated session. **Drift item DI-1.**

2. **S58 naming slip (Compliance: Y).** `umbrella/pages-site-v1` is
   a single-issue (#402), single-session, four-commit branch with no
   sub-branches under it — i.e., a 1:1:1 feature branch with the
   `umbrella/*` prefix attached. The work itself is compliant (one
   issue, one branch, one session, merged via PR#403 with `fixes
   #402`). The misuse is purely nominal: per the policy's "Use an
   umbrella when any of: >3 sub-branches expected; cross-cutting files
   touched by multiple issues; broad-context acceptance that cannot
   run per-sub-branch; explicit user call at planning time", a Pages
   site v1 build qualifies under none of those triggers. Per-policy
   branch name should have been `feat/402-pages-site-v1` or
   `docs/402-pages-site-v1`. **Drift item DI-2** (naming convention,
   not 1:1:1 process).

3. **S28 umbrella sub-issue filing (Compliance: Y).** Filing seven
   LSKB issues under the umbrella's planning context, not opening
   sub-branches — neutral with respect to the umbrella mechanic, just
   normal Plan-B execution prep.

**No post-policy umbrella sub-branch was merged direct-to-main
bypassing its umbrella.** No sub-branch that should have been
direct-to-main was misrouted through an umbrella.

### Sub-step 5 — Introspection-sidebar audit

**Trigger** (CLAUDE.md "Session Protocol" + the introspection-sidebar
block in `feedback_*` corpus): every 5–7 sessions OR 3+ unresolved
carry-forward operator-reminders, whichever first.

**Expected over a 55-session window** (5–7 cadence, no double-count
of the reminder trigger): floor(55/7) ≤ expected ≤ floor(55/5) = **8
to 11 sidebars**.

**Actual** (explicit "introspection sidebar" framing or unambiguous
sidebar-scope work): **2 sidebars — S20 and S57.**

- **S20** (2026-05-09): introspection sidebar — closed #362, #363,
  LSM#1, #364, #365, #366. Carry-forward cleanup + governance fixes.
  Cadence trigger satisfied (S20 = 9 sessions into the window, within
  the 5–7 range counting from a pre-window prior sidebar).
- **S57** (2026-05-19): introspection sidebar — filed #401, #402.
  Cadence trigger overdue (S57 follows S20 by 37 sessions, far beyond
  5–7).

**Adherence ratio**: 2 / (8–11) = **18 – 25 %**. Substantially below
expected.

**Counter-reading: housekeeping bundles as de-facto sidebars.** 17
housekeeping bundles in the window (S15, S16, S19, S21–S27, S32, S38,
S39, S40–S44) materially overlap with the introspection-sidebar
scope ("documentation scrubs, wording fixes, structural reorganization
of MEMORY.md or other auto-loaded docs, filing tracker issues for
recycled reminders, dropping resolved or terminally-homed items"). If
each housekeeping bundle in fact discharged a sidebar's purpose
without the label, adherence is implicitly satisfied; the labelling
gap is the real finding.

Two readings, both legitimate:

- **Strict reading**: 2 sidebars / 55 sessions → **drift item DI-3**:
  introspection-sidebar cadence is not being honoured.
- **Generous reading**: 19 (sidebars + housekeeping bundles) / 55 →
  trigger is being honoured but the **session-type labels are
  collapsing** sidebars and housekeeping bundles together; the
  distinction in CLAUDE.md is then poorly load-bearing.

**Recommended verdict (operator to confirm at joint review)**:
Generous reading is the better fit for the visible work; the explicit
"introspection sidebar" label is being used sparingly (only for
sessions whose primary purpose is sidebar-shaped, not for sessions
that incidentally include sidebar-class work). Corrective measure
candidates:

- **CM-A**: Tighten the CLAUDE.md distinction so housekeeping bundle
  vs introspection sidebar is mechanically separable (e.g., "any
  session that touches `MEMORY.md` indexing or drops carry-forward
  items is a sidebar even when other housekeeping issues close in
  the same bundle").
- **CM-B**: Loosen the cadence trigger (e.g., "every 5–7 sessions OR
  ≥3 unresolved carry-forward — count housekeeping bundles that
  perform sidebar-class work toward the cadence").
- **CM-C**: Leave the policy as-is; accept that the labelling is
  aspirational and the substantive practice is fine.

### Sub-step 6 — Pre-#358 wip/* + `umbrella/ladder-fixture` carry-overs

Cross-references Stage 1 Sub-step 2 (audit report lines 661–678). Three
pre-#358 `wip/*` branches + one orphan umbrella:

| # | Repo | Branch | Date | Status | Stage-5 verdict |
|---:|---|---|---|---|---|
| 1 | ce_sri | `wip/2026-03-25` | 2026-03-25 | pre-policy carry-forward | exempt (pre-#262/#236 by ~28 days); documented in `project_wip_consolidation_plan.md` |
| 2 | ce_sri_svc | `wip/2026-03-31` | 2026-03-31 | pre-policy carry-forward | exempt; documented |
| 3 | route_planner / BtlMng | `wip/2026-03-31` (+ `phase-1-fixture-equivalent` + `feat/371-wip-consolidation-phase-1`) | 2026-03-31 onward | pre-policy + post-policy consolidation sub-branches | exempt for the `wip/*`; the `feat/371-*` and `phase-1-fixture-equivalent` are post-policy and compliant (sub-branches of the LSKB umbrella) |
| 4 | ESACP | `umbrella/ladder-fixture` | pre-#358 | **local-only orphan, no remote tracking** | exempt as a violation (pre-policy); ESACP#361 is the resolution tracker; standalone session per S66 agenda's "Out of scope" list |

**Visibility**: all four carry-overs are documented in
`project_wip_consolidation_plan.md` and (for #4) ESACP#361. None alter
the Stage 5 compliance rate.

### Stage 5 summary

- **Compliance rate**: **96.4 %** (53 Y / 2 N across 55 sessions).
- **Drift items**:
  - **DI-1** — S11 umbrella certification combined with non-cert work
    (LSV PR#1 + LSV PR#3 + architectural-discovery pivot in same
    session). Policy violated:
    `feedback_umbrella_branches.md` "Certification session: a distinct
    session dedicated to merging umbrella → main".
  - **DI-2** — S58 `umbrella/pages-site-v1` is a nominal-only umbrella
    (single-session, single-issue, no sub-branches). Naming-policy
    slip; the 1:1:1 substance is compliant. Per-policy name would have
    been `feat/402-pages-site-v1`.
  - **DI-3** — S29 substantive code (`bucket_survey.py` + extension)
    merged direct-to-main with esacp-qa reject explicitly overridden
    by operator. Documented in S29 minutes + qa-log; operator
    acknowledged the 1:1:1 violation at the time.
  - **DI-4** — Introspection-sidebar labelling gap: 2 explicit
    sidebars vs 8–11 expected by cadence; the gap is filled in
    practice by housekeeping bundles that perform sidebar-class work
    without the label. Either the policy distinction is not
    mechanically applied or the cadence trigger is loose.

- **Corrective measures**:
  - **CM-1 (DI-1)**: No new code change; institutional memory
    already captures this (S11 minutes are explicit). Optional
    follow-up: cross-reference DI-1 from
    `feedback_umbrella_branches.md` so future cert sessions cite the
    S11 precedent. **Soft** — operator decides at joint review.
  - **CM-2 (DI-2)**: Add a one-line clarification to the umbrella
    section of `feedback_umbrella_branches.md` and CLAUDE.md: "single-
    issue / single-session multi-commit work uses `feat/{issue#}-...`
    even when the work happens to be doc-flavoured. `umbrella/*` is
    reserved for branches that actually have sub-branches or are
    long-lived across sessions." **Soft** — small wording fix; file
    as a tracker if operator accepts.
  - **CM-3 (DI-3)**: No new code change; the override was
    operator-explicit and documented at the time. No corrective
    measure beyond what S29 already captured.
  - **CM-4 (DI-4)**: Operator decision among CM-A / CM-B / CM-C
    above. Default recommendation = **CM-C** (leave policy as-is,
    accept aspirational labelling); the substantive sidebar work is
    happening at the cadence the policy intends.

- **Non-drift findings**:
  - **No housekeeping-bundle abuse** in the window (Sub-step 3 empty).
  - **No post-policy umbrella sub-branch misrouted** (no sub-branch
    that should have been direct-to-main routed through an umbrella;
    no sub-branch that should have been under an umbrella merged
    direct-to-main).
  - **Pre-#358 carry-overs** (Sub-step 6) documented but unchanged —
    resolution remains paced by `project_wip_consolidation_plan.md`
    and ESACP#361.

### Joint-review outcome (S66 operator)

Operator signed off Stage 5 with the following decisions:

- **CM-1** → **Y**. Add a cross-reference from
  `feedback_umbrella_branches.md` to S11 as a precedent for
  "certification session must be dedicated." Folds into the
  consolidation-session housekeeping pass.
- **CM-2** → **Y**. Add a one-line clarification to
  `feedback_umbrella_branches.md` + CLAUDE.md "Session Protocol"
  umbrella block reserving `umbrella/*` for branches that actually
  have sub-branches or multi-session lifespan. Single-issue /
  single-session multi-commit work uses `feat/{issue#}-…` or
  `docs/{issue#}-…` even when the work is doc-flavoured. Folds into
  the consolidation-session housekeeping pass.
- **CM-4** → **A**. Tighten the CLAUDE.md "Session Protocol"
  introspection-sidebar block so housekeeping-bundle vs
  introspection-sidebar is mechanically separable (e.g., "any
  session that touches `MEMORY.md` indexing or drops carry-forward
  items is a sidebar even when other housekeeping issues close in
  the same bundle"). Carries to the consolidation session as a
  policy-redesign item, not a one-line fix.

The premise correction in Sub-step 4 (both policies pre-date S11,
no pre-policy exemption applies in-window) stands without
amendment.

**Carry-forward to Stage 6** (M&V alignment): none. Stage 5 is
mechanistic / process-focused; Stage 6 is mission-focused. Stage 4's
51-close corpus + the substantive-session subset of Sub-step 2's table
(26 substantive sessions) jointly feed Stage 6.

**Carry-forward to consolidation session** (Step 3, S6X) — operator
sign-off recorded above; the consolidation session executes:

- **CM-1** — small memory cross-reference (operator: Y).
- **CM-2** — one-line `feedback_umbrella_branches.md` / CLAUDE.md
  clarification on `umbrella/*` naming reservation (operator: Y).
- **CM-4 = Option A** — policy redesign making housekeeping-vs-sidebar
  mechanically separable in CLAUDE.md (operator: A). Sized as a
  small-but-not-one-line edit to the "Session Protocol" block;
  consolidation session may file a dedicated tracker if scope
  expands beyond a wording pass.

**No Stage 6 execution this session.** Stage 6 (M&V alignment) starts
S67 at the earliest, per the S66 agenda's "Out of scope" list.

---

## Stage 6 — Mission-and-Vision alignment (S67)

**Question**. Does shipped work in the audit window advance the
self-repairing-platform mission stated in
[`mission_vision.md`](../../.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/mission_vision.md),
or has the execution surface drifted away from it?

**Primary inputs**.
- Stage 4 51-close corpus (audit-report lines ~1497–1762) — primary
  categorisation surface.
- Stage 5 substantive-session subset (26 of 55 in-window sessions) —
  cross-reference for "every close-target maps to a substantive
  session or housekeeping bundle."
- S60 observations #3 (M&V mentions concentrated in two clusters)
  and #6 (`mission_vision.md` staleness) — both home in Stage 6 per
  Step 2 mapping table (audit-report lines 504–512).

### Sub-step 1 — Mandatory grep gate

| Grep | Hits | Read |
|---|---:|---|
| `grep -rl mission_vision /home/hasan/.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/` | 8 | `MEMORY.md` (index), `mission_vision.md` (canonical), `feedback_no_manual_v14_cutover.md`, `context_domains.md`, `project_buffer_overflow_audit_plan.md`, `PROTOCOLS.md`, `feedback_consultant_not_peer_engineer.md`, `project_erpnext_idiomatic_refactor.md`. Cross-link fan-out is healthy at the memory level — both Plan-B execution memo and audit-procedure memo cite the canonical M&V doc. |
| `grep -rln 'mission\|vision\|ERPNext MCP\|self-repair' internal_docs/SessionLogs/` (loose, per agenda) | 277 of 384 (72%) | **Loose form is noise-dominated.** `provision` (170 files) and `commission` (81 files) inflate the count by ~250. See word-boundary correction below. |
| `grep -rln -wE 'mission\|vision\|self-repair' internal_docs/SessionLogs/` (word-boundary correction) | 23 of 384 (6%) | True signal corpus — sessions where the mission/vision/self-repair vocabulary appears as a whole word, not as a substring inside `provision`/`commission`/`revision`/`supervisor`. |
| `grep -rln 'ERPNext MCP' internal_docs/SessionLogs/` | 3 of 384 (0.8%) | Three sessions in the entire log history mention "ERPNext MCP" by name: `2026-04-19-1159-session-minutes`, `2026-05-19-1130-next-agenda`, `2026-05-20-1659-next-agenda` (this session's agenda). The mission's core technical artefact is essentially absent from execution-level minutes. |
| `grep -rln 'mission_vision' internal_docs/SessionLogs/` (literal filename) | 14 of 384 (3.6%) | Cluster: S39–S41 (project_pages_site_v1 planning), S58–S59 (Stage-1/Stage-2 audit prep), S60–S67 (this audit). Outside the audit window and the Pages-site planning window, `mission_vision.md` is rarely cited at session level. |
| `grep -rln 'self-repair' internal_docs/SessionLogs/` (literal) | 4 of 384 (1.0%) | Four sessions reference "self-repair" by name: `2026-04-15-2300-session-minutes`, `2026-05-12-0619-next-agenda`, `2026-05-12-0619-session-minutes`, `2026-05-19-2104-session-minutes`. Sparse. |

**Corpus** (Stage 6 working set).
- Memory: `mission_vision.md`, `feedback_mission_priority_check.md`,
  `feedback_not_perfection_project.md`, `project_generic_site_purpose.md`,
  `project_pages_site_v1.md` (per agenda Pre-flight #6); plus the 8
  memory files containing `mission_vision` references for cross-check.
- Minutes: 55 session-minutes files for S11→S65 (same window as
  Stage 4 / Stage 5).
- Issues: Stage 4's 51-close corpus.

**Gate verdict — pass with caveat**.
- **Pass**: M&V canonical document is cross-linked from 7 other memory
  files (8 total grep hits including MEMORY.md), including the
  audit-procedure memo itself and the consultant-mode feedback memo.
  Memory-level cross-reference fan-out is healthy.
- **Caveat (deferred to Sub-step 4 cluster analysis)**: at the
  session-log execution surface, mission vocabulary is sparse (6%
  word-boundary, 1% for `self-repair`, 0.8% for `ERPNext MCP`). The
  agenda-specified loose grep (72%) is misleading — it captures
  `provision`/`commission` as accidental substring matches, not
  genuine mission-vocabulary use. **This sparsity is consistent with
  S60 observation #3** ("M&V mentions concentrated in two clusters;
  sparse at execution level") and feeds the Sub-step 4 cluster
  analysis directly. It is not, on its own, a drift finding — many
  substantive sessions do mission-advancing work without naming the
  mission. The categorisation in Sub-step 3 tests whether the *work*
  (not the vocabulary) advances the mission.

**Grep-noise finding** (methodology-improvement candidate): the
audit-report Stage 6 spec at line 448 specified
`grep -rln 'mission\|vision\|ERPNext MCP\|self-repair'` without
word boundaries. For future Stage-6-class audits, the spec should
use `-wE 'mission|vision|self-repair'` (or equivalent) plus a
separate literal grep for `ERPNext MCP`. Noted here; not raised as a
corrective measure (single-use audit spec; corrective measures track
to executable behaviour changes, not in-document method notes).

### Sub-step 2 — Categorisation methodology

**Mission-property definitions** (operationalised from `mission_vision.md`):

- **ERPNext MCP advance** — directly reduces `in_place_core_edit`, moves
  DB-resident customisations to source-controlled bespoke apps, or
  otherwise makes AI-assisted ERP access more reliable / reachable /
  capable.
- **Self-repair advance** — improves the running system's ability to
  recover itself (backup/restore, observability that triggers action,
  runtime watchdog) or to explain its state to a non-technical operator.
- **Persistent records / tutorial generation** — durable institutional
  knowledge that helps family + staff use the system without a
  developer. Includes customisation inventories, naming conventions,
  Server Script catalogues.
- **Substrate / pipeline / portability** — infrastructure that exists
  so the mission-aligned work is possible: build pipeline, dev fleet,
  CI/CD discipline, QA verdict layer, organisational architecture.
  Allowed but should not dominate.
- **Unrelated** — work that does not advance any mission property and
  is not substrate for one.

**Decision rules used to resolve borderline calls** (transparency for
future re-audits):

- *Development-process discipline ≠ runtime self-repair.* Mechanisms
  that prevent the AI from losing thread between sessions (Discipline
  #2 surveys, three-bucket architecture, LSM memory repo, qa-contract
  amendments) classify as **Substrate** — they enable mission work
  but do not deliver runtime recovery capability.
- *Customisation inventory ≠ MCP advance.* An inventory becomes
  Persistent records; the MCP advance category is reserved for work
  that materially reduces the customisation surface or enables MCP
  reasoning at runtime.
- *Generic-site / Pages-site work* classifies by *driving intent in
  this audit window*. The S58–S59 Pages work was driven by
  `project_pages_site_v1.md` (external outreach), not by
  `project_generic_site_purpose.md` (portability testing). Classified
  **Unrelated** with note that a portability-testing framing would
  have classified them Substrate.
- *Plan-B Phase work* classifies as **ERPNext MCP advance** when the
  shipped artifact reduces `in_place_core_edit` count (catalogues
  count: cataloguing a customisation is the prerequisite to MCP
  reasoning about it). Plan-B substrate-only work (repo standup,
  memo amendments, redis/rq decision, localisation infra) classifies
  as **Substrate**.
- *Backup/restore declaration (BaRe#9)* classifies as **Self-repair
  advance** even though the README is declarative — the close
  formalises BaRe as the canonical institutional self-repair tool,
  which is the substantive change.

**Headline tally** (per Sub-step 3 table below):

| Category | Count | % of 51 |
|---|---:|---:|
| ERPNext MCP advance | 8 | 15.7% |
| Self-repair advance | 1 | 2.0% |
| Persistent records / tutorial | 2 | 3.9% |
| **Mission-advancing subtotal** | **11** | **21.6%** |
| Substrate / pipeline / portability | 38 | 74.5% |
| Unrelated | 2 | 3.9% |

**Sub-step 4 advance flag**: non-mission-advancing (substrate +
unrelated) = 78.4%. Exceeds the 30% threshold from the agenda by
~2.6×; **Sub-step 4 cluster analysis is mandatory**.

### Sub-step 3 — Categorisation table

51 rows, ordered by bucket then by close-class (preserving Stage 4
ordering). Mission-property column uses abbreviations:
**MCP** = ERPNext MCP advance · **SR** = Self-repair advance ·
**PR** = Persistent records / tutorial · **Sub** = Substrate / pipeline
/ portability · **U** = Unrelated.

#### Bucket 1 — ESACP (37 closes)

##### Migration / supersession (13)

| # | Issue | Title (truncated) | Mission | Justification |
|---:|---:|---|:-:|---|
|  1 | #284 | Industry→Company race (Plan-A wizard-replay) | Sub | Plan-A path superseded by Plan-B; close is cleanup of a retired execution surface. |
|  2 | #285 | B06 cold-system regen (Plan-A wizard-replay) | Sub | Same as #284. |
|  3 | #290 | Español/Mexico locale fail (Plan-A wizard-replay) | Sub | Same as #284. |
|  4 | #292 | Playwright en/Canada fixture (Plan-A wizard-replay) | Sub | Same as #284. |
|  5 | #296 | HTTP 499 race (Plan-A wizard-replay) | Sub | Same as #284. |
|  6 | #297 | welcome-modal multi-Next race (Plan-A wizard-replay) | Sub | Same as #284. |
|  7 | #354 | Server Script event-name doc → LSKB#1 | PR | Durable institutional record of Server Script naming convention migrated to a more stable tracker; this is exactly the "persistent records of development process" category. |
|  8 | #356 | Phase 1 fixture_json → LSKB#2 | Sub | Tracker re-homing of a Plan-B execution work-item; the work itself is MCP-advance (counted under LSKB#2) but the close is a migration of bookkeeping. |
|  9 | #357 | Phase 1B Custom DocPerm → LSKB#3 | Sub | Same as #356. |
| 10 | #345 | ce_sri_svc retry-with-backoff exhaustion → ce_sri_svc#3 | Sub | Op-3 tracker migration; ce_sri_svc work is V14-precondition infra. |
| 11 | #344 | ce_sri_svc retry-with-backoff transient → ce_sri_svc | Sub | Same as #345. |
| 12 | #343 | dev01 lab egress ECONNRESET → ce_sri#5 | Sub | Same as #345. |
| 13 | #307 | hrms+payments eval → LSKB#21 | Sub | Tracker re-homing of bucket-2 evaluation work; bucket-2 evaluation itself is substrate-grade for MCP enablement. |

##### Code / infra (11)

| # | Issue | Close | Class | Mission | Justification |
|---:|---:|---|---|:-:|---|
| 14 | #369 | `a85cde0` S29 | feat — bucket surveys | Sub | Discipline #2 mechanism (bucket-explicit session-start surveys). Prevents Session-13 failure mode where AI loses thread between sessions — development-process discipline, not runtime self-repair. |
| 15 | #371 | route_planner PR#1 S30 | track — wip-consolidation pilot | Sub | Pre-#358 wip-branch consolidation; institutional hygiene. |
| 16 | #372 | LSM PR#2 S31 | bug — dev02 deploy-key | Sub | Pipeline plumbing fix on dev fleet substrate. |
| 17 | #373 | LSM `1d3fce8` S39 | chore(memory) — fixes-keyword correction | Sub | Memory-tooling correction; institutional process. |
| 18 | #377 | BtlMng PR#1 S33 | chore — BtlMng wip-consolidation | Sub | Wip-consolidation Phase 2; pre-#358 hygiene. |
| 19 | #378 | `6910f48` S33 | chore(hosts) — BtlMng rename | Sub | Hosts-map cleanup; latent fix during #377 pre-flight. |
| 20 | #388 | `e94e9a5` S49 | infra(saconsole) — packer dep | Sub | Saconsole / fleet-build infrastructure. |
| 21 | #390 | PR#391 S51 | bug(packer) — env-var stripping | Sub | Build-pipeline correctness. |
| 22 | #392 | PR#393 S52 | bug(packer) — uv override for yanked deps | Sub | Build-pipeline correctness. |
| 23 | #398 | PR#399 S55 | bug(substrate) — MariaDB perf-schema | Sub | Substrate runtime fix on the dev DB layer. |
| 24 | #404 | PR#405 S59 | feat(pages) — slideshow nav + QR-code | U | Pages-site outreach surface (per `project_pages_site_v1.md`); non-tech external audience, hidden agenda = invite municipal interest. Not mission-aligned, not substrate for it. |

##### Docs / decision / methodology (13)

| # | Issue | Close | Class | Mission | Justification |
|---:|---:|---|---|:-:|---|
| 25 | #312 | manual S12 | docs — customisation inventory | PR | Customisation inventory landed at LogiSoluValidations + #353; institutional durable record of what makes this ERP non-stock. Persistent record by mission-category definition. |
| 26 | #339 | manual S12 | feat(audit) — language alias map | Sub | Audit tooling, superseded by #353 Phase 6 ownership. |
| 27 | #358 | `b52de7f` S32 | decision — three-bucket architecture | Sub | Organisational architecture preventing Session-13 failure; development-process discipline, not runtime self-repair. |
| 28 | #359 | manual S17 | decision — LogiSoluMemory private repo | Sub | Memory-infrastructure decision; institutional. |
| 29 | #362 | `ed73877` S20 | docs — CLAUDE.md trailer Opus 4.6→4.7 | Sub | Process housekeeping. |
| 30 | #363 | `abcdd02` S20 | docs — introspection-sidebar session-type | Sub | CLAUDE.md policy addition; process meta. |
| 31 | #364 | manual S32 | chore(audit-hook) — pre-close audit-grep timing | Sub | Audit-hook timing meta; process discipline. |
| 32 | #367 | `611c03e` S20 | chore(qa-contract) — §5 malformed-verdict semantics | Sub | QA-contract clarification; process meta. |
| 33 | #380 | PR#381 S37 | chore(qa) — risk-tier triggers | Sub | QA-contract amendment; process meta. |
| 34 | #382 | PR#384 S39 | chore(qa) — §2.1 condition 2 broaden | Sub | QA-contract amendment; process meta. |
| 35 | #385 | manual S40 | docs(chronology) — Phase 4 substrate re-target | Sub | Plan-B chronology amendment; substrate-side bookkeeping. |
| 36 | #386 | manual S41 | arch — Phase 4 bespoke-app placement | Sub | Plan-B architectural decision (`sales_partner_commissions` placement); precursor to MCP-advance LSKB#12/#13/#14 work. |
| 37 | #402 | PR#403 S58 | feat(pages) — Pages site v1 | U | Same as #404: outreach surface for external (non-tech) audience; not substrate for mission. |

#### Bucket 1-associate — BaRe (1 close)

| # | Issue | Close | Class | Mission | Justification |
|---:|---:|---|---|:-:|---|
| 38 | #9 | `8653412` | docs(README) — bucket-1 association | SR | BaRe = backup/restore = canonical institutional self-repair tool. README declaration formalises its mission-role; backup/restore IS direct runtime-recovery capability. |

#### Bucket 2 — LSKB (12 closes)

| # | Issue | Close | Class | Mission | Justification |
|---:|---:|---|---|:-:|---|
| 39 | #2 | manual S35 | Plan-B Phase 1 — 14 fixture_json Custom Fields | MCP | Eliminates 14 in_place_core_edit blockers by routing to source-controlled bespoke apps (11→ce_sri, 2→route_planner, 1 discarded). Direct MCP advance. |
| 40 | #3 | ce_sri PR#8 S35 | Plan-B Phase 1B — 3 Custom DocPerm patches | MCP | Eliminates 3 in_place_core_edit blockers by porting to ce_sri. Direct MCP advance. |
| 41 | #4 | manual S36 | Plan-B Phase 2 — 12 patches (classification-only) | MCP | Catalogues 12 vendored-Frappe patches with per-entry strategy field; cataloguing is the MCP-reasoning prerequisite. Execution deferred to CloudStack Epoch-2 substrate standup (per LSKB#11 continuation). |
| 42 | #5 | manual S36 | Plan-B Phase 3 — redis/rq decision | Sub | Infrastructure decision (match V14 stock 3.5.3/1.8.0); enables V14 cutover but does not directly reduce in_place_core_edit count. |
| 43 | #7 | manual S38 | Plan-B Phase 5 — 22 DB-resident TBDs catalogue | MCP | Catalogues 22 DB-resident TBDs with per-entry disposition keep/move/port/patch/drop. Catalogue is the MCP-reasoning surface. |
| 44 | #8 | ce_sri `924ff2e` S36 | Plan-B Phase 6 — es-EC aliasing | Sub | Localisation infrastructure; precursor for V14 but does not itself reduce in_place_core_edit count. |
| 45 | #12 | manual S42 | Plan-B Phase 4 design | MCP | Sales_partner_commissions bespoke-app placement design; the structural template for moving in_place_core_edit cases to bespoke apps. Direct MCP advance. |
| 46 | #13 | sales_partner_commissions cross-repo S45 | Plan-B Phase 4 migration patch | MCP | Migrates customisations to bespoke app + colocated tests; direct in_place_core_edit reduction. |
| 47 | #14 | sales_partner_commissions cross-repo S46 | Plan-B Phase 4 Server Script rewrites | MCP | Server Script rewrites against master/detail shape land in source-controlled bespoke app; direct MCP advance. |
| 48 | #17 | sales_partner_commissions cross-repo S43 | chore — repo standup | Sub | Empty Frappe app skeleton; precursor substrate to LSKB#12/#13/#14 MCP-advance work. |
| 49 | #19 | LSM `bd31a50` cross-repo S44 | Plan-B Phase 4 currency re-freeze | Sub | Design-memo amendment (Currency fieldtype + Data anomaly handling); substrate-side bookkeeping. |
| 50 | #20 | manual S53 | infra — substrate-readiness | Sub | Pin-discipline chain verified end-to-end; substrate-build discipline. |

#### Bucket 3 — ce_sri (1 close)

| # | Issue | Close | Class | Mission | Justification |
|---:|---:|---|---|:-:|---|
| 51 | #6 | PR#7 `dd7199e` S34 | Plan-B Phase 1 — 11 ce_sri-routed Custom Fields onto main | MCP | Receives 11 of LSKB#2's routed Custom Fields onto ce_sri/main; eliminates 11 in_place_core_edit blockers. Direct MCP advance. |

**Bucket 2 (LogiSoluValidations): 0 closes in window.**
**Bucket 3 (ce_sri_svc): 0 closes in window.**

### Sub-step 4 — Cluster analysis (substrate + unrelated)

**Trigger**. Substrate (74.5%) + Unrelated (3.9%) = 78.4% non-mission-
advancing. Far exceeds the agenda's 30% drift threshold; cluster
analysis is mandatory.

**Test**. Per agenda: sub-cluster the non-mission-advancing items;
identify whether they form a coherent "system maintaining itself"
loop (acceptable) or a "yak-shave" pattern (drift).

**Operational definitions**:
- *System-maintaining-itself loop* — work that is one-time
  (foundational decision, migration, retirement), enables downstream
  mission-aligned work, or is convergent (each instance stabilises a
  recurring class so the class stops recurring).
- *Yak-shave pattern* — work that proliferates without convergence,
  generates more of itself, or is not load-bearing for any
  downstream mission-aligned work.

#### Cluster table (38 substrate items + 2 unrelated)

| Cluster | Items | n | % of 38 sub | Verdict | Reason |
|---|---|---:|---:|---|---|
| A — Plan-A wizard-replay retirement | #284, #285, #290, #292, #296, #297 | 6 | 15.8% | Acceptable | One-time cleanup of retired Plan-A execution surface; all share `reopen anchor #355`. Strategy-pivot hygiene. |
| B — Plan-B execution tracker migration | #356, #357, #307 | 3 | 7.9% | Acceptable | One-time post-#358 re-homing of Plan-B work to LSKB; ESACP-cleanup, not recurring. |
| C — Bucket-3 ce_sri/ce_sri_svc migration | #345, #344, #343 | 3 | 7.9% | Acceptable | One-time post-#358 re-homing of ce_sri/ce_sri_svc bugs to their own trackers. |
| D — Wip-branch consolidation hygiene | #371, #377, #378 | 3 | 7.9% | Acceptable | Pre-#358 wip-branch consolidation (per `project_wip_consolidation_plan.md`); multi-phase but bounded by the plan. |
| E — Pipeline & build infrastructure | #372, #388, #390, #392, #398 | 5 | 13.2% | Acceptable | Substrate that mission-aligned work runs on. Pipeline-fix rate is low (5 across 55 sessions ≈ 0.09/session); not divergent. |
| F — QA/process verdict-layer amendments | #367, #364, #380, #382 | 4 | 10.5% | Acceptable (convergent) | All four amendments land S20→S39. Zero further qa-contract amendments in S40→S65 (26 subsequent sessions). Verdict layer reached stable state mid-window — textbook convergence. |
| G — Memory / discipline tooling | #369, #373, #339 | 3 | 7.9% | Acceptable | Discipline #2 mechanism + memory-tooling fixes + retirement of #353-superseded audit tooling. One-time. |
| H — Institutional architecture | #358, #359, #363 | 3 | 7.9% | Acceptable | Three-bucket architecture + LSM private repo + introspection-sidebar policy. Foundational decisions that prevent Session-13 failure mode; landed early window (S17, S20, S32) with no re-decision in subsequent sessions. |
| I — Plan-B architectural & chronology | #385, #386 | 2 | 5.3% | Acceptable | Plan-B Phase 4 chronology + bespoke-app placement decisions; directly precursor to MCP-advance LSKB#12/#13/#14 work that lands later. |
| J — LSKB substrate | LSKB#5, #8, #17, #19, #20 | 5 | 13.2% | Acceptable | Plan-B Phase 3/6 infra + sales_partner_commissions repo standup + currency re-freeze memo + substrate-readiness Pin discipline. All load-bearing for the 7 LSKB MCP-advance closes. |
| K — Housekeeping micro-fix | #362 | 1 | 2.6% | Acceptable | One-off CLAUDE.md trailer correction; no recurrence in window. |
| **Unrelated — Pages site v1** | #402, #404 | 2 | (4% of 51) | **See below** | Bounded micro-initiative S58–S59 driven by `project_pages_site_v1.md`. |

#### Per-cluster yak-shave test

- **No cluster shows divergence.** No cluster grew session-over-session
  without convergence. Cluster F (QA amendments) is the most-watched
  candidate — it landed 4 amendments S20→S39 but went silent S40→S65.
  Verdict layer stabilised; not a yak-shave.
- **No cluster is load-light** for downstream mission work. Each
  substrate cluster is traceable to mission-aligned dependents:
  Cluster A retires the path that Cluster I + the LSKB Phase-4 trio
  replace; Cluster H establishes the discipline that prevents the
  Session-13 failure that motivated #358; Cluster J's LSKB substrate
  is directly load-bearing for LSKB#12/#13/#14.
- **All substrate clusters are "system maintaining itself" loops**
  under the operational definition.

#### Unrelated cluster — Pages site v1

Two items: #402 (Pages site v1, S58), #404 (slideshow nav + QR, S59).
Coherent micro-initiative driven by `project_pages_site_v1.md`.

**Mission alignment test**:
- The Pages site v1 audience is "non-tech economic-development" per the
  driving memo; hidden agenda = "invite municipal/Chamber interest in
  scaling AI-assisted ERP-maintenance locally."
- `mission_vision.md` (per the canonical statement) describes a
  family-owned business mission: "maintain and enhance their heavily
  customised ERPNext system without depending on any single developer."
- The Pages-site initiative therefore points to a *mission expansion*
  (from single-tenant family-business toolkit → multi-tenant /
  municipal-scale offer) that is not stated in `mission_vision.md`.

**Yak-shave vs. mission-expansion test**:
- The Pages-site work is *bounded* (2 closes, 2 sessions) and
  *coherent* (single driving memo, single deliverable).
- It is not load-bearing for any in-window mission-aligned work.
- But it is also not classically yak-shave (proliferating without
  convergence) — it's a deliberate micro-initiative with stated intent.

**Disposition**: Pages-site work is **mission-adjacent / expansion-
candidate**, not drift. Whether to bring it inside `mission_vision.md`
is a Sub-step 5 question (Observation #6 resolution: R-B candidate).

#### Sub-step 4 overall verdict

**No drift detected** despite 78.4% non-mission-advancing surface.

Three findings carry forward:

1. **Substrate dominance is justified per-cluster but high in aggregate.**
   Every substrate item is load-bearing for downstream mission-aligned
   work; no cluster shows divergence; verdict-layer cluster (Cluster F)
   demonstrably converged mid-window. The 78.4% figure is consistent
   with an audit window dominated by Plan-B-execution substrate work
   that enables (rather than substitutes for) MCP-advance work.

2. **Mission-advance throughput is bounded by Plan-B phase cadence.**
   11 mission-aligned closes (22%) over ~14-day window ≈ 0.78
   mission-advance/day. Phase 4 (LSKB#12/#13/#14) accounted for 3 of
   the 11; Phase 1/1B/2/5 (LSKB#2/#3/#4/#7 + ce_sri#6) for 5 more.
   Throughput is gated by phase definition, not by substrate burden.

3. **Pages-site initiative is mission-adjacent.** Does not register as
   drift. Surfaces a mission-statement question (R-B candidate for
   Sub-step 5).

### Sub-step 5 — S60 Observation #6 resolution

**Observation #6** (from Step 1, audit-report line 511):
`mission_vision.md` 60d old; pre-dates Plan B amendments — staleness
refresh-trigger candidate.

**Test**. Read current `mission_vision.md` against the Plan-B-era
understanding accumulated in the audit window. Does the canonical
mission statement need amendment, or is the execution surface
adequately downstream of the unchanged mission?

**Audit-window content vs. canonical mission**:

| Mission claim | Plan-B-era observation | Consistent? |
|---|---|:-:|
| "Self-repairing modification and maintenance platform" | BaRe institutional declaration (BaRe#9); MariaDB perf-schema substrate (#398); Pin discipline (LSKB#20). All advance the self-repair surface. | ✓ Consistent |
| "Self-explanatory — operable by non-technical family members" | Tutorial/persistent-records work is sparse in window (2/51 = 4%); MCP-advance work (8/51) does not yet surface to a non-tech operator UI. | ⚠ Behind, not contradicted |
| "Backed by persistent records of the development process and MCP connectors" | Three-bucket architecture (#358), LSM private repo (#359), introspection-sidebar policy (#363), QA verdict layer (#367/#380/#382): the persistent-records discipline has *intensified* in window. | ✓ Consistent (over-delivered) |
| "ERPNext MCP is the core of the mission" | 8 MCP-advance closes are all Plan-B Phase work (eliminating in_place_core_edit). MCP work itself (writing the ERPNext MCP server, exercising it through the AI) has not landed in window. | ⚠ Behind, not contradicted |
| "The system is not complete and not intended to be. It grows with the business." | Plan-B is explicitly multi-phase, multi-epoch; LSKB#21 (hrms+payments), Phase 7/8, V13→V14 trial all parked / queued. Growth posture intact. | ✓ Consistent |
| Audience: family-owned manufacturing business | Pages-site v1 (#402, #404) targets non-tech *external* audience (municipal/Chamber), not family/staff. **First in-window instance of work targeting an audience outside the canonical mission.** | ✗ Surfaces audience-scope question |

**Plan-B-era additions absent from canonical text** (candidates for an
amendment block, if R-B chosen):
- DB-resident customisations are acceptable; only `in_place_core_edit`
  blocks V14 (per `feedback_db_resident_customisations_acceptable.md`).
- V14 cutover is the gating event for MCP feasibility (PLan-B's whole
  raison d'être).
- Three-bucket architecture (ESACP-platform / LogiSoluKnowBase /
  LogiSoluMemory) — institutional structure preventing Session-13
  failure mode (#358).
- BaRe institutional self-repair (#9) — backup/restore declared as
  bucket-1 associate.

**Resolution selection**:

**R-A chosen** — Mission is still accurately stated; only the execution
surface needs realignment (no canonical-memo edit required).

Reasoning:
- Sub-step 4 verdict was "no drift detected." The mission is being
  pursued; substrate is load-bearing for downstream mission work.
- Plan-B-era additions are *downstream specifics* of the mission, not
  amendments to it. They live correctly in
  `project_erpnext_idiomatic_refactor.md`, `bucket_definitions.md`,
  `feedback_db_resident_customisations_acceptable.md`,
  `project_bare_bucket_1_association.md`. The mission stays abstract;
  the specifics live in topical memos.
- The "Behind, not contradicted" rows (non-tech UI surface,
  ERPNext-MCP-server execution) are throughput observations, not
  mission-statement defects. Mission still describes the destination;
  execution still tracks toward it.
- The Pages-site audience-scope question is the *one* place the
  mission statement is at risk. **But the work is bounded (2 closes,
  S58–S59) and the in-window verdict is "mission-adjacent, not drift."**
  Single-bounded-instance is below the threshold for amending the
  canonical mission.

**R-B not chosen** — would add Plan-B-era specifics to canonical text;
specifics belong in topical memos. Amending the mission with
phase-specific framing risks coupling the canonical doc to the
current epoch (Plan-B), which is itself a Plan-A successor — the
canonical mission should outlast both.

**R-C not chosen** — ESACP#360 (split mission_vision into LogiSolu-M&V
+ ESACP-M&V) stays parked. The multi-tenant split is premature: the
single Pages-site initiative (2 closes) is the only in-window evidence
of multi-tenant intent; #383 (tablet WG enrollment), Phase 7/8 work,
and any LogiSoluValidations governance maturation precede a clean
split. **Recommendation: revisit R-C when (a) a second-tenant
engagement is concrete, or (b) the Pages-site work expands beyond the
S58–S59 bounded micro-initiative.**

**Observation #6 status**: **RESOLVED — mission is not stale.**
`mission_vision.md` accurately describes the destination; the
execution surface is converging toward it, not drifting away. The
60-day age is not a defect; it reflects the mission's intended
abstraction level.

**Carry-forward to consolidation session**: optional single-line
amendment to `mission_vision.md` adding a cross-link footer
("Current execution surface: see `project_erpnext_idiomatic_refactor.md`
for Plan-B status; see `bucket_definitions.md` for institutional
architecture") — operator-decision at consolidation session. Sized as
a one-line edit, not a rewrite.

### Sub-step 6 — Partitioning safeguard

**Trigger conditions** (per agenda): split Stage 6 if (a)
categorisation surface >~100 items OR (b) "unrelated" cluster requires
drill-in beyond shallow categorisation.

| Condition | Threshold | Actual | Triggered? |
|---|---:|---:|:-:|
| Categorisation surface | >100 | 51 | No |
| Unrelated cluster requires deep drill-in | qualitative | 2 items, single coherent micro-initiative, shallow row sufficed | No |
| Substrate clusters required deep drill-in | qualitative | 11 clusters, single-row verdict each | No |

**Verdict — no split required.** Stage 6 executed in one session as
planned.

### Sub-step 7 — Joint review at session end (S67 operator)

**Sub-step 4 + 5 + 6 verdicts presented; operator sign-off recorded:**

| Decision | Operator call | Notes |
|---|:-:|---|
| Stage 6 verdict: **no drift detected** | Accept | Substrate 75% justified per-cluster; all 11 substrate clusters classified "system-maintaining-itself"; QA-amendments cluster demonstrably converged S20→S39. |
| Observation #6 resolution: **R-A** (mission still accurate; no canonical-memo edit) | Accept | Plan-B-era specifics belong in topical memos, not canonical mission. |
| ESACP#360 split (LogiSolu-M&V + ESACP-M&V): **stays parked** | Accept | Multi-tenant evidence insufficient (single Pages-site initiative, 2 closes). |
| Pages-site framing: **mission-adjacent, no corrective action** | Accept | Bounded micro-initiative; flag for awareness, not drift. |
| Cross-link footer in `mission_vision.md`: originally optional, **promoted to required** for consolidation session | Accept (Y) | Operator surfaced the upcoming `on_boarding` branch use case (S68): a fresh Claude on a Win-11 controller will develop new-user onboarding functionality. That work derives user-facing onboarding from the Claude-internal canonical mission; the footer becomes load-bearing for the deriving party, not just a navigational nicety. |
| New carry-forward: **`mission_vision.md` is memory-resident, not repo-resident** | Add to consolidation backlog | End-users encountering ESACP for the first time never see `mission_vision.md` (it sits in the private memory dir, symlinked from LogiSoluMemory). The on_boarding branch (S68+) will need to author a *repo-resident, tenant-free* user-facing mission/orientation doc derived from the canonical. **Scoping question for on_boarding session, not a Stage 6 corrective measure.** |

### Stage 6 final summary

**Mission-alignment verdict: NO DRIFT.**

- 51-close corpus categorised: 22% directly mission-advancing, 75%
  substrate (all justified), 4% unrelated (bounded Pages-site
  micro-initiative).
- 78.4% non-mission-advancing surface exceeded the 30% drift threshold,
  triggered mandatory cluster analysis (Sub-step 4), which found all
  11 substrate clusters to be "system-maintaining-itself" loops with
  no yak-shave patterns and the most-watched cluster (QA-contract
  amendments) demonstrably convergent.
- Observation #6 (M&V staleness) resolved as R-A: mission is still
  accurately stated; only the navigation surface around it benefits
  from a one-line cross-link footer (consolidation-session work).
- Two soft findings (informational, no immediate action):
  (a) non-tech UI surface and ERPNext-MCP-server execution are *behind*
  mission, not contradicting it;
  (b) Pages-site initiative is mission-adjacent, surfacing an
  audience-scope question that the upcoming `on_boarding` branch will
  address.

**Corrective measures**:

| CM | Sized | Target session |
|---|---|---|
| CM-6-A: add one-line cross-link footer to `mission_vision.md` ("Current execution surface: see `project_erpnext_idiomatic_refactor.md` for Plan-B status; see `bucket_definitions.md` for institutional architecture; see `project_bare_bucket_1_association.md` for self-repair") | Single edit | Consolidation session (S69+, after on_boarding-branch S68) |

**Carry-forward to consolidation session** (joins Stage 5 CM-1/CM-2/CM-4=A):

1. **CM-6-A** (above) — `mission_vision.md` footer.
2. **On_boarding-branch scoping flag** (informational; not a CM
   because the on_boarding branch will own it): the new branch (S68)
   must author a repo-resident, tenant-free user-facing
   mission/orientation doc; consolidation session may want to ratify
   whether the on_boarding branch's user-facing mission doc satisfies
   ESACP#360's split intent (and therefore allows #360 to close
   `not_planned` with pointer to the on_boarding deliverable) or whether
   #360 stays parked as a separate concern.

**Audit closure status**: ESACP#400 remains OPEN through S68 (on_boarding
branch creation, dedicated session) and lands at S69+ consolidation
session, which executes Step 3 with carry-forwards from Stages 4, 5,
and 6.

