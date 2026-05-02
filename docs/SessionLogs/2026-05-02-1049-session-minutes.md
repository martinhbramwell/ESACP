# 2026-05-02 1049 — Session minutes

**Branch:** none (planning session — no controller code touched).
**Objective:** Session 1 of 4 — produce consultant-mode design plan for Phase 5
(`upgrade_to_v14.py` + V14 patch generator) per `~/.claude/plans/phase-5-v14-patch-generator.md`. Design only; no implementation.

## Pre-flight

- `bash platforms/kvm/sync_check.sh` → 46 ✅ / 8 ⚠️ / 2 ❌ (dev02 shut off, expected per `feedback_one_vm_at_a_time.md`).
- main at `9318b11`. Working tree clean.
- Latest agenda: `2026-04-30-1641-next-agenda.md` followed by `2026-05-01-1510-next-agenda.md` — operator picked Option A path (Phase 5 V14 critical path) and chose four-session sequencing: Session 1 = A-design (today); Session 2 = #326 ruamel chore; Session 3 = A-impl; Session 4 = Phase 3 generalised G2.
- 30 open issues at session start.

## What ran

### Phase 5 plan drafted

`~/.claude/plans/phase-5-v14-patch-generator.md` produced. Initial draft ~340 lines, covering: mission frame, success contract, 22 v14_patch_script shape inventory, 3 human_review_core_edit automation routes, `upgrade_to_v14.py` 9-stage orchestrator, module breakdown (~43 files), 6 open questions, Session 3 decomposition.

### Mid-session scope corrections (3 substantive narrowings)

