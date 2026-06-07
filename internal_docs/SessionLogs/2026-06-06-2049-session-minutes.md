# 2026-06-06 2049 — Session 107 minutes

## Objective (operator-pinned)

**#631 — version-parameterize the Packer build → produce `template_v15` → provision `dev15_01`
(Beaverdam V15 baseline).** First executable increment of the S106 V15-baseline / dual-template
plan. **Fully achieved**: dual-template build shipped, dev15_01 provisioned + acceptance-verified,
merged to main, #631 closed.

## Class

Substantive 1:1:1 pipeline session. One issue (#631), one branch (`feat/631-template-v15`), direct
to main via PR #638. Two follow-up issues filed mid-session (#636 fixed in-branch; #637 deferred).
Not an introspection-sidebar (no MEMORY.md indexing edits; LogiSoluMemory updated separately).

## What happened

### Pre-flight
sync_check 45✅/10⚠️/2❌ — both ❌ are dev02 (parked V16 box, expected-down per agenda); not real
failures. Issues ESACP 85 / LSKB 13 (matched agenda). TRIVIAL_FIXES: 1 monitor-only entry. Branch
cut from `main`.

### Root finding
The build was *already* branch-parameterized (`build.sh --frappe-branch/--erpnext-branch`, HCL
vars). What was hardcoded to `erpnext-v13` was the **artifact name, metadata filename, and the
single-template clone** — so a v15 build would collide with / mislabel v13, and the provision side
had no way to pick a template. That hardcoding was the work.

### #631 — dual-template parameterization (commit `eee25a5`)
- **build.sh**: derive `VERSION_MAJOR` from `--frappe-branch` (validated numeric) → artifact
  `erpnext-v{MAJOR}-DATE.qcow2` + metadata `erpnext-v{MAJOR}-latest.json` + `version_major` in JSON.
  v13/v15/v16 now coexist as independent templates.
- **03_dep_fix.sh** guarded to the v13 line (its setuptools/urllib3 pin would downgrade a healthy
  v15 env). Node 18 + Python 3.10 from 01_os_prep are adequate for v15 (no substrate gap).
- **Selector = `target_frappe_major`** (existing per-host attr, default 13): threaded through
  `template_metadata` (`metadata_basename/path(major)`) → `clone_template(major)` →
  `run_stage_1(target_major)` → both macros (`target_frappe_major(host_cfg)` accessor). v13 path
  unchanged.
- Build trigger threads the branch through `build_template` / `job_worker` / API (`BuildTemplateReq`).
- **dev15_01** added to hosts_map (virbr0 .28, wg .18, `target_frappe_major: 15`); inventory regen.
- 6 colocated tests (`test_template_metadata.py`). esacp-qa approve-with-conditions (both met).

### #636 (NEW) — version-label the post-provision snapshot (commit `1f02e2e`, fixes #636)
QA flagged the duplicated `_take_final_snapshot` in both macros hardcoding "ERPNext v13 … Baseline"
(would mislabel dev15_01). Operator chose to fold the fix in. **Deleted** the duplicated helper from
both macros, delegated to the existing `snapshot_ops.create_snapshot` primitive with a
version-derived name. Side-effect: both macros dropped **under** the 80-line cap (87→69, 93→75),
clearing the grandfathered over-cap violation. esacp-qa approve.

### Acceptance — RUN on the real substrate
- v15 Packer template built on the hub (~8 min build + autoinstall): `erpnext-v15-latest.json`
  (version_major 15, frappe/erpnext version-15) + `erpnext-v15-2026-06-06.qcow2`. **v13 template
  intact alongside — dual-template coexistence proven.** 03_dep_fix correctly skipped on the v15 line.
- Live pipeline selected v15: `Template line: v15 (erpnext-v15-latest.json)` → cloned to
  `dev15_01.qcow2` (selector works end-to-end).
- dev15_01 (generic/clean, stages 1–9, no wizard): **HTTPS 200**; frappe `v15.110.0` + erpnext
  `v15.110.0`; currentsite `dev15_01.iridium.blue`.
- Snapshot: the run (pre-#636 code) stamped "ERPNext v13 Generic Baseline"; deleted + re-took
  **"ERPNext v15 Generic Baseline"** via the fixed primitive. dev15_01 now: `Baseline` +
  `ERPNext v15 Generic Baseline`.

### #637 (NEW, deferred) — build_template false-failure
job_worker reported "build.sh exited with code 1" ~5 min before the build actually finished
(succeeded). Root cause: the poll's `cat .exit || echo -1` runs *remotely*; on a transient SSH/
ProxyJump blip the transport returns **empty** stdout, which isn't the `-1` sentinel, so
`"".isdigit()` is False → `exit_code` defaults to 1 → false `RuntimeError`. Build is nohup-detached
on the hub so it completes regardless. Filed #637 with the fix (treat empty/non-numeric as
transient). Not in #631 scope (pre-existing; own 1:1:1).

### Scope reconciliation (operator-decided)
#631's "bespoke apps installed" clause conflicts with the operator-confirmed **generic/clean**
path: generic mode skips ce_sri/returnable/route_planner by design, and those clone from v13-era
`wip/2026-*` branches (not v15-ported). Operator chose the clean baseline as #631-complete;
**bespoke-apps-on-v15 is downstream migration work (#480 re-target / Plan B)**. Recorded in the
#631 close comment.

### Merge + close
WG keypair for dev15_01 committed (`bf20b52`). PR #638 → main (merge `14e7642`, mergedAt set).
#631 + #636 auto-closed. #631 close comment records acceptance + reconciliation + hashes. esacp-qa
approve at pre-merge. Branch `feat/631-template-v15` kept (no prune).

## Outcomes
- **#631 CLOSED** — dual-template build + dev15_01 v15 baseline, acceptance-verified.
- **#636 CLOSED** — snapshot version-label fix (folded in).
- **#637 OPEN** — build_template false-failure poll bug (deferred, 1:1:1).
- dev15_01 is the live clean v15 baseline; the V13→V15 migration script will target it.
- Dual-template capability lives in build.sh + pipeline + hosts_map (saconsole fleet record).

## esacp-qa ledger
approve-with-conditions (#631 pre-commit, both met) · approve (#636 pre-commit) · approve
(pre-merge, hard_block=true marker only — no operational effect on approve).
