# ESACP — Claude Code Project Context

Enterprise System Administration & Chaos Planning
A home-lab infrastructure automation and observability training project.

---

## Current State

| Stage | Status | Description |
|---|---|---|
| Stage 1 | ✅ Complete | Security-hardened Ubuntu 22.04 VM + full observability stack |
| Stage 1.5 | ✅ Complete | Observability validation, alert profiles, dashboards, chaos framework |
| Stage 2.1 | ✅ Complete | KVM/Xubuntu parallel path: WireGuard mesh, saconsole + target1, multi-host Prometheus |
| Stage 2.x | 🔜 Next | Hypervisor abstraction, chaos framework on KVM, version watchdog pipeline |

---

## Architecture

### Stage 1–1.5: VirtualBox/WSL Path
- **Host**: Windows 11 with WSL2 (Ubuntu) + VirtualBox
- **Guest VM**: Ubuntu 22.04 (`console`), bridged networking, DHCP
- **Provisioning**: Ansible run from WSL via `orchestration/provision.py`
- **Snapshot management**: VirtualBox via `orchestration/revertToBaseline.py`

### Stage 2.1: KVM/Xubuntu Path
- **Host**: Xubuntu workstation (`${HOSTNAME}`) with KVM/QEMU/libvirt
- **Guest VMs** (both Ubuntu Server 24.04.4, created via cloud-init + virt-install):

| VM | virbr0 IP | WireGuard IP | Role |
|---|---|---|---|
| `saconsole` | 192.168.122.10 | 10.10.0.1 | WireGuard hub · full observability stack |
| `target1` | 192.168.122.11 | 10.10.0.3 | WireGuard spoke · monitored host |
| controller (host) | — | 10.10.0.2 | WireGuard spoke |

- **Provisioning**: `orchestration/provision_kvm.py` → runs `ansible/site-kvm.yml`
- **Inventory source of truth**: `hosts_map.yml` → `tools/generate_inventory.py` → `ansible/inventory/kvm.yml`
- **Snapshot management**: `platforms/kvm/snapshot.py` (virsh wrapper)

### Observability Stack (Docker Compose on saconsole)
All services run in Docker at `/opt/observability/`.

| Service | Port | Role |
|---|---|---|
| Prometheus | 9090 | Metrics scraping + alert evaluation |
| Grafana | 3000 | Dashboards and log exploration |
| Loki | 3100 | Log storage (Loki 2.9.3) |
| Promtail | — | Log shipping via Docker socket (Promtail 3.3.2) |
| Alertmanager | 9093 | Alert routing (→ Telegram) |
| node_exporter | 9100 | Host metrics (network_mode: host) |
| cAdvisor | 8080 | Container metrics (v0.55.1) |

**Promtail version mismatch** (intentional): Promtail 2.9.3 embeds Docker SDK API v1.42;
Docker CE 25+ requires v1.44 minimum. Promtail 3.3.2 resolves this. The Loki push API
is stable across major versions.

**node_exporter host networking**: runs with `network_mode: host` + `pid: host` so
the container inherits the host's UTS namespace (nodename = "saconsole", not a container ID)
and sees all host interfaces including wg0. Prometheus reaches it via
`host.docker.internal:9100` (docker compose `extra_hosts: host-gateway`).

### Alert Profiles
Two sets of alert rules, selected by Ansible based on inventory group:
- `docker/observability/prometheus/alerts/` — **production** profile (`for:` 2–10m)
- `docker/observability/prometheus/alerts-drill/` — **drill** profile (`for:` 20–30s)

`ansible/inventory/kvm.yml` places KVM hosts in `development` and `lab` groups.
`group_vars/lab.yml` sets `alert_profile: drill`.
`group_vars/production.yml` enforces `alert_profile: production`.
The Ansible role refuses to run drill profile against production/protected hosts.

---

## Key Files

```
hosts_map.yml                       # Authoritative host directory (source of truth)
tools/generate_inventory.py         # Derives ansible/inventory/kvm.yml from hosts_map.yml

config/wireguard/
  generate_keys.sh                  # Generates keypairs + PSKs → keys.sops.yml
  keys.sops.yml                     # SOPS/age encrypted WireGuard keys (committed)
  .gitignore                        # Excludes plaintext keys/

platforms/kvm/
  create_seeds.sh                   # cloud-localds wrapper for seed ISOs
  create_vms.sh                     # virt-install for both VMs
  snapshot.py                       # virsh snapshot lifecycle CLI
  cloud-init/
    saconsole/{user-data,meta-data}
    target1/{user-data,meta-data}

orchestration/
  provision_kvm.py                  # KVM lifecycle: seeds, VMs, snapshots, Ansible
  provision.py                      # VirtualBox path (Stage 1-1.5, untouched)
  revertToBaseline.py               # VirtualBox snapshot restore (untouched)
  chaos/
    run_scenario.py                 # 9-step failure injection lifecycle
    scenarios.yml                   # 10 scenarios with parameters
  requirements.txt                  # Python deps: rich, pyyaml, paramiko

ansible/
  inventory/kvm.yml                 # Generated — do not edit directly
  inventory/dev.yml                 # Stage 1-1.5 VirtualBox hosts
  group_vars/all.yml                # alert_profile default + WireGuard network vars
  group_vars/kvm.yml                # SSH connection vars for KVM guests only
  group_vars/lab.yml                # alert_profile: drill
  group_vars/production.yml         # alert_profile: production (enforced)
  site-kvm.yml                      # Top-level KVM playbook (4 plays)
  roles/
    wireguard/                      # Hub/spoke config; hub sets UFW forward policy
    node_exporter/                  # Binary install + systemd for target1
    desktop/                        # xfce4 + x2goserver for saconsole
    observability/tasks/main.yml    # Profile-aware copy + force-recreate + UFW rules

docker/observability/
  docker-compose.yml                # Stack definition
  prometheus/prometheus.yml         # 8 scrape jobs (prometheus, node, cadvisor,
                                    #   alertmanager, grafana, loki, promtail, node-target1)
  prometheus/alerts/                # Production alert rules (12 alerts)
  prometheus/alerts-drill/          # Drill alert rules (same, faster)
  grafana/provisioning/
    datasources/datasources.yml     # UIDs pinned: prometheus, loki
    dashboards/json/                # node-exporter-full, cadvisor, management-console

docs/
  RUNBOOK.md                        # Operational runbook for all 10 scenarios
  SETUP_GUIDE.md                    # Setup instructions (VirtualBox + KVM paths)
```

