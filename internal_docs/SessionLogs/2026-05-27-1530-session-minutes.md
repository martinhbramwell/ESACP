# 2026-05-27 1530 — Session 84 minutes

## Stated objective (chosen at session start)

Candidate **A** from the S84 next-agenda: **#503 R1/R3 invocation
alignment**. Discharge the QA T1+T3 non-blocking condition recorded at
S83 close — `_run_r3` was using bare `python3` (system Python) while
`_run_r1` used bench venv + sudo + cwd at `sites/`; align both before
R6e.2 (#496) adds a third callsite. Strict 1:1:1 substantive session,
child of #480 V13→V16 re-migration umbrella.

## Class

**1:1:1 substantive code session.** New branch
(`feat/503-align-r1-r3-invocation`), single commit (`b9cd4e3`), PR
(#504), squash-merge (`f0a84e3` mergedAt `2026-05-27T15:26:23Z`),
issue #503 auto-close via `fixes #503` at `2026-05-27T15:26:25Z`.
Direct-to-main per established #480 sub-PR precedent (#500, #502).
No memory edits; one cross-issue follow-up comment on #496; not a
sidebar.

## What happened — substantive sequence

### Pre-flight

- sync_check: 49 pass / 8 warn / 0 fail (long-standing WG hub peer
  drift + dormant-VM + Chrome manual-verify warnings; non-blocking
  per agenda).
- Open ESACP issues: **72** (matches agenda expectation).
- LSKB issues: 12 (matches agenda).
- Branch state: `main`, clean tip = `371b8bf` (S83 close-batch).
- TRIVIAL_FIXES.md: 3 open items unchanged.
- Memory PROTOCOLS.md + MEMORY.md auto-load: clean.

### Planning + approval

Plan presented in plain language before any edit per
`feedback_plan_before_code.md` + `feedback_plain_language_approval_requests.md`:
two-file minimal-alignment change (rewrite `_run_r3` cmd shape to
match `_run_r1`; extend test assertion to cover R3). Explicitly NOT
extracting a `_bench_venv_cmd` helper — two callsites, defer to R6e.2
(#496) when it crosses the 3-callsite DRY threshold. Operator
approved.

### Implementation (round 1)

- **Branch** `feat/503-align-r1-r3-invocation` cut off `main` tip
  `371b8bf`.
- **Primitive edit**
  `tools/pipeline/orchestration/v16_post_migrate_fixups.py`:
  `_run_r3` cmd string rewritten to
  `sudo -u {erp_user} bash -c 'cd {bench_dir}/sites && {bench_dir}/env/bin/python {R3_SCRIPT} ...'`
  matching `_run_r1`. Added 4-line in-code comment naming the WHY
  (silent venv-mismatch trap if a future R3 edit adds Frappe imports).
- **Test edit**
  `tools/pipeline/orchestration/test_v16_post_migrate_fixups.py`:
  extended `test_both_fresh_apply_sets_changed` assertion on
  `cmds[1]` from a single filename-check to the same 3-term
  `all(s in cmds[1] for s in (...))` pattern already used on `cmds[0]`
  — `r3_disable_irs_1099_pf.py` + `sudo -u erpadm` + `/sites &&`.

### Pre-commit pytest + e2e (acceptance before commit)

- `pytest tools/pipeline/orchestration/test_v16_post_migrate_fixups.py` —
  5/5 green.
- `./tools/esacp.py applyV16PostMigrateFixups dev02` — R1 probe=home=present
  + R3 probe=disabled=1, both idempotent on already-applied substrate.
  Output: `V16 post-migrate fixups applied: R1 probe=home=present;
  R3 probe=disabled=1 (no-op)`.

### Size-baseline ratchet hit at commit time

Pre-commit hook rejected: `tools/pipeline/orchestration/v16_post_migrate_fixups.py`
baseline was **62**; my edit grew it to **67**. Surfaced to operator as
three options in plain-language prose:

- **A. Bump baseline** 62 → 67. Smallest change; entry climbs but file
  stays well under 80-line pipeline cap.
- **B. Extract `_bench_venv_cmd` helper** in same file. Net structural
  cleanup but scope-creep relative to approved plan.
- **C. Extract helper into new file** `fix_script_invocation.py`. Most
  files, thinnest helper, weakest signal-to-noise.

Operator chose **A**. `tools/size_baselines.json` updated 62 → 67.
`tools/pre_commit_size_check.py` clean after bump.

### QA verdicts

- **T1 pre-commit** (verdict block ID inline in agent reply, this
  session): `approve` / hard_block: false. One cosmetic-only advisory
  on pre-existing variable shadowing of `s` in test line 47 (loop var
  inside generator expression shadows outer `patch` alias; Python
  scoping makes it correct; cosmetic-only; not addressed this session).
- **T3 pre-push** (post-baseline-bump): `approve` / hard_block: false.
  Push target is a feature branch (`feat/503-align-r1-r3-invocation`),
  not `main` and not `umbrella/*`; advisory-equivalent under the
  branch-topology rule.
- **T2 pre-merge** to main: `approve` / hard_block: false. §2.2
  carve-out cleanly held — same head commit `b9cd4e3` as T1+T3, no
  rebase/amend, MERGEABLE clean fast-forward.
- **T5**: auto via `fixes #503` on merge (no explicit close action).

### Outputs

- **Commit** `b9cd4e3` `chore(pipeline): align _run_r1 / _run_r3
  invocation — bench venv + sudo + sites/ cwd (#503)`. GPG-signed,
  Co-Authored-By trailer, Conventional Commits format, `fixes #503`
  in body, baseline-bump rationale in body.
- **PR** #504 → squash-merge `f0a84e3`, mergedAt
  `2026-05-27T15:26:23Z`.
- **Issue #503** auto-closed `2026-05-27T15:26:25Z` via `fixes #503`.
- **Issue #496** comment `issuecomment-4556783201` posted at
  session-end audit — captures the future helper-extraction
  recommendation for whoever picks up R6e.2 (3rd callsite crosses
  DRY threshold).

## Counts at session close

- **ESACP open**: 72 → 71 (net −1; −#503 closed via fixes).
- **LSKB open**: 12 → 12 (unchanged).
- **Sibling-tracker counts** (ce_sri 6 / ce_sri_svc 2 /
  LogiSoluValidations 2 / BaRe 2): unchanged.
- **dev02 state**: V16 (frappe 16.18.3 / erpnext 16.19.1); R1 + R3
  pipeline-applied; R5 + R6 nginx template parity intact. Web Page
  'home' present (pipeline-applied at S83). IRS 1099 Print Format
  disabled (pipeline-applied at S82). Pre-S83-r1-acceptance snapshot
  persists on toshy.
- **dev01 state**: V13 lab live; R3 pipeline-applied at S82, R5
  manual nginx patch from S79.
- **Saconsole**: 4 GiB; live.
- **TRIVIAL_FIXES.md**: 3 entries unchanged.

## Decisions

- **Option A (baseline bump)** over B (helper extraction) or C (new
  helper file). Rationale: minimal scope to the approved plan;
  helper extraction defers naturally to R6e.2 (#496) when the third
  callsite materializes; documented as a comment on #496 so the
  next picker has the design hint.
- **Acceptance before commit** (S83-emergent pattern continued):
  pytest + dev02 e2e ran *before* `git commit`, not after. Worked
  cleanly this session (no acceptance-driven fixes; idempotent
  e2e on first try).
- **Cosmetic variable shadowing not addressed**. QA flagged the `s`
  loop var in test line 47 at both T1 and T2. Pre-existing,
  correctness-safe per Python generator-expression scoping rules.
  Out of scope for this PR; not promoted to a tracker issue —
  cosmetic-only fits the "not a perfection project" rule.

## Carry-forward (new from S84)

- **Helper-extraction hint on #496** — when R6e.2 lands as the third
  fix in `apply_v16_post_migrate_fixups`, the bench-venv invocation
  becomes a 3-callsite duplication; extract `_bench_venv_cmd(config,
  script)` at that point. Captured in #496
  [issuecomment-4556783201](https://github.com/martinhbramwell/ESACP/issues/496#issuecomment-4556783201).
- **Size-baseline pre-flight discipline** — pre-commit ratchet caught
  the 62 → 67 growth that the parent did NOT pre-flight. Per
  `feedback_check_size_baselines_at_commit_time.md`, the parent
  should have run `python3 tools/pre_commit_size_check.py` before
  invoking T1 QA. Recurring trap (S82, S83, S84). Not promoted to
  tracker issue this session — it's a discipline rule, not a code
  bug; recurrence implies the rule needs structural reinforcement
  (e.g. parent-side preflight script).

## Issue-count audit and unchanged carry-forward

Items unchanged from S83, continue to S84 close — see S83 minutes
for full enumeration. Highlights still load-bearing:

- **ESACP#440** (snapShotVM dispatcher) — encounter count unchanged
  at 4 (this session did not run snapshot ops). **5th-encounter
  warning still applies if hit in S85**; promote-to-primary flag
  still active.
- S71 minutes backfill decision — unchanged.
- S81 minutes gap — unchanged.
- `on_boarding` branch handoff — Junior owns.
- LogiSoluMemory cross-repo cleanup (~28 refs).
- ESACP#401 + dev02 intermittents.
- ESACP#426 / #427 — pending operator pickup.
- LSKB#11 / #16 / #18 / #21 — Phase 2/3.
- LSKB#24 (trivial doc edit) / LSKB#31 (File doctype role lockdown).
- ESACP#387 / #394 / #395 / #396 / #397 — pre-S48 carry.
- TRIVIAL_FIXES.md monitors (3): `sync_check.sh:2 Mighty` (S58);
  `tools/secrets.py +x` (S47); LSMem T3-miss pattern (S33).
- MariaDB-10.6 default PS=OFF (S55 carry).
- Tablet WG sidebar (#383).
- Pages site tenant-detail scrub gate.
- `session_focus.txt` / `session_buckets.txt` controller-root.
- Stage-6-equivalent M&V check every ~50 substantive closes.
- Sub-rule #6 (operator walkthrough on systematic audits ≥2 findings).
- Frame-shift discipline (platform vs tenant M&V).
- Qualys regression-check as standard nginx-change acceptance.
- `applyV16PostMigrateFixups` primitive remains the canonical
  extensible entry point for V13→V16 post-migrate fixes (R1 + R3
  aligned this session; R6e.2 next).
- Ad-hoc pytest venv at `/tmp/esacp-pytest-venv/` — uncommitted,
  re-used this session without friction; defer surfacing as tracker
  issue unless next test-authoring session hits an actual block.

## Diff-based introspection-sidebar trigger

**NEGATIVE.** No MEMORY.md edits this session; no operator-reminders
attrition; pure substantive 1:1:1. Not a sidebar.

## SESSION END audit (4 prongs)

1. **Forward-tense audit** — one hit: forward-looking helper-extraction
   recommendation surfaced during the size-baseline detour had no
   durable home. Discharged via comment
   [issuecomment-4556783201](https://github.com/martinhbramwell/ESACP/issues/496#issuecomment-4556783201)
   on #496. All other "I'll" / "will" promises map to executed tool
   calls (branch creation, edits, pytest, e2e, commit, push, PR,
   merge).
2. **GH issue references** — #503 closed via `fixes`; rationale lives
   in commit body + PR#504 body; no new findings beyond the approved
   plan. #496 received the helper-extraction hint as a comment. #486,
   #480, #440 referenced only as context; no new findings to post.
3. **PRs opened** — #504 opened and merged in-session per
   `feedback_pr_merge_before_session_close.md`; `mergedAt` non-null
   confirmed before this minutes file was written.
4. **Unresolved operator doubts** — none lingering: plan approved
   upfront; size-baseline detour resolved by operator choice (A);
   close-batch acknowledged.
