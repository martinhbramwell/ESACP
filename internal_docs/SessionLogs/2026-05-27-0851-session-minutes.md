# 2026-05-27 0851 — Session 83 minutes

## Stated objective (chosen at session start)

Candidate **A** from the S83 next-agenda: **R1 pipeline integration**
— `Web Page route='home'` salvage from `tabSingles` Homepage singleton
after V13→V16 migrate. Strict 1:1:1 substantive session, child of
#480 V13→V16 re-migration umbrella.

## Class

**1:1:1 substantive code session.** New branch (`feat/486-r1-pipeline-integration`),
new commit (`857ac80`), PR (#502), merge (`9873c79` mergedAt
`2026-05-27T12:50:02Z`), issue #486 auto-close via `fixes #486`.
No memory edits; no carry-forward attrition; not a sidebar.

## What happened — substantive sequence

### Pre-flight

- sync_check: 49 pass / 8 warn / 0 fail (long-standing WG hub peer
  drift + dormant-VM warnings; WG functional from controller).
- Open ESACP issues: **72** (agenda expected 70; +2 drift unaudited at
  start, no impact on R1 scope).
- LSKB issues: 12 (matches agenda).
- Branch state: `main`, clean tip = `e3c4c0e` (S82 post-close
  encounter-count audit-fix).
- TRIVIAL_FIXES.md: 3 open items unchanged.
- Memory PROTOCOLS.md + MEMORY.md auto-load: clean.

### Alignment with operator

Operator stated the umbrella framing explicitly:

> Goal: code for a fully automated and easily repeatable V13→V16
> migration with all known defects corrected — migration artifacts,
> bad customizations, bad config, bad implementations in V13
> production. This session is to create code for properly
> implementing the home page.

Restated and confirmed: R1 belongs to the *migration-artifact* class
(Homepage DocType upstream-deleted in V14+; singleton row survives;
no V16 render target). Tenant-content concern flagged at planning:
salvaged values (`company`, `tag_line`, `description`) must be read
runtime from `tabSingles`, never hardcoded — protects against
`feedback_no_hardcoded_params.md` + `feedback_no_real_client_names.md`.

Operator chose **option (a)** for acceptance: exercise the from-absent
INSERT path on dev02 this session, since that is the load-bearing code
path for cutover (idempotent-skip is just a doesn't-break-on-re-runs
property). Lab is disposable; pre-snapshot taken for revert safety.

### Pre-snapshot

Snapshot **`pre-S83-r1-acceptance`** taken on dev02 via
`tools/pipeline/orchestration/snapshot_ops.create_snapshot()` with
`hypervisor='toshy'` — NOT the bugged `snapShotVM` CLI (#440, 4th
encounter unchanged).

### Implementation

- **Branch** `feat/486-r1-pipeline-integration` cut off `main` tip.
- **VM-side script** `tools/vm_scripts/r1_recreate_web_page_home.py`
  (80 lines, +x): runs as `erpadm` under bench venv python with cwd
  at `bench_dir/sites/`. Reads salvaged company/tag_line/description
  from `tabSingles WHERE doctype='Homepage'` at runtime, escapes via
  `html.escape`, INSERTs via `frappe.get_doc(...).insert()`, calls
  `frappe.clear_cache()` for route-cache invalidation. Three [PROBE]
  outcomes: `home=present` (idempotent skip), `home=created`
  (from-absent INSERT), `homepage=absent` (no singleton).
