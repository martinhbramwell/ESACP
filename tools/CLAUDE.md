# Tools — Claude Code Context

## Dispatcher layer — CLI + API thin shells (#195, Phase 7)

Per CLAUDE.md anti-spiral rules, `tools/esacp.py`, `tools/api/`, and
`tools/job_worker.py` are dispatchers only — they parse input, call one
pipeline primitive, format output. Business logic lives in
`tools/pipeline/**`.

- **`tools/esacp.py`** (~100 lines, cap 150): argparse + dispatch dict.
  Per-subcommand entry points live in `tools/cli/*.py` (each ≤80). Shared
  presentation helpers in `tools/cli/_common.py`. `displayConfiguration`
  tree builders in `tools/cli/display/`.
- **`tools/api/`** (package): `__init__.py` wires the FastAPI app + middleware
  + exception handlers; endpoint handlers live in `tools/api/routes/*.py`
  (each ≤80). Shared helpers: `tools/api/helpers.py` (hosts_map, 404),
  `tools/api/jobs.py` (`spawn_job` / `read_job`). Pydantic request models
  in `tools/api_models.py`.
- **`tools/job_worker.py`** (~90 lines, cap 100): argv parsing + 5-entry
  RUNNERS dict. Each runner delegates to a macro in `tools/pipeline/macro/`
  or a primitive in `tools/pipeline/orchestration/`.

Subprocess is banned in dispatchers except:
1. `tools/api/jobs.py` — `subprocess.Popen` to spawn `tools/job_worker.py`

The pre-commit ratchet (`tools/pre_commit_size_check.py`) enforces the caps.

## Standalone harnesses — subprocess bridges from pipeline

Not everything that calls `subprocess` is a dispatcher leak. Some scripts are
measurement/assertion harnesses that exist outside the provisioning CRUD flow
and are intentionally kept as standalone files:

| Harness | Invoked via | Why standalone |
|---|---|---|
| `orchestration/validate_observability.py` (27-check suite) | `tools/pipeline/orchestration/observability_creds.py:validate_observability()` runs `subprocess.run(["python3", script_path])` | Long-lived assertion harness with its own output format. Decomposing it into IoC primitives would not change the capability — each check is a single query + assert, and the script is already one-responsibility-per-function internally. Kept as an auditable single-file test harness, invoked through a pipeline primitive that sources credentials. |

Rule: a standalone harness is acceptable when it is **measurement, not
state-mutation**. If a script mutates VM/host/hub state, it belongs in the
pipeline as atomic units. Pure assertion/measurement scripts can stay as
single files invoked from a pipeline primitive, because decomposition adds
no safety over "run the assertions, report pass/fail".

## api/ — FastAPI Control Plane (port 8088)

Start: `uvicorn tools.api:app --port 8088 --reload` from project root. Will move to hub when promoted from prototype.

### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/hosts` | KVM hosts + IP suggestions + default hypervisor; includes `vm_role`, `vm_state`, `erp_user`, `erp_url`, `hypervisor` |
| POST | `/api/hosts/add` | Append to `hosts_map.yml`, regen inventory; accepts `zone`, `vm_role` |
| POST | `/api/provision/erpnext` | Template-based deploy via `macro/provision.py`: stages 1–9 + final snapshot |
| POST | `/api/provision/erpnext-generic` | Generic deploy (no prod data) + wizard completion (record/replay/existing) |
| GET | `/api/wizard/recordings` | List available Playwright wizard recordings (`recordings/wizard/*.spec.js`) |
| GET | `/api/wizard/backups` | List golden backup files (`platforms/kvm/golden_backups/*.tgz`) |
| POST | `/api/refresh/{host}` | Re-run stages 3–9 via `macro/refresh.py` (idempotent, over WireGuard) |
| GET | `/api/health/{host}` | SSH checks: nginx (`systemctl is-active`), app (supervisorctl RUNNING count), db (mysql SELECT 1) |
| GET | `/api/template/status` | Metadata for latest undifferentiated ERPNext image on toshiba |
| POST | `/api/build/template` | Start background Packer build on hub (one at a time) |
| DELETE | `/api/template` | Delete template artifact from toshiba, reset to not_built |
| POST | `/api/vm/{host}/start` | Start a shut-off VM (memory guard rejects if host RAM insufficient) |
| POST | `/api/vm/{host}/stop` | Graceful shutdown (`virsh shutdown`); rejects hub nodes |
| POST | `/api/vm/{host}/reboot` | Reboot a running VM (`virsh reboot`) |
| POST | `/api/destroy/{host}` | Full destroy pipeline: WG peer → snapshots → virsh → hosts_map cleanup → regen → Ansible |
| POST | `/api/promote` | Stub: Staging→Production initiation (Telegram approval deferred) |
| GET | `/api/jobs` | List all jobs (for page-refresh reconnect) |
| GET | `/api/jobs/{id}` | Poll job status + log |

