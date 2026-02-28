# ESACP — Claude Code Project Context

Enterprise System Administration & Chaos Planning
A home-lab infrastructure automation and observability training project.

---

## Current State

| Stage | Status | Description |
|---|---|---|
| Stage 1 | ✅ Complete | Security-hardened Ubuntu 22.04 VM + full observability stack |
| Stage 1.5 | ✅ Complete | Observability validation, alert profiles, dashboards, chaos framework |
| Stage 2 | 🔜 Next | KVM/Xubuntu hypervisor support alongside VirtualBox/WSL |

---

## Architecture

### Target Environment (Stage 1–1.5)
- **Host**: Windows 11 with WSL2 (Ubuntu) + VirtualBox
- **Guest VM**: Ubuntu 22.04 (`console`), bridged networking, DHCP
- **Provisioning**: Ansible run from WSL via `orchestration/provision.py`
- **Snapshot management**: VirtualBox via `orchestration/revertToBaseline.py`

### Observability Stack (Docker Compose on the guest)
All services run in Docker on the VM at `/opt/observability/`.

| Service | Port | Role |
|---|---|---|
| Prometheus | 9090 | Metrics scraping + alert evaluation |
| Grafana | 3000 | Dashboards and log exploration |
| Loki | 3100 | Log storage (Loki 2.9.3) |
| Promtail | — | Log shipping via Docker socket (Promtail 3.3.2) |
| Alertmanager | 9093 | Alert routing (→ Telegram) |
| node_exporter | 9100 | Host metrics |
| cAdvisor | 8080 | Container metrics |

**Note**: Promtail is intentionally version-mismatched from Loki (3.3.2 vs 2.9.3).
Reason: Promtail 2.9.3 embeds Docker SDK API v1.42; the host Docker daemon requires
v1.44 minimum. Promtail 3.x resolves this. The Loki push API is stable across versions.

### Alert Profiles
Two sets of alert rules, selected by Ansible based on inventory group:
- `docker/observability/prometheus/alerts/` — **production** profile (`for:` 2–10m)
- `docker/observability/prometheus/alerts-drill/` — **drill** profile (`for:` 20–30s)

`ansible/inventory/dev.yml` places `console` in both `development` and `lab` groups.
`group_vars/lab.yml` sets `alert_profile: drill`.
`group_vars/production.yml` enforces `alert_profile: production`.
The Ansible role refuses to run drill profile against production/protected hosts.

---

## Key Files

```
ansible/
  inventory/dev.yml               # Hosts: development + lab groups
  group_vars/all.yml              # alert_profile: production (default)
  group_vars/lab.yml              # alert_profile: drill
  group_vars/production.yml       # alert_profile: production (enforced)
  roles/observability/tasks/main.yml  # Profile-aware copy + force-recreate

docker/observability/
  docker-compose.yml              # Stack definition
  prometheus/prometheus.yml       # 7 scrape jobs
  prometheus/alerts/              # Production alert rules (12 alerts)
  prometheus/alerts-drill/        # Drill alert rules (same, faster)
  grafana/provisioning/
    datasources/datasources.yml   # UIDs pinned: prometheus, loki
    dashboards/json/              # node-exporter-full, cadvisor, management-console

orchestration/
  provision.py                    # Runs Ansible against target
  revertToBaseline.py             # VirtualBox snapshot restore (WSL/Windows)
  chaos/
    run_scenario.py               # 9-step failure injection lifecycle
    scenarios.yml                 # 10 scenarios with parameters
  requirements.txt                # Python deps: rich, pyyaml, paramiko

docs/
  RUNBOOK.md                      # Operational runbook for all 10 scenarios
```

---

## Environment Variables (orchestration tools)

```bash
export VM_IP=<VM IP address>
export VM_HOSTNAME=console          # VirtualBox VM name
export VM_USER=ernest               # SSH username on VM
export SSH_KEY_PATH=~/.ssh/id_ed25519
export SNAPSHOT_NAME="Stage 1.5 Complete"
```

---

## Known Decisions & Gotchas

- **`docker-compose up -d --force-recreate`** is used in the Ansible role so that config
  file changes (bind-mounted) are always picked up without manual container restarts.

- **Grafana metrics path**: With `serve_from_sub_path = true` in grafana.ini, Grafana
  serves metrics at `/grafana/metrics`, not `/metrics`. The Prometheus scrape job
  includes `metrics_path: /grafana/metrics`.

- **Datasource UIDs must be pinned** in `datasources.yml` (`uid: prometheus`, `uid: loki`)
  so provisioned dashboard JSONs can reference them reliably.

- **Promtail docker_sd_configs** requires the Docker socket mounted:
  `/var/run/docker.sock:/var/run/docker.sock:ro`
  This provides `container_name` labels on all log streams.

- **VirtualBox snapshot detection bug** (fixed): `snapshot_exists()` in
  `revertToBaseline.py` previously matched only top-level snapshot names. Fixed to
  match `SnapshotName*=` prefix for nested snapshots.

- **Secrets**: `ansible/group_vars/all.sops.yml` holds encrypted credentials
  (Telegram bot token, Grafana admin password). Requires SOPS + age key to decrypt.
  See `SETUP_GUIDE.md` for key setup.

---

## Stage 2 Scope (next)

Extend hypervisor support so the project works on **Xubuntu + KVM** in addition to
**Windows + VirtualBox**. Key work:

- Abstract hypervisor operations in `revertToBaseline.py` and `run_scenario.py`
  (currently hardcoded to VirtualBox/`VBoxManage`)
- KVM equivalent: `virsh snapshot-create-as`, `virsh snapshot-revert`, `virsh start`
- Detect hypervisor from environment (env var or config) rather than hard-coding
- Update Ansible inventory and provisioning for KVM networking differences
  (KVM uses `virbr0` NAT by default vs VirtualBox bridged)
- Update `SETUP_GUIDE.md` with KVM setup path
