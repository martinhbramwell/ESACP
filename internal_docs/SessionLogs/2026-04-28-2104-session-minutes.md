# 2026-04-28 2104 — Session minutes

## Objective stated at session start

Confirm whether the platform has the capability to: (1) receive a production DB backup, (2) identify all incorrectly registered customisations, (3) reconfigure them upgrade-safely, (4) build a V13 dev VM with the reconfigured backup, (5) upgrade V13→V14. If not, plan the work to acquire it.

## Actual objective delivered

A multi-session plan for filling the capability gaps (1)–(5) was designed, reviewed, re-scoped, and committed. Phase 1 of 8 was approved and filed as an issue. **No code was written this session.** This was a planning + alignment session.

## What happened

### 1. Capability assessment

- Read the just-merged audit (`internal_docs/upgrade/DMCustomisationCapabilityAudit.md`, PR #314).
- Reported per-step capability against operator's 5-step goal:
  - Step 1 (receive backup) ✅ existing pipeline.
  - Step 2 (identify) ❌ 0 of 11 classes have Discover coverage.
  - Step 3 (reconfigure) ❌ 0 of 11 classes have Promote coverage.
  - Step 4 (build V13 VM) ⚠ pipeline supports it but "reconfigured" gates on Step 3.
  - Step 5 (upgrade V13→V14) ⚠ proven on clean substrate (dev02, 2026-04-27); not exercised against real production customisations.

### 2. Initial plan — operator rejected the framing

Drafted a 52-session plan (10 discovery sessions + 7 promotion sessions + 25 in-place-core-edit reconciliation sessions + 6 V14 sessions). Operator pushed back on three grounds:
- **Mission inversion**: 52 sessions of human-driven work contradicts the mission of AI-assisted automation.
- **Architecture confusion**: conflated "atomic operation" with "session". 1:1:1 means 1 issue/branch/session per cohesive deliverable, not per atomic library function.
- **Steady-state cost extrapolation**: per-backup-refresh cost projected at 0–5 sessions implied that 30 daily backups would cost ~600 sessions. Mathematically ridiculous and confirms the framing was wrong.

### 3. Fact-check that surfaced a real audit error

Operator challenged the "1126-line rewrite of `sales_partner.json`" claim cited from the audit. Verification:
- File on disk: 238 lines.
- Upstream `version-13` baseline: 921 lines.
- `git diff version-13` output: 1126 lines, mostly deletions.

**Reality**: production has *stripped* ~682 lines from upstream, not added a 1126-line redesign. The audit's framing of this as "the single biggest unknown" was wrong. V14 risk profile inverts: `git checkout version-14` restores the deleted upstream content; `bench migrate` adds any missing `tabSalesPartner` columns forward-only; likely **low V14 risk**, not high.

This finding posted as comment on #313: https://github.com/martinhbramwell/ESACP/issues/313#issuecomment-4340168933

The other 17 erpnext + 5 frappe file claims in audit §8 are similarly unverified narrative. The new plan handles this by verifying every diff at runtime in Phase 4's classifier, not by re-running a manual audit session.

### 4. Reassessed plan

Per operator framing: **8 phases = 8 issues = 8 branches = 8 sessions**, each delivering one cohesive automation capability. End product:

| # | Deliverable |
|---|---|
| 1 | `./tools/identify_bad_customisations.py` + library — read-only delta report (next session) |
| 2 | `./tools/correct_bad_customisations.py` + library — promotion executor |
| 3 | `g2_clear_all_fixture_records.py` — generalised pre-restore deletion |
| 4 | In-place core-tree edits classifier |
| 5 | `./tools/upgrade_to_v14.py` |
| 6 | `./tools/migrate_production_to_v14.py` end-to-end orchestrator |
| 7 | Real-prod-data V14 dry-run acceptance |
| 8 | Production V14 cutover (operator-driven) |

Standards: ≤50 lines per file (operator-tightened from CLAUDE.md's ≤80), shebanged + chmod +x, dispatchers thin, library at `tools/customisation_audit/`, tests colocated.

Phase 1 approved exclusively for the next session. Phases 2–8 carried as placeholders, designed when each becomes the active phase, informed by Phase 1's actual output.

### 5. Pre-planned interface for Phase 1 → Phase 2 + Phase 4

Operator approved pre-designing the delta report schema even though only Phase 1 ships next session, since Phase 2 (promotion) and Phase 4 (classifier) consume it. Schema captured in plan §6 with `schema_version: "1"`, stable IDs, verdict enum, promotion-strategy enum, and the contract that Phase 4 writes `class: in_place_core_edit` entries into the same report.

## Artefacts produced

| Artefact | Path | Status |
|---|---|---|
| New plan file | `~/.claude/plans/customisation-discovery-promotion.md` | Written |
| Umbrella plan updated | `~/.claude/plans/production-v14-migration-prep.md` | Steps 2–6 re-scoped + status table updated |
| GitHub issue | [#315](https://github.com/martinhbramwell/ESACP/issues/315) — `feat(audit): discovery library + identify_bad_customisations.py` | Filed |
| Audit-correctness comment | [#313 comment 4340168933](https://github.com/martinhbramwell/ESACP/issues/313#issuecomment-4340168933) | Posted |

## Commits + branches

**None.** All artefacts live under `~/.claude/plans/` (user-private) or as GitHub artefacts. No project-repo commits, no branches cut, no PRs opened. `git status` clean throughout.

## Issues state

- Open: 26 (was 25; #315 added).
- Closed: 0 this session.
- New comments: 1 (on #313).

## sync_check

45 ✅ / 9 ⚠ / 2 ❌ at session start. The 2 ❌ are dev01 unreachable per #278 carve-out (expected). No new failures.

## Key facts established this session

- The audit (PR #314, merged earlier 2026-04-28) contains at least one factual error in its §8 narrative; resolution is to verify diff content at runtime in Phase 4, not to re-audit.
- The mission demands automation; multi-session plans that scale linearly with future-backup count violate the mission frame.
- 1:1:1 discipline operates at the **issue/cohesive-deliverable level**, not the atomic-function level.
- The delta report schema is the durable interface contract between Phase 1 (writer) and Phases 2 + 4 (consumers).

## Memory rules applied / reinforced

- `feedback_tactical_vs_consultant_mode.md` — caught my own propagation of the audit's unverified "1126-line rewrite" claim only after operator challenge; should have verified before repeating.
- `feedback_plan_before_code.md` — plan written and approved before any code commitment; correct ordering.
- `feedback_mission_priority_check.md` — operator forced re-alignment when initial plan drifted from mission framing.
- `feedback_domain_research_first_for_cross_major.md` — research belongs upfront, not after deviation; would have caught the audit's narrative weakness earlier.

## Cross-references

- Plan: `~/.claude/plans/customisation-discovery-promotion.md`
- Umbrella plan: `~/.claude/plans/production-v14-migration-prep.md`
- Audit: `internal_docs/upgrade/DMCustomisationCapabilityAudit.md`
- Inventory (Pass A, held branch): `internal_docs/upgrade/CustomisationInventory_v13.md` @ `c6f7f79`
- Mission: `memory/mission_vision.md`

## SCC handoff

Audit clean, no commits to make. Next agenda separate file.
