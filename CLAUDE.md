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
| Stage 2.x | 🔜 Next | 4-platform abstraction, VPS backend (CloudStack), chaos on KVM, version watchdog |

---

## Architecture

### Target Platform Model

ESACP supports 4 controller platforms. Each controller manages a mix of local VMs
and/or remote VPS hosts via Ansible + SSH. The configuration layer (`hosts_map.yml`)
is designed to handle both in all 4 cases.

| # | Controller OS | Hypervisor / VPS | Status |
|---|---|---|---|
| 1 | Windows 11 + WSL2 | VirtualBox (local VMs) | ✅ Stage 1–1.5 |
| 2 | Xubuntu | KVM/libvirt (local VMs) | ✅ Stage 2.1 |
| 3 | Ubuntu Server + XFCE + X2Go | External VPS (iwStack) | 🔜 Planned |
| 4 | macOS | External VPS (iwStack) | 🔜 Planned |

Platforms 3 and 4 are **controller-only** — no local hypervisor. The controller runs
Ansible, Python orchestration scripts, SOPS/age, and SSH. All managed hosts
(Grafana server + workhorse VMs) are external VPS instances.

**VPS Provider: iwStack/cdStack (Prometeus)**
- URL: https://prometeus.net — datacenters in Milan and Rome (Italy)
- Underlying platform: **CloudStack** (not KVM-direct, not OpenStack)
- API: **CloudStack API** accessible via `CloudMonkey` CLI or Python SDK
- Snapshots: supported via API (disk-only; schedulable hourly/daily/weekly/monthly)
- Billing: pay-as-you-go credit system (€1 = 1 cdCredit)
- The VPS abstraction backend for `revertToBaseline.py` and `run_scenario.py`
  will target the CloudStack API

**macOS controller hosting** (for Platform 4 testing without physical hardware):
MacStadium, Mac Mini Vault, HostMyApple, MacinCloud all offer bare-metal Mac hosting.
Since the Mac is controller-only (just Ansible/Python/SSH), even the lowest tier suffices.
Note: hosted Macs are current macOS on Apple Silicon; the end-user target is
decade-old Intel Macs — functionally equivalent for the toolchain (Python, SSH, Ansible).

### Stage 1–1.5: Platform 1 Detail (VirtualBox/WSL)
- **Host**: Windows 11 with WSL2 (Ubuntu) + VirtualBox
- **Guest VM**: Ubuntu 22.04 (`console`), bridged networking, DHCP
- **Provisioning**: Ansible run from WSL via `orchestration/provision.py`
- **Snapshot management**: VirtualBox via `orchestration/revertToBaseline.py`

### Stage 2.1: Platform 2 Detail (KVM/Xubuntu)
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
  validate_observability.py         # End-to-end stack validation (27 checks, 6 sections)
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

### Observability validation
```bash
export GRAFANA_ADMIN_USER=<user>
export GRAFANA_ADMIN_PASSWORD=<password>
python3 orchestration/validate_observability.py          # auto-detects saconsole
python3 orchestration/validate_observability.py --obs-host <name>  # explicit host
python3 orchestration/validate_observability.py -v       # verbose (show passing detail)
```
All check targets (jobs, nodenames, datasource UIDs, dashboard titles) are derived
from the project's own config files — nothing is hardcoded in the script.

---

## Commit Conventions

All commits must:
1. **Follow Conventional Commits** format: `<type>[optional scope]: <description>`
2. **Be GPG-signed** (`git commit -S`)
3. **Include the co-author trailer**: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
4. **Update CLAUDE.md** if the commit changes architecture, key files, stage status, or gotchas

Common types and scopes used in this project:

| Type | When to use |
|---|---|
| `feat` | New capability (new role, new VM, new script) |
| `fix` | Bug or misconfiguration fix |
| `docs` | CLAUDE.md, RUNBOOK.md, SETUP_GUIDE.md, comments |
| `refactor` | Code restructure with no behaviour change |
| `chore` | Dependency updates, generated files, housekeeping |
| `ci` | Ansible playbook changes, provisioner scripts |
| `perf` | Performance improvements |
| `test` | Validation scripts, chaos scenarios |

Common scopes: `kvm`, `vbox`, `observability`, `wireguard`, `ansible`, `claude`, `chaos`

Examples:
```
feat(kvm): add Stage 2.1 parallel platform with WireGuard
fix(observability): node_exporter host networking, cAdvisor v0.55.1
docs(claude): update for Stage 2.1 completion — KVM architecture, new gotchas
chore(ansible): regenerate kvm inventory from hosts_map.yml
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
  Note: docker_sd_configs does NOT auto-set a `job` label — logs appear in Loki
  under `container_name`, not `job=docker`. Query by `{container_name="..."}`.

- **Promtail systemd-journal** requires three additional mounts to reach journald
  from inside the container: `/run/log/journal`, `/var/log/journal`, `/etc/machine-id`
  (all `:ro`). Without these, the `journal` scrape config silently produces no logs.

- **cAdvisor dashboard template variables**: Grafana 10 blocks `label_values()` queries
  that use `{__name__=~"..."}` regex selectors for performance reasons — the host and
  container dropdowns return empty and all panels show no data. Use a concrete metric name
  instead: `label_values(container_cpu_usage_seconds_total, instance)` and
  `label_values(container_cpu_usage_seconds_total{instance=~"$host"}, name)`.

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

Stage 2.1 (KVM parallel path) is complete. Remaining work, in rough priority order:

### Abstraction layer (`revertToBaseline.py`, `run_scenario.py`)
Currently hardcoded to VirtualBox/`VBoxManage`. Needs three backends:
- **VirtualBox**: existing (Platform 1)
- **KVM/virsh**: `virsh snapshot-create-as`, `virsh snapshot-revert`, `virsh start`
- **CloudStack API**: via `CloudMonkey` or Python SDK for iwStack VPS hosts
  (Platforms 3 & 4 — external VPS, no local hypervisor)
Backend selected by environment variable or per-host config in `hosts_map.yml`.

### Platform 3 (Ubuntu Server + XFCE + X2Go controller)
- New `ansible/inventory/ubuntu-server.yml` + `ansible/site-ubuntu-server.yml`
- External VPS workhorse VMs provisioned via CloudStack API
- WireGuard mesh extended to VPS hosts

### Platform 4 (macOS controller)
- New `ansible/inventory/macos.yml` + provisioner script
- macOS-specific dependency install (Homebrew, Python, SOPS/age)
- External VPS workhorse VMs same as Platform 3

### Mixed local + VPS inventory
`hosts_map.yml` schema to be extended with a `backend:` field per host
(`vbox` | `kvm` | `cloudstack`) so all 4 platforms can manage a mix of
local VMs and remote VPS instances from the same inventory.

### Chaos framework on KVM
Port `orchestration/chaos/run_scenario.py` and `scenarios.yml` to work
against KVM VMs (Platform 2), replacing VirtualBox-specific assumptions.

### Version watchdog + staging rebuild pipeline
Monitor upstream releases of all pinned components (Prometheus, Grafana, Loki,
Promtail, cAdvisor, node_exporter, Alertmanager, Docker CE, Ansible collections,
Ubuntu LTS). Trigger from-scratch rebuild on staging VMs, run the proof-of-life
checklist automatically, report pass/fail before promoting to the main lab.
Motivated by the cAdvisor/Promtail SDK compatibility issues found in Stage 2.1.
