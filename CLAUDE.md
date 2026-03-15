# ESACP — Claude Code Project Context

Enterprise System Administration & Chaos Planning
A home-lab infrastructure automation and observability training project.

---

## Session Protocol

**At the start of every session**, before doing anything else:

1. **Identify the platform** — WSL/VBox (Windows) or Xubuntu/KVM?
2. **Run the sync check** for that platform:
   - VBox/WSL: `bash platforms/vbox/sync_check.sh`
   - KVM/Xubuntu: *(sync check TBD)*
3. **Fix any failures** reported by the sync check, commit and push repairs.
4. **State one objective** for the session. Do not pursue other issues that
   arise — note them and handle in a dedicated session.

**One objective per session.** This is a hard rule. Context degrades across
long sessions and leads to poor triage decisions. If a blocking sub-problem
emerges, assess whether it truly blocks the objective before diving in.

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
| `saconsole` | 192.168.122.10 | 10.10.1.1 | WireGuard hub · full observability stack |
| `target1` | 192.168.122.11 | 10.10.1.3 | WireGuard spoke · monitored host |
| controller (host) | — | 10.10.1.2 | WireGuard spoke |

- **Provisioning**: `orchestration/provision_kvm.py` → runs `ansible/site-kvm.yml`
- **Inventory source of truth**: `hosts_map.yml` → `tools/generate_inventory.py` → `ansible/inventory/kvm.yml`
- **Snapshot management**: `platforms/kvm/snapshot.py` (virsh wrapper)
- **Current snapshots** (both VMs):

| Snapshot | State captured |
|---|---|
| Fresh Install | Post cloud-init, pre-Ansible |
| Stage 2.1 Baseline | Full Ansible provision + WireGuard verified |
| Stage 2.1 Validated | 27/27 validation pass — full from-scratch rebuild confirmed |

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
tools/esacp.py                      # Unified lab CLI (10 subcommands — see below)

config/wireguard/
  generate_keys.sh                  # Generates keypairs + PSKs → keys.sops.yml
  add_peer.sh                       # Surgically adds ONE new peer to existing keys.sops.yml
  keys.sops.yml                     # SOPS/age encrypted WireGuard keys (committed)
  .gitignore                        # Excludes plaintext keys/

platforms/vbox/
  build_lab.sh                      # Thin wrapper: create_vms → install_wireguard → handoff_console
  create_vms.sh                     # Import OVAs, detect IP, update configs, wait SSH
                                    #   Pre-flight: detects existing VMs, offers revert to Fresh Install
  install_wireguard.sh              # Runs site-bootstrap.yml on all 3 VMs (WireGuard + passwordless sudo)
  handoff_console.sh                # Clone repo + deploy age key + operator SSH key to saconsole + bring up WSL wg0
  revert_to_fresh.sh                # Revert all 3 VMs to "Fresh Install" snapshot + start + wait SSH
  create_console.sh                 # VBoxManage: import console OVA (called by create_vms.sh)
  create_target.sh                  # VBoxManage: import target OVA + NAT port forwarding
  provision_targets.sh              # Runs on saconsole: full Ansible provisioning (all plays)
  utils.sh                          # Shared helpers sourced by all vbox scripts (tg_notify)
  full_provision.sh                 # One-command wrapper: ensure_vms → revert → wireguard → handoff → provision
                                    #   Phase 0 creates any missing VMs from esacp-base.ova (SKIP_SSH_WAIT=1)
                                    #   Sets NO_TELEGRAM=1; sends single Telegram summary on exit
  cloud-init/
    target1/{user-data,meta-data}   # DHCP networking; WireGuard provides stable overlay
    target2/{user-data,meta-data}

# VBox rebuild sequences:
# VBox rebuild sequences:
#   One-command (any state):  bash platforms/vbox/full_provision.sh  ← Phase 0 creates missing VMs
#   Full rebuild (VMs gone):  create_vms.sh → install_wireguard.sh → handoff_console.sh
#   Iterative test loop:      revert_to_fresh.sh → install_wireguard.sh → handoff_console.sh
#   From saconsole (both):    bash /opt/esacp/platforms/vbox/provision_targets.sh

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
  inventory/dev.yml                 # VirtualBox hosts: saconsole, target1, target2
  group_vars/all.yml                # alert_profile default + WireGuard network vars
  group_vars/kvm.yml                # SSH vars + wg_hub_endpoint for KVM guests
  group_vars/vbox.yml               # SSH vars + wg_hub_endpoint for VBox guests
  group_vars/lab.yml                # alert_profile: drill
  group_vars/production.yml         # alert_profile: production (enforced)
  site-kvm.yml                      # Top-level KVM playbook (4 plays)
  site-vbox.yml                     # Top-level VBox playbook (3 plays)
  roles/
    wireguard/                      # Hub/spoke config; hub sets UFW forward policy
    node_exporter/                  # Binary install + systemd for targets
    mariadb/                        # Docker Compose: MariaDB 10.11 + mysqld_exporter 0.15.1
                                    #   deploy_dir: /opt/mariadb; mysqld_exporter port: 9104
    desktop/                        # xfce4 + x2goserver for saconsole
    observability/tasks/main.yml    # Profile-aware template + force-recreate + UFW rules
    observability/templates/
      prometheus.yml.j2             # Jinja2 template — host label = {{ inventory_hostname }};
                                    #   target1+target2 jobs gated on 'kvm' OR 'vbox' in group_names;
                                    #   mariadb-target1/target2 jobs included in same gate