- **Extracted helper** `tools/pipeline/orchestration/fix_script_runner.py`
  (34 lines): `run_fix_script(config, emit, label, cmd, expected,
  changed_marker) -> TaskResult`. Reusable for R6e.2 (#496) and
  future #480 children. Parses `  [PROBE] <key>=<value>` lines +
  detects `(was X, now Y)` markers.
- **Primitive update** `tools/pipeline/orchestration/v16_post_migrate_fixups.py`
  (62 lines, was 69): added `_run_r1` paralleling `_run_r3`;
  refactored both to use the new helper; aggregator runs R1 then R3
  sequentially, aggregates `changed`.
- **Helper test** `test_fix_script_runner.py` (63 lines, new): 5
  cases (changed-marker detected, no-change marker false, absent
  probe, unexpected probe, ssh failure emits tails).
- **Primitive test** `test_v16_post_migrate_fixups.py` (70 lines, was
  76): rewrote mocks to use `side_effect=[r1, r3]` for the two
  sequential ssh calls; 5 cases (both-fresh, both-idempotent, R1
  singleton-absent, rsync failure, R1 ssh failure short-circuits R3).
- **CLI dispatcher** `tools/cli/apply_v16_post_migrate_fixups.py`:
  docstring + help updates only; line count unchanged at 44.
- **Docs**: `tools/CLAUDE.md` `applyV16PostMigrateFixups` catalog
  entry updated; `tools/vm_scripts/README.md` R1 row added.

### Acceptance — dev02 e2e

All three paths green on dev02 V16 substrate:

| Path | Setup | Probe | result.changed | GET / |
|---|---|---|---|---|
| Idempotent (Web Page present from S79) | none | `home=present` | False (no-op) | 200 |
| From-absent INSERT | DELETE Web Page + `bench clear-website-cache` | `home=created` | True (changed) | 200 |
| Re-idempotent after pipeline INSERT | none | `home=present` | False (no-op) | 200 |

**DB row inspection**: pipeline-inserted `tabWeb Page` row is
byte-equal to the S79 lab-applied row (same `name=logichem-solutions-s-a`
slug, same `route='home'`, same `published=1`, same
`content_type='Page Builder'`, same `main_section` HTML structure
populated with the same runtime-salvaged values). Parity-with-S79
confirmed.

### Two bugs discovered during acceptance + fixed in-session

Both surfaced after the prior T1+T3 QA verdict; remediated via
direct edits + re-staging + size-check + T1+T3 re-verdict.

1. **Frappe v16 logger relative-path invariant**. R1 originally ran
   with `cd $BENCH_DIR &&`; Frappe v16's `frappe/utils/logger.py:25`
   uses `os.path.join("..", "logs", logfile)` for the
   `RotatingFileHandler`, so `../logs/` resolved to `~erpadm/logs/`
   (FileNotFoundError). Fix: change cwd to `$BENCH_DIR/sites/` so
   `..` resolves to `$BENCH_DIR/`. Path change + load-bearing
   in-code comment citing the Frappe source + #486.
2. **Marker contiguity in R1's success print**. `R1_CHANGED_MARKER =
   "(was absent, now 1)"` matched substring-wise; the original print
   format had `(route='home', was absent, now 1)` — the `(` and
   `was absent, now 1)` weren't a contiguous substring. CLI reported
   `(no-op)` on a successful INSERT. Fix: reformatted print so
   `(was absent, now 1)` is contiguous.

Both fixes are tightening fixes inside the architecture QA originally
approved. Test regression-guard added: `test_both_fresh_apply_sets_changed`
now asserts `/sites &&` is present in the R1 cmd.

### QA verdicts

- **T1+T3 pre-commit round 1** (a79e4b892c65ef586): `approve` /
  hard_block: false. No conditions on the initial diff (pre-acceptance).
- **T1+T3 pre-commit round 2** (a3d93488ae5e2262b): `approve-with-conditions`
  / hard_block: false after the two acceptance-driven fixes landed.
  Conditions: `fixes #486` in commit message, GPG-sign,
  Co-Authored-By trailer, follow-up issue for R1/R3 invocation
  asymmetry — all met.
- **T2 advisory** (ad2a4317469070ca6): `approve` / hard_block: false.
  §2.2 carve-out cleanly held (single commit, prior verdicts
  conditions met, no rebase/amend, squash-merge).
- **T5**: auto via `fixes #486` on merge.

### Follow-up issue filed

**ESACP#503** — `chore(pipeline): align _run_r1 / _run_r3 python
invocation — bench venv vs system python3`. Per QA T1+T3 re-verdict
non-blocking condition. `_run_r3` uses bare `python3`; `_run_r1` uses
`$BENCH_DIR/env/bin/python` + sudo + cwd. Risk: silent failure if a
future contributor adds Frappe imports to R3 or copies R3's pattern.
To be addressed before R6e.2 (#496).

## Counts at session close

- **ESACP open**: 72 → 72 (net 0; -#486 closed via fixes, +#503 filed).
- **LSKB open**: 12 → 12 (unchanged).
- **Sibling-tracker counts** (ce_sri 6 / ce_sri_svc 2 / LogiSoluValidations 2 / BaRe 2): unchanged.
- **dev02 state**: V16 (frappe 16.18.3 / erpnext 16.19.1); R1 + R3
  now both pipeline-applied (lab-applied → pipeline-applied parity);
  R5 + R6 nginx template parity intact since S81.
- **dev01 state**: V13 lab live; R3 pipeline-applied at S82, R5 manual nginx patch from S79.
- **Saconsole**: 4 GiB; live.
- **TRIVIAL_FIXES.md**: 3 entries unchanged.

## Decisions

- **Acceptance test option (a)** — from-absent INSERT exercised on
  dev02 this session; pre-snapshot taken for safety. Rationale: from-
  absent is the load-bearing path for production cutover.
- **Order of operations** — acceptance BEFORE commit, not after.
  Rationale: evidence in commit message, cleaner failure mode if
  acceptance reveals bugs (single corrective commit, not two).
- **Helper extraction** — `fix_script_runner.py` factored as a new
  file rather than inline duplication. Rationale: R6e.2 will be a
  third fix needing the same probe-parsing; extract-once-reuse-twice
  beats duplicate-and-refactor-later.
- **#503 filed non-blocking** — invocation-shape alignment between
  R1 (bench venv) and R3 (system python) is a real-but-latent risk;
  deferred to its own session to keep S83 strict-1:1:1.

## Outputs

- **Commit**: `857ac80` `feat(pipeline): V13->V16 post-migrate fix
  R1 — recreate Web Page 'home' from tabSingles (fixes #486)`. GPG-signed,
  Co-Authored-By trailer, conventional commits format.
- **PR**: #502 → squash-merge `9873c79`, mergedAt
  `2026-05-27T12:50:02Z`.
- **Issue #486** auto-closed `2026-05-27T12:50:04Z` via `fixes #486`.
- **Issue #503** filed (follow-up; open).
- **dev02 Web Page 'home'**: now pipeline-applied (was S79 lab-applied).
- **dev02 snapshot** `pre-S83-r1-acceptance`: persists on toshy.

## Carry-forward (new from S83)

- **`run_fix_script` helper** at `tools/pipeline/orchestration/fix_script_runner.py`
  is the canonical entry-point for adding new V13→V16 post-migrate
  fix-scripts. R6e.2 (#496) and future #480 children should plug in
  via the same helper rather than spawning sibling code.
- **R1 cwd invariant** (cwd at `bench_dir/sites/` so Frappe v16's
  `../logs/` resolves correctly) — documented in-code at
  `v16_post_migrate_fixups.py:_run_r1`. If a future fix-script also
  uses Frappe API, copy this cwd pattern.
- **dev02 snapshot revert** — `pre-S83-r1-acceptance` exists; revert
  if any post-session issue surfaces traceable to the in-session
  Web Page DELETE + INSERT cycle.
- **Issue counts +2 drift at session-start** (agenda expected 70,
  observed 72) — not investigated this session; no impact on R1
  scope. Audit at S84 start if drift recurs.

## Issue-count audit and unchanged carry-forward

(Items unchanged from S82, continue to S83 close — see S82 minutes
for full enumeration.)

- ESACP#440 (snapShotVM dispatcher) — encounter count unchanged at 4
  (this session used the pipeline primitive directly, not the bugged
  CLI). Carries to S84 with the **promote-to-primary** flag from S82
  next-agenda.
- S71 minutes backfill decision — unchanged.
- ESACP#426 / #427 — pending operator pickup.
- `on_boarding` branch handoff — Junior owns.
- LogiSoluMemory cross-repo cleanup (~28 refs).
- ESACP#401 + dev02 intermittents.
- LSKB#11 / #16 / #18 / #21 — Phase 2/3.
- LSKB#24 / LSKB#31.
- ESACP#387 / #394 / #395 / #396 / #397 — pre-S48 carry.
- TRIVIAL_FIXES.md monitors (3).
- T3-miss pattern monitor.
- MariaDB-10.6 default PS=OFF.
- LSMem Trigger-3 skip pattern monitor.
- Tablet WG sidebar (#383).
- Pages site tenant-detail scrub gate.
- `session_focus.txt` / `session_buckets.txt` controller-root.
- Stage-6-equivalent M&V check every ~50 substantive closes.
- Sub-rule #6 (operator walkthrough on systematic audits ≥2 findings).
- Frame-shift discipline (platform vs tenant M&V).
- Qualys regression-check as standard nginx-change acceptance.
- S81 minutes gap — backfill decision unchanged.

## Diff-based introspection-sidebar trigger

**NEGATIVE.** No MEMORY.md edits this session; no operator-reminders
attrition; pure substantive 1:1:1. Not a sidebar.

## SESSION END audit (4 prongs)

1. **Forward-tense audit** — all "I'll" / "will" promises resolved:
   #486 closed via merge, #503 filed at QA non-blocking condition,
   acceptance test executed end-to-end. No deferred-to-S84 items
   except routine carry-forward.
2. **GH issue references** — R1 implementation documented in #486
   body (issue closed), PR#502 description, and commit message body.
   #503 captures the follow-up invocation-asymmetry concern with
   citation to the originating QA verdict ID.
3. **PRs opened** — #502 opened and merged in-session per
   `feedback_pr_merge_before_session_close.md`; `mergedAt` non-null
   confirmed before this minutes file was written.
4. **Unresolved operator doubts** — none lingering. Goal-restatement
   alignment confirmed at session start; option (a) acceptance choice
   resolved; from-absent path proven; no late-emerging concerns.
