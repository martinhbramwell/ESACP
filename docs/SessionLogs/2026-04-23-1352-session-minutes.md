# Session Minutes — #289 Sub-1: Stage 6 Generic-Mode Gate

**Date:** 2026-04-23 ~12:15–13:52 EDT
**Branch on main:** unchanged — this session's code landed on umbrella
**Branches touched:**
- `fix/bench-generic-provision-contamination` (sub-branch 1 of umbrella/ladder-fixture) — new, merged, retained per `feedback_keep_merged_branches.md`
- `umbrella/ladder-fixture` — advanced from `3dbac2d` to `9c66ccf` (merge of PR #291)
- `main` — only this minutes file
**Commits on the sub-branch:** `bc1742d` (fix) + `9c66ccf` (merge)
**PRs:** **#291 merged** to `umbrella/ladder-fixture` at 2026-04-23T17:52:37Z (mergedAt non-null — satisfies `feedback_pr_merge_before_session_close.md`).
**Issues closed:** **none** — #289 remains OPEN on the tracker because `fixes #289` only auto-closes on merge-to-default (main). It will close when the umbrella certifies. This is the expected umbrella pattern.
**Issues opened:** none
**Baseline:** entered at `main @ def32bf` (2026-04-23 0915 minutes tip)

## Declared objective

Cut sub-branch `fix/bench-generic-provision-contamination` off
`umbrella/ladder-fixture`, fix #289 (Stage 6 bench-level ce_sri
contamination in generic mode), merge back to umbrella, open
PR, carry the MATRIX-CLOSEOUT.md erratum. Not touching main
directly. One objective, 1:1:1 discipline maintained.

## What happened

### Session-start review

- `sync_check`: 46 ✅ / 11 ⚠️ / 0 ❌. All 11 warnings benign (dormant
  dev02/dev03/target5, Chrome-tab manual-verify, sops minor-version
  nag).
- Open issues at entry: 20. Latest minutes read: 2026-04-23 0915.
- Objective declared in one line; operator approved; operator
  pre-approved the `/opt/ce_sri/envars.sh` disposition recommendation
  (option b — rename to `/opt/generic/envars.sh`).

### Branch cut

`git checkout -b fix/bench-generic-provision-contamination
origin/umbrella/ladder-fixture && git push -u`. Clean cut; empty
relative to umbrella tip.

### Boundary-crossing — ratchet-triggered decomposition call

First pass edits blew the pre-commit size ratchet: `platform_setup.sh`
and `clone_and_services.sh` were each 87 lines pre-modify (no baseline
in `size_baselines.json`) and grew to 100+ after adding the generic
branches — the ratchet treats unbasefleined files over the 80-line
category limit as new-file violations on first modify.

Paused per `feedback_enumerate_mechanisms_before_committing.md`, gave
the operator three paths (shrink in-place / decompose per-section /
convert to Python). Operator's call: **decompose**, with explicit
rationale — controller-side logic must be OS-agnostic Python, but
VM-side bash is acceptable **provided it is optimally decomposed to
"one file ↔ one task" clarity**. Matches the #220 bootstrap_hub
pattern.

### Decomposition

`tools/pipeline/stages/stage_6_base_platform/`:

- `platform_setup.sh` — thin orchestrator, 33 lines, dispatches on MODE
- `clone_and_services.sh` — thin orchestrator, 43 lines, dispatches on MODE; re-runs section C once BaRe is cloned (folds back the symlink step that was previously a trailing SSH call from `__init__.py`)
- `sections/_helpers.sh` — shared `_gh_clone` wrapper
- `sections/ps_*` — 7 platform_setup section files (A, A2, A2b, A2c, A2e, B, C)
- `sections/cs_*` — 6 clone_and_services section files (A2d-bespoke, A2d-bare, A3a, A3b, A3c, B2b)
- Each section: one task, ≤40 lines, self-contained with declared env-var contract

verify.py split into four check modules to meet the 80-line
category cap (all ≤54 lines):

- `check_ssh.py` — SSH helper (shared)
- `check_envars.py` — envars path + BaRe symlink (mode-sensitive)
- `check_apps.py` — app-clone + deploy-keys (mode-sensitive, includes absence checks in generic)
- `check_infra.py` — bench symlink + supervisor (mode-invariant)
- `verify.py` — orchestrator + CLI entry; absolute imports with a
  `sys.path` prelude so `./verify.py` still invokes directly per
  `feedback_invoke_as_executable.md`

`__init__.py` plumbs `config.provision_mode` into both orchestrator
invocations, rsyncs `sections/` to `/tmp/sections/` on the VM, and no
longer needs the trailing BaRe-symlink SSH call.