docker/observability/
  docker-compose.yml                # Stack definition
  prometheus/prometheus.yml         # SOURCE — not deployed directly; rendered via template above
  prometheus/alerts/                # Production alert rules (12 alerts)
  prometheus/alerts-drill/          # Drill alert rules (same, faster)
  grafana/provisioning/
    datasources/datasources.yml     # UIDs pinned: prometheus, loki
    dashboards/json/                # node-exporter-full, cadvisor, management-console, mariadb

docs/
  RUNBOOK.md                        # Operational runbook for all 10 scenarios
  SETUP_GUIDE.md                    # Setup instructions (VirtualBox + KVM paths)
  BuildOutProcedure.md              # Step-by-step operator rebuild guide (KVM path)
  SystemOverview.md                 # Non-technical system description
  SystemOverview_tech.md            # Technical system description (developer-facing)

prototypes/
  cytoscape/                        # Cytoscape.js standalone prototype (Vite + vanilla JS)
                                    # Dev: cd prototypes/cytoscape && npm run dev
                                    # Access: http://localhost:5173 (WSL → Windows)
                                    # node_modules/ and dist/ are gitignored
```

---

## Unified CLI — tools/esacp.py

Single entry point for the full lab lifecycle. All defaults come from config files
(`hosts_map.yml`, `ansible/group_vars/`). Run from the project root:

```
python tools/esacp.py <subcommand> [options]
```

| Subcommand | What it does |
|---|---|
| `confirmPrerequisites` | Checks required tools and files; offers to `apt install` missing packages |
| `validateKeys` | SOPS-decrypts `config/wireguard/keys.sops.yml`; verifies all key blocks exist |
| `clearKnownHosts` | Removes stale `~/.ssh/known_hosts` entries for all ESACP VMs (hostnames, nicknames, IPs) |
| `destroyVM <vm>` | Shows what will be deleted, asks for confirmation, then destroys VM + all storage |
| `buildVM <vm>` | Builds seed ISO → creates VM → polls for autoinstall completion → polls SSH |
| `provisionVM <vm>` | SSH check → Fresh Install snapshot → Ansible (task names + changes only) → Baseline snapshot |
| `verifyVPN` | Pings each VM's WireGuard IP; shows `wg show` on hub; cross-VM pings |
| `validateObservability` | Auto-retrieves Grafana creds (env → saconsole .env → prompt); runs 27-check suite |
| `snapShotVM <vm> [name]` | Creates a named snapshot; if name omitted, lists existing snapshots |
| `displayConfiguration` | Rich tree of all user-alterable settings, each annotated with its source file |

`provisionVM` Ansible output filter: shows PLAY headers, ✓ ok tasks, ★ changed tasks, ❌ fatal errors,
and the PLAY RECAP summary. All other output is suppressed.

`validateObservability` credential resolution order: `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD` env vars
→ SSH to saconsole and read `/opt/observability/.env` → interactive prompt.

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

- **`prometheus.yml` is a Jinja2 template**, not a static file. The source reference copy
  lives in `docker/observability/prometheus/prometheus.yml` but is NOT deployed directly.
  The Ansible observability role renders `templates/prometheus.yml.j2` to the VM. Two
  platform-specific values are injected: `host: '{{ inventory_hostname }}'` on the `node`
  scrape job, and the `node-target1` job block is gated on `{% if 'kvm' in group_names %}`.
  Edit the `.j2` file, not the source copy.

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

- **Grafana provisioned dashboards — `${DS_PROMETHEUS}` unresolved**: dashboards
  downloaded from Grafana.com use an `__inputs` block and `${DS_PROMETHEUS}` as a
  datasource placeholder (the import-dialog maps this to a real datasource). When a
  dashboard is provisioned from a file (not UI import), Grafana 10 does NOT resolve
  `${DS_PROMETHEUS}` — every panel and template variable has no datasource and renders
  nothing. Fix: replace all `${DS_PROMETHEUS}` occurrences with the pinned datasource
  UID (`prometheus`) and remove the `__inputs` block. Use the object form:
  `{"type": "prometheus", "uid": "prometheus"}` to match Grafana 10 native format.

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

- **`wg_hub_endpoint`**: Platform-aware variable that replaces the formerly hardcoded
  `192.168.122.10` in `wg0.conf.j2`. Set in `group_vars/kvm.yml` (192.168.122.10) and
  `group_vars/vbox.yml` (operator must set this to console VM's current bridged DHCP IP).

- **generate_inventory.py backend filter**: Only hosts with `backend: kvm` (or no backend
  field) are written to `kvm.yml`. VBox and future CloudStack hosts are excluded via
  `attrs.get("backend", "kvm") != "kvm"` check. VBox hosts use `ansible/inventory/dev.yml`.

- **VBox bootstrap sequence**: Targets connect via WireGuard IPs after provisioning but
  first Ansible run (before WireGuard) requires the bridged DHCP IP. Use `-e ansible_host=<IP>`
  on the command line for the first run; revert to WireGuard IP thereafter.
  Get DHCP IP: `VBoxManage.exe guestproperty get target1 '/VirtualBox/GuestInfo/Net/0/V4/IP'`

- **MariaDB Docker Compose on targets**: Deployed to `/opt/mariadb/`. MariaDB port 3306 is
  Docker-internal only (not exposed to host). mysqld_exporter port 9104 is UFW-restricted to
  10.10.0.1 (saconsole). Credentials are in `/opt/mariadb/.env` (mode 0600).
  The compose file is templated — edit `ansible/roles/mariadb/templates/docker-compose.mariadb.yml.j2`.

- **mysqld_exporter v0.15.x — `DATA_SOURCE_NAME` removed**: In v0.15.x, the `DATA_SOURCE_NAME`
  environment variable is no longer supported. Credentials must come from a `.my.cnf`-style
  config file. Three pitfalls discovered:
  1. The container's `HOME` may be unset, so the default `~/.my.cnf` resolves to `.my.cnf`
     in the working directory — not `/root/.my.cnf`. Always pass `--config.my-cnf=<absolute-path>`
     explicitly via `command:` in the compose service.
  2. Volume mounts with relative paths (`./my.cnf`) don't resolve correctly when compose is
     invoked with `-f /absolute/path/docker-compose.yml` from a different directory. Use
     `{{ mariadb_deploy_dir }}/my.cnf` (absolute) in the compose template.
  3. The container runs as non-root (`nobody`). The my.cnf file must be mode `0644` (not `0600`)
     or the process cannot read it.
  Template: `ansible/roles/mariadb/templates/my.cnf.j2`. Mounted at `/etc/mysqld_exporter/my.cnf`.

- **VirtualBox NAT source IP in UFW**: SSH connections from WSL2 to VBox target VMs via NAT
  port-forwarding (127.0.0.1:2222/2223) appear inside the VM as source `10.0.2.2` — the
  VirtualBox NAT gateway address. `allowed_ssh_ips` in `group_vars/vbox.yml` must include
  `10.0.2.2`, otherwise UFW blocks all Ansible connections and SSH banner exchange times out.
  `10.0.2.2` is confirmed via `ss -tnp` and `/var/log/auth.log` inside the VM.

- **`ansible_become_pass` required on fresh VMs**: Before the `common` role installs
  passwordless sudo, Ansible cannot escalate privileges without being given the password
  explicitly. Add `-e ansible_become_pass=wawa` (bootstrap password for OVA-built targets)
  for any full provisioning run against a freshly imported VM. Not required on re-runs.

- **VirtualBox snapshot detection bug** (fixed): `snapshot_exists()` in
  `revertToBaseline.py` previously matched only top-level snapshot names. Fixed to
  match `SnapshotName*=` prefix for nested snapshots.

- **SSH polling and autoinstall** (handled automatically): `provision_kvm.py` detects
  whether a VM is mid-autoinstall by probing SSH for 30s after `create_vms.sh`. If SSH
  is unreachable, it waits up to 30 min for the VM to power off (autoinstall complete),
  then starts it. Normal post-boot SSH is then ready in ~30s. Run `provision_kvm.py`
  immediately after `create_vms.sh` — no manual waiting required.

- **known_hosts must be cleared on VM rebuild**: after destroying and recreating VMs,
  the new host keys differ from the cached entries and SSH rejects connections.
  Clear with: `ssh-keygen -R saconsole && ssh-keygen -R target1 &&
  ssh-keygen -R 192.168.122.10 && ssh-keygen -R 192.168.122.11`

- **Docker daemon race on first boot** (fixed in docker role): after `daemon.json` is
  written, the `notify: restart docker` handler can leave Docker in a failed state before
  the observability role runs `docker-compose pull`. Fixed by adding `meta: flush_handlers`
  + `service: state=started retries=5 delay=5` at the end of the docker role to confirm
  the daemon is running before any downstream role uses it.

- **Secrets**: `ansible/group_vars/all.sops.yml` holds encrypted credentials
  (Telegram bot token, Grafana admin password). Requires SOPS + age key to decrypt.
  See `SETUP_GUIDE.md` for key setup.

- **UFW enable hangs Ansible over WireGuard tunnel**: enabling UFW on a spoke briefly
  disrupts the WireGuard tunnel, dropping Ansible's SSH connection and hanging
  indefinitely. Fixed in the `firewall` role: `Enable UFW` uses `async: 10 / poll: 0`
  (fire and forget) followed by `wait_for_connection: delay: 5 timeout: 60`.

- **sshpass required on saconsole before running Ansible with `ansible_password`**:
  Ansible wraps all SSH calls in sshpass when `ansible_password` is set, even when key
  auth succeeds. `provision_targets.sh` installs sshpass via apt before invoking
  any `ansible-playbook` command.

- **`provision_targets.sh` pre-generates saconsole SSH keypair**: `dev.yml` uses the
  LAN IP for saconsole (not localhost), so Ansible opens a real SSH connection even for
  self-targeting plays. The keypair is generated and added to saconsole's own
  `authorized_keys` before Ansible runs, so key auth works on the first connection.
  `site-vbox.yml` Play 6 is tagged `controller_wg` and skipped via `--skip-tags` —
  saconsole is the hub; running the spoke role on localhost would overwrite its config.

- **VBox/NEM headless boot stall (intermittent)**: Under Memory Integrity + Hyper-V NEM,
  VMs occasionally stall at the kernel initramfs stage (`Begin: Loading essential drivers`)
  and never complete the boot when started headlessly. VMState shows "running" and VBox NAT
  accepts TCP connections (false positive), but sshd never starts. Root cause: Hyper-V
  starves the guest of CPU cycles until something forces framebuffer access. Almost always
  resolves on the second attempt. `revert_to_fresh.sh` detects this after 300s, saves a
  screenshot to `/tmp/esacp_<vm>_stuck.png`, and exits with a clear retry message.

- **VBoxManage `--machinereadable` silently omits NAT port forwarding rules**: `grep natpf`
  or `grep -i rule` on machinereadable output returns nothing even when rules exist.
  Use human-readable `showvminfo` (without `--machinereadable`) to verify NAT rules.

- **dpkg lock race on `apt install`**: unattended-upgrades can reacquire the dpkg lock
  between `apt-get update` and the install, even after the dpkg wait task passes.
  Fixed in the `common` role with `retries: 10 / delay: 15` on `Install essential packages`.

- **`pkill` SIGTERM kills the shell — `|| true` doesn't save it**: `pkill -f unattended-upgrade || true`
  exits with `rc: -15` (SIGTERM) when `pkill` sends SIGTERM to a process that is an ancestor of the
  current shell. The shell is killed before `|| true` can execute. The fix is `ignore_errors: true` on
  the Ansible task — not a shell-level workaround. `|| true` only handles normal non-zero exit codes,
  not signals.

- **Loki /ready returns 503 for ~30s after fresh provision**: Loki's ingester emits
  "waiting for 15s after being ready" on first startup. `validate_observability.py` will report
  a FAIL on the Loki health check if run immediately after `provision_targets.sh` completes.
  Wait ~30s and re-run — it resolves on its own.

- **Operator SSH key flow (VBox path)**: `handoff_console.sh` copies `~/.ssh/id_ed25519.pub`
  into saconsole's `~/.ssh/authorized_keys` (direct operator SSH access) and to
  `~/.ssh/operator.pub` (read by Ansible). The `common` role reads `operator_ssh_key`
  (from `~/. ssh/operator.pub` on the control node) and installs it on every managed host,
  so the WSL operator can SSH directly to any VM. `operator_ssh_key` is silently skipped
  if `operator.pub` is absent (safe when running Ansible from WSL rather than saconsole).

- **VBox cloud-init files are not applied**: `platforms/vbox/cloud-init/` exists but the
  OVA-based VMs do not use a seed ISO — cloud-init in those files is never executed.
  Hostname, SSH keys, and user setup come entirely from the OVA and Ansible. The `common`
  role sets hostname via the `hostname` module and writes
  `/etc/cloud/cloud.cfg.d/99_preserve_hostname.cfg` to prevent any cloud-init override.

- **WSL sudoers rule required for non-interactive `handoff_console.sh`**: `handoff_console.sh`
  calls `sudo tee /etc/wireguard/wg0.conf`, `sudo chmod`, and `sudo wg-quick` on the WSL host.
  Without a sudoers rule these prompt interactively, breaking unattended runs. One-time setup:
  ```
  echo "you ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/wireguard/wg0.conf, /usr/bin/chmod 600 /etc/wireguard/wg0.conf, /usr/bin/wg-quick, /usr/sbin/wg-quick" \
    | sudo tee /etc/sudoers.d/esacp-wireguard
  sudo chmod 440 /etc/sudoers.d/esacp-wireguard
  ```

---

## Stage 2.x Scope (next)

Stage 2.1 (KVM parallel path) is complete. The architectural direction for Stage 2.x
and beyond was settled in a design session on 2026-03-03. See `docs/ControlPlaneDesign.md`
for the full rationale.

### Architectural Direction: saconsole as Control Plane

The physical host's role is being reduced to a single responsibility: **bootstrap
saconsole**. After that, saconsole manages all sibling VMs by calling back to the
host hypervisor remotely:

- **KVM**: via `qemu+ssh://host/system` (libvirt remote protocol)
- **VirtualBox**: via VBoxWebSrv SOAP API or SSH → VBoxManage
- **CloudStack**: via CloudStack API over HTTPS (cleanest case)