### Key Design Points

- `provisioned` = VM has a snapshot containing "Baseline" (not just VM exists)
- `vm_state` = libvirt domain state string (`running`, `shut off`, or `null` if hypervisor unreachable); polled by UI every 30s
- VM power actions (`/api/vm/{host}/start|stop|reboot`) are synchronous — no job/polling. Each dispatches to `tools/pipeline/orchestration/vm_power.py`; `start` first calls `memory_guard.check_memory()` (virsh nodeinfo + dominfo sums vs 2 GiB host reserve). HTTP 409 on insufficient RAM; HTTP 400 when a hub stop is rejected
- **Jobs run as independent OS processes** (GH #37) — `tools/api/jobs.py` spawns `tools/job_worker.py` via `subprocess.Popen` with `start_new_session=True`. Child process survives uvicorn restart. Log → `/tmp/esacp-job-{id}.log`, status → `/tmp/esacp-job-{id}.status`, metadata → `/tmp/esacp-job-{id}.meta`. API endpoints read from these files (fully stateless)
- `POST /api/provision/erpnext` delegates to `macro/provision.py` which runs stages 1–9 sequentially. Each stage has a verify-based idempotency gate — if all postconditions are already met, the stage is skipped. The final snapshot step runs unconditionally
- `POST /api/refresh/{host}` delegates to `macro/refresh.py` which runs stages 3–9 (skipping VM creation and network). Same idempotency gates apply
- ce_sri secrets deployment, deploy keys, Cloudflare DNS, TLS certs, and all differentiation steps are now handled by pipeline stage units, not by api.py helpers
- `erp_user` sourced from `ansible/group_vars/all.yml` (single source of truth)

## job_worker.py — Standalone Job Runner (GH #37)

Spawned by `tools/api/jobs.py` as an independent OS process. Survives uvicorn restarts.

Usage: `python3 tools/job_worker.py <job_type> <job_id> '<json_args>'`

Job types: `provision`, `provision_generic`, `refresh`, `destroy`, `build_template`

- Writes timestamped lines to stdout (redirected to `/tmp/esacp-job-{id}.log` by the spawner)
- Writes `done` or `error` to `/tmp/esacp-job-{id}.status` on completion
- `tools/api/jobs.py` writes `/tmp/esacp-job-{id}.meta` (JSON: hostname, type, started_at) at spawn time
- `provision_generic` delegates wizard completion (record/replay/existing) to `tools/pipeline/orchestration/wizard_run.py`

## esacp.py — Unified Lab CLI

`./tools/esacp.py <subcommand> [options]` — run from project root; `--help` lists all subcommands. 14 subcommands routed through `tools/cli/*.py` per-command dispatchers.

Non-obvious behaviours:
- `provisionVM` Ansible output filter: shows PLAY headers, ✓ ok, ★ changed, ❌ fatal, RECAP only (filter lives in `tools/pipeline/stages/common/ansible_output.py`; orchestrator is `tools/pipeline/orchestration/ansible_provision.py`)
- `validateObservability` credential order: `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD` env vars → SSH hub `/opt/observability/.env` → interactive prompt
- `buildVM`: uses `virsh vol-create-as` + `virsh vol-upload` for seed ISO — not `sudo cp` (hangs in uvicorn threads)
- `snapShotVM`: KVM-only; dispatcher calls `pipeline/orchestration/snapshot_ops.py` (local virsh). Standalone `platforms/kvm/snapshot.py` still exists for operator use (revert/delete/start/state) per `internal_docs/BuildOutProcedure.md`.
- `destroyVM` (legacy, local libvirt only): uses `tools/pipeline/orchestration/local_vm_teardown.py` for inspect + teardown; not to be confused with `destroy` which runs the full `macro/destroy.py`
- `applySubstrateMigration` (#418): bundles `g1_seed_patch_log.py` + `g2_clear_fixture_custom_fields.py` + `bench migrate` over SSH on a lab VM. Use for LSKB#15-style bespoke-app migration tests on already-restored production data — closes the bypass that caused two cascading failures in S54/S55. Dispatcher calls `tools/pipeline/orchestration/substrate_apply.py`. See `tools/vm_scripts/README.md` for the protection catalogue.

## diagnose.py — Remote VM Process Diagnostics

`python3 tools/diagnose.py <host> <subcommand> [args]` — reusable diagnostic functions for inspecting hung/stuck processes on KVM guest VMs via SSH.

Subcommands:
- `hung-procs` — list long-running bench/frappe/ce_sri processes with elapsed time
- `proc-detail <pid>` — threads (wchan + kernel stack), file descriptors, TCP connections
- `site-health` — quick check: currentsite.txt, gunicorn workers, supervisor services, nginx
- `bench-log <job_id> [-n lines]` — tail a differentiation job log on hub

All functions are importable (`from tools.diagnose import hung_procs, site_health, ...`) for use in other scripts or `api.py` health endpoints.

## host_identity.py — Host Identity Constants

Resolves host identities from `hosts_map.yml` at import time. Provides:
- Hub: `HUB_KEY`, `HUB_VM_NAME`, `HUB_HOSTNAME`, `HUB_DISPLAY_NAME`, `HUB_VIRBR0_IP`, `HUB_WG_IP`, `HUB_HYPERVISOR`
- Domains: `ZONE_DOMAINS` (dict), `domain_for_zone(zone)`
- Hypervisor: `DEFAULT_HYPERVISOR`
- IP helpers: `virbr0_gateway(ip)`, `virbr0_subnet_prefix()`
- Lookups: `hub_vm(config)`, `kvm_hosts(config)`, `host_field(key, field)`

All Python code that previously hardcoded host-specific values imports from here instead.

**Shell-eval emitter.** Also callable directly as an executable
(`#!/usr/bin/env python3`, `chmod +x`). Prints KEY=VALUE lines for
bash consumption — use from shell scripts that need the hub identity
without a `python -c` / `PYTHONPATH` layer:

```bash
eval "$(./tools/host_identity.py)"
echo "$HUB_VM_NAME $HUB_HYPERVISOR"
```

Emits: `HUB_KEY`, `HUB_VM_NAME`, `HUB_HOSTNAME`, `HUB_VIRBR0_IP`,
`HUB_WG_IP`, `HUB_HYPERVISOR`, `DEFAULT_HYPERVISOR`.

## secrets.py — Build Secrets Loader

Loads `erp_user_pwd` and `db_root_pwd` from env vars (`ESACP_ERP_USER_PWD`, `ESACP_DB_ROOT_PWD`) or from `config/build_secrets.sops.yml` (sops-encrypted). No hardcoded password defaults in code.

## install_specific — VM Differentiation (SCP'd to VM, Phase 9 #197)

Replaces the old monolithic `ce_sri/install.py`. Runs standalone as the
bench user — NOT via `bench execute` (avoids #136 deadlock, closed by
PR #137).

**Layout** (Phase 9, #197 — decomposed from a 721-line monolith):

| Path | Role |
|---|---|
| `tools/install_specific.py` (≤50 lines) | Thin entry: argparse + dispatch. SCP'd to `/tmp/install_specific.py` |
| `tools/vm_scripts/install_specific/` (package, each file ≤80) | Per-subcommand + helper modules. Rsynced to `/tmp/vm_scripts/install_specific/` by `stage_4/config_bundle.py` |

The thin entry resolves `sys.path` to either `./vm_scripts`
(controller) or `/tmp/vm_scripts` (VM), then
`from install_specific import cmd_before_install, cmd_after_restart`.

**API URLs use `localhost`** (gunicorn binds 127.0.0.1); the site name is sent as `Host` header via `_HOST_SITE` (in `_http.py`) for Frappe multi-tenant routing. All doc names in URLs are encoded via `urllib.parse.quote`.

### Subcommands

| Subcommand | Module | What it does |
|---|---|---|
| `before-install` | `before_install/` | Write ce_sri.conf, patch site_config.json, nginx.conf, Procfile, supervisor.conf |
| `after-restart` | `after_restart/` | Confirm API, install Client Scripts, logo, naming series, test data |

Called from `stage_8_app_config/pre_restart_config.sh` (`before-install`)
and `post_restart_config.sh` (`after-restart`).

Config comes from environment variables (envars.sh sourced by the stage scripts) + `ce_sri_parms.json` + `site_config.json`. HTTP via stdlib `urllib` — no `requests` dependency.

Golden-backup capture/restore is handled directly by the pipeline:
`stages/wizard_completion/capture_backup.py` runs `handleBackup.sh` after
wizard completion; `stages/stage_7_data_restoration/data_restore.sh` and
`stages/wizard_completion/restore_backup.py` invoke `handleRestore.sh`.

Acceptance test: `./tools/verify_phase9.py`.

## pipeline/ — Provision/Refresh Pipeline

3-level decomposition: `macro/` → `stages/` → unit files. See `tools/pipeline/`.

- **runner.py** — generic task executor: iterates `(Config, Emit) → TaskResult` functions, stops on first failure
- **stages/common/** — `Config` (frozen dataclass), `Emit`, `TaskResult`, SSH/SCP/rsync helpers
- **env_kvm.py** — `KvmEnv` dataclass (hypervisor alias, pool, image paths)

### Macros

| Macro | What | Called by |
|---|---|---|
| `macro/provision.py` | Stages 1–9 sequentially | `job_worker.py` (provision job) |
| `macro/provision_generic.py` | Stages 1–9 + wizard completion | `job_worker.py` (provision_generic job) |
| `macro/refresh.py` | Stages 3–9 (WG transport) | `job_worker.py` (refresh job) |
| `macro/destroy.py` | 8-step teardown: WG peer → VM → hosts_map → group_vars → inventory → Ansible WG → SOPS keys → known_hosts cleanup | `job_worker.py` (destroy job), `esacp.py` (destroy cmd) |

### Destroy orchestration primitives (in `orchestration/`)

Each is a single-task atomic script — no duplicated logic:

| File | Single responsibility |
|---|---|
| `destroy_vm.py` | Delete snapshots + virsh destroy + undefine on hypervisor |
| `wg_pubkey.py` | Decrypt SOPS keyring, return a host's WG public key |
| `wg_peer_remove.py` | Remove a live WG peer from the hub |
| `hosts_map_remove.py` | Remove a host block from hosts_map.yml |
| `group_vars_remove.py` | Remove wg_pubkey line from group_vars/all.yml |
| `inventory_regen.py` | Run generate_inventory.py |
| `ansible_wg_update.py` | Run Ansible to update hub WG config |
| `sops_key_remove.py` | Remove host keys from SOPS-encrypted keyring |
| `known_hosts_cleanup.py` | Clear stale `~/.ssh/known_hosts` entries (used by destroy + addHost) |
| `hub_seed_iso.py` | Render hub autoinstall seed ISO from Jinja2 templates + hosts_map.yml (#202) |

### Dispatcher-extracted primitives (Phase 7, #195)

Added when `esacp.py`, `api.py`, and `job_worker.py` were thinned. Each keeps
subprocess out of dispatchers and funnels through `emit`:

| File | Used by | Responsibility |
|---|---|---|
| `snapshot_ops.py` | `ansible_provision`, CLI | list + create virsh snapshots (local + SSH) |
| `local_vm_teardown.py` | `cli/destroy_vm.py` | inspect + destroy a local libvirt VM |
| `ansible_provision.py` | `cli/provision_vm.py` | full provisionVM orchestration |
| `ansible_playbook_run.py` | `ansible_provision` | filtered `ansible-playbook` streamer |
| `template_metadata.py` | API `/api/template/*` | read/delete Packer template JSON via SSH |
| `host_health.py` | API `/api/health/{host}` | nginx/supervisor/mysql SSH probes |
| `wizard_run.py` | `job_worker` | Playwright record/replay/existing dispatch |
| `stages/preflight/apt_install.py` | `cli/confirm_prerequisites.py` | `sudo apt install -y` wrapper |

### Host-registration primitives (in `orchestration/`)

Shared across `/api/hosts/add`, `/api/provision/erpnext`,
`/api/provision/erpnext-generic`. Exceptions raised by the primitives are
mapped to HTTP status codes by FastAPI exception handlers in `tools/api/__init__.py`:

| File | Single responsibility | Errors raised |
|---|---|---|
| `host_registration.py` | Validate hostname/IPs, insert YAML block at marker, regen inventory | `HostRegistrationError` (400), `HostConflictError` (409), `RuntimeError` (500) |
| `host_registration_block.py` | Build the YAML block string + `ZONE_GROUPS` mapping | — |
| `vm_state_query.py` | SSH to hypervisor, return `{vm: {provisioned, vm_state}}` or `None` | — |
| `host_cleanup_check.py` | Decide whether an already-registered host needs pre-provision cleanup | `HostAlreadyProvisionedError` (409) |

### Stages (all 9 extracted)

| Stage | Package | Orchestrator | Units |
|---|---|---|---|
| 1 — VM Creation | `stage_1_vm_creation/` | `run_stage_1()` | cleanup_residue, wireguard_peer, seed_iso, upload_seed, clone_template, virt_install, wait_ssh, baseline_snapshot |
| 2 — Network | `stage_2_network/` | `run_stage_2()` | hub_wg_hub, cloudflare_dns, tls_cert, wireguard_spoke |
| 3 — Connectivity | `stage_3_connectivity/` | `run_stage_3()` | deploy_keys, controller_pubkey, cesri_secrets, backup, ddl_views |
| 4 — Content Delivery | `stage_4_content_delivery/` | `run_stage_4()` | config_bundle (render + rsync) |
| 5 — TLS | `stage_5_tls/` | `run_stage_5()` | cert install, nginx vhost, DH params |
| 6 — Base Platform | `stage_6_base_platform/` | `run_stage_6()` | envars, bench symlink, deploy keys, app clone, supervisor, BaRe symlink |
| 7 — Data Restoration | `stage_7_data_restoration/` | `run_stage_7()` | currentsite, bench doctor, ddlViews, erpnext install, DB restore |
| 8 — App Config | `stage_8_app_config/` | `run_stage_8()` | /etc/hosts, apikey, secrets, nginx.conf, before-install, .env, gunicorn, after-restart |
| 9 — Service Activation | `stage_9_service_activation/` | `run_stage_9()` | HTTPS check, Social Login, stop.py, bash_aliases |

### Verification / idempotency

Each stage has a `verify.py` colocated with its code. All 9 stages use the same pattern:
1. Call `verify_stage_N()` → returns `list[tuple[bool, str]]`
2. `all_passed()` → True = skip the stage ("already satisfied")

CLI: `python3 tools/pipeline/stages/stage_N_.../verify.py <hostname>` → exit 0/1.
Importable: `verify_stage_N()` returns `list[tuple[bool, str]]`; `all_passed()` for gate logic.

Verify functions serve three roles:
1. **Acceptance test** — confirm a stage worked after running it
2. **Idempotency gate** — skip the stage if all postconditions already met
3. **Self-repair diagnostic** — pinpoint which unit needs re-running

## generate_inventory.py

- Reads `hosts_map.yml`, writes `ansible/inventory/kvm.yml`
- Excludes non-kvm backends: `attrs.get("backend", "kvm") != "kvm"`
- Injects `ansible_ssh_common_args: "-o ProxyJump=..."` for hosts with a `hypervisor` field