Mode parsing in the verify CLI: initially routed via
`common/verify_cli.py`'s shared helper; reverted and localised in
stage-6's `verify.py` `__main__` to keep the sub-branch blast
radius tight (no drive-by change to a helper shared by all 9
stages).

### envars.sh disposition — option (b) chosen before code wrote

Inspecting `platforms/kvm/templates/envars.sh.j2` (15 lines): contents
are purely ERPNext deployment env vars (`ERP_USER_PWD`,
`ERPNEXT_SITE`, `TARGET_BENCH`, etc.) — zero ce_sri-specific keys.
The `/opt/ce_sri/…` path was the cosmetic coupling; the content was
always innocuous. Generic mode now writes to `/opt/generic/envars.sh`;
BaRe's symlink retargets accordingly. No BaRe source change needed
(BaRe scripts source `BaRe/envars.sh` via local relative path; the
symlink target is transparent to them). Restore mode untouched.

### MATRIX-CLOSEOUT.md erratum

Added a dated paragraph at the foot of `docs/SessionLogs/acceptance-matrix/MATRIX-CLOSEOUT.md`
noting that runs 03/04/06/07 were **site-generic** (apps.txt /
apps.json / `bench list-apps` clean) but **not bench-generic**
(bench layer contained ce_sri et al until #289). CLI↔UI parity
verdicts stand — both sides ran against the same contaminated
substrate. Tracked as part of sub-branch 1 scope per 0915 handoff,
not filed as its own issue.

### Acceptance — live end-to-end on dev02

Per `feedback_one_vm_at_a_time.md`, toshy has 16 GB and runs
saconsole + 1 dev VM. Operator approved path A (stop dev01 → provision
dev02 generic → verify → destroy dev02 → restart dev01).

1. `ssh toshy virsh shutdown dev01` (graceful ACPI).
2. `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay --wizard-arg=pseudo-co-wizard.spec.js` launched in background, output tail'd to `/tmp/dev02-generic-acceptance.log`.
3. Monitor armed on stage banners + error patterns. Stages 1→9 + Final snapshot fired in sequence; snapshot "ERPNext v13 Generic Baseline" taken.
4. `./tools/pipeline/stages/stage_6_base_platform/verify.py dev02 --mode=generic` → **6/6 ✅**:
   ```
   ✅  /opt/generic/envars.sh deployed; /opt/ce_sri absent
   ✅  Bench symlink /home/erpadm/frappe-bench-D2IRBL present
   ✅  No you_gh_* keys (generic mode)
   ✅  BaRe cloned; no ce_sri/route_planner/returnable; Procfile clean
   ✅  Supervisor: 8 processes RUNNING
   ✅  BaRe/envars.sh -> /opt/generic/envars.sh
   ```
5. Manual SSH to dev02 confirmed:
   - `apps/` = {`frappe`, `erpnext`} only
   - `Procfile` has no `ce_sri_svc` entry (bench default)
   - `/opt/` contains only `generic`
   - `/home/erpadm/.ssh/` has only `authorized_keys`
   - `BaRe/envars.sh` → `/opt/generic/envars.sh`
   - 8 `frappe-bench-*` supervisor procs; no `ce-sri-svc`
6. Wizard replay (post-pipeline step, outside Stage 6 scope) exited 1 — tracked under #284/#285 (race class). Orthogonal to #289; no new issue filed per `feedback_not_perfection_project.md`.
7. `./tools/esacp.py destroy dev02` — 8-step teardown complete.
8. Reverted the four config files the destroy mutated (`hosts_map.yml`, `ansible/inventory/kvm.yml`, `ansible/group_vars/all.yml`, `config/wireguard/keys.sops.yml`) so the sub-branch committed only fix-related changes.
9. `ssh toshy virsh start dev01` — back to pre-acceptance fleet state.

### Commit + PR + merge

Commit `bc1742d` (GPG-signed, Conventional Commits, Co-Authored-By trailer).
PR #291 opened against `umbrella/ladder-fixture` with full test plan
and scope notes. PR state CLEAN / MERGEABLE. Operator-approved merge
via `gh pr merge --merge` → merge commit `9c66ccf` at 2026-04-23T17:52:37Z.
Sub-branch retained.

## Audit (session-close)

1. **Forward-tense phrases** — all resolved or tracked with durable homes:
   - Sub-2 / sub-3 / umbrella certification → `~/.claude/plans/open-issues-purge.md` (updated: sub-1 row marked ✅ DONE with commit pointer; First-move pointer advanced from sub-1 to sub-2; clean-bench flake data point carried as context note).
   - "Restore-verify green" / "Umbrella certification" / "Sub-2 & sub-3 need new issues at session start" → plan file Pre-Tier 0 section.
   - Tier 0 (#278, #288) deferred until umbrella certifies → plan file.
2. **GH issues** — findings posted as comments on the issues themselves (not only in minutes):
   - #289 resolution comment: https://github.com/martinhbramwell/ESACP/issues/289#issuecomment-4306747819 (PR #291 / `9c66ccf` / acceptance evidence / closed-when pointer).
   - #284 data point comment: https://github.com/martinhbramwell/ESACP/issues/284#issuecomment-4306748365 (wizard flake reproduces on clean-bench substrate).
   - #285, #290, #202, #278, #288, #220 referenced for context only — no new findings in this session.
3. **PRs opened** — #291. `gh pr view 291 --json mergedAt` → `2026-04-23T17:52:37Z` (non-null). DONE justified.
4. **Scope discipline** — one concern surfaced mid-session (ratchet-triggered decomposition call) and was resolved in-scope per operator direction; no drive-by changes to shared helpers (verify_cli.py reverted; mode parsing localised in stage-6).

## Files changed

| File / path | Change |
|---|---|
| `tools/pipeline/stages/stage_6_base_platform/__init__.py` | Orchestrator plumbs `config.provision_mode`, rsyncs `sections/`, drops trailing BaRe-symlink SSH step |
| `tools/pipeline/stages/stage_6_base_platform/platform_setup.sh` | Thin orchestrator, MODE arg, dispatches sections |
| `tools/pipeline/stages/stage_6_base_platform/clone_and_services.sh` | Thin orchestrator, MODE arg, dispatches sections, re-runs section C post-BaRe |
| `tools/pipeline/stages/stage_6_base_platform/verify.py` | Orchestrator + CLI; absolute imports; `--mode=generic|restored` flag |
| `tools/pipeline/stages/stage_6_base_platform/check_{ssh,envars,apps,infra}.py` | NEW — decomposed checks; mode-sensitive + absence checks |
| `tools/pipeline/stages/stage_6_base_platform/sections/*.sh` | NEW — 1 `_helpers.sh`, 7 `ps_*`, 6 `cs_*` section files |
| `tools/size_baselines.json` | Ratchet bookkeeping for the new files + shrunk verify.py |
| `docs/SessionLogs/acceptance-matrix/MATRIX-CLOSEOUT.md` | Erratum appended |
| `docs/SessionLogs/2026-04-23-1352-session-minutes.md` | this file (on main) |

Landing summary: 24 files, +515/-282 LOC on the sub-branch. Code lands on umbrella only. Main gets the minutes.

## State handed to next session

- `main` tip: `<this minutes commit>` (only-doc).
- `umbrella/ladder-fixture` tip: `9c66ccf` (contains #289 fix).
- **Open issues: 20** (unchanged — #289 auto-closes at umbrella→main).
- **Umbrella progress:** sub-1 done. Sub-2 (Playwright fixture regen for generic substrate) and sub-3 (restore-verify green) still to cut. Umbrella → main only at certification session.
- **First move for next umbrella-session:** cut sub-branch 2 off
  `umbrella/ladder-fixture`, file a new issue for Playwright fixture
  updates covering the clean bench (no ce_sri references), run a
  generic wizard-replay acceptance. Scope to be decided at session
  start per `~/.claude/plans/open-issues-purge.md` Pre-Tier 0.
- **Tier 0** (#278, #288) remains deferred until umbrella certifies.

## Reminders to operator

1. **Wizard replay exit 1** on dev02 acceptance — this is the
   Industry→Company / modal race already tracked as #284 / #285.
   No new issue; sub-branch 2's Playwright work will re-attack it
   against the clean-bench substrate.
2. **MATRIX-CLOSEOUT.md erratum is on umbrella only** until
   certification. Main will only learn about the erratum when the
   umbrella merges.
3. **Sub-branches 2 and 3 still need issues filed at the start of
   their sessions** (carried forward from 0915 handoff).
4. **Remaining parked items unchanged:** #284 race-class, #285 B06
   regen, #202 cloud-init template, `project_upgrade_v13_to_v16.md`
   stub.

## File trail

- Prior minutes: `docs/SessionLogs/2026-04-23-0915-session-minutes.md`
- Purge plan: `~/.claude/plans/open-issues-purge.md` (Pre-Tier 0 section)
- Matrix closeout (with erratum on umbrella): `docs/SessionLogs/acceptance-matrix/MATRIX-CLOSEOUT.md`
- PR: [#291](https://github.com/martinhbramwell/ESACP/pull/291) (merged `9c66ccf`)
- Commit: `bc1742d`
- This minutes: `docs/SessionLogs/2026-04-23-1352-session-minutes.md`
- Issue: [#289](https://github.com/martinhbramwell/ESACP/issues/289) (open until umbrella→main)
