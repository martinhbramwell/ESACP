# Tools — Claude Code Context

## api.py — FastAPI Control Plane (port 8088)

Start: `uvicorn tools.api:app --port 8088 --reload` from project root. Will move to saconsole when promoted from prototype.

### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/hosts` | KVM hosts + IP suggestions + default hypervisor; includes `vm_role`, `erp_user`, `erp_url`, `hypervisor` |
| POST | `/api/hosts/add` | Append to `hosts_map.yml`, regen inventory; accepts `zone`, `vm_role` |
| POST | `/api/provision/{host}` | Job: cloud-init + WG + buildVM + provisionVM + saconsole WireGuard hub update (Step 5) |
| POST | `/api/provision/erpnext` | Template-based deploy: vol-clone + `--import` + differentiation (Steps 1–18) |
| POST | `/api/refresh/{host}` | Re-SCP + `sudo bash` the saved `{hostname}-differentiate.sh` artifact |
| GET | `/api/health/{host}` | SSH checks: nginx (`systemctl is-active`), app (supervisorctl RUNNING count), db (mysql SELECT 1) |
| POST | `/api/destroy/{host}` | Full destroy pipeline: WG peer → snapshots → virsh → hosts_map cleanup → regen → Ansible |
| POST | `/api/promote` | Stub: Staging→Production initiation (Telegram approval deferred) |
| GET | `/api/jobs` | List all jobs (for page-refresh reconnect) |
| GET | `/api/jobs/{id}` | Poll job status + log |

### Key Design Points

- `provisioned` = VM has a snapshot containing "Baseline" (not just VM exists)
- Template build uses `nohup` on saconsole — survives uvicorn reload; log polled via SSH tail every 5s; exit code written to `/tmp/packer-build-output.log.exit`
- `POST /api/provision/erpnext` writes `platforms/kvm/{hostname}-differentiate.sh` at Step 12 — committed as repo artifact; re-runnable via Refresh
- `erp_user` sourced from `ansible/group_vars/all.yml` (single source of truth)
- Python f-string templates in the differentiate.sh generator: `${BASH_VAR}` must be `${{BASH_VAR}}` — single braces are parsed as Python format expressions → NameError

## esacp.py — Unified Lab CLI

`python tools/esacp.py <subcommand> [options]` — run from project root; `--help` lists all subcommands.

Non-obvious behaviours:
- `provisionVM` Ansible output filter: shows PLAY headers, ✓ ok, ★ changed, ❌ fatal, RECAP only
- `validateObservability` credential order: `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD` env vars → SSH saconsole `/opt/observability/.env` → interactive prompt
- `buildVM`: uses `virsh vol-create-as` + `virsh vol-upload` for seed ISO — not `sudo cp` (hangs in uvicorn threads)
- `snapShotVM`: KVM-only, hardwired to `platforms/kvm/snapshot.py` → `virsh`

## generate_inventory.py

- Reads `hosts_map.yml`, writes `ansible/inventory/kvm.yml`
- Excludes non-kvm backends: `attrs.get("backend", "kvm") != "kvm"`
- Injects `ansible_ssh_common_args: "-o ProxyJump=..."` for hosts with a `hypervisor` field
