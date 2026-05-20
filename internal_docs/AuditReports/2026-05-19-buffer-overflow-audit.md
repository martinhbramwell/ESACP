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
