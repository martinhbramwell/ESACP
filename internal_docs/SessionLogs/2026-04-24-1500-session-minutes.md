# Session Minutes — #292 acceptance attempted, blocked on Baseline snapshot pollution

**Date:** 2026-04-24 ~13:30 → ~15:00 EDT
**Branches touched:** `umbrella/ladder-fixture` (force-push rebase), `feat/playwright-wizard-generic-fixture` (force-push rebase)
**Commits on main:** this minutes file + next agenda
**PRs opened:** none
**PRs merged:** none
**Issues closed:** #295 (filed this session, closed `not planned` as misframed)
**Issues filed:** #295 (closed same session)
**Baseline:** entered at `main @ 38d74f1`; 21 open issues
**Exit:** `main @ <this minutes commit>`; 21 open issues

## Declared objective

Resume sub-2 of `umbrella/ladder-fixture`: rebase umbrella onto main (picks up #294), rebase `feat/playwright-wizard-generic-fixture` onto rebased umbrella, re-run `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay` on a clean-bench substrate, verify the #292 gate fires green, archive the 4 contaminated `.tgz` artefacts, commit the clean one, and open the sub-2 PR targeting umbrella.

## What happened

### Session-start review

- `sync_check`: 46 ✅ / 11 ⚠️ / 0 ❌ (matches baseline)
- Open-issues review: 21; #292 confirmed as the active sub-2 objective

### Rebases (both content-preserving, GPG-signed, force-pushed)

Local `umbrella/ladder-fixture` was stale (`3dbac2d`) vs origin (`9c66ccf`) — fast-forwarded to origin first. Zero file overlap between `main` post-divergence (wizard spec + minutes files) and either sub-1 (`bc1742d`, Stage 6 files) or sub-2 (`f0b9bbc`, wizard_completion files) — verified via `comm`-intersection of changed file lists before touching history.

| Branch | Before | After | Content change |
|---|---|---|---|
| `umbrella/ladder-fixture` | `9c66ccf` (merge #291) | `ea5cf92` (linear) | None — replay of `bc1742d` |
| `feat/playwright-wizard-generic-fixture` | `f0b9bbc` atop merge | `bb84fb7` atop `ea5cf92` | None — replay of `f0b9bbc` |

Both force-pushed after explicit operator approval.

### Pipeline acceptance attempt — failed, but on a substrate issue

`virsh snapshot-revert dev02 Baseline --running` → `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay --wizard-arg pseudo-co-wizard.spec.js`

- Stages 1–9 all green
- Final snapshot step warned `"ERPNext v13 Generic Baseline"` already existed (non-fatal)
- Wizard replay failed:
  ```
  page.waitForResponse: Timeout 180000ms exceeded while waiting for event "response"
      at pw-replay-1777053131544.cjs:178:10 — TimeoutError
  ```

### Diagnosis — Baseline snapshot was polluted

Post-failure queries on dev02 (via ProxyJump):

| Query | Result |
|---|---|
| nginx access.log `setup_complete` POST | `499 0` at 13:52:34 EDT (client closed before response) |
| `SELECT * FROM tabCompany` | `Pseudo-Co / Canada / CAD / CAD - PSC` |
| `System Settings.setup_complete` | `1` |
| `TIMESTAMPDIFF(SECOND, tabCompany.creation, NOW())` | **5669 s — ~27 min before the pipeline started** |

The wizard completed server-side, but `Pseudo-Co` existed in the DB *before* this session's pipeline ran. `virsh snapshot-revert Baseline` restored the VM to a state that already had a wizard-completed DB. The 180 s `waitForResponse` hung because `setup_complete` re-entered on already-set state.

### Wrong turns this session (recorded so future sessions do not retrace)

- Initially filed **#295** framing the failure as a cold-worker timing bug on `setup_complete`. Closed same session as `not planned` once `TIMESTAMPDIFF` showed `Pseudo-Co` pre-dated the pipeline run.
- Proposed "three new pipeline subcommands" (`installGeneric` / `captureGolden` / `restoreGolden`) before reading the existing `provisionGeneric` macro + matrix closeout. Retracted after operator pointed to the original 7-stage matrix — the capability already exists under `provisionGeneric --wizard-mode={replay,existing}` (matrix runs 03/04/06/07, all previously green). Only two small additions are actually needed: (a) post-capture snapshot at end of `wizard_run._replay` branch, (b) pre-revert-to-`Baseline` step for `existing` mode.
- Framed repeated wizard-replay failures as a "treadmill" — retracted. Today's failure was a dirty substrate, not a new layer of timing races.

### Session close

Direction from operator: defer #292 closure; next session re-runs matrix phases 2–7 on a contamination-fixed substrate per the destroy→rebuild plan summarised in the comment posted to #292.

## Files changed

| File | Change | Branch |
|---|---|---|
| `internal_docs/SessionLogs/2026-04-24-1500-session-minutes.md` | this file | main |
| `internal_docs/SessionLogs/2026-04-24-1500-next-agenda.md` | next agenda | main |

No code commits. Branch tips unchanged from rebased state.

## State handed to next session

- **`main` tip**: `<this minutes commit>`
- **`umbrella/ladder-fixture` tip**: `ea5cf92` (rebased onto main; +1 commit)
- **`feat/playwright-wizard-generic-fixture` tip**: `bb84fb7` (rebased onto rebased umbrella; +2 commits)
- **Open issues: 21** (#295 filed + closed this session, net zero)
- **Fleet**: dev02 in broken intermediate state (wizard half-run on polluted Baseline) — will be destroyed per the next-session plan. dev01 running, saconsole running.
- **Uncommitted work**: none in repo.

## Issue comments posted this session

- [#292](https://github.com/martinhbramwell/ESACP/issues/292#issuecomment-4315693879) — rebase done, Baseline-pollution blocker identified, roundtrip plan deferred to next session, maps to matrix 03/04/06/07
- [#295](https://github.com/martinhbramwell/ESACP/issues/295) — filed and closed `not planned` as misframed (cold-worker framing wrong; real cause was Baseline pollution)

## First move for next session

See `2026-04-24-1500-next-agenda.md` — matrix phases 2–7 rerun on contamination-fixed substrate.
