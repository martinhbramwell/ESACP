# 2026-04-29 1435 — Session minutes

## Objective

Land #318 (`fix(audit): enumerate_only classes should emit promotion_strategy=none, not manual`) — the smallest meaningful step from the 2026-04-29 1315 agenda's recommended sequencing, chosen to keep the round-trip-clean track moving without committing to the full #318→#322→#319→Phase-2 sequence.

## State at session start

- main tip: `9b5172a` (docs commit on top of #321 merged)
- 24 open issues
- dev01: real-prod-data substrate UP (HTTPS 200), `ERPNext v13 Restored Baseline` snapshot retained — used directly, no re-provisioning
- dev02: V14-baseline shut off (expected per `feedback_one_vm_at_a_time.md`)
- sync_check: 46 ✅ / 8 ⚠️ / 2 ❌ — both ❌ are dev02 shut-off, pre-flight predicted

## What happened

### Branch + minimal-fix scope

Branch `fix/enumerate-only-strategy-none-318` cut from main. Operator's own comment on #318 recommended the minimal-fix scope (literal `MANUAL` → `NONE`); proceeded with that, deferring the wider attribution-lookup wiring to whichever future issue actually consumes per-name attribution on enumerate_only classes.

### Edits

| File | Change |
|---|---|
| `tools/customisation_audit/discover_custom_doctype.py:26` | `PromotionStrategy.MANUAL.value` → `PromotionStrategy.NONE.value` |
| `tools/customisation_audit/discover_server_script.py:26` | same |
| `tools/customisation_audit/test_discover_custom_doctype.py:21` | assertion `"manual"` → `"none"` |
| `tools/customisation_audit/test_discover_server_script.py:21` | same |

Total: 4 files, 4 insertions / 4 deletions.

### Verification

- 18/18 colocated audit tests green (`tools/customisation_audit/test_*.py`)
- End-to-end discovery against dev01 substrate confirmed:

| Metric | Pre-#318 (post-#320 baseline `/tmp/delta_report_dev01_post320.json`) | Post-#318 (`/tmp/delta_report_318_post.json`) | Δ |
|---|---|---|---|
| total drifts | 360 | 360 | 0 |
| by_verdict.enumerate_only | 9 | 9 | 0 |
| by_strategy.manual (computed) | 228 | 219 | **−9** |
| by_strategy.none (computed) | 120 | 129 | **+9** |
| unmapped (manual + empty owner) | 228 | 219 | **−9** |

Issue body's `231→222` numbers were a pre-#320 baseline; transition magnitude (−9) matches exactly. Acceptance criterion #4 references `summary.by_strategy` which the current summary structure doesn't include — verified by computing manually from `drifts[*].promotion_strategy`. Posted as comment on #318 (issue-comment-4344715278).

### Commit + PR

- Commit `1b61527` on `fix/enumerate-only-strategy-none-318`, GPG-signed, conventional, `fixes #318`, Co-Authored-By trailer
- Pushed to origin
- **PR #323 opened**: https://github.com/martinhbramwell/ESACP/pull/323

## State at session close

- Branch `fix/enumerate-only-strategy-none-318` @ `1b61527`, pushed
- **PR #323 OPEN, `mergedAt: null`** — fix is complete on branch but #318 is NOT marked DONE per `feedback_pr_merge_before_session_close.md`
- main tip unchanged: `9b5172a`
- 24 open issues (no new issues filed; no issues closed)
- dev01: substrate still UP (HTTPS 200), snapshot retained — usable for next session without re-provisioning
- dev02: still shut off

## Issue ledger delta

| Issue | Status change |
|---|---|
| #318 | OPEN → fix-implemented, PR #323 awaiting merge. **NOT yet closed.** Closes on merge of PR #323. |
| All others | unchanged |

## Forward-tense audit (run before writing these minutes)

| Phrase used | Resolution |
|---|---|
| "Cut branch …off main" | Executed: `git checkout -b` |
| "Edit 4 files" | Executed: 4× Edit calls |
| "Run colocated tests" | Executed: 18/18 green |
| "Acceptance: re-run discovery on dev01" | Executed: report at `/tmp/delta_report_318_post.json` |
| "Commit `fixes #318` … PR" | Executed: commit `1b61527`, PR #323 |
| "merge, close issue" | NOT executed — operator gate; carry-forward state |
| "holding 'done' until mergedAt is non-null" | Honoured — these minutes do NOT mark #318 DONE |

No unresolved forward-tense promises.

## Memory updates

None this session. The minimal-fix-vs-wider-fix tradeoff was already captured in operator's comment on #318; nothing new to abstract.