---

## Environment Variables

### Stage 1–1.5 (VirtualBox path)
```bash
export VM_IP=<VM IP address>
export VM_HOSTNAME=console          # VirtualBox VM name
export VM_USER=ernest               # SSH username on VM
export SSH_KEY_PATH=~/.ssh/id_ed25519
export SNAPSHOT_NAME="Stage 1.5 Complete"
```

### Stage 2.1 (KVM path)
```bash
# provision_kvm.py reads these from ansible/group_vars/ and hosts_map.yml
# No additional env vars required beyond SOPS age key at ~/.config/sops/age/keys.txt
```

---

## Known Decisions & Gotchas

- **`docker-compose up -d --force-recreate`** is used in the Ansible role so that config
  file changes (bind-mounted) are always picked up without manual container restarts.

- **Grafana metrics path**: Grafana 10 serves `/metrics` at the HTTP root regardless
  of `serve_from_sub_path` — it is a separate handler outside the application router.
  The Prometheus scrape job uses the default `/metrics` path (no `metrics_path` override).

- **Datasource UIDs must be pinned** in `datasources.yml` (`uid: prometheus`, `uid: loki`)
  so provisioned dashboard JSONs can reference them reliably.

- **ContainerRestartLoop alert** uses `{name!=""}` filter. cAdvisor exposes a root
  cgroup entry with an empty `name` label (representing the host machine) whose
  `container_start_time_seconds` rate trips the threshold — the filter excludes it.

- **Promtail docker_sd_configs** requires the Docker socket mounted:
  `/var/run/docker.sock:/var/run/docker.sock:ro`
  This provides `container_name` labels on all log streams.

- **node_exporter host networking**: `network_mode: host` + `pid: host` gives correct
  hostname and interface visibility. Prometheus uses `host.docker.internal:9100`
  (via `extra_hosts: host-gateway` on the prometheus service). UFW must allow
  `172.16.0.0/12 → port 9100` (the observability bridge range) — set by Ansible role.

- **cAdvisor Docker SDK**: `gcr.io/cadvisor/cadvisor:v0.47.2` and `v0.49.1` embed
  Docker SDK API v1.41; Docker CE 25+ requires v1.44 minimum. Use `v0.55.1`.
  `ghcr.io/google/cadvisor` tags do NOT exist despite the README claiming migration there —
  stay on `gcr.io/cadvisor/cadvisor`.

- **WireGuard hub forward policy**: saconsole (hub) must have
  `DEFAULT_FORWARD_POLICY="ACCEPT"` in `/etc/default/ufw` for spoke-to-spoke routing.
  This is set by the `wireguard` Ansible role (hub hosts only).

- **group_vars scope for WireGuard**: `wg_port`, `wg_subnet`, `wg_pubkey_*` live in
  `group_vars/all.yml` (not `kvm.yml`) so the `controller` group (localhost) also
  receives them when running the `wireguard` role.

- **VirtualBox snapshot detection bug** (fixed): `snapshot_exists()` in
  `revertToBaseline.py` previously matched only top-level snapshot names. Fixed to
  match `SnapshotName*=` prefix for nested snapshots.

- **Secrets**: `ansible/group_vars/all.sops.yml` holds encrypted credentials
  (Telegram bot token, Grafana admin password). Requires SOPS + age key to decrypt.
  See `SETUP_GUIDE.md` for key setup.

---

## Stage 2.x Scope (next)

Stage 2.1 (KVM parallel path) is complete. Remaining Stage 2 work:

- Abstract hypervisor operations in `orchestration/revertToBaseline.py` and
  `orchestration/chaos/run_scenario.py` (currently hardcoded to VirtualBox/`VBoxManage`)
  → detect hypervisor from environment or config; add KVM equivalents via `virsh`
- Port the chaos framework (`run_scenario.py`, `scenarios.yml`) to work on KVM VMs
- Design a **version watchdog + staging rebuild pipeline**:
  monitor upstream releases of all pinned components, trigger from-scratch rebuild
  on staging VMs, run the proof-of-life checklist automatically, report pass/fail
  before promoting to the main lab (motivated by cAdvisor/Promtail SDK compatibility
  issues discovered during Stage 2.1 validation)
- Update `SETUP_GUIDE.md` with the full KVM setup path
