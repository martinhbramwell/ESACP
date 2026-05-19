# Session Minutes — #293 Closed End-to-End

**Date:** 2026-04-24 ~08:50 → ~12:07 EDT
**Branches on main:** PR #294 merge (`473f058`) + this minutes file
**Branch cut + merged:** `fix/wizard-freeze-backdrop-guards` → main via PR #294 (`473f058`)
**Commits on fix branch:** `18d5aab`
**PRs opened:** **#294** (merged, `mergedAt=2026-04-24T16:04:23Z`)
**Issues closed:** **#293** (`fixes #293` trailer, `closedAt=2026-04-24T16:04:25Z`)
**Issue comments posted (post-merge, session-close audit):**
- [#284 comment](https://github.com/martinhbramwell/ESACP/issues/284#issuecomment-4314709395) — PR #294 extends #284's coverage with a DOM-remove fallback when Escape fails to dismiss the Industry-screen modal; root cause of the intermittent Escape-consumption left open
- [#292 comment](https://github.com/martinhbramwell/ESACP/issues/292#issuecomment-4314710162) — pre-req cleared; handover path for sub-2 rebase + resume
**Issues filed:** none
**Baseline:** entered at `main @ 130f8fa`; 22 open issues
**Exit:** `main @ <this minutes commit>`; **21 open issues**

## Declared objective

Fix #293 direct-to-main: harden `pseudo-co-wizard.spec.js` so `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay` completes reliably to `[OK] Golden backup saved:`. Operator re-scoped early: "solving this Playwright wizard blocker, definitively, IS the purpose of this session" — pushed past the narrow Next-click race into whatever was blocking the pipeline.

## What happened

### Session-start review

- `sync_check`: 46 ✅ / 11 ⚠️ / 0 ❌
- Open-issues review: 22 open; prior-session minutes named #293 as the first move (direct-to-main unblocker for umbrella/ladder-fixture sub-2)
- Branch cut `fix/wizard-freeze-backdrop-guards` off `main @ 130f8fa`

### Initial fix — waitForFrappeIdle helper

Extracted the two existing inline `waitForFunction(#freeze.modal-backdrop.in)` blocks (lines 76 & 124 in the pre-fix spec) into a reusable `async function waitForFrappeIdle(page, timeout = 30_000)` at module scope. Added `await waitForFrappeIdle(page)` before every `Next` click (lines 60, 62, 70, 116, 131 in the pre-fix numbering) and before the `Complete Setup` `Promise.all`. Syntax-checked.

### Bisection — pipeline still failed at new sites

Per the `feedback_bisect_before_hypothesizing` discipline from the prior session, ran the full bisection matrix rather than stopping at "fix looks right":

| Invocation | Outcome | Notes |
|---|---|---|
| Manual `node replay_wizard.js` (warm workers) | PASS 35.6 s | Identical to prior session baseline |
| Manual replay after `supervisorctl restart all` (cold repro) | PASS 37.4 s | Cold-worker hypothesis falsified |
| Pipeline run #1 | FAIL — `waitForResponse: Timeout 180000ms` at `setup_complete` | One-time flake; nginx logged 499 (client close) after 3 s; Company `Pseudo-Co` was in fact created with `default_bank_account` populated |
| Pipeline run #2 | FAIL — `waitForFunction: Timeout 5000ms` at Industry modal dismiss | The #284 fix relied on Escape; Escape was consumed without dismissing the backdrop |

### Diagnostics

Built a throwaway `debug-wizard.spec.js` (attached `page.on('request'|'response'|'requestfailed'|'pageerror'|'framenavigated'|'close'|'websocket')` plus a modal-DOM dump block). Pipeline run with instrumentation PASSED (37.55 s, `setup_complete` response in 25 s). The modal simply did not appear that time — confirming the Escape-fail path is intermittent, not universal.

### Hardening

Three changes landed in the real spec:

1. **`waitForFrappeIdle` helper** (as above) — subsumes the two prior inline waits; called before every navigation click. No narration-only claim — every click in the wizard sequence now has an explicit guard.
2. **Modal-dismiss DOM-remove fallback** — Escape stays as the fast path (2 s budget). On Escape timeout, fall through to `document.querySelectorAll('.modal-backdrop, .modal.show, .modal.fade.show').forEach(n => n.remove())` + restoration of `body` state, then re-verify absence.
3. **`waitForURL` bumped to 90 s** — one later pipeline run hit 30 s Playwright default at `waitForURL('**/app**')`. Nginx access log showed the client idle for 29 s between login POST and the `/app` redirect under cold-worker conditions (workers/redis warming up). 90 s absorbs it; fast runs are unaffected.

### Final acceptance

After the hardening:

| Invocation | Outcome |
|---|---|
| Pipeline fresh-revert run #3 | PASS — `[OK] Golden backup saved: 20260424_104107-dev02_iridium_blue.tgz (1.3 MB)` + `Generic provision complete` |
| Pipeline fresh-revert run #4 | PASS — `[OK] Golden backup saved: 20260424_110235-dev02_iridium_blue.tgz (1.3 MB)` |

Two consecutive fresh-revert pipeline runs green, plus the two manual replays from earlier — 4× acceptance.

### Commit + PR + merge

- `18d5aab` GPG-signed on `fix/wizard-freeze-backdrop-guards`, `fixes #293` trailer
- PR [#294](https://github.com/martinhbramwell/ESACP/pull/294) opened with full test-plan checklist
- Merge-state `CLEAN` / `MERGEABLE` — merged via `gh pr merge --merge` (merge commit `473f058`)
- #293 auto-closed by the `fixes` trailer (`closedAt=2026-04-24T16:04:25Z`)

### Session-close

- dev01 restarted on toshy to restore fleet invariant; HTTP 200 on 4th probe
- `sync_check`: 46 ✅ / 11 ⚠️ / 0 ❌ (matches entry)
- dev02 left `shut off`; baseline snapshot intact
- Debug spec `debug-wizard.spec.js` deleted; no stray files
- `MEMORY.md` open-issue block updated to 21 with #293 closure pointer

## Files changed

| File | Change | Branch |
|---|---|---|
| `prototypes/cytoscape/recordings/wizard/pseudo-co-wizard.spec.js` | +52 / −19 — helper, modal fallback, 90 s waitForURL | merged to main via PR #294 |
| `MEMORY.md` | Open-issue ledger 22→21 with #293 pointer | (memory, not repo) |
| `internal_docs/SessionLogs/2026-04-24-1207-session-minutes.md` | this file | main |

## State handed to next session

- **`main` tip**: `<this minutes commit>`
- **`umbrella/ladder-fixture` tip**: `9c66ccf` (unchanged) — needs rebase onto main to pick up #294
- **`feat/playwright-wizard-generic-fixture` tip**: `f0b9bbc` (unchanged) — needs rebase onto umbrella after umbrella rebase
- **Open issues: 21** (−#293)
- **Fleet**: dev01 running, dev02 shut off, saconsole running
- **Uncommitted work**: none in repo

## First move for next session

Sub-2 prerequisite now cleared. Next action per prior-session's purge plan: open-issue sub-2 can resume — rebase `umbrella/ladder-fixture` onto main (picks up #294), then rebase `feat/playwright-wizard-generic-fixture` onto the umbrella, then re-run `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay` against sub-2 to verify the #292 gate fires green on a clean-bench substrate, archive the 4 contaminated `.tgz`s, commit the clean one, and open the sub-2 PR to umbrella.

## Posterity — what surprised me

1. **The "fix for #293" was only the first of three flake classes.** The initial waitForFrappeIdle fix advanced the pipeline past the Next-click race but exposed a modal-Escape race and a post-login cold-worker race that were latent behind it. Useful reminder that "fix exposes next blocker" is normal when you remove a single guard.
2. **499 (client close) on `setup_complete` was a one-time flake.** I spent time characterising it as if reproducible; subsequent pipeline runs with the hardening never reproduced it. The rule `feedback_bisect_before_hypothesizing` held — the single-run failure was not enough signal to design against.
3. **Instrumentation can change timing.** Attaching `page.on()` handlers produced a pass where the plain spec had failed moments earlier. Not a reason to ship instrumentation in production specs, but a useful reminder to re-run without instrumentation before claiming the bug is fixed.

## File trail

- Prior minutes: `internal_docs/SessionLogs/2026-04-24-0841-session-minutes.md`
- Fix commit: `18d5aab`
- Merge commit: `473f058`
- PR: [#294](https://github.com/martinhbramwell/ESACP/pull/294)
- Issue: [#293](https://github.com/martinhbramwell/ESACP/issues/293) (closed)
- This minutes: `internal_docs/SessionLogs/2026-04-24-1207-session-minutes.md`