This eliminates the need for `revertToBaseline.py`, `run_scenario.py`, and
`provision_kvm.py` to run on the physical host after bootstrap. `esacp.py` becomes
the pipeline engine called by saconsole's REST API, not a human-facing CLI.

### Source of Truth: Generate Cloud-init from hosts_map.yml

Cloud-init `user-data` files are currently static and duplicate data from
`hosts_map.yml` (hostname, virbr0 IP, OS username). They must become generated
artifacts, like `ansible/inventory/kvm.yml`:

- Add `vm_user` to `hosts_map.yml` per host (or as KVM default)
- Create `tools/generate_cloud_init.py` — renders `user-data.j2` templates
- Add `esacp.py generateConfig` subcommand to run all generators
- Cloud-init files: do not edit directly (same convention as inventory)

### Production vs Lab/Dev Distinction

Two classes of parameter, explicitly separated in `hosts_map.yml`:

- **Live-safe** (Production): alert thresholds, scrape intervals, dashboards,
  notification channels — Grafana manages these; Ansible pushes in-place, no rebuild
- **Rebuild-required** (Lab/Dev): hostnames, IPs, WireGuard subnet, OS username —
  changing these triggers `destroyVM → buildVM → provisionVM` pipeline

### Grafana Control Plane (staged implementation)

