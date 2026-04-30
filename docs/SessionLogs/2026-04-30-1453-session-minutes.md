# 2026-04-30 1453 — Session minutes

## Objective

Phase 2 (promotion library) design lock — answer §7 design questions
Q1–Q5, file the Phase 2 issue, capture deferred work. Plan-only session
per `feedback_plan_before_code.md`; no code written.

Operator side-task: file an issue tracking `python3-ruamel.yaml` as an
unsurfaced controller prereq.

## State at session start

- main tip: `806b3da`
- 26 open issues
- Working tree clean
- sync_check 46✅ / 8⚠️ / 2❌ (dev02 shut-off + ping — expected per
  `feedback_one_vm_at_a_time.md`)

## What happened

### 1. Ruamel preflight gap → #326

Confirmed root cause: `tools/customisation_audit/attribution.py:10`
imports `from ruamel.yaml import YAML`, but
`tools/pipeline/stages/preflight/check_tools.py` only validates CLI
binaries via `shutil.which()` — no schema for Python packages. Filed:

- [#326](https://github.com/martinhbramwell/ESACP/issues/326) —
  `chore(preflight): register python3-ruamel.yaml as controller prereq
  in check_tools.py`. Body flags the broader schema-extension question
  (`apt-bin | apt-py | manual` kinds) as a design call for the
  implementation session.

### 2. Phase 2 §7 design lock

Walked operator through the five design questions held over from the
1335 close. Operator confirmed all five recommendations:

| Q | Decision |
|---|---|
| Q1 | **Per-strategy** modules (not per-class) — 4 modules + dispatcher |
| Q2 | Round-trip empty for *promotable* strategies only (`fixture_json`, `fixtures_custom_scripts`, `app_translations_csv`, `v14_patch_script`) |
| Q3 | `custom_docperm` deferred to its own issue (opaque-hash attribution) |
| Q4 | Source-tree mutation gate: refuse-if-dirty, stage+diff+exit, never auto-commit, `--dry-run` flag |
| Q5 | `v14_patch_script` ships fixture-tested only; 3 real-data rows fold into Phase 5 |

Plan file `~/.claude/plans/customisation-discovery-promotion.md` §7
updated to replace the placeholder paragraph with the locked design
(library structure, acceptance criteria, substrate counts).

Filed:

- [#327](https://github.com/martinhbramwell/ESACP/issues/327) —
  `feat(audit): promotion library + correct_bad_customisations.py —
  Phase 2`. Body carries the locked Q1–Q5 design + 8 acceptance
  criteria + branch name `feat/promotion-library-phase-2`.
- [#328](https://github.com/martinhbramwell/ESACP/issues/328) —
  `feat(audit): richer attribution schema for opaque-hash drift classes
  (custom_docperm + future)`. Captures the Q3 carve-out.

Cross-link comments added: #327 ↔ #328.

## Substrate (Phase 1, unchanged from 1335)

- `fixture_json`: 8 rows
- `fixtures_custom_scripts`: 7 rows
- `app_translations_csv`: 10 rows
- `v14_patch_script`: 3 rows (fixture-tested only per Q5)
- `manual` (custom_docperm): 203 rows (deferred per Q3)
- **Phase 2 round-trip target: 25 rows clear → 0**

## Issues touched

| Issue | Action |
|---|---|
| #326 | Filed (ruamel preflight) |
| #327 | Filed (Phase 2 promotion library) |
| #328 | Filed (deferred custom_docperm attribution) |
| #315 | Cross-referenced as Phase 1 predecessor |
| #317 | Cross-referenced as Phase 4 sequencing context |

No PRs opened this session.

## State at session close

- main tip: `806b3da` (unchanged — no commits this session)
- 29 open issues (was 26; +#326, #327, #328)
- Working tree clean
- Plan file `~/.claude/plans/customisation-discovery-promotion.md` §7
  updated (operator-local, not in repo)

## Reminders

- Phase 2 implementation is the next session: cut
  `feat/promotion-library-phase-2` off main, build per locked Q1–Q5.
  Reference: #327 + plan §7.
- #326 first design call: minimal fix vs schema extension. Recorded on
  #326 body.
- sync_check ❌ for dev02 remains expected; #278 (sync_check carve-out
  documentation) is the standing chore.
