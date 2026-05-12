# 2026-05-12 1117 — Session 37 minutes

## Stated objective at session start

Per `2026-05-12-0619-next-agenda.md` (operator-selected Area 3 via "do that" after introspection discussion): **Risk-tier the QA verdict layer's trigger contract based on Sessions 5.5–36 catch-rate data.**

## How the session went

Introspection conversation first. Operator asked three questions: refactoring progress (5/6 Epoch-1 done, compression real), clerical reduction (per-deliverable ~3x better; per-session unchanged; TRIVIAL_FIXES.md underutilized), block sizing (right-sized; substrate-discovery cost is the wildcard). Operator probed which elements are excessive, then selected Area 3 (QA layer signal review) as the highest-EV slim.

Initial proposal was intuition-driven (carve out T1 on doc-sweeps). Data from a `bash awk` over `docs/qa-log.md` contradicted: T1 has the highest catch rate (49%), not lowest. Revised proposal landed: codify T1+T3 combination, carve T2 down to advisory under three categorical conditions, add §7.1 rolling-window audit. Operator approved revised shape.

Execution: 1 issue filed (#380), 1 branch, 1 PR, 1 merge, 1 auto-close — all in-session. QA chain caught 3 load-bearing conditions on T1+T3 (§2.2 wording-hedge, §7.1 scope, §10 span label); all addressed pre-commit. T2 verdict on PR #381 was clean approve under v1 (bootstrapping correctly handled).

## 109-verdict rollup (durable home: #380 body)

| Trigger | catch rate (AwC + reject) |
|---|---|
| T1 alone (commit) | 49% |
| T5 (issue close) | 43% |
| T1+T3 combined | 36% |
| T2 (merge) | 17% |
| T3 alone (push) | 14% |

4–5 of 6 total rejects concentrated in Sessions 5.5–10 (early-calibration). Recent 26 sessions: 1 reject. The layer's catch curve is decreasing as the parent has internalised rules — this is what §7.1 exists to detect going forward.

## Contract change

Single file: `docs/qa-contract.md` (+38 / -1).

- **§2 row 2 (T2)** — "Hard-block by default; advisory when the §2.2 carve-out conditions all hold."
- **§2.1** — combined T1+T3 invocation codified (S33+ de facto practice).
- **§2.2** — three categorical T2 carve-out conditions + rationale (cites #380) + fallback-to-hard-block.
- **§7.1** — rolling-window recalibration audit at Session-25 boundaries (ESACP-session-scoped); detection-only.
- **§10** — v2 revision row dated 2026-05-12 citing #380.

No change to the agent file, T1, T3-alone, T4, T5, §3, §4, §5, §8, §9.

## QA invocations

3 verdicts:

| # | Trigger | Invocation | Verdict | Outcome |
|---|---|---|---|---|
| 1 | T1+T3 combined on `607d34c` | `abb7d0d82982fc576` | `approve-with-conditions`, hard_block: true | 3 conditions addressed pre-commit |
| 2 | T2 on PR #381 | `a10b39026117b1dca` | `approve`, hard_block: true | 1 non-blocking cosmetic (issue title) fixed pre-merge |
| 3 | T1+T3 combined on session-close | (this commit) | (this row's verdict) | — |

## Activation semantics

v2 is active from `0137977a` forward. Agent file (`.claude/agents/esacp-qa.md`) unchanged; the layer's behavior is governed by the parent's reading of `docs/qa-contract.md` at trigger time. No retroactive effect on already-issued verdicts.

## Files at session-end

- `docs/qa-contract.md` — v2, merged via PR #381 mid-session at `0137977a`
- `docs/SessionLogs/2026-05-12-1117-session-minutes.md` (this file)
- `docs/SessionLogs/2026-05-12-1117-next-agenda.md` (Session 38 brief)
- `docs/qa-log.md` — Session 37 rows appended (3 rows)
- `martinhbramwell/ESACP#380` — auto-closed via cross-repo `fixes` (7th auto-close event)
- `martinhbramwell/ESACP/issues/373` — 7th-auto-close datapoint comment posted

## GH issue activity

| Issue | Action |
|---|---|
| #380 | Filed + auto-closed via PR #381 (`closedAt 2026-05-12T11:17:20Z`, 1s after merge) |
| #381 (PR) | Opened + squash-merged to main (`mergedAt 2026-05-12T11:17:19Z`) |
| #373 | 7th-auto-close datapoint comment posted |

## Plan-B Epoch-1 roadmap progress

Unchanged from Session 36. D3 (LSKB#7 — 22 DB-resident TBDs documentation) remains for Session 38+.

## Findings carried forward

- **v2 contract is live.** First T2 carve-out application will land in Session 38+ if a substantive PR is merged.
- **§7.1 first audit boundary** — at Session 50; ~13 sessions away.
- **Areas 1/2/4/5 deferred without tracker issues** — agenda's "others get tracker issues filed" rule overridden in-session per operator's clerical-reduction theme. The areas remain available for future introspection sessions; not filing speculative issues is itself an Area-4 application (memory/issue-surface restraint).
- **Trimmed session-close ceremony as introspection-lesson application.** S36 minutes were ~220 lines; this file is ~70. Tracking whether the trim affects Session 38's pickup quality.
