# 2026-04-29 0735 — Session minutes

## Objective stated at session start

Phase 1 of the customisation-discovery+promotion plan
(`~/.claude/plans/customisation-discovery-promotion.md` §5) — implement
the discovery library + `./tools/identify_bad_customisations.py`
dispatcher emitting a delta report per plan §6, on branch
`feat/discovery-library-phase-1` off main, per [#315](https://github.com/martinhbramwell/ESACP/issues/315).

## Outcome

PR [#316](https://github.com/martinhbramwell/ESACP/pull/316) merged
(`mergeCommit` `5024ae5`, `mergedAt` 2026-04-29T11:35:28Z); #315 closed.
Phase 1 of 8 complete.

## What happened

### 1. Substrate prep — path (a)

Operator selected path (a) from agenda pre-flight: shut down dev02 (V14),
re-provision dev01 from scratch with real-prod-data backup, develop +
acceptance against dev01.

Sequence executed:

1. `virsh shutdown dev02` — graceful, confirmed `shut off`.
2. `./tools/esacp.py destroy dev01` — full teardown (8 steps, including
   the new known_hosts cleanup primitive from #300/PR #305).
3. `./tools/esacp.py addHost dev01 --wg-ip 10.10.0.16
   --virbr0-ip 192.168.122.26 …` — re-registration with original identity.
4. `./tools/esacp.py provision dev01` — full pipeline (stages 1-9). Stage 3
   rsync'd `~/projects/Logichem/ce_sri/BKP/` (April 19 backup, operator's
   choice over April 4 PRODUCTION_20260404 since it was already
   `BACKUP.txt`-active). Stage 7 `handleRestore.sh` succeeded. Final
   snapshot `ERPNext v13 Restored Baseline` taken.

Acceptance: HTTPS 200 on `https://dev01.iridium.blue`. State commit
`d91b2c4` recorded the dev01 re-registration.

### 2. Library implementation

Built `tools/customisation_audit/` per plan §5.2 — 22 source modules +
18 colocated test files, every file ≤50 lines (the operator-tightened
limit, stricter than CLAUDE.md's ≤80).

Highlights:
- **Foundation**: `drift.py` (`Drift` dataclass + 12-char `stable_id`
  sha256), `verdict.py` (Verdict + PromotionStrategy enums per plan §6),
  `delta_report.py` (`emit` + `to_json` with `sort_keys=True` for
  byte-identical round-trip), `audit_config.py` (per-run config).
- **DB transport**: `_remote_query.py` (SCP'd onto substrate; reads
  site_config.json, runs mysql, emits JSON) + `db_query.py`
  (controller-side wrapper using `shlex.quote`d SQL — required after
  early acceptance attempts revealed SSH's argv-rejoining loses the
  backtick quoting otherwise). The deploy + run pattern satisfies
  CLAUDE.md's ban on heredocs-feeding-code.
- **Per-class detection**: 11 `discover_*.py` modules covering all
  audited classes plus a `discover_unknown.py` stub.
- **Testing**: project's no-pytest standalone-script convention
  (`./test_X.py` exits 0/1). Used contextlib-based `patched()` helper
  for monkey-patch ergonomics.

Dispatcher `tools/identify_bad_customisations.py` is 49 lines; calls one
library entry point (`runner.run_audit`) per CLAUDE.md anti-spiral rules.

### 3. Schema reality check — v13 lacks `module`

First acceptance run failed:
`ERROR 1054 (42S22): Unknown column 'module' in 'SELECT'` against
`tabCustom Field`. Investigation showed only `tabPrint Format` carries
a `module` column on this v13 substrate; the other six customisation
tables don't. Frappe added `module` to those tables as part of the v14
schema modernisation.

Fixed all six SQL queries at once (root cause over symptoms), with inline
notes pointing future readers at the v14 reintroduction. Owning-app
attribution for db_only entries on those classes falls back to `""` /
`manual` strategy when neither module-based nor fixture-membership
heuristics fire.

### 4. Attribution layer — operator-requested mid-session

After the first acceptance run came back showing 360 drifts (most with
`owning_app=""` due to the missing-`module` problem), operator requested
a persistent operator-curated mapping file so they're queried only once
per newly-discovered unmapped row.

Built `tools/customisation_audit/attribution.py` (50 lines):
- `load(path) -> dict`
- `lookup(amap, drift_class, name) -> Optional[dict]` — TODO entries
  treated as unresolved.
- `append_stubs(path, class, names) -> int` — idempotent.
- `stub_unmapped_from_report(path, report) -> dict[str, int]` — walks the
  delta report and stubs every (class, name) flagged unmapped.

Added `config/customisation_attribution.yml` with per-class buckets and
schema docs.
Added `--write-stubs` flag to the dispatcher: default off (read-only);
when set, appends TODO placeholders for unmapped names.
Wired attribution into all six v13-affected discover modules + translation.
Verified end-to-end against dev01: appended 231 stubs across 6 classes;
restored the YAML to empty defaults pre-commit.

### 5. Acceptance — all §5.4 criteria green

Against dev01 real-prod-data substrate:

```
total_drifts: 360
by_class:    custom_field=8 client_script=7 print_format=4 workflow=0
             custom_docperm=203 translation=10 server_script=5
             custom_doctype=4 naming_series=119 property_setter=0
by_verdict:  db_only=232 enumerate_only=9 informational=119
```

- ✅ Runs without error
- ✅ Emits `delta_report.json` matching plan §6 schema
- ✅ Per-class counts on stdout
- ✅ Round-trip byte-identical (`to_json(json.loads(to_json(report)))`)
- ✅ IDs identical across two consecutive runs (proves stable hashing)
- ✅ Every module ≤50 lines (mechanical check)
- ✅ Each per-class module has a colocated test (18 test files; all pass)
- ✅ No source-tree mutation; no production interaction

## Artefacts

| Artefact | Path |
|---|---|
| State commit (main) | `d91b2c4` chore(state): record dev01 re-registration |
| Library commit | `b75982b` feat(audit): discovery library + dispatcher (#315) |
| Attribution commit | `91d6e5e` feat(audit): operator-curated attribution map + --write-stubs |
| PR | [#316](https://github.com/martinhbramwell/ESACP/pull/316) — merged |
| Issue | [#315](https://github.com/martinhbramwell/ESACP/issues/315) — closed |
| Plan file | `~/.claude/plans/customisation-discovery-promotion.md` (§5 done; Phase 2 still placeholder per design) |

## Issues state

- Open: 25 (#315 closed; no new issues filed).
- Closed: 1 (#315).

## sync_check

46 ✅ / 8 ⚠ / 2 ❌ at session end. The 2 ❌ are dev02 shut off (expected
per `feedback_one_vm_at_a_time.md` — dev01 currently active with prod
data; dev02 V14-baseline parked). No real failures.

## Key facts established this session

- **v13 schema lacks `module` on 6 of 7 customisation tables.** Frappe
  added these in v14. Audit handles via fixture-membership + the new
  attribution map; v14 substrates won't need the attribution fallback.
- **Custom DocPerm hash-keyed names** make file-based attribution
  unfriendly; flagged as a Phase 2 concern (richer parent+role+permlevel
  schema).
- **231 unmapped stubs** is the current operator backlog if `--write-stubs`
  is run against dev01. Mostly Custom DocPerm (203) — the per-class table
  above shows the breakdown. Attribution work is queueable but not
  blocking for Phase 2 design.
- **Round-trip stability is real** — sort_keys + sorted-by-id gives
  byte-identical re-emit, IDs deterministic across runs. Phase 2 + 4 can
  rely on the stable ID as a row identifier across consecutive audit runs.

## Memory rules applied / reinforced

- `feedback_check_tool_actual_cli_before_following_agenda.md` — verified
  destroy/addHost/provision CLI signatures via Read before composing the
  substrate-prep sequence.
- `feedback_plan_before_code.md` — read plan §5 + §6 in full before
  cutting branch; design questions answered before any module written.
- `feedback_remote_script_pattern.md` + CLAUDE.md ban on heredocs —
  remote runner is a real file SCP'd to substrate, not an inline
  python3 -c.
- `feedback_no_monolith_patching.md` — when v13 schema reality forced
  SQL changes across 6 modules, fixed all 6 in one pass not reactively.
- `feedback_pr_merge_before_session_close.md` — held the session open
  until PR #316 merged and #315 auto-closed.

## Cross-references

- Plan: `~/.claude/plans/customisation-discovery-promotion.md` §5 (done)
- Umbrella plan: `~/.claude/plans/production-v14-migration-prep.md`
- Mission: `memory/mission_vision.md`
- Audit (Phase 4 input): `docs/upgrade/DMCustomisationCapabilityAudit.md`

## SCC handoff

Repo clean. main at `5024ae5`. Phase 1 complete. Next agenda separate file.
