# Gen 3 Pipeline Completion — Session Agendas

**Plan file**: `~/.claude/plans/synthetic-mapping-pretzel.md`
**Execution order**: front-to-back through the pipeline; no building on unresolved upstream.

Each session: 1 issue = 1 branch = 1 PR. Load the plan file. Run acceptance criteria before closing.

---

## Session: Phase 1 — Pre-flight validation primitives (#189)

**Objective**: Extract `cmd_confirm_prerequisites` + `cmd_validate_keys` from `esacp.py` into `tools/pipeline/stages/preflight/`.

**Plan reference**: `synthetic-mapping-pretzel.md` → Phase 1

**Steps**:
1. Branch `fix/189-preflight-primitives` from main
2. Create `tools/pipeline/stages/preflight/` with `check_tools.py`, `check_keys.py`, `check_files.py`, `__init__.py`, `verify.py`
3. Replace `esacp.py` lines 224-412 with two thin dispatchers
4. Delete `REQUIRED_TOOLS`, `MANUAL_INSTALL_HINTS`, `cmd_confirm_prerequisites`, `cmd_validate_keys` from esacp.py
5. Run acceptance criteria (see plan) — especially: `verify.py` exits 0, both CLI commands produce identical output, esacp.py shrinks ~145 lines
6. Commit with `fixes #189`, PR, merge

---

## Session: Phase 3 — VM build primitives (#191)

**Objective**: Extract `cmd_build_vm` (~490 lines) from `esacp.py` into `tools/pipeline/orchestration/`.

**Plan reference**: `synthetic-mapping-pretzel.md` → Phase 3

**Steps**:
1. Branch `fix/191-vm-build-primitives` from main
2. Create `build_vm_remote.py`, `build_vm_local.py`, `hypervisor_helpers.py`, `common/known_hosts.py`
3. Replace esacp.py's `cmd_build_vm` with 15-line dispatcher
4. Run acceptance: `buildVM <host>` provisions a VM on toshiba, esacp.py shrinks ~400 lines, no virsh/ssh subprocess calls remain in esacp.py
5. Commit with `fixes #191`, PR, merge

**Note**: Biggest single extraction. May need the full session.

---

## Session: Phase 2 — Host registration primitive (#190)

**Objective**: Extract host registration logic (~200 lines duplicated across 3 api.py endpoints) into `tools/pipeline/orchestration/`.

**Plan reference**: `synthetic-mapping-pretzel.md` → Phase 2

**Steps**:
1. Branch `fix/190-host-registration` from main
2. Create `host_registration.py`, `vm_state_query.py`, `host_cleanup_check.py`
3. 3 api.py endpoints now call the same primitive
4. Run acceptance: Cytoscape UI drag-to-provision works, `GET /api/hosts` returns same JSON, api.py shrinks ~170 lines
5. Commit with `fixes #190`, PR, merge

---

## Session: Phase 4 — macro/destroy.py (#192)

**Objective**: Extract destroy logic from `job_worker.py` + `esacp.py` into `tools/pipeline/macro/destroy.py`.

**Plan reference**: `synthetic-mapping-pretzel.md` → Phase 4

**Steps**:
1. Branch `fix/192-macro-destroy` from main
2. Create `tools/pipeline/macro/destroy.py` — 8-step sequence using existing `destroy_helpers.py`
3. Replace trapped logic in job_worker.py and esacp.py with calls to macro
4. Run acceptance: destroy via Cytoscape UI + CLI both work, both monoliths shrink, destroy logic gone from dispatchers
5. Commit with `fixes #192`, PR, merge

---

## Session: Phase 5 — Packer build + memory guard + VM power (#193)

**Objective**: Extract template build, memory guard, and VM power operations from `job_worker.py` + `api.py`.

**Plan reference**: `synthetic-mapping-pretzel.md` → Phase 5

**Steps**:
1. Branch `fix/193-build-template-vm-power` from main
2. Create `build_template.py`, `memory_guard.py`, `vm_power.py` in `tools/pipeline/orchestration/`
3. Replace trapped logic in job_worker.py and api.py
4. Run acceptance: VM start/stop/reboot via Cytoscape, template build job, no virsh/subprocess in api.py
5. Commit with `fixes #193`, PR, merge

---

## Session: Phase 6 — VPN verify + observability + Ansible filter (#194)

**Objective**: Extract remaining esacp.py trapped logic (~150 lines).

**Plan reference**: `synthetic-mapping-pretzel.md` → Phase 6

**Steps**:
1. Branch `fix/194-vpn-observability-extract` from main
2. Create `verify_vpn.py`, `observability_creds.py`, `ansible_output.py`
3. Replace esacp.py trapped logic with thin dispatchers
4. Run acceptance: `validateVPN` and `validateObservability` produce identical output, esacp.py shrinks ~150 lines
5. Commit with `fixes #194`, PR, merge

---

## Session: Phase 7 — Thin dispatchers (#195)

**Objective**: Final restructure of `esacp.py`, `api.py`, `job_worker.py` into thin dispatch layers.

**Plan reference**: `synthetic-mapping-pretzel.md` → Phase 7

**Pre-requisite**: Phases 1-6 all merged.

**Steps**:
1. Branch `fix/195-thin-dispatchers` from main
2. Create `tools/cli/` with per-command files, `tools/api_models.py`
3. Reduce: esacp.py ≤150, api.py ≤300, job_worker.py ≤100
4. Run acceptance: full e2e (Cytoscape provision + destroy + power), all CLI subcommands work, subprocess grep returns only `_spawn_job`
5. Commit with `fixes #195`, PR, merge

---

## Session: Phase 8 — Delete dead Gen 1 (#196)

**Objective**: Remove dead orchestration files after confirming no unique logic remains.

**Plan reference**: `synthetic-mapping-pretzel.md` → Phase 8

**Pre-requisite**: Phase 3 merged (autoinstall detection captured).

**Steps**:
1. Branch `fix/196-delete-gen1` from main
2. Audit each file for unique logic: `orchestrator.py`, `provision_kvm.py`, `provision.py`, `validate_observability.py`, `chaos/run_scenario.py`
3. Extract any unique logic to pipeline, then delete the files
4. Run acceptance: zero imports from `orchestration/` remain, e2e still works
5. Commit with `fixes #196`, PR, merge

---

## Session: Phase 9 — install_specific.py decomposition (#197)

**Objective**: Split `install_specific.py` (721 lines, runs on VMs) into per-subcommand files.

**Plan reference**: `synthetic-mapping-pretzel.md` → Phase 9

**Steps**:
1. Branch `fix/197-install-specific-decompose` from main
2. Create `tools/vm_scripts/install_specific/` with per-subcommand files
3. Reduce entry point to ≤50 lines
4. SCP to dev VM, test each subcommand (`phase1`, `gate`, `before-install`, `after-restart`)
5. Full provision e2e: stages 6-8 complete successfully using decomposed package
6. Commit with `fixes #197`, PR, merge
