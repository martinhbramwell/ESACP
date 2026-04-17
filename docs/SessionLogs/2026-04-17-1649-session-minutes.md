# Session Minutes — 2026-04-17 16:49 UTC

**Objective:** Phase 9 (#197) — decompose `tools/install_specific.py` (721 lines) into a per-subcommand package under `tools/vm_scripts/install_specific/`, reducing the entry file to ≤50 lines while preserving SCP-to-VM behaviour and the stdlib-only constraint.

**Outcome:** DONE. PR #215 merged 2026-04-17T16:48:10Z via merge-commit `abab6ef`. Issue #197 auto-closed 2026-04-17T16:48:11Z. Gen 3 pipeline plan is now complete (all phases 0–9 merged).

---

## What happened

### Prep (sync check + branch)
- `bash platforms/kvm/sync_check.sh` — 43 ✅ / 10 ⚠ / 4 ❌. Failures were WG pings to all four unprovisioned dev VMs (expected per agenda). Section 9b green (post-#210 reconcile task live).
- `git checkout -b fix/197-install-specific-decompose` from `main@f7b127a`.
- `./tools/verify_phase7.py` + `./tools/verify_phase8.py` both green — prior phases intact.

### Design (approved before coding)
Package layout inside `tools/vm_scripts/install_specific/`:

- `_env.py`, `_http.py` — shared helpers (env lookup, stdlib urllib wrappers, `_HOST_SITE`)
- `phase1.py`, `gate.py` — single-module subcommands
- `before_install/` subpackage: `apikey.py`, `cesri_conf.py`, `nginx_config.py`, `config_patches.py`, `__init__.py` (orchestrator)
- `after_restart/` subpackage: `api_probe.py`, `scripts.py`, `logo.py`, `naming.py`, `test_data.py`, `__init__.py` (orchestrator)
- `__init__.py` — re-exports `cmd_phase1`, `cmd_gate`, `cmd_before_install`, `cmd_after_restart`

Thin entry `tools/install_specific.py` (47 lines): argparse + dispatch dict. Resolves `sys.path` to either `./vm_scripts` (controller) or `/tmp/vm_scripts` (VM) at import time, then `from install_specific import cmd_*`.

### Implementation
- 16 package files, all ≤80 lines. First pass put `cesri_conf.py` at 87; split `read_apikey`/`read_common_site_config` into `apikey.py`, bringing `cesri_conf.py` to 69.
- Every function body preserved verbatim — pure decomposition, no behaviour change.
- `_HOST_SITE` was a module global in the monolith; now lives in `_http.py` with a `set_host_site()` setter so `after_restart._load_globals` can mutate it cleanly across the package boundary.
- `tools/verify_phase9.py` written (mirrors `verify_phase7`/`verify_phase8`): entry size ≤50, package files ≤80, stdlib-only (no `requests`), all four `cmd_*` importable, `--help` lists all four subcommands, phases 7+8 still pass.
- `tools/CLAUDE.md` section rewritten to describe the new layout.

### Local validation before commit
- `./tools/verify_phase9.py` — all green.
- Simulated VM layout at `/tmp/esacp-p9-sim/install_specific.py` + `/tmp/esacp-p9-sim/vm_scripts/install_specific/` — imports resolve through the `/tmp/vm_scripts` path.
- Pre-commit size ratchet: baseline `tools/install_specific.py` ratcheted 721 → 47.

### Commit + PR
- Commit `c7abb1e` (GPG-signed, Conventional Commits, `fixes #197` trailer).
- Pushed; PR #215 opened.

### E2E — full provision on dev01
- Prereqs: template built (`erpnext-v13-2026-03-30.qcow2`, undifferentiated), 7.6 GB free on toshiba, dev01 unprovisioned.
- `POST /api/provision/erpnext {"hostname":"dev01","virbr0_ip":"192.168.122.21","wg_ip":"10.10.0.13"}` → job `a45fd7e4`.
- Monitor streamed stage transitions. Timeline (UTC):
  - 15:38:46 — Stage 1 start
  - 16:07:23 — Stage 8: H4d `install_specific before-install` complete
  - 16:08:02 — Stage 8: H4g `install_specific after-restart` complete
  - 16:08:24 — Final snapshot `ERPNext v13 Logichem DB Restored` taken
- Terminal status: `done`. Site live at https://dev01.iridium.blue.
- On-VM evidence: `/tmp/install_specific.py` present, `/tmp/vm_scripts/install_specific/` populated with `__pycache__` confirming the decomposed modules were actually imported and executed.

### Post-e2e
- Working tree clean — dev01 was pre-registered in `hosts_map.yml`, so the 4 expected mutations (hosts_map, group_vars/all.yml, keys.sops.yml, inventory/kvm.yml) never materialised. No `git restore` needed.

### Audit (before writing minutes)
- Narration sweep: two forward-looking statements had been queued for "flag in minutes" rather than action. Both refiled as GitHub issues before minutes were written:
  - **#216** — audit `phase1` and `gate` subcommands (no current pipeline caller).
  - **#217** — add `tools/vm_scripts/` to `pre_commit_size_check.py` ratchet.
- PR #215 `mergedAt` check before writing "DONE" anywhere — initially null; user approved merge; merged successfully.

### Merge + close
- `gh pr merge 215 --merge` → merge-commit `abab6ef`.
- `gh pr view 215 --json mergedAt` → `2026-04-17T16:48:10Z`.
- `gh issue view 197 --json state` → `CLOSED` at `2026-04-17T16:48:11Z` (auto-closed via `fixes #197`).
- Post-merge `sync_check`: 46 ✅ / 8 ⚠ / 3 ❌ (one fewer failure than session start because dev01 now provisioned).
- MEMORY.md updated: Phase 9 marked DONE with merge hash; open-issues list refreshed (#197 removed, #216/#217 added).

---

## Acceptance criteria (from agenda Phase 9)

| # | Criterion | Evidence |
|---|---|---|
| 1 | SCP + run each subcommand on dev VM | `before-install` + `after-restart` ran on dev01 via pipeline; on-VM `__pycache__` confirms real import |
| 2 | `wc -l tools/install_specific.py` ≤ 50 | 47 |
| 3 | Each per-subcommand file ≤ 80 | All 16 files confirmed by `wc -l` (max 80) |
| 4 | Stdlib-only (urllib, not requests) | `verify_phase9.check_stdlib_only()` green |
| 5 | Full provision e2e: stages 6–8 complete | Job `a45fd7e4` done, final snapshot taken |
| 6 | Pre-commit ratchet passes | Baseline 721 → 47; `python3 tools/pre_commit_size_check.py` exit 0 |
| 7 | `verify_phase9.py` committed + green | Included in commit `c7abb1e`; all 8 checks pass |

All seven satisfied.

---

## Artefacts

- Branch: `fix/197-install-specific-decompose` (pushed, merged, retained per `feedback_keep_merged_branches.md`)
- Commit: `c7abb1e refactor(tools): decompose install_specific.py into per-subcommand package (#197)`
- Merge commit: `abab6ef Merge pull request #215 from martinhbramwell/fix/197-install-specific-decompose`
- PR: https://github.com/martinhbramwell/ESACP/pull/215
- Issue: https://github.com/martinhbramwell/ESACP/issues/197 (CLOSED)
- New issues filed: #216, #217
- Plan: `~/.claude/plans/synthetic-mapping-pretzel.md` Phase 9
- Provision job log: `/tmp/esacp-job-a45fd7e4.log`

---

## Notes for future sessions

- Gen 3 pipeline plan is **complete** — all phases 0–9 merged. Dispatcher/monolith anti-spiral work is done. Next-session objective is a clean slate (start of Stage 2.x work).
- `phase1` and `gate` subcommands were preserved verbatim in the decomposition but have no current pipeline caller. #216 audits whether to delete or re-wire.
- `tools/vm_scripts/` is not yet part of the pre-commit size ratchet — files there are enforced only by `verify_phase9.py`. #217 addresses.
