# Session Minutes — Ladder-Fixture Discovery + Umbrella Cut

**Date:** 2026-04-23 ~07:10–09:15 EDT
**Branch:** `main` (baseline) + `umbrella/ladder-fixture` (cut)
**Commits:** minutes + plan revision only (this session does not change any SUT/pipeline code)
**PRs:** none
**Issues closed:** none
**Issues opened:** #289 (bench ce_sri contamination), #290 (wizard es/MX posterity)
**Baseline:** entered at `main @ 3dbac2d` (2026-04-23 0620 minutes tip)

## Declared objective (revised mid-session)

**Original intent at session start:** execute Tier 0 of the open-issues-purge plan (#278 + #288 housekeeping bundle).

**Revised once contamination surfaced:** enumerate three findings
from dev01 inspection, file appropriate issues, cut the
`umbrella/ladder-fixture` branch, update the purge plan, produce a
revised first-rung readiness assessment. Tier 0 deferred until
umbrella certifies.

Zero SUT/pipeline code changes this session. Pure investigate +
file + structure + plan.

## What happened

### Session-start review

`bash platforms/kvm/sync_check.sh` — 46 ✅ / 11 ⚠️ / 0 ❌. All 11
warnings benign (dormant VMs expected-off, sops minor version nag,
Chrome-tab manual-verify reminder).

Open issues at entry: 18. Latest minutes read: `2026-04-23-0620`
(open-issues-purge ladder re-draft).

### Finding 1 — bench-level `ce_sri` contamination on dev01

Operator ran `bench start` against `/home/erpadm/frappe-bench-dev0`
and the log included:

```
07:12:13 system        | ce_sri_svc.1 started (pid=1751)
07:12:13 ce_sri_svc.1  | Launching from '/home/erpadm/frappe-bench/apps/ce_sri/services/ce_sri_svc'
07:12:16 ce_sri_svc.1  | Bind: port 3000
07:12:16 ce_sri_svc.1  | * * *  [ API Server : undefined://undefined:undefined/ ] * * *
```

Operator flagged: "This was supposed to be a 100% generic 0%
customized ERPNext installation."

Read-only probes (confirmed 2026-04-23):

| Layer | State | Verdict |
|---|---|---|
| `sites/apps.txt` | `frappe`, `erpnext` | ✅ clean |
| `sites/apps.json` | frappe v13.58.22 + erpnext v13.55.2 | ✅ clean |
| `bench --site dev01.iridium.blue list-apps` | `frappe`, `erpnext` | ✅ clean (DB) |
| `apps/` dir | `ce_sri, erpnext, frappe, returnable, route_planner` | ❌ contaminated |
| `Procfile` | contains `ce_sri_svc: apps/ce_sri/services/ce_sri_svc/go.sh` | ❌ contaminated |
| `/opt/ce_sri/envars.sh` | present; BaRe symlinks to it | ⚠️ architectural coupling |
| `BaRe/` | handleBackup.sh et al. present | ✅ wanted (per operator) |
| `BKP/` | missing — auto-created by handleBackup.sh line 39 | ✅ no action needed |

Single point of failure: `tools/pipeline/stages/stage_6_base_platform/platform_setup.sh`
(lines 11–15, 28–36, 38–52, 81–87) treats generic mode identical
to restore mode. Stages 3 / 7 / 8 / 9 honour
`provision_mode="generic"`; Stage 6 does not.

Filed as **#289**.

### Finding 2 — wizard fails post-completion on Español/Mexico locale

Operator attempted the ERPNext setup wizard with Spanish/Mexico
locale selection; failure declared after wizard completion. Log
excerpt shows `get_charts_for_country` and `validate_bank_account`
both return HTTP 200 — failure is downstream, not at the visible
API layer.

English/Canada succeeds on the same VM (and was what the
acceptance matrix used — `params/03-cli-pseudo-wizard.yml`:
`country: Canada, currency: CAD, language: en`).

**Scope decision** (operator-declared): posterity only. Ladder
regression suite scoped to en/Canada for all three rungs. Do NOT
debug this defect in the v13→v14→v15→v16 arc. Re-open with
fix-intent only when production-locale coverage becomes required.

Filed as **#290**.

### Finding 3 — company-logo prompt during wizard

Operator noted wizard invites a company logo. Confirmed this is
covered by closed issue #250 (won't-fix under generic-site scope
precedent, 2026-04-22). Playwright fixture handles this with a
[SKIP] click, per `feedback_generic_site_purpose`. No new scope,
no re-open — unchanged from 2026-04-22 decision.

### Matrix-closeout implication

Phases 03/04/06/07 (pseudo-company variant) declared the substrate
"generic" in `MATRIX-CLOSEOUT.md`. At site/DB level that claim
holds. At bench level it does not. `MATRIX-CLOSEOUT.md` needs a
post-fix erratum noting the bench-layer nuance. The matrix's
CLI↔UI parity verdicts remain valid (both sides ran on the same
contaminated substrate — apples-to-apples). Erratum tracked as
part of sub-branch 1 work, not filed separately.

### Umbrella `umbrella/ladder-fixture` cut