**1. Q-A correction — `in_core` routing.** First-draft Q-A proposed an `in_core_host: ce_sri` defaulting scheme. Operator pushed back: this question was already answered in the prior session (per `customisation_attribution.yml` header docs and operator's earlier explanation). The answer: `in_core` is a routing decision; patches go to a project-level directory **or** a synthetic Frappe app. Locked: synthetic Frappe app **`legacy_error_fixes`** (lowercase, version-agnostic, parallels other bespoke-app naming).

**2. Audit over-eagerness for db-resident classes — deferred.** Operator surfaced a foundational concern: the audit's `discover_translation` (and likely other discoverers) flag every db_only row as a drift needing externalisation, but per `feedback_db_resident_customisations_acceptable.md` (added 2026-05-01) those rows ride through migrate intact. The 3 in_core translations + ~3 print_formats marked `v14_patch_script` are conceptually spurious (their patches would be no-ops via `frappe.db.exists` guards). Filing a GH issue for the audit-design fix was offered; operator declined explicitly: *"does this not drive us deeper into the quagmire of patches-on-patches and fixes-on-fixes? Solid ground is a valid V14 ERPNext from the production backup."* Deferred — see U4 below.

**3. Scope narrowing via "True/False" question.** Operator framed the synthetic app's purpose precisely: *"changes made in Frappe development mode that should have been made in production mode."* True for 15 of 16 in_place_core_edit drifts marked v14_patch_script (12 Custom Field equivalents + 3 Custom DocPerm equivalents). False for 1 outlier (es.csv translation pair) and the 3 human_review files.

### Diff-evidence read for #332 — verdict: debug residue, not customisations

| File | Diff content |
|---|---|
| `frappe/model/delete_doc.py` | One line: bare `print(df)` debug statement |
| `frappe/model/document.py` | Three lines: all commented-out `# print(...)` debug statements (do nothing) |
| `frappe/requirements.txt` | Two version pins (`redis 3.5.3→4.3.0`, `rq 1.8.0→1.10.1`); no new deps |

Verdict: V14 `git checkout -f` discards harmlessly. **No automation needed.** Posted as `gh issue comment 332` → comment `4364062700`. #332 ready for operator-driven close as wontfix-with-rationale.

### Production-side resolution of es.csv outlier

Two HR-related Spanish translations live in `tabTranslation`:
| Source | Target | Salary Slip field |
|---|---|---|
| Gross Year To Date | Año Bruto Hasta La Fecha | `gross_year_to_date` |
| Hour Rate (Company Currency) | Tarifa por Hora (Divisa por defecto) | `base_hour_rate` |

Operator anchored both as `tabTranslation` rows via production UI (Setup → Translation), `language: es` (not `es-EC` — V13 country-level translations don't resolve well per operator empirical knowledge). Captured in production backup `20260502_091736` at `~/projects/Logichem/PRODUCTION_20260404/`. Will ride through V14 as DB rows. **No Phase 5 automation needed.**

This action is a worked example of a broader pattern (P2 in Q-G below) that may extend to the 15 dev-mode-leakage drifts.

### New strategic question Q-G surfaced (must be decided before Session 3)

How do the 15 dev-mode-leakage drifts get resolved?

| Option | Mechanism | Burden | Code |
|---|---|---|---|
| **P1** | Synthetic app `legacy_error_fixes` + 15 generated patches | Zero clicks | ~30 new files |
| **P2** | Operator pre-creates Custom Field/DocPerm rows in production V13 via UI; rides through V14; mirrors today's es.csv resolution | ~30 min UI work | ~11 files (orchestrator + runbook only) |
| **P3** | Hybrid: P2 for 12 Custom Fields, P1 for 3 Custom DocPerm | ~15 min UI work | ~12 files |

**Status: OPEN.** Operator paused decision at session-end; will pick before Session 3 begins.

## Plan changes baked into `~/.claude/plans/phase-5-v14-patch-generator.md`

- Q-A locked: A2 + name `legacy_error_fixes`
- Q-B obviated: 3 human_review files are debug residue (not customisations needing host)
- Scope reduced from "22 v14_patch_script + 3 human_review" to "15 dev-mode-leakage" (the rest resolved via DB-resident strategy or natural V14 wipe)
- Module breakdown rewritten to reflect three implementation modes (P1 / P2 / P3) under Q-G
- New §3 Q-G strategic decision; promoted to gating-question status for Session 3
- §10 cross-references updated to point at #332 comment 4364062700, the production substrate `20260502_091736`, and these minutes

## Issues touched

| # | Action | State |
|---|---|---|
| #332 | Comment posted (4364062700) with diff evidence; verdict: debug residue, no automation; recommended operator-driven close | Open (operator decides close) |
| #331 | No comment; folded into Phase 5 Stage 4 per operator's prior Option A on the issue (will close when Phase 5 ships) | Open (carried forward) |
| #326 | Untouched — Session 2 scope | Open |
| #328 | Untouched — kept out of Phase 5 per Q-D | Open |

## PRs opened

**None.** Output is plan file only — operator-local, not in repo.

## State at session close

- `main`: `9318b11` (unchanged from session start). ESACP working tree clean.
- `~/.claude/plans/phase-5-v14-patch-generator.md`: locked-with-Q-G-open. ~430 lines after rewrite.
- `~/projects/Logichem/PRODUCTION_20260404/`: now contains both April backup and new May backup `20260502_091736-*` (post-translation-insertion).
- Bespoke-app worktrees (ce_sri/returnable/route_planner): **24 staged Phase 2 promotion writes still uncommitted** (carried from prior session, unchanged). See U2.
- Tasks: 7 of 7 completed (TaskList).

## Memory updates

None this session. Load-bearing knowledge captured durably in:
- The plan file (`~/.claude/plans/phase-5-v14-patch-generator.md`)
- `#332` comment 4364062700 (diff evidence)
- These minutes (mid-session corrections + Q-G open question)
- Production backup `20260502_091736` (es.csv resolution)

The `language: es` vs `es-EC` finding (operator empirical knowledge) is captured here in §"Production-side resolution of es.csv outlier" and as U3 below.

## Forward-tense audit (session-close)

Every "I'll X" / "I will X" / "should X" promised in this session resolved as either (a) executed tool call, (b) durable home (plan file, GH comment, minutes), or (c) flagged unresolved below. None deferred to "noted for next session."

## Unresolved at close (operator hand)

1. **U1 — Q-G strategic decision (P1 / P2 / P3)** for the 15 dev-mode-leakage drifts. Gates Session 3 (Phase 5 implementation). Operator picks before Session 3 starts.

2. **U2 — 24 staged Phase 2 promotion writes** still sitting in `ce_sri`/`returnable`/`route_planner` worktrees from session 2026-05-01 1510. Operator decision per Q4 design (commit each independently, restore, or acknowledge deferred). Unchanged from prior session; flagged again because U3 below may invalidate some.

3. **U3 — `es-EC` retroactive question.** Phase 2 promoted 7 translations to bespoke-app `<lang>.csv` files using language code `es-EC`. Operator empirical knowledge surfaced today: V13 country-level translations don't resolve well; family-level `es` is correct. **Are those 7 promotions correct as-is, or do they need re-routing to `es`?** Decision pending; affects U2 (whether to commit, amend, or restore those writes).

4. **U4 — Audit over-eagerness for db-resident classes.** `discover_translation` and likely other discoverers surface db_only rows as drifts needing externalisation, but per `feedback_db_resident_customisations_acceptable.md` they ride through migrate intact. Operator deferred GH-issue filing as quagmire-avoidance. **Will resurface every time `identify_bad_customisations.py` runs.** Carried as known-and-deferred backlog.

5. **U5 — db-resident "noise" in v14_patch_script bucket.** 3 in_core translations + ~3 print_formats are conceptually spurious (idempotent guards make any generated patches no-ops). Resolves naturally with Q-G choice: P1 emits harmless patches; P2 ignores them entirely.

6. **U6 — Smoke-test prerequisite for P2/P3** (if either chosen): on dev01 substrate, confirm Frappe deduplicates `(dt, fieldname)` at form-render time when both source-tree definition AND `tabCustom Field` row exist for the same field. If duplicate rendering occurs → P2 unsafe; P3 must address or fall back to P1.

## Reads for next session

- These minutes (U1–U6 list).
- Updated plan: `~/.claude/plans/phase-5-v14-patch-generator.md` (Q-G is the gate).
- #332 comment `4364062700` (debug-residue verdict).
- Last session minutes (`2026-05-01-1510-session-minutes.md`) for Phase 2 staged-write context.

## Standing reminders

- **PR merged before session closes** — applies to Sessions 2/3/4 (this Session 1 had no PR).
- **`fixes #A, fixes #B`** comma syntax for any multi-issue PR.
- **One-VM rule**: dev02 shut off whenever dev01 is up; only one dev VM at a time on toshy's 16 GiB.
- **"NOTHING by hand at cutover"** still holds — but DB-resident artifacts created via UI BEFORE cutover are not "by hand at cutover," they're operator-curated production state that rides through. Distinction confirmed by today's es.csv work.
