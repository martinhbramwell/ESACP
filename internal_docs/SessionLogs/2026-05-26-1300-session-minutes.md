# 2026-05-26 1300 — Session 82 minutes

## Session numbering note

S81 (R6 implementation, ESACP#483 / PR#495 / commit `1afe93f`) landed
after the S80 close commit but **without** S81 minutes being written.
Per operator decision at S82 session-start, S82 covers R3 only; R6 is
recorded as "S81 no minutes" — a one-off gap, not a recurring practice.

## Stated objective (chosen at session start)

Candidate **D** from the S81 (now-orphaned) agenda: **R3 pipeline
integration** — disable orphan `IRS 1099 Form` Print Format after
V13→V16 migrate. Strict 1:1:1 substantive 1-issue session, child of
#480 V13→V16 re-migration umbrella.

## Class

**1:1:1 substantive code session.** New issue (#498), new branch
(`feat/498-r3-irs-1099-disable`), new commit (`6d9929d`), PR (#500),
merge (`da8343f` mergedAt `2026-05-26T22:08:28Z`), issue auto-close.
No memory edits; no carry-forward attrition; not a sidebar.

## What happened — substantive sequence

### Pre-flight

- sync_check: 26 pass / 10 warn / 7 fail (WG hub peer drift + MCP
  grafana + dev01/dev02 unreachable warnings — long-standing #401-class
  intermittents; not S82 work). WG actually functional from controller
  when exercised.
- Open issues: ESACP 70 (agenda expected 67; +3 deltas = #496 R6e.2
  policy, #492 pipeline content-blind refresh, #488 Qualys re-enable
  — all S81 R6-vintage byproducts).
- LSKB 12 (matches agenda).
- Branch state: `main`, clean tip = `1afe93f` (S81 R6 squash).
- TRIVIAL_FIXES.md: 3 open items unchanged.
- Memory PROTOCOLS.md + MEMORY.md auto-load: clean.

### Decisions at session-start

Two procedural decisions resolved in plain-language Q&A before any
code:

1. **Branch topology** — direct-to-main, no umbrella. CLAUDE.md
   umbrella criteria (>3 sub-branches AND cross-cutting AND
   broad-context acceptance) not all met; #480 children are
   independent post-migrate fixes. R6 (#483 / PR#495) set the
   direct-to-main precedent at S81.
2. **#486 disposition** — split: file R3 as fresh issue (#498),
   retitle #486 to R1-only and add comment explaining the split.
   Strict 1:1:1 catalog hygiene; the "one extra issue number" cost
   is near-zero, the catalog-integrity payoff is durable.

### Implementation

- **Issue #498** filed (child of #480): `bug(pipeline): V13→V16
  post-migrate fix R3 — disable IRS 1099 Print Format`.
- **#486** retitled to R1-only; comment posted explaining R3 split.
- **Branch** `feat/498-r3-irs-1099-disable` cut off `main` tip.
- **VM-side script** `tools/vm_scripts/r3_disable_irs_1099_pf.py`
  (72 lines, +x): reads `site_config.json`, runs `mysql UPDATE
  tabPrint Format SET disabled=1 WHERE name='IRS 1099 Form'` if
  record exists. Emits `[PROBE] disabled=…` line. Idempotent; safe
  if record absent.
- **Pipeline primitive** `tools/pipeline/orchestration/v16_post_migrate_fixups.py`
  (69 lines): IoC `(Config, Emit) -> TaskResult`. Rsyncs `vm_scripts/`,
  runs R3 over SSH, parses probe. Extensible — R1 (#486) and R6e.2
  (#496) will plug in here when picked up.
- **Colocated test** `test_v16_post_migrate_fixups.py` (76 lines):
  6 cases covering first-apply / already-disabled / record-absent /
  rsync-fail / ssh-fail / unexpected-probe. All 6 pass.
- **CLI dispatcher** `tools/cli/apply_v16_post_migrate_fixups.py`
  (44 lines): thin shell registering `applyV16PostMigrateFixups <vm>`.
- **esacp.py wiring** (106 lines, = baseline): added subcommand to
  DISPATCH + VM_COMMANDS + `_build_parser`. Refactored 4-line
  `add_subparser` sequential block into a 2-line for-loop to
  recover budget after the new wiring exceeded baseline. Pattern
  matches the existing for-loop at the VM-arg-command registrations
  in the same function.
- **README + tools/CLAUDE.md**: catalogue + subcommand description
  updated.

### QA verdicts

- **T1+T3 round 1**: `approve-with-conditions` (`hard_block: true`).
  Two size violations flagged: `r3_disable_irs_1099_pf.py` 82 > 80
  cap; `tools/esacp.py` 109 > 106 baseline. Both addressable.
- **Trim round**: R3 docstring compressed (82→72). esacp.py
  compressed via import-reflow + add_subparser-loop conversion
  (109→106 = baseline). Test file compressed via `_run()` helper +
  redundant-assertion removal (115→76, all 6 tests still pass).
- **T1+T3 round 2**: `approve-with-conditions` (`hard_block: false`).
  Sole condition: commit-message format (Conventional Commits +
  `fixes #498` + GPG-sign + Co-Authored-By). Satisfied at commit.
- **T2 advisory (PR#500 merge)**: `approve` (`hard_block: false`).
  All three §2.2 carve-out conditions held (prior T1+T3 verdict
  addressed, no new commits since, clean squash-merge).
- **T5 (issue close)**: auto via `fixes #498` in commit body.
- **Session-close T1+T3** on this minutes commit: _to be invoked
  next._

### Acceptance evidence (real-VM)

- **dev01 V13 first-apply**: `(was 0, now 1)` → probe `disabled=1`
  → `changed=True`.
- **dev02 V16 already-disabled** (S79 lab-applied): `already disabled`
  → probe `disabled=1` → `changed=False`.
- **dev01 idempotence**: 2nd run = `(no-op)`, probe still `disabled=1`.
- **6/6 unit tests pass** (`/tmp/esacp-pytest-venv/bin/pytest`).
- **pre_commit_size_check.py**: exit 0 (post-trim).

## Decisions

- **Direct-to-main** for all #480 children unless cross-cutting
  scope emerges (so far R6 + R3 both landed direct-to-main).
- **Issue split** on bundled markers at implementation-time is the
  default disposition; preserve catalog 1-issue-1-fix hygiene over
  issue-number economy.
- **Ad-hoc pytest venv** at `/tmp/esacp-pytest-venv/` for this
  session's test runs. Not committed; not normalized. Test-runner
  setup is a separate concern outside this session's scope.
- **Substrate-name framing** kept (`v16_post_migrate_fixups`) even
  though R3 runs cleanly on V13 too — the catalogue arose from
  V13→V16 work and the name reflects intended caller context.

## Outputs

| Artifact | Repo | Status |
|---|---|---|
| Issue #498 (R3 pipeline integration) | ESACP | closed via `fixes #498` |
| Issue #486 retitled to R1-only + split comment | ESACP | open (R1 marker, awaiting pickup) |
| PR #500 / squash-commit `da8343f` | ESACP | merged 2026-05-26T22:08:28Z |
| Branch `feat/498-r3-irs-1099-disable` | ESACP | merged, persists |
| R3 lab-applied on dev01 V13 (`disabled=1`) | (lab state) | applied |
| R3 lab-applied on dev02 V16 | (lab state) | already-applied from S79 |

## Carry-forward (new from S82)

- **`applyV16PostMigrateFixups`** is now an ESACP CLI subcommand.
  Use this primitive for any future V13→V16 post-migrate fix.
- **R1 (#486)** + **R6e.2 (#496)** are the next natural
  catalogue additions; both should plug into
  `tools/pipeline/orchestration/v16_post_migrate_fixups.py` rather
  than spawning sibling primitives.
- **Pytest venv missing** — colocated tests pass but no project-
  standard test runner config exists. Surface as a tracker issue
  when the next test-author session hits it. (Not filed in S82
  to avoid scope creep.)

## Carry-forward (unchanged from S80→S81→S82)

- ESACP#440 (5th encounter; promoted ripe to "should be primary"
  in S83 agenda)
- S71 minutes backfill decision
- ESACP#426 / #427 — pending operator pickup
- on_boarding branch handoff — Junior owns
- LogiSoluMemory cross-repo cleanup (~28 refs)
- ESACP#401 + dev02 intermittents (WG hub peer drift visible in
  this session's sync_check too)
- LSKB#11 / #16 / #18 / #21 — Phase 2/3 follow-on
- LSKB#24 (trivial doc edit)
- LSKB#31 (File doctype role lockdown — needs upload-flow audit)
- ESACP#387 / #394 / #395 / #396 / #397 — pre-S48 carry
- `sync_check.sh:2 Mighty` (S58 TRIVIAL_FIXES)
- `tools/secrets.py +x` (S47 TRIVIAL_FIXES)
- T3-miss pattern (S58) monitor
- MariaDB-10.6 default PS=OFF (S55 carry)
- LSMem Trigger-3 skip pattern monitor
- Tablet WG sidebar (#383)
- Pages site live — tenant-detail scrub gate
- `session_focus.txt` / `session_buckets.txt` controller-root
- Stage-6-equivalent M&V check every ~50 substantive closes
- **Sub-rule #6** (operator-walkthrough on systematic audits ≥2
  findings) — load-bearing for all #480-umbrella future work
- **Frame-shift discipline** (platform M&V vs tenant M&V)
- **Qualys regression check** as standard nginx-change acceptance

## Counts

- ESACP open issues: **70 → 70** (+1 #498 filed, −1 #498 closed
  on merge; net 0)
- LSKB open issues: **12 → 12** (unchanged)
- Sibling-tracker counts unchanged
- dev01 state: V13 lab still live; **R3 now applied** (was 0, now 1)
- dev02 state: V16 lab unchanged; R3 already-applied since S79
- TRIVIAL_FIXES.md: unchanged (3 entries)

## Files committed (ESACP, S82)

- PR#500 squash-commit `da8343f`:
  - `tools/cli/apply_v16_post_migrate_fixups.py` (new, 44L)
  - `tools/pipeline/orchestration/v16_post_migrate_fixups.py` (new, 69L)
  - `tools/pipeline/orchestration/test_v16_post_migrate_fixups.py` (new, 76L)
  - `tools/vm_scripts/r3_disable_irs_1099_pf.py` (new, 72L, +x)
  - `tools/esacp.py` (modified, 106L = baseline)
  - `tools/CLAUDE.md` (modified, +3 lines)
  - `tools/vm_scripts/README.md` (modified, +1 line)
  - `tools/size_baselines.json` (auto-staged by pre-commit hook)
- This session-close commit: S82 minutes + S83 next-agenda +
  qa-log S82 close-batch row

## Session classification

**1:1:1 discipline + substantive code session.** Substantive code
change (R3 pipeline integration) went through proper 1:1:1
(issue #498 → branch → commit → PR → merge → auto-close).
Branch topology: direct-to-main, no umbrella (matches R6/PR#495
precedent at S81).

Diff-based introspection-sidebar trigger: MEMORY.md untouched;
carry-forward additive only (+3 items). Trigger NEGATIVE.
