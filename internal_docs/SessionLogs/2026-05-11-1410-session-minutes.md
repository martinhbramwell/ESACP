# 2026-05-11 1410 — Session 33 minutes

## Stated objective at session start

Per `2026-05-11-1013-next-agenda.md` (operator selected Candidate B):
**Consolidate `returnable` `wip/*` work onto `main` via a 1:1:1 sub-branch
on the returnable repo, file the consolidation tracker issue, and execute
the Track C step 5 dev02 repoint per Session 31's
`feedback_ssh_askpass_for_bespoke_repos.md` procedure** — direct equivalent
to Session 30's route_planner pilot.

## How the session went

Substantive — and a meaningful pre-flight pivot. The agenda assumed the
returnable repo was at `martinhbramwell/returnable`. Pre-flight 404 revealed
the actual repo is `martinhbramwell/BtlMng` (the app is named `returnable` on
the bench; the repo name is different). Default branch on BtlMng is `master`,
not `main`. Operator approved scope-correcting Session 33 to **Phase-2-only
consolidation onto `master`**, deferring Phase 8 production-baseline + the
`master`→`main` rename as separate decisions.

A second finding surfaced mid-session: `platforms/kvm/bucket_survey.py:13`
(the canonical source the bucket_definitions.md memory mirror reflects) also
carried the stale `martinhbramwell/returnable` reference. Filed and fixed
in-session as ESACP #378 — direct-to-main on ESACP, smoke-tested against
live GitHub before merge.

Net: two substantive ESACP issues filed, both closed via auto-close. One
BtlMng PR merged. One ESACP PR merged. One LogiSoluMemory commit landed.
Track C step 5 fetch-half executed cleanly on dev02; checkout+migrate
deferred per the master-behind-wip carve-out documented in
`project_wip_consolidation_plan.md`.

## Pre-flight

- `bash platforms/kvm/sync_check.sh` — 45 ✅ / 9 ⚠️ / 2 ❌. Both ❌ are the
  documented `dev01` carve-out (#278). Expected per Sessions 17+.
- `gh issue list --repo martinhbramwell/ESACP --state open --limit 100 --json number --jq 'length'`
  — 36 open at session start (agenda expected 37 — drift of 1, no
  operational impact).
- Read agenda + Session 32 minutes. Operator selected Candidate B
  ("returnable wip-consolidation"). Stated objective acknowledged.

## Sub-task execution

### Sub-task 1 — Pre-flight reads + repo identity pivot

Read `project_wip_consolidation_plan.md` Track A + LSKB#10 (Phase 8
elimination tracker) + `feedback_ssh_askpass_for_bespoke_repos.md` + Session
30's route_planner PR #1 metadata as template.

