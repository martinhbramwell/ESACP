# Tools — Claude Code Context

## api.py — FastAPI Control Plane (port 8088)

Start: `uvicorn tools.api:app --port 8088 --reload` from project root. Will move to saconsole when promoted from prototype.

### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/hosts` | KVM hosts + IP suggestions + default hypervisor; includes `vm_role`, `vm_state`, `erp_user`, `erp_url`, `hypervisor` |
| POST | `/api/hosts/add` | Append to `hosts_map.yml`, regen inventory; accepts `zone`, `vm_role` |
| POST | `/api/provision/{host}` | Cloud-init provision for pre-registered host (buildVM + provisionVM) |
| POST | `/api/provision/erpnext` | Template-based deploy via `macro/provision.py`: stages 1–9 + final snapshot |
| POST | `/api/refresh/{host}` | Re-run stages 3–9 via `macro/refresh.py` (idempotent, over WireGuard) |
| GET | `/api/health/{host}` | SSH checks: nginx (`systemctl is-active`), app (supervisorctl RUNNING count), db (mysql SELECT 1) |
| GET | `/api/template/status` | Metadata for latest undifferentiated ERPNext image on toshiba |
| POST | `/api/build/template` | Start background Packer build on saconsole (one at a time) |
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
- VM power actions (`/api/vm/{host}/start|stop|reboot`) are synchronous — no job/polling. `start` runs a memory guard check first (`_check_memory()`: virsh nodeinfo + dominfo sums vs 2 GiB host reserve). HTTP 409 on insufficient RAM
- Template build uses `nohup` on saconsole — survives uvicorn reload; log polled via SSH tail every 5s; exit code written to `/tmp/packer-build-output.log.exit`
- `POST /api/provision/erpnext` delegates to `macro/provision.py` which runs stages 1–9 sequentially. Each stage has a verify-based idempotency gate — if all postconditions are already met, the stage is skipped. The final snapshot step runs unconditionally
- `POST /api/refresh/{host}` delegates to `macro/refresh.py` which runs stages 3–9 (skipping VM creation and network). Same idempotency gates apply
- ce_sri secrets deployment, deploy keys, Cloudflare DNS, TLS certs, and all differentiation steps are now handled by pipeline stage units, not by api.py helpers
- `erp_user` sourced from `ansible/group_vars/all.yml` (single source of truth)

## esacp.py — Unified Lab CLI

`python tools/esacp.py <subcommand> [options]` — run from project root; `--help` lists all subcommands.

Non-obvious behaviours:
- `provisionVM` Ansible output filter: shows PLAY headers, ✓ ok, ★ changed, ❌ fatal, RECAP only
- `validateObservability` credential order: `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD` env vars → SSH saconsole `/opt/observability/.env` → interactive prompt
- `buildVM`: uses `virsh vol-create-as` + `virsh vol-upload` for seed ISO — not `sudo cp` (hangs in uvicorn threads)
- `snapShotVM`: KVM-only, hardwired to `platforms/kvm/snapshot.py` → `virsh`

## diagnose.py — Remote VM Process Diagnostics

`python3 tools/diagnose.py <host> <subcommand> [args]` — reusable diagnostic functions for inspecting hung/stuck processes on KVM guest VMs via SSH.

Subcommands:
- `hung-procs` — list long-running bench/frappe/ce_sri processes with elapsed time
- `proc-detail <pid>` — threads (wchan + kernel stack), file descriptors, TCP connections
- `site-health` — quick check: currentsite.txt, gunicorn workers, supervisor services, nginx
- `bench-log <job_id> [-n lines]` — tail a differentiation job log on saconsole

All functions are importable (`from tools.diagnose import hung_procs, site_health, ...`) for use in other scripts or `api.py` health endpoints.

## install_specific.py — VM Differentiation (standalone, SCP'd to VM)

Replaces the old monolithic `ce_sri/install.py`. Runs standalone as the bench user — NOT via `bench execute` (avoids #136 deadlock, closed by PR #137). SCP'd to `/tmp/install_specific.py` on the VM.

**API URLs use `localhost`** (gunicorn binds 127.0.0.1); the site name is sent as `Host` header via `_HOST_SITE` module global for Frappe multi-tenant routing. All doc names in URLs are encoded via `urllib.parse.quote`.

### Subcommands

| Subcommand | When called | What it does |
|---|---|---|
| `phase1` | After envars deployed, before app clones | Clone BaRe, symlink envars.sh, render bash_aliases |
| `gate` | After installApps + G-pre strip DEFINER | If no BKP/BACKUP.txt → handleBackup → exit; else → handleRestore |
| `before-install` | After H4a/H3/H4b/H4c (secrets + nginx setup) | Write ce_sri.conf, patch site_config.json, nginx.conf, Procfile, supervisor.conf |
| `after-restart` | After H4e/H4f/H4f-poll (gunicorn ready) | Confirm API, install Client Scripts, logo, naming series, test data |

Config comes from environment variables (envars.sh sourced by differentiate.sh) + `ce_sri_parms.json` + `site_config.json`. HTTP via stdlib `urllib` — no `requests` dependency.

**First run** (no golden backup): `gate` runs handleBackup.sh and exits. The backup is copied to `platforms/kvm/golden_backups/` on the controller.

**Subsequent runs**: `gate` runs handleRestore.sh, then `before-install` and `after-restart` complete the ce_sri customization.

## pipeline/ — Provision/Refresh Pipeline

3-level decomposition: `macro/` → `stages/` → unit files. See `tools/pipeline/`.

- **runner.py** — generic task executor: iterates `(Config, Emit) → TaskResult` functions, stops on first failure
- **stages/common/** — `Config` (frozen dataclass), `Emit`, `TaskResult`, SSH/SCP/rsync helpers
- **env_kvm.py** — `KvmEnv` dataclass (hypervisor alias, pool, image paths)

### Stages (all 9 extracted)

| Stage | Package | Orchestrator | Units |
|---|---|---|---|
| 1 — VM Creation | `stage_1_vm_creation/` | `run_stage_1()` | cleanup_residue, wireguard_peer, seed_iso, upload_seed, clone_template, virt_install, wait_ssh, baseline_snapshot |
| 2 — Network | `stage_2_network/` | `run_stage_2()` | saconsole_wg_hub, cloudflare_dns, tls_cert, wireguard_spoke |
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