Decision criteria from `CLAUDE.md` all met:
- ≥3 sub-branches expected (contamination fix, Playwright fixture, restore-verify)
- Cross-cutting files (pipeline stage + prototypes + tests)
- Broad-context acceptance impossible per-sub-branch (fresh-VM destroy→build→wizard→backup→restore→verify end-to-end)

Branch cut, pushed with `-u`, operator-returned-to-main:

```
git checkout -b umbrella/ladder-fixture
git push -u origin umbrella/ladder-fixture
git checkout main
```

Per `feedback_umbrella_branches.md`: sub-branches merge to umbrella,
umbrella merges to main only at certification session with
explicit operator sign-off.

### Plan revision — `~/.claude/plans/open-issues-purge.md`

Inserted a new "Pre-Tier 0 — `umbrella/ladder-fixture`" section
ahead of Tier 0. Updated:

- Baseline: 18 open → 20 open (+#289, +#290)
- First move: `fix/bench-generic-provision-contamination` sub-branch (#289) off umbrella, not Tier 0
- Exit condition: umbrella certification now precedes Tier 0 in the unblock sequence
- Cost ledger: +4 sessions (3 sub-branches + 1 certification), +1 end-to-end matrix run
- Total projection revised: 7 sessions, ~3 matrix re-runs, ~2–3 hrs wall time

Appendix A (prior matrix-era plan) untouched — historical record.

## Audit (session-close)

1. **Forward-tense phrases** — all resolved:
   - "Sub-branches merge to umbrella" → durable home: plan file Pre-Tier 0 section + `feedback_umbrella_branches.md` (already exists).
   - "Playwright fixture delivered" → tracked as sub-branch 2 in plan file; no work promised *this session*.
   - "Restore-verify green" → tracked as sub-branch 3 in plan file; no work promised *this session*.
   - "`MATRIX-CLOSEOUT.md` needs erratum" → tracked as part of sub-branch 1 scope in plan file (not a loose promise).
   - "Re-open #290 when production-locale coverage is required" → captured in issue body and plan file.
2. **GH issue findings posted** — all new findings live on the issues themselves:
   - #289: bench contamination symptom + pipeline SPOF + acceptance criteria → full issue body.
   - #290: log excerpt + posterity scope → full issue body.
3. **PRs opened** — none. Nothing to verify `mergedAt` for.

## Files changed

| File | Change |
|---|---|
| `~/.claude/plans/open-issues-purge.md` | Pre-Tier 0 umbrella block inserted; baseline 18→20; first move revised to sub-branch 1; exit condition + cost ledger updated |
| `docs/SessionLogs/2026-04-23-0915-session-minutes.md` | this file |

Branches touched:
- `umbrella/ladder-fixture` — cut and pushed, empty (same tip as main at entry)
- `main` — minutes + plan only, committed at close

Issues opened:
- [#289](https://github.com/martinhbramwell/ESACP/issues/289) — bench ce_sri contamination (Stage 1 of umbrella)
- [#290](https://github.com/martinhbramwell/ESACP/issues/290) — wizard es/MX posterity

## State handed to next session

- `main @ <this minutes commit>` (after commit+push)
- `umbrella/ladder-fixture` at same tip, empty
- **Open issues: 20** (was 18; +#289, +#290)
- **First move:** cut `fix/bench-generic-provision-contamination` sub-branch off `umbrella/ladder-fixture`; 1:1:1 session for #289. Scope: gate Stage 6 on `provision_mode="generic"`, strip ce_sri/route_planner/returnable clones, keep BaRe, resolve `/opt/ce_sri/envars.sh` + BaRe symlink decision.
- Tier 0 (#278, #288) deferred until umbrella certifies.

## Reminders to operator (unresolved concerns)

1. **`/opt/ce_sri/envars.sh` disposition is undecided.** Sub-branch 1 must decide: delete (BaRe symlink points elsewhere or nowhere), rename to `/opt/generic/envars.sh` (update BaRe target), or keep as an innocuous env-var set (minimal scope). The decision belongs in that session, not pre-allocated.
2. **Sub-branches 2 and 3 will need new issues filed at the start of their sessions.** The plan file flags them as *(new — file at start of sub-N session)* rather than pre-filing here — they acquire meaningful scope only after sub-branch 1 lands.
3. **#284 race-class, #285 B06 regen, #202 cloud-init template** remain at their 2026-04-23 0620 positions (Tier 1). Umbrella does not absorb them.
4. **`project_upgrade_v13_to_v16.md` stub** is still parked. First-rung planning session happens after umbrella certification, per the 0620 minutes reminder carried forward.

## File trail

- Prior minutes: `docs/SessionLogs/2026-04-23-0620-session-minutes.md`
- Revised purge plan: `~/.claude/plans/open-issues-purge.md`
- Matrix closeout pointer (needs erratum in sub-1 session):
  `docs/SessionLogs/acceptance-matrix/MATRIX-CLOSEOUT.md`
- This minutes: `docs/SessionLogs/2026-04-23-0915-session-minutes.md`
- Issues: [#289](https://github.com/martinhbramwell/ESACP/issues/289), [#290](https://github.com/martinhbramwell/ESACP/issues/290)