`gh api repos/martinhbramwell/returnable/branches` → **404 Not Found**.
Investigation: `gh repo list martinhbramwell` returns no `returnable`; GitHub
search reveals `martinhbramwell/BtlMng` ("ERPNext module for serial numbered
returnable containers"). dev02 confirms: bench has app `returnable` with
remote `https://github.com/martinhbramwell/BtlMng.git`.

Branch state on BtlMng: 6 branches — `master` (default, `707d661c`),
`wip/2026-03-31` (`b7a50f3`, dev02 currently here), plus 4 stale-named
historical branches.

Profile mismatch with route_planner pilot: returnable's wip Phase 1 work
(`e8a50c8`, SI commission fields) was reverted on wip by `9aa21e4`. Only
Phase 2 (`b7a50f3`) + Phase 8 (`65985ec`) content remains.

Operator approved scope-correcting Session 33 to Phase-2-only consolidation
onto `master`. Phase 8 deferred (gated on Plan B Phase 7 + CloudStack per
LSKB#10); `master`→`main` rename deferred (separate decision).

### Sub-task 2 — File ESACP #377 + cherry-pick + PR + merge

Filed [ESACP #377](https://github.com/martinhbramwell/ESACP/issues/377) —
`chore(consolidation): returnable (BtlMng) wip-consolidation — Phase 2
staged drift promotions onto master`. Body approved verbatim by operator
(first-of-class for BtlMng repo).

Inspected `b7a50f3` content: 2 files changed, +13 lines total
(`returnable/fixtures/custom_field.json` +9 lines, one new Custom Field;
`returnable/translations/es.csv` new file, 4 rows). Cleanly isolated from
the Phase 8 baseline content.

Cherry-picked `b7a50f3` onto `feat/377-wip-consolidation-phase-2` (off
`master`). Amended commit message to add consolidation context + `fixes
martinhbramwell/ESACP#377` keyword in body. Commit `08d6101`, GPG-signed
(G).

QA Trigger 1 (advisory, retrospective) + Trigger 3 (hard-block, push) —
combined invocation. Verdict: `approve`, `hard_block: true`. Pushed
`feat/377-wip-consolidation-phase-2` to origin.

Opened [BtlMng PR #1](https://github.com/martinhbramwell/BtlMng/pull/1). PR
body mirrors Session 30 route_planner PR #1 structure adapted for the
Phase-2-only scope.

QA Trigger 2 (hard-block, pre-merge). Verdict: `approve`, `hard_block:
true`. Squash-merged with `--delete-branch=false`. Merge commit
`8bd44620`, `mergedAt: 2026-05-11T17:39:07Z`.

**ESACP #377 auto-closed at `2026-05-11T17:39:09Z`** (2 seconds after
merge) via cross-repo `fixes` keyword in commit body. Another data point
for #373 (Session-31 finding confirmed in Session 32; now also confirmed
in Session 33).

### Sub-task 3 — Track C step 5 (dev02 repoint, fetch-half only)

Found dev02's returnable clone uses HTTPS (BtlMng is public) — the
SSH_ASKPASS preamble from `feedback_ssh_askpass_for_bespoke_repos.md` does
not apply (deploy keys exist for ce_sri / ce_sri_svc / route_planner only).

Plain fetch on dev02:
```
ssh dev02 'sudo -u erpadm bash -c "cd /home/erpadm/frappe-bench/apps/returnable && git fetch origin --prune"'
```
Result: clean — `origin/master` advanced `707d661..8bd4462`; new ref
`origin/feat/377-wip-consolidation-phase-2` pulled.

Checkout+migrate deferred as planned: `master` (Phase 2 content only) is
behind `wip/2026-03-31` (Phase 2 + Phase 8). Per the master-behind-wip
carve-out, deferred until Phase 8 consolidation lands.

### Sub-task 4 (mid-session insertion) — File ESACP #378 + fix bucket_survey.py

During the memory-update pre-flight for #377 acceptance criterion 4,
discovered `platforms/kvm/bucket_survey.py:13` references
`martinhbramwell/returnable` as the canonical source for `tenant_business_apps`
bucket. The memory file `bucket_definitions.md` line 28 mirrors it.
Fixing memory without code would create inconsistency in the opposite
direction.

Surfaced to operator (option 1 in offered choices: file new ESACP issue +
fix in this session). Filed
[ESACP #378](https://github.com/martinhbramwell/ESACP/issues/378). Branch
`fix/378-bucket-survey-btlmng` off main, one-line edit
(`martinhbramwell/returnable` → `martinhbramwell/BtlMng`). Commit
`0342929`, GPG-signed (G).

QA Trigger 1+3. Verdict: `approve-with-conditions`. Condition: smoke test
before merge (Trigger 2). Pushed.

**Smoke test** (manual acceptance per
`feedback_acceptance_test_required.md`):
```
python3 -c "from bucket_survey import survey_buckets; print(survey_buckets(['tenant_business_apps']))"
```
Returned real survey output for both `martinhbramwell/route_planner` and
`martinhbramwell/BtlMng`, including this session's just-merged `8bd4462`
on BtlMng's master. No 404. Acceptance test satisfied.

Opened [ESACP PR #379](https://github.com/martinhbramwell/ESACP/pull/379).
QA Trigger 2. Verdict: `approve`, `hard_block: true`. Squash-merged.
Merge commit `6910f48f`, `mergedAt: 2026-05-11T17:58:00Z`.
**ESACP #378 auto-closed at `2026-05-11T17:58:01Z`** (1 second after
merge).

### Sub-task 5 — LogiSoluMemory companion commit

Updated `bucket_definitions.md` line 28 (mirror of canonical
bucket_survey.py dict) + `project_wip_consolidation_plan.md` (added "Repo
identity" sub-bullet clarifying app→repo mapping for bucket-2 apps + noting
BtlMng default branch is `master`).

Commit `a2c2fa6`, GPG-signed. Pushed `LogiSoluMemory` `main`.

## Files at session-end

- `docs/SessionLogs/2026-05-11-1410-session-minutes.md` (this file)
- `docs/SessionLogs/2026-05-11-1410-next-agenda.md` (Session 34 brief)
- `docs/qa-log.md` — Session 33 rows appended (4 verdicts: Trigger 1+3 on
  BtlMng commit; Trigger 2 on BtlMng PR#1; Trigger 1+3 on ESACP #379
  commit; Trigger 2 on ESACP PR#379)
- `martinhbramwell/BtlMng/pull/1` — Phase-2 consolidation, MERGED
  `8bd44620`
- `martinhbramwell/ESACP/issues/377` — auto-closed via cross-repo `fixes`
  keyword
- `martinhbramwell/ESACP/pull/379` — `bucket_survey.py` source-of-truth
  fix, MERGED `6910f48f`
- `martinhbramwell/ESACP/issues/378` — auto-closed via `fixes` keyword
- `martinhbramwell/LogiSoluMemory/commit/a2c2fa6` — bucket_definitions.md
  mirror + project_wip_consolidation_plan.md app-to-repo note

## GH issue activity

| Issue | Action | URL |
|---|---|---|
| ESACP #377 | Created (BtlMng Phase-2 consolidation tracker) + auto-closed via merge | https://github.com/martinhbramwell/ESACP/issues/377 |
| ESACP #378 | Created (bucket_survey.py drift) + auto-closed via merge | https://github.com/martinhbramwell/ESACP/issues/378 |

## QA invocations (this session)

4 verdicts, all approve / approve-with-conditions. Details in `docs/qa-log.md` Session 33 rows.

## Operator-decided sequencing notes

- **Repo identity correction**: memory drift between app name (`returnable`) and repo name (`BtlMng`) discovered + corrected in canonical source + mirror in same session. Pattern reusable for future apps where similar drift may exist.
- **Phase-1 absence on returnable**: noted in Session 33; the Track A table's existing Phase 1 row already lists only ce_sri + route_planner sources (returnable absent), so the table is structurally accurate. The "Repo identity" sub-bullet added to `project_wip_consolidation_plan.md` adds explicit app→repo clarification.
- **`master`→`main` rename on BtlMng**: parked as separate decision; not filed as an issue this session (low-pain, latent).
- **Plan B Phase 2 LSKB sub-issue creation**: deferred (no Plan B execution decisions made this session — consolidation lands BtlMng-side content without LSKB-side sub-issue).
