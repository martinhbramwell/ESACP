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
