# V13→V14 Upgrade Trial — dev02 — Session 74 Notes

**Date**: 2026-05-22
**Branch**: `feat/428-v14-trial-dev02`
**Parent issue**: ESACP#428
**Plan file**: `~/.claude/plans/v14-trial-dev02.md`

## Pre-flight log

### Step 1 — `clearKnownHosts`

Ran `./tools/esacp.py clearKnownHosts`. Reported "3 removed" but `dev02.iridium.blue` entries on lines 73–75 of `~/.ssh/known_hosts` remained (hashed). SSH to `dev02.iridium.blue` failed with "Host key for dev02.iridium.blue has changed".

**Workaround**: `ssh-keygen -f ~/.ssh/known_hosts -R 'dev02.iridium.blue'` — removed 3 hashed entries directly.

**Defect classification**: tooling bug (NEW failure class for `clearKnownHosts` primitive — `known_hosts_entries` collects only bare hostname/nickname/IPs from `hosts_map.yml`, never the FQDN form `dev02.iridium.blue` that ansible / curl / manual SSH actually persist in `~/.ssh/known_hosts`). Filed as [ESACP#438](https://github.com/martinhbramwell/ESACP/issues/438). Not a V14-trial defect; not blocking.

### Step 2 — `sync_check`

Two runs gave different shapes (flapping):
- Run 1: 46 ✅ / 9 ⚠️ / 2 ❌ (dev01 unreachable; manual Chrome-tab warning).
- Run 2: 45 ✅ / 9 ⚠️ / 3 ❌ (dev01 shut off; dev02 ping unreachable; dev02 also failed).

Direct verification: `ping dev02.iridium.blue` returned 0% loss / 8ms RTT. The Run-2 dev02 failure is a transient race, not a real outage. dev01 truly is shut off (consistent with `feedback_dev_vms_are_disposable.md` — dev01 is irrelevant to this trial). Proceeded per operator decision #1 (sync_check tolerance = yes).

### Step 3 — Baseline capture

SSH alias used: `dev02-erp` (User=`erpadm`, IdentityFile=`~/.ssh/hasan_mighty`). Earlier connection via FQDN `dev02.iridium.blue` failed with "Too many authentication failures" — the FQDN does not match the `Host dev02` alias in `~/.ssh/config`, so SSH bypassed the IdentityFile directive and tried all agent keys (none of which dev02 accepts). Resolved by using the alias.

**Versions**:
- `bench --site dev02.iridium.blue version`:
  - `frappe 13.58.22`
  - `erpnext 13.55.2`
  - `ce_sri 0.0.1`
  - `returnable 0.0.1`
  - `route_planner 0.0.1`
  - `sales_partner_commissions 0.0.1`
- `bench --version`: `5.29.1`
- Python: `3.10.12`
- OS: Ubuntu 22.04.5 LTS

**App branches** (from `bench list-apps`):
- frappe / erpnext: `HEAD` (detached on v13 tags)
- returnable: `wip/2026-03-31`
- ce_sri: `wip/2026-03-25`
- route_planner: `wip/2026-03-31`
- sales_partner_commissions: `main`

**Row counts** (3 representative tables):
- `tabSales Invoice`: **22 433**
- `tabCustomer`: **1 803**
- `tabItem`: **312**

**HTTP**: `curl -sI https://dev02.iridium.blue/` → `HTTP 200`. Tenant homepage loads.

**`tabPatch Log` tail (most recent 8)**:

| # | Patch | Creation |
|---|---|---|
| 1 | `sales_partner_commissions.patches.v14_0.migrate_commissions_to_child_table` | 2026-05-21 15:42:17 |
| 2 | `frappe.patches.v12_0.delete_duplicate_indexes  # 2022-12-15` | 2026-05-21 15:42:00 |
| 3 | `execute:frappe.db.set_value("Accounts Settings", … "service_provider", "frankfurter.app")` | 2026-05-21 14:42:09 |
| 4 | `erpnext.patches.v13_0.correct_asset_value_if_je_with_workflow` | 2026-05-21 14:42:09 |
| 5 | `erpnext.patches.v13_0.update_docs_link` | 2026-05-21 14:42:09 |
| 6 | `erpnext.patches.v13_0.update_asset_value_for_manual_depr_entries` | 2026-05-21 14:42:08 |
| 7 | `erpnext.patches.v13_0.update_schedule_type_in_loans` | 2026-05-21 14:42:08 |
| 8 | `frappe.patches.v13_0.clear_large_email_queues` | 2026-05-21 14:42:07 |

**Phase 4 SPC patch present** ✓ (row #1 above — `migrate_commissions_to_child_table`).

### Step 4 — Snapshot

`./tools/esacp.py snapShotVM dev02 pre-v14-upgrade-trial-S74` **failed** with `error: failed to get domain 'dev02'`. Root cause: dispatcher calls `snapshot_ops` without `hypervisor=` kwarg, so virsh runs locally; dev02 lives on toshiba. Filed as [ESACP#440](https://github.com/martinhbramwell/ESACP/issues/440) — same root-cause class as #438 (primitives not consulting `hosts_map.yml` derived attributes).

**Workaround** (per S71 lighter-weight directive — raw virsh acceptable in lieu of primitive):

```
ssh toshy 'virsh --connect qemu:///system snapshot-create-as dev02 pre-v14-upgrade-trial-S74 --atomic --description "Pre V13->V14 upgrade trial S74 ESACP#428"'
```

Result: `Domain snapshot pre-v14-upgrade-trial-S74 created` in 19s (06:53:36 → 06:53:55).

### Step 5 — Snapshot list (confirmation)

```
ssh toshy 'virsh --connect qemu:///system snapshot-list dev02'
```

```
 Name                            Creation Time               State
----------------------------------------------------------------------
 Baseline                        2026-05-21 15:16:31 -0400   running
 ERPNext v13 Restored Baseline   2026-05-21 15:46:02 -0400   running
 pre-v14-upgrade-trial-S74       2026-05-22 06:53:39 -0400   running
```

Three restore points available. **Revert target for this trial**: `pre-v14-upgrade-trial-S74` (data-current; the older "ERPNext v13 Restored Baseline" snapshot is from the same day but pre-dates any patches applied since).

## Operator decisions locked at pre-flight close

1. **sync_check tolerance**: yes — proceed (acknowledged Run-2 flap is noise; dev02 reachable directly).
2. **Step 5 fail-mode**: revert immediately on `applySubstrateMigration` irrecoverable failure, then file failure class and plan per-class drill-down.
3. **Wall-clock budget**: 2hr cap on the upgrade sequence; revert + log + continue S75 if not at HTTP 200 by 2hr.

## Upgrade sequence log

### Step 1 — Stop services (06:57 → 06:58, ~2s)

Plan command `sudo supervisorctl stop frappe-bench-all` failed — group `frappe-bench-all` does not exist on this VM. Actual groups in `/etc/supervisor/conf.d/`:

- `ce-sri-svc.conf` → process `frappe-bench-ce-sri-svc`
- `frappe-bench.conf` → groups `frappe-bench-web`, `frappe-bench-workers`, `frappe-bench-redis`

Used `sudo supervisorctl stop all` instead. All 9 processes confirmed STOPPED via `supervisorctl status`.

**Defect**: plan-doc gap (not a code/V14 defect) — the `frappe-bench-all` group name in the plan is generic; the actual supervisor topology varies per VM. Captured for plan-file update post-trial.

### Step 2 — `bench switch-to-branch version-14 frappe erpnext --upgrade` (06:58 → 07:06, ~8 min)

```
SUCCESS: Successfully switched branches for: frappe, erpnext
[... yarn + snyk patches ... 40.65s ...]
Installing 6 applications...
  Installing frappe       ✓ (uv pip install --upgrade, then yarn build)
  Installing route_planner ✓
  Installing ce_sri        ✓
  Installing sales_partner_commissions ✓
  Installing returnable    ✗  (gunicorn URL-dep crash — #331)
Error occurred during app install: ...returnable...
BENCH_EXIT=167
```

**#331 behavior observation** — only `returnable` actually hit the gunicorn URL-dep crash. The other 3 bespoke apps (route_planner, ce_sri, sales_partner_commissions) installed cleanly **with full dependency resolution**. This is a narrower failure than the plan predicted (plan said all 4 needed the `--no-deps` workaround).

**Anomaly observation**: `erpnext` is NOT in the "Installing" list above. Either bench processed it before bespoke apps (silently re-run on already-v14 source), or it was skipped because frappe-erpnext share dep resolution. Not blocking; flagged for post-trial review (full log at `dev02:/tmp/v14-switch.log`).

### Step 3 — #331 workaround (07:07, ~8s)

```
for app in returnable ce_sri route_planner sales_partner_commissions; do
  uv pip install --quiet --no-deps -e apps/$app --python env/bin/python
done
```

All 4 bespoke apps + erpnext sanity check: exit 0. (3 of the 4 were already installed with deps from Step 2; the `--no-deps` install is idempotent.)

### Step 4 — `bench build` (07:07 → 07:08, ~28s)

```
DONE  Total Build Time: 22.303s
WARN  Cannot connect to redis_cache to update assets_json   [x3]
BUILD_EXIT=0
```

All asset bundles built (frappe + erpnext × js / web / css / css-rtl). Redis warnings non-fatal (services stopped per Step 1). Full log at `dev02:/tmp/v14-build.log`.

**No bespoke-app asset-build defects observed** — plan §Step 4 predicted possible ce_sri/returnable/route_planner JS/HTML failures against v14 frappe; none surfaced. (Possible they have no custom assets, or v14 changes were benign for their patterns.)

### Step 5 — `applySubstrateMigration dev02` — first attempt failed on redis prerequisite (07:10)

```
[OK] g1_seed_patch_log
[OK] g2_clear_fixture_custom_fields
[FAIL] bench migrate: rc=1
  stdout: Service redis_cache is not running.
```

**Plan-sequencing defect**: plan §Step 1 stops *all* services; plan §Step 5 invokes `bench migrate` which requires `redis_cache` running. `bench migrate`'s explicit precondition check fired immediately. Worked around by starting only the `frappe-bench-redis:` group (cache + queue), leaving web/workers stopped to avoid racing the migrate.

**Note for plan revision**: between Step 1 (stop all) and Step 5 (migrate), Step 4.5 needs to be "start redis only" (or Step 1 should be "stop everything except redis"). Capture for post-trial plan-file update.

### Step 5 — retry with redis up (07:12 → 07:23, ~11 min)

```
[OK] g1_seed_patch_log
[OK] g2_clear_fixture_custom_fields
[OK] bench migrate
✅  substrate migration applied
MIGRATE_EXIT=0
```

**Primitive-output gap**: `apply_substrate_migration._run_step` discards stdout/stderr on success — the entire `bench migrate` output (which patches applied, which were skipped, schema warnings, fixture conflicts) was lost. For a trial whose entire purpose is *capturing defects*, this is a planning + primitive gap. Captured for follow-up; not blocking.

**Verification (post-migrate, on dev02)**:

- `bench --site dev02.iridium.blue version`:
  - **frappe 14.101.1** ✓ (was 13.58.22)
  - **erpnext 14.92.14** ✓ (was 13.55.2)
  - All bespoke apps still present at 0.0.1 (returnable, ce_sri, route_planner, sales_partner_commissions)
- **Row counts unchanged**:
  - `tabSales Invoice`: 22 433 (same as baseline) ✓
  - `tabCustomer`: 1 803 (same) ✓
  - `tabItem`: 312 (same) ✓

**Patch-log timestamp anomaly** (unexplained — minor): `MAX(creation) FROM tabPatch Log` = `2026-05-22 06:21:34.639749`, which is *before* the migrate completed (07:23). Pre-flight baseline at 06:50 showed MAX(creation) = yesterday 15:42:17. So patches with 06:20-06:21 timestamps appeared between the baseline read and now, but with timestamps preceding both. Either (a) frappe v14's patch_handler backdates `creation` to a known reference time during initial v14-migrate, (b) my pre-flight query somehow missed pre-existing patches, or (c) a parallel process applied patches between baseline and migrate. Flagged for follow-up; not blocking — schema + data integrity confirmed by version + row counts.

### Step 6 — Restart services + HTTP smoke (07:36, ~16s)

`sudo supervisorctl start all` (instead of `frappe-bench-all` — see Step 1 note).

All 9 processes RUNNING:
- `frappe-bench-redis:` cache + queue (already up since the redis-prereq workaround)
- `frappe-bench-web:` frappe-web + node-socketio
- `frappe-bench-workers:` 4 workers (default, short, long, schedule)
- `frappe-bench-ce-sri-svc` (standalone)

```
curl -sI https://dev02.iridium.blue/        → HTTP 200 ✓
curl -sI https://dev02.iridium.blue/login   → HTTP 200 ✓
curl  https://dev02.iridium.blue/api/method/ping → {"message":"pong"} ✓
```

Tenant homepage loads. Login page renders. API responds.

**gunicorn 23.0.0** booted with 5 sync workers at 07:36:22 — no errors in `web.error.log` since restart.

### Step 7 — Phase 3 redis/rq verification (LSKB#5 result)

**redis-py: 3.5.3** ✓ matches LSKB#5 target.

**rq: 1.14.1** ✗ does **NOT** match LSKB#5 target (1.8.0). However:

- Workers booted cleanly (supervisor RUNNING, uptime stable).
- Worker log (`logs/worker.log`) shows >20 successful job completions in the first second after restart — frappe internal v14-cleanup jobs (`frappe.model.delete_doc.delete_dynamic_links` for retired Scheduled Job Types). All "Job OK".
- `logs/worker.error.log` mtime = 06:57 (Step 1 stop time) — ZERO new errors post-restart. All stack traces in that file are pre-session redis-disconnect noise from when supervisor was stopping.

**LSKB#5 verification result**: redis-py pin (3.5.3) matches and works fine. rq pin diverges (1.14.1 vs 1.8.0 target) but no observable regression against production data — workers process jobs cleanly, no redis-side errors. The rq-version divergence needs a deliberate decision (downgrade to 1.8.0 vs accept 1.14.1) — file as LSKB follow-up.

**Minor defect: `frappe.utils.background_jobs.get_workers`** returns `rq.worker.Worker` objects that `bench execute` cannot JSON-serialize. CLI-side display defect only; the function itself works.

**Minor pre-existing state**: `bench scheduler status` reports `Scheduler is disabled for site dev02.iridium.blue`. Disabled by operator pre-trial (not a v14 regression).

## Trial result — **SOMEWHAT SUCCESSFUL (per `feedback_progress_over_perfection_for_v14.md` bar)**

Per acceptance criteria in plan §"Acceptance criteria":

- [x] V13→V14 upgrade attempted end-to-end ✓
- [x] Every defect captured with command + classification ✓
- [x] **(a) dev02 reachable on V14 with site loading** ✓ (HTTP 200, login renders, API responds, workers process jobs)
- [x] Phase 3 redis/rq behavior observed and recorded ✓

**No revert needed.** dev02 is on v14, data intact, services healthy. Snapshot `pre-v14-upgrade-trial-S74` retained for re-runs.

Total wall-clock from Step 1 to "all green": 06:57 → 07:36 = **39 minutes** (well under the 2hr cap).

## Defect summary (NEW classification per plan defect-capture protocol)

| # | Class | Origin | Severity | Issue filed |
|---|---|---|---|---|
| 1 | tooling — clearKnownHosts misses FQDN entries | Pre-flight 1 | Annoyance | ESACP#438 |
| 2 | tooling — snapShotVM doesn't resolve hypervisor from hosts_map | Pre-flight 4 | Blocks remote-VM snapshot via primitive | ESACP#440 |
| 3 | plan-doc — `frappe-bench-all` is generic, doesn't match actual supervisor groups | Step 1 | Annoyance | (capture for plan-file update) |
| 4 | #331 narrower than predicted — only `returnable` actually crashed | Step 2 | Reduces future workaround burden | (memory update candidate) |
| 5 | plan-sequence — `bench migrate` requires redis_cache running, plan §Step 1 stops it | Step 5 | Cost: one retry | (capture for plan-file update; or add to substrate primitive to auto-start redis) |
| 6 | tooling — `applySubstrateMigration` discards bench-migrate stdout on success | Step 5 | Loses defect-capture surface for the trial's whole purpose | (NEW issue — file post-session) |
| 7 | unexplained — tabPatch Log creation timestamps for v14 patches are 06:20-06:21, before migrate ran (07:12-07:23) | Step 5 | Cosmetic; doesn't affect schema or data | (capture for review) |
| 8 | tooling — `bench execute frappe.utils.background_jobs.get_workers` JSON-serialize TypeError | Step 7 | Minor CLI-side display defect | (capture for review) |
| 9 | Phase 3 finding — rq is 1.14.1, not 1.8.0 per LSKB#5 target | Step 7 | Acceptance decision needed | (file LSKB follow-up) |

No defects from the plan's predicted classes (fixture_equivalent / discardable / human_review core edits / DocPerm clashes / patch_log v13-internal failures) — those may have been silently handled by the migration, or our primitive's stdout-discard meant they would not be visible. With #6 fixed, a re-run on the snapshot would reveal whichever applies.

## Final snapshot list (post-trial)

```
 Name                            Creation Time               State
----------------------------------------------------------------------
 Baseline                        2026-05-21 15:16:31 -0400   running
 ERPNext v13 Restored Baseline   2026-05-21 15:46:02 -0400   running
 pre-v14-upgrade-trial-S74       2026-05-22 06:53:39 -0400   running
```

Snapshot retained — operator may revert to v13 at any time via:
```
ssh toshy 'virsh --connect qemu:///system snapshot-revert dev02 pre-v14-upgrade-trial-S74'
```

---

## Exploratory extensions (operator-greenlighted scope expansion)

After Step 7 closed with HTTP-200 V14 success, operator asked whether to play out V14→V15 and V15→V16 as toy probes on the disposable dev02 substrate. Framing agreed:

- Informal probes within the V14 trial session — no separate plan files, no separate issues unless a new defect class surfaces.
- Snapshot between each step (revert insurance).
- Hard stop on cascading failures (>2 manual workarounds beyond the established `--no-deps` pattern → revert + stop).
- ESACP#428 remains the parent issue.

### Extension 1 — V14→V15 (07:58 → 08:09, ~11 min) — **SUCCESS**

Snapshot `post-v14-pre-v15-S74` taken first (insurance).

Steps mirrored V13→V14:

| Step | Result |
|---|---|
| Stop web + workers + ce-sri-svc (left redis up — Step-5 lesson learned) | ✓ |
| `bench switch-to-branch version-15 frappe erpnext --upgrade` | Frappe + erpnext switched ✓. Pip-install pass crashed on `returnable` again — but with a **different URL-dep**: `pypika @ git+https://github.com/frappe/pypika@2c50e614...` instead of v14's `gunicorn`. Same #331 shape, different package. (Exit 167.) |
| `--no-deps` workaround for 4 bespoke apps + erpnext sanity | All exit 0 (~6s total) |
| `bench build` | 42s, exit 0 |
| `applySubstrateMigration dev02` | OK (5.8 min — faster than v14's 11 min; smaller patch delta v14→v15 vs. v13→v14) |
| Restart all services | ✓ |
| Smoke (HTTP root / login / API ping) | All ✓ |
| Final version | **frappe 15.108.0 / erpnext 15.108.3** |

**Finding — #331 evolves**: the URL-dep package name varies per frappe major version. v13→v14 hit `gunicorn`, v14→v15 hit `pypika`. The `--no-deps` workaround is version-agnostic (works for both), but the canonical "open dep" name in `frappe/pyproject.toml` rotates.

**Finding — substrate has no v15-specific surprises** on this production data. Patches applied cleanly, services restarted clean, no worker-error noise.

### Extension 2 — V15→V16 (08:10 → 08:11, ~1 min attempt) — **HARD WALL**

Snapshot `post-v15-pre-v16-S74` taken first.

Stop web + workers + ce-sri-svc, then `bench switch-to-branch version-16 frappe erpnext --upgrade`:

**Defect A** (system-package — NEW class): `ERROR: pkg-config is not installed. Please install it before proceeding.` Bench's pre-install check fails immediately. Worked around with `sudo apt-get install -y pkg-config`.

Retry hit a more fundamental wall:

**Defect B — HARD BLOCKER**: frappe v16 source uses PEP 695 `type X = ...` syntax which requires **Python 3.12+**.

Exact trace:
```
File "/home/erpadm/frappe-bench/apps/frappe/frappe/__init__.py", line 93
    type ConfType = _dict[str, Any]  # type: ignore[no-any-explicit]
         ^^^^^^^^
SyntaxError: invalid syntax
```

dev02 ships with **Python 3.10.12** (Ubuntu 22.04 system Python). Working around this requires:
- Installing Python 3.12+ on dev02 (deadsnakes PPA, pyenv, or OS upgrade to 24.04), AND
- Rebuilding the bench venv on that interpreter, AND
- Re-installing all 6 apps in the new venv.

Outside the toy-probe scope. Reverted dev02 to snapshot `post-v15-pre-v16-S74`.

**Post-revert verification**: bench reports frappe 15.108.0 / erpnext 15.108.3, HTTP 200 — full restoration ✓.

### Aggregate findings (V14→V15→V16)

| # | Finding | Significance |
|---|---|---|
| E1 | #331 evolves per major: gunicorn (v14) → pypika (v15). `--no-deps` workaround is version-agnostic. | Reduces uncertainty for future trials |
| E2 | V14→V15 succeeded with same pattern as V13→V14 — no v15-specific surprises | Plan B Phase 5 (assumed v14 cutover) could be re-scoped to "v15 cutover" with marginal risk |
| E3 | V15→V16 requires **system pkg-config** + **Python 3.12+** | V16 needs OS-substrate work, NOT just frappe-side prep. Captures a real epoch-3 cost. |
| E4 | dev02 currently on v15 (per operator decision — see below). Both pre-v14 and post-v15 snapshots retained. | Future Plan B phases can pick v13/v14/v15 starting points cheaply. |

### Final snapshot list (post-exploration)

```
 Name                            Creation Time               State
----------------------------------------------------------------------
 Baseline                        2026-05-21 15:16:31 -0400   running
 ERPNext v13 Restored Baseline   2026-05-21 15:46:02 -0400   running
 pre-v14-upgrade-trial-S74       2026-05-22 06:53:39 -0400   running
 post-v14-pre-v15-S74            2026-05-22 07:57:53 -0400   running
 post-v15-pre-v16-S74            2026-05-22 08:09:42 -0400   running
```

Five restore points covering every major-version transition on this VM. Operator may revert to any.

### Session-level state for handoff (after first V15→V16 attempt)

dev02 currently on **frappe 15.108.0 / erpnext 15.108.3** with full production data + all bespoke apps. HTTP 200, services healthy.

---

## Extension 3 — V16 on a current substrate (11:08 → 11:46, ~38 min) — **partial; halted at v16 schema patch defect**

After the operator articulated the long-term end-state (see [[end-state-v16-lts-current-stack]] in memory), explored the "quick" path to v16 on the existing 22.04 substrate: install newer Python via deadsnakes PPA, rebuild bench venv on it, retry v16.

Snapshot taken first: `pre-py312-rebuild-S74` (v15 on python3.10 baseline).

### What worked

| Step | Result |
|---|---|
| Install Python 3.12 from deadsnakes | ✓ 40s |
| `mv env env-py310` + `bench setup env --python python3.12` | ✓ Created new env, installed frappe v15 in it |
| `bench setup requirements` | Hit pypika URL-dep on returnable (same #331 shape) |
| `--no-deps` workaround for **5 apps** (`returnable`, `ce_sri`, `route_planner`, `sales_partner_commissions`, **erpnext** — overcorrection — see Defect E5 below) | All exit 0 |
| Restart + verify v15 on python3.12 | HTTP 200 ✓ — **v15 runs on python3.12 without modification** |
| Attempt `switch-to-branch v16` | **NEW finding: frappe v16.18.3 pyproject pins `Python>=3.14,<3.15`** — not just ≥ 3.12 |
| Install Python 3.14 from deadsnakes | ✓ 15s (3.14.5) |
| `bench setup env --python python3.14` | ✓ Created env, installed frappe v16.18.3 |
| `bench setup requirements` | **NEW finding: frappe v16 requires Node ≥ 24** (`engines.node` in package.json). dev02 had Node 18.20.8 |
| Install Node 24 via NodeSource repo | ✓ 24.15.0 |
| `bench setup requirements` (retry) | Hit pypika URL-dep on returnable (consistent with v14/v15) |
| `--no-deps` workaround for 5 apps | All exit 0 — but this **broke erpnext deps** (see Defect E6 below) |
| `bench build` | ✓ 49s, exit 0 |

All 6 v16 apps installed in env (frappe 16.18.3, erpnext 16.19.1, 4 bespoke at 0.0.1).

### Where it halted: real v16 patch defect

`applySubstrateMigration dev02` → bench migrate failed twice:

**Failure 1**: `No module named 'mt940'` — erpnext's bank-statement-import dep was missing because erpnext got `--no-deps`'d. Fixed: `env/bin/pip install mt940`.

**Failure 2** (the real wall): Direct `bench migrate` with full stdout captured the exact patch:

```
File "/home/erpadm/frappe-bench/apps/erpnext/erpnext/patches/v16_0/make_workstation_operating_components.py", line 65, in execute
    doc.save()
  File ".../frappe/model/document.py", line 1102, in validate_update_after_submit
    self._validate_update_after_submit()
frappe.exceptions.UpdateAfterSubmitError:
  Not allowed to change Operating Components Cost after submission from 0 to 3
```

The v16 patch `make_workstation_operating_components` calls `doc.save()` on a submitted document, attempting to backfill `Operating Components Cost` from 0 to 3. Frappe's `validate_update_after_submit` blocks this because the field isn't whitelisted as `allow_on_submit`. This is an upstream erpnext defect — the patch should use `frappe.db.set_value(...)` (bypasses validation) OR add `ignore_update_after_submit=True` to `doc.save()`, OR mark the field `allow_on_submit`.

Patch log file: `apps/erpnext/erpnext/patches/v16_0/make_workstation_operating_components.py`.

### Aggregate findings — V15→V16 substrate distance

| # | Finding | Action |
|---|---|---|
| E5 | frappe v16 pins **Python >=3.14, <3.15** (not just 3.12+) | Capture in memory; saconsole / packer template for the v16 era must ship Python 3.14 |
| E6 | frappe v16 requires **Node >= 24** (declared in `apps/frappe/package.json` engines) | Capture in memory; saconsole / packer template must ship Node 24 |
| E7 | `pkg-config` missing on Ubuntu 22.04 baseline — needed for v16 frappe pip install | Add to base image / ansible role |
| E8 | erpnext v16 needs `mt940` Python package; gets missed when `--no-deps` is overcorrected | Refine the workaround: `--no-deps` only for `returnable`, not the other apps |
| E9 | `pypika` URL-dep crash on `returnable` consistent v14→v15→v16. NOT a v16-specific issue — `returnable` claiming `frappe` as dep + frappe's pyproject URL-deps = the actual root cause | The proper fix is to drop frappe from returnable's deps OR remove URL-deps from frappe upstream. Either way — file as a known bespoke-app pattern issue |
| E10 | **Real v16 patch defect**: `erpnext.patches.v16_0.make_workstation_operating_components` cannot save on submitted docs. **Halts v16 migration.** | File as defect / file with upstream erpnext / skip via patch_log seed in g1; decide policy |

### V16 substrate readiness — closer-than-expected

The end-state-v16-lts-current-stack memory paints the destination. Distance from there to here, today:

- ✓ Python 3.14 — can install on 22.04 via deadsnakes; Ubuntu 26.04 ships its own; one apt-line away
- ✓ Node 24 — NodeSource has it for 22.04; latest LTS shipping on most current OSes
- ✓ pkg-config + build deps — one apt-install
- ✓ mt940 + other transitive Python deps — work with `bench setup requirements` once `--no-deps` is scoped to `returnable` only
- ✗ Bespoke-app `returnable` declares unpinned `frappe` dep that hits URL-deps — needs fix in returnable's setup
- ✗ erpnext v16 `make_workstation_operating_components` patch crashes on submitted-doc save — needs upstream fix OR documented local skip

The substrate work is mostly mechanical. The blockers are **one upstream patch defect** + **one bespoke-app pattern fix**. Both are catalogable.

### Snapshot state after Extension 3

```
 Name                            Creation Time               State
----------------------------------------------------------------------
 Baseline                        2026-05-21 15:16:31 -0400
 ERPNext v13 Restored Baseline   2026-05-21 15:46:02 -0400
 pre-v14-upgrade-trial-S74       2026-05-22 06:53:39 -0400
 post-v14-pre-v15-S74            2026-05-22 07:57:53 -0400
 post-v15-pre-v16-S74            2026-05-22 08:09:42 -0400
 pre-py312-rebuild-S74           2026-05-22 11:09:13 -0400
```

dev02 **currently** in a mid-v16-migration state: env on python3.14 with v16 apps, schema migration halted on `make_workstation_operating_components`. Recoverable to v15 via `pre-py312-rebuild-S74` snapshot.
