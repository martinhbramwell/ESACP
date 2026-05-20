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

## Step 2 — Stage list proposal (S61 — pending)

To be drafted in S61 against the initial stage list in
`project_buffer_overflow_audit_plan.md` (Stages 1–6). Each stage will
be sized to fit one stage-iteration without buffer overflow.