A REST API on saconsole wraps `esacp.py` and exposes VM lifecycle operations over
HTTP. The Grafana UI calls this API. Implementation stages:

1. **Canvas + HTML panel** — Grafana Canvas for topology visualisation (node colour
   = live VM state); separate HTML panel with action buttons. Functional immediately.
2. **draw.io embedded** — draw.io self-hosted on saconsole; shape actions POST to
   the API; diagram XML mirrors `hosts_map.yml` structure.
3. **Custom Grafana app plugin** — React + Cytoscape.js; live metric overlays;
   inline job progress; integrated action menus.

PlantUML and Mermaid.js are suitable for architecture documentation only — they
cannot bind to live data or fire API calls.

### Remaining Platform Work

- **Platform 3** (Ubuntu Server + X2Go): external VPS via CloudStack API
- **Platform 4** (macOS): Homebrew toolchain; external VPS same as Platform 3
- `hosts_map.yml` `backend:` field per host (`vbox` | `kvm` | `cloudstack`)

### Chaos framework on KVM
Port `orchestration/chaos/run_scenario.py` and `scenarios.yml` to work
against KVM VMs (Platform 2), replacing VirtualBox-specific assumptions.
Will be driven from the saconsole REST API once that exists.

### Version watchdog + staging rebuild pipeline
Monitor upstream releases of all pinned components (Prometheus, Grafana, Loki,
Promtail, cAdvisor, node_exporter, Alertmanager, Docker CE, Ansible collections,
Ubuntu LTS). Trigger from-scratch rebuild on staging VMs, run the proof-of-life
checklist automatically, report pass/fail before promoting to the main lab.
Motivated by the cAdvisor/Promtail SDK compatibility issues found in Stage 2.1.
