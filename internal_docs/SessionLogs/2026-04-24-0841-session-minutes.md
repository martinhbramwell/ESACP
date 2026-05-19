# Session Minutes — #292 Sub-2 Diagnostic + #293 Filed

**Date:** 2026-04-23 ~18:45 EDT → 2026-04-24 ~08:41 EDT (date rolled mid-session)
**Branches on main:** only this minutes file
**Branches touched:**
- `feat/playwright-wizard-generic-fixture` (sub-2 of umbrella/ladder-fixture) — cut off `origin/umbrella/ladder-fixture @ 9c66ccf`, one commit landed (`f0b9bbc`), pushed, **no PR yet**
- `main` — minutes only
**Commits on sub-branch:** `f0b9bbc` (gate + helper extraction)
**PRs opened:** none (sub-2 acceptance blocked on #293; PR deferred to next session)
**Issues filed:** **#293** (recording-race `waitForFrappeIdle` helper, direct-to-main scope)
**Issues with diagnostic comments:** #284 (scope reframing), #292 (progress update)
**Issues closed:** none
**Baseline:** entered at `main @ 0d5fb3d` (2026-04-23-1352 minutes tip); 20 open issues
**Exit:** `main @ <this minutes commit>`; 22 open issues (+ #292 pre-filed at session-start, + #293 filed mid-session)

## Declared objective

Cut sub-branch 2 off `umbrella/ladder-fixture`, file #292, drive `feat/playwright-wizard-generic-fixture` to a working clean-bench fixture.

## Revised mid-session

Acceptance bisection revealed the Playwright wizard replay races on Frappe's freeze-backdrop under pipeline context even after #289 produced a clean-bench substrate. Scope split: #292 gate code committed to the sub-branch; recording-race fix filed as #293 (direct-to-main, not umbrella). Sub-2 acceptance deferred until #293 lands.

## What happened

### Session-start review

- `sync_check`: 45 ✅ / 11 ⚠️ / **1 ❌** at entry — hub WG peer drift (dev02 peer missing after 1352 destroy cleanup)
- Fixed via `ansible-playbook -i ansible/inventory/kvm.yml site-kvm.yml --limit saconsole --tags wireguard` — hub re-added dev02 peer from SOPS; sync_check back to 46/11/0
- Open-issues review: 20 open, purge-plan Pre-Tier 0 pointed at sub-2 as the first move

### Issue filed + branch cut

- **#292** filed: `feat(test): Playwright wizard-generic fixture — en/Canada clean-bench golden artefact`
- `feat/playwright-wizard-generic-fixture` cut off `origin/umbrella/ladder-fixture @ 9c66ccf`, pushed with `-u`

### Mechanism enumeration — operator redirected scope

Initial survey found the terrain was richer than the issue body implied: `pseudo-co-wizard.spec.js` exists, `replay_wizard.js` exists, `capture_golden_backup` exists, `stage_6_base_platform/verify.py --mode=generic` exists. I initially proposed writing a new ~300-line Playwright spec lifted from `accept-03-cli-pseudo-wizard.spec.js`. Operator flagged this as a monolith-patching anti-pattern ("yet another new monolith").

Revised mechanism: **no new Playwright code**. Wire a bench-layer gate into `capture_golden_backup` (the existing capture flow) so any future contaminated substrate fails hard before staging the `.tgz`. Regenerate fixture on a clean-bench acceptance run.

### Gate code landed on sub-branch

Commit `f0b9bbc` on `feat/playwright-wizard-generic-fixture`:

- **New**: `tools/pipeline/stages/wizard_completion/clean_bench_gate.py` (38 lines) — calls `verify_stage_6(..., provision_mode="generic")`, raises `RuntimeError` with failing-check list if bench-layer contaminated
- **New**: `tools/pipeline/stages/wizard_completion/run_handle_backup.py` (36 lines) — extracted from `capture_backup.py` for cohesion + ratchet compliance
- **Modified**: `tools/pipeline/stages/wizard_completion/capture_backup.py` (74 → 55 lines) — three-step flow: gate → run → rsync
- Ratchet green (baselines auto-updated); imports sanity-checked

### Acceptance attempt #1 — pipeline failed at wizard race (line 128)

Full `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay --wizard-arg=pseudo-co-wizard.spec.js`. Stages 1-9 green (~22 min, Stage 6 produced clean-bench substrate). Wizard replay failed at `pw-replay-*.cjs:128:43` — Company-screen textbox fill via `.getByRole('textbox').first()`.

Dev02 left mid-wizard; Pseudo-Co uncreated at that point.

### False hypothesis #1 — "brittle codegen locators"

I proposed the recording's positional locators (`.getByRole('textbox').first()`, `.nth(N)`) were the root cause. Argued for hand-written identity-selector rewrites (`input[data-fieldname="company_name"]`). Operator asked sharp question: *does codegen actually use position cheats?*

Correction: codegen tries `getByRole(role, { name })` first, falls back to position only when the DOM exposes no unique accessible name. The `.first()` fallbacks on Company fields happen because Frappe's wizard doesn't label those inputs accessibly — codegen isn't cheating, it's reporting an honest DOM limitation.

Locator-rewrite hypothesis: falsified (not the root cause).

### False hypothesis #2 — "headed vs. headless"

Operator ran `pseudo-co-wizard.spec.js` manually (URL swapped dev01→dev02) after reverting dev02 to "ERPNext v13 Generic Baseline" snapshot. Result: **passed 100%, no alteration required**. I proposed the variable was `replay_wizard.js` forcing `headless: true`. Operator tested headless directly (sed-flipped `headless: false → true`): **passed 35.5s**. Headless hypothesis falsified.

### Bisection — the actual variable

With false hypotheses eliminated, the remaining variable was the invocation-wrapper stack:

| Invocation | Outcome | Time |
|---|---|---|
| Manual bash, headed (direct spec) | PASS | ~39s |
| Manual bash, headless (sed) | PASS | 35.5s |
| Manual bash, `node recordings/replay_wizard.js --script ... --url ...` (identical to pipeline's subprocess arguments) | PASS | 39.6s |
| `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay` (idempotency skips stages 1-9; 9 verify gates run) | **FAIL** at line 61 (Country Next click) | 1m50s |
| Prior pipeline fresh run (stages 1-9 executed) | **FAIL** at line 128 (Company textbox) | ~22 min |

**Finding**: the race only reproduces when `replay_wizard.js` is invoked via Python `subprocess.run` from `wizard_run.py`, with 9 idempotency-verify SSH probes against the VM running immediately before. The probes generate enough Frappe background load (supervisor workers, MariaDB queries, nginx logging) that the post-screen-transition `#freeze.modal-backdrop.in` clearance time crosses the click tolerance on the first un-guarded Next click.

The recording has `waitForFunction` guards at lines 76 (Industry checkbox) and 124 (Company fill) — added in prior race-fix rounds — but the Next clicks at lines 60, 62, 70, 116, 131 are un-guarded.

### Fix decision — recording-side, not pipeline-side

Operator asked: which approach best secures the saconsole future? Recording-side `waitForFrappeIdle(page)` helper called before every Next click wins because:

1. **Saconsole is resource-tighter than Mighty** — the race will be worse on the hub. Recording-side guards adapt to load; pipeline-side warmup is fixed-duration.
2. **Pipeline-side warmup only guards the first click** — subsequent screen transitions race independently.
3. **Ladder scalability** — recording drives the wizard for each rung v13→v14→v15→v16; recording-side guards auto-adapt across ERPNext versions.

### #293 filed

`bug(wizard-replay): add waitForFrappeIdle helper before every Next click in pseudo-co-wizard recording` — direct-to-main scope (benefits matrix specs AND ladder fixture), single-file recording change.

### Session-close (this block)

- Gate code committed to `feat/playwright-wizard-generic-fixture` as `f0b9bbc`, pushed. **No PR yet** — acceptance blocked until #293 lands.
- Diagnostic comments posted on #284 (scope reframing), #292 (progress + bisection summary)
- Memory written: `feedback_bisect_before_hypothesizing.md` — durable guidance against symptom-reading during flaky-failure debugging
- Purge plan updated: sub-2 row marked ⏸ with #292 pointer, new sub-2-prereq row for #293, first-move advanced
- Fleet restored: dev02 shut off, dev01 running
- sync_check: 46 ✅ / 11 ⚠️ / 0 ❌

## Files changed

| File / path | Change | Branch |
|---|---|---|
| `tools/pipeline/stages/wizard_completion/clean_bench_gate.py` | NEW — 38 lines, bench-layer gate | feat/playwright-wizard-generic-fixture |
| `tools/pipeline/stages/wizard_completion/run_handle_backup.py` | NEW — 36 lines, extracted cohesive unit | feat/playwright-wizard-generic-fixture |
| `tools/pipeline/stages/wizard_completion/capture_backup.py` | 74 → 55 lines (ratchet shrink + gate wire) | feat/playwright-wizard-generic-fixture |
| `tools/size_baselines.json` | Ratchet bookkeeping | feat/playwright-wizard-generic-fixture |
| `memory/feedback_bisect_before_hypothesizing.md` | NEW — feedback memory | (memory, not repo) |
| `memory/MEMORY.md` | Added pointer; open-issue count 18→22 | (memory, not repo) |
| `~/.claude/plans/open-issues-purge.md` | Sub-2 row ⏸; sub-2-prereq (#293) row; counts refreshed; first-move advanced | (plan, not repo) |
| `internal_docs/SessionLogs/2026-04-24-0841-session-minutes.md` | this file | main |

## State handed to next session

- **`main` tip**: `<this minutes commit>`
- **`umbrella/ladder-fixture` tip**: `9c66ccf` (unchanged)
- **`feat/playwright-wizard-generic-fixture` tip**: `f0b9bbc` (gate + helper extraction, awaiting #293)
- **Open issues: 22** (+ #292, + #293 vs. session-start 20)
- **Fleet**: dev01 running, dev02 shut off
- **Uncommitted work**: none in repo

## First move for next session

Cut a direct-to-main branch for **#293**:

1. `git checkout main && git pull`
2. `git checkout -b fix/wizard-freeze-backdrop-guards`
3. Add `waitForFrappeIdle(page)` helper to `prototypes/cytoscape/recordings/wizard/pseudo-co-wizard.spec.js`
4. Call it before every Next click (lines 60, 62, 70, 116, 131 at minimum; verify against full recording)
5. Acceptance: the bisection matrix above re-runs all PASS; in particular `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay` completes to `[OK] Golden backup saved:` (exercises the #292 gate inline)
6. Commit with `fixes #293`, PR to main, merge
7. `git checkout umbrella/ladder-fixture && git rebase main` — umbrella picks up the recording fix
8. `git checkout feat/playwright-wizard-generic-fixture && git rebase umbrella/ladder-fixture` — sub-2 picks up the recording fix
9. Rerun `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay` — this time gate fires green, `.tgz` staged
10. Archive 4 contaminated `.tgz`s in `platforms/kvm/golden_backups/` to `archive/`; commit the clean one
11. Open sub-2 PR to umbrella

## Posterity — what I got wrong this session

1. **Proposed a ~300-line spec lift before thinking about extraction** — would have been a monolith-patching anti-pattern violation. Operator caught it; scope revised to gate-in-pipeline. Zero-new-Playwright-spec was correct.
2. **Pattern-matched on symptoms (locator fragility) instead of bisecting variables.** Codegen's `.first()` / `.nth(N)` emissions were the most-visible-looking fragility in the recording and I stuck to them through two sessions before operator redirected. The actual root cause was upstream timing under Python-subprocess load — not locator craft. Memory added: `feedback_bisect_before_hypothesizing.md`.
3. **Mislabelled codegen** as "using coordinate cheats" when it does exactly what it's supposed to — prefers accessible-name selectors, falls back to position only when DOM limits force it. Correction is on record in #292 and #284 comments.

## File trail

- Prior minutes: `internal_docs/SessionLogs/2026-04-23-1352-session-minutes.md`
- Purge plan: `~/.claude/plans/open-issues-purge.md` (Pre-Tier 0 section, sub-2 row + sub-2-prereq)
- Memory: `memory/feedback_bisect_before_hypothesizing.md` (NEW)
- Issue: [#292](https://github.com/martinhbramwell/ESACP/issues/292) (open; PR deferred)
- Issue: [#293](https://github.com/martinhbramwell/ESACP/issues/293) (open; direct-to-main next session)
- Issue: [#284](https://github.com/martinhbramwell/ESACP/issues/284) (open; diagnostic comment posted; superseded in scope by #293)
- Comments: [#292 progress](https://github.com/martinhbramwell/ESACP/issues/292#issuecomment-4313198751) · [#284 diagnostic](https://github.com/martinhbramwell/ESACP/issues/284#issuecomment-4313196647)
- Feat branch: `feat/playwright-wizard-generic-fixture` @ `f0b9bbc`
- This minutes: `internal_docs/SessionLogs/2026-04-24-0841-session-minutes.md`
