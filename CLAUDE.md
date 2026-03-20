# ESACP — Claude Code Project Context

Enterprise System Administration & Chaos Planning
A home-lab infrastructure automation and observability training project.

---

## Session Protocol

**At the start of every session**, before doing anything else:

1. **Identify the platform** — which controller machine are you on?
2. **Run the sync check** for that platform:
   - KVM/Xubuntu (Mighty): *(sync check TBD)*
   - VBox/WSL: `bash platforms/vbox/sync_check.sh` *(platform retired — for reference only)*
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
| Stage 2.2 | 🔧 In Progress | Remote KVM hypervisor (toshiba): saconsole bootstraps target1+target2 with MariaDB+MariaDB MCP+Nginx UI+node_exporter; mcp-grafana on saconsole |
| Stage 2.x | 🔜 Next | Heterogeneous fleet: CloudStack backend, chaos on KVM, version watchdog |

---

## Architecture

### Controller Role (bootstrap only)

Controller machines (Mighty, Ultra, a future MacBook, any Ubuntu Server) have **one
job**: bootstrap saconsole. After saconsole is running, the controller steps back.
saconsole manages all sibling VMs by calling back to the hypervisor directly.

**Ultra** (the specific Windows 11 machine) died — hardware failure, spontaneous
reboots, 2026-03-17. **VirtualBox will never be used again** — Hyper-V always made
more sense. Windows/WSL2 as a controller platform remains valid and may be revisited
on a future machine. VBox scripts in `platforms/vbox/` are preserved as reference;
they will need adaptation for a Hyper-V/WSL2 path if that work resumes.

| # | Controller OS | Hypervisor / VPS | Status |
|---|---|---|---|
| 1 | Windows 11 + WSL2 | Hyper-V (replaces VBox) | ⏸ On hold — no hardware |
| 2 | Xubuntu (Mighty) | KVM/libvirt — remote (toshiba) | 🔧 Stage 2.2 in progress |
| 3 | Ubuntu Server + XFCE + X2Go | External VPS (iwStack/CloudStack) | 🔜 Planned |
| 4 | macOS | External VPS (iwStack/CloudStack) | 🔜 Planned |

### Production Topology (target state)

The final fleet is **heterogeneous by design**. saconsole manages all targets
regardless of where they live. The `backend:` field in `hosts_map.yml` is a
per-host routing key — not a lab-wide flag. A single chaos run can span local
KVM VMs, CloudStack pay-by-the-minute instances, and dedicated servers simultaneously.

| Layer | Hosting | Backend |
|---|---|---|
| saconsole (control plane) | VM on 1 owned physical server (e.g. toshiba) | kvm |
| Production targets | 2 pay-by-month dedicated/VPS servers | kvm or cloudstack |
| Dev targets | Local KVM VMs on owned server | kvm |
| Staging targets | CloudStack VMs (pay-by-minute, ephemeral) | cloudstack |

Example mixed config: 2 local KVM dev targets + 2 CloudStack staging targets, all
provisioned and managed from saconsole in a single Ansible run.

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

### Stage 2.2: toshiba — Remote KVM Hypervisor

- **Hypervisor host**: toshiba — Ubuntu 20.04.6, KVM/libvirt 6.0.0, virt-install 2.2.1
- **LAN IP**: 192.168.40.16 — SSH alias: `toshy` — SSH user: `hasan`
- **Storage**: system disk 98% full — ALL VM images on LUKS-encrypted 1TB disk
  - Stable mount: `/mnt/esacp-disk` (fstab + crypttab, requires passphrase on reboot)
  - libvirt pool `esacp` → `/mnt/esacp-disk/var/lib/libvirt/images/` (540 GB free)
- **`--os-variant`**: toshiba's osinfo-db (Ubuntu 20.04 stock) tops out at `ubuntu20.04` —
  both `ubuntu22.04` and `ubuntu24.04` are absent. Use `ubuntu20.04` in all `virt-install`
  calls on this host.
- **virsh session**: plain `virsh` = user session (`qemu:///session`). Always use
  `virsh --connect qemu:///system` or `sudo virsh` for pool/VM operations.
- **Bootstrap — saconsole**: `platforms/kvm/bootstrap_saconsole.sh` *(built — Stage 2.2)*
  9 phases: seed ISO → upload → VM create → autoinstall wait → "Fresh Install" snapshot →
  Ansible provision (saconsole only, ProxyJump through toshy) → "Stage 2.2 Baseline"
  snapshot → handoff (saconsole SSH pubkey → toshiba authorized_keys). Controller ends here.
  **Note**: Play 5 (controller WireGuard spoke) requires toshiba UDP 51820 port-forward first.
- **Bootstrap — targets**: `platforms/kvm/bootstrap_targets.sh` *(built — Stage 2.2)*
  Runs FROM saconsole after `control_plane` role applied. 9 phases: inject saconsole pubkey →
  build seed ISOs (envsubst) → upload → VM create → wait → "Fresh Install" snapshot →
  Ansible provision (direct virbr0 — no ProxyJump) → "Stage 2.2 Targets Baseline" snapshot.
  Cloud-init templates: `platforms/kvm/cloud-init/toshiba-target{1,2}/`
- **site-kvm.yml plays** (5 total): base-all → saconsole (docker+obs+desktop+control_plane+mcp_grafana)
  → authorise saconsole pubkey on targets → targets (node_exporter+docker+mariadb+nginx_ui) → controller WG
- **MCP servers** (Stage 2.2):
  - `mcp-grafana` on saconsole — `grafana/mcp-grafana:0.11.3`, SSE on port 8000,
    joins `observability_network`, endpoint: `http://10.10.0.1:8000/sse`
  - `MariaDB MCP` on each target — built from source (no published image), SSE on port 9001,
    endpoint: `http://10.10.0.3:9001/sse` / `http://10.10.0.4:9001/sse`
  - `Nginx UI MCP` on each target — `uozi/nginx-ui:v2.3.5`, admin/MCP on port 9000,
    endpoint: `http://10.10.0.3:9000/mcp?node_secret=<secret>`
- saconsole then manages sibling VMs via `qemu+ssh://hasan@toshiba/system`

### Stage 1–1.5: Platform 1 Detail (VirtualBox/WSL — on hold)
- **Host**: Windows 11 (Ultra) + WSL2 + VirtualBox — **Ultra is dead (hardware failure)**
- Windows/WSL2 as a controller platform is not abandoned — may resume on future hardware
- VirtualBox will not be used again; Hyper-V is the intended hypervisor for any Windows path
- Scripts in `platforms/vbox/` preserved as reference; will need Hyper-V adaptation if resumed

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

platforms/vbox/                     # RETIRED (Stage 1–1.5, VBox). Scripts preserved as reference for future Hyper-V/WSL2 adaptation.

platforms/kvm/
  bootstrap_saconsole.sh            # Stage 2.2: idempotent 9-phase bootstrap for toshiba saconsole
                                    #   Phases: seed ISO → upload → VM create → wait → snapshot → Ansible → snapshot → handoff
                                    #   ProxyJump through toshy; skips Play 5 (controller WireGuard)
  bootstrap_targets.sh              # Stage 2.2: idempotent 9-phase bootstrap for toshiba targets
                                    #   Runs FROM saconsole; injects saconsole pubkey via envsubst
                                    #   Direct virbr0 SSH (no ProxyJump); provisions both target1+target2
  create_seeds.sh                   # cloud-localds wrapper for seed ISOs (Mighty path — Stage 2.1)
  create_vms.sh                     # virt-install for both VMs (Mighty path — Stage 2.1)
  snapshot.py                       # virsh snapshot lifecycle CLI
  cloud-init/
    saconsole/{user-data,meta-data}
    target1/{user-data,meta-data}         # Stage 2.1 (Mighty) — hardcoded hasan_mighty pubkey
    toshiba-target1/{user-data,meta-data} # Stage 2.2 (toshiba) — ${CONTROLLER_PUBKEY} placeholder
    toshiba-target2/{user-data,meta-data} # Stage 2.2 (toshiba) — ${CONTROLLER_PUBKEY} placeholder

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
    mariadb/                        # Docker Compose: MariaDB 10.11 + mysqld_exporter 0.15.1 + MariaDB MCP
                                    #   deploy_dir: /opt/mariadb; mysqld_exporter port: 9104; mcp port: 9001
                                    #   mariadb-mcp image built from source (no published image): /opt/mariadb-mcp-build
    mcp_grafana/                    # Docker Compose: grafana/mcp-grafana:0.11.3 on saconsole
                                    #   deploy_dir: /opt/mcp-grafana; SSE port: 8000; joins observability_network
                                    #   endpoint: http://10.10.0.1:8000/sse (WireGuard peers only)
    nginx_ui/                       # Docker Compose: uozi/nginx-ui:v2.3.5 on targets
                                    #   deploy_dir: /opt/nginx-ui; HTTP port: 80; admin/MCP port: 9000
                                    #   MCP endpoint: http://<target-wg-ip>:9000/mcp?node_secret=<secret>
                                    #   Headless setup via NGINX_UI_NODE_SKIP_INSTALLATION env var
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

- **MariaDB MCP has no published Docker image**: `MariaDB/mcp` must be built from source.
  The `mariadb` Ansible role clones `https://github.com/MariaDB/mcp.git` to
  `/opt/mariadb-mcp-build` and runs `docker build -t mariadb-mcp:local` on first deploy.
  The build is skipped if the `mariadb-mcp:local` image already exists. SSE transport
  runs on port 9001; `ALLOWED_HOSTS: "*"` is set (lab is WireGuard-isolated).
  UFW restricts port 9001 to saconsole's WireGuard IP (10.10.0.1) only.

- **Nginx UI bundles nginx — do not run a separate nginx container**: `uozi/nginx-ui`
  is built on top of the official `nginx` image. A separate nginx container is not needed.
  The `/etc/nginx` volume must be EMPTY on first run — map a fresh directory.
  Port 80 = nginx HTTP; port 9000 = nginx-ui admin UI + REST API + MCP SSE endpoint.
  nginx-ui does NOT expose Prometheus-format metrics; rely on node_exporter for host metrics.

- **nginx-ui headless setup**: Set `NGINX_UI_NODE_SKIP_INSTALLATION=true` plus
  `NGINX_UI_PREDEFINED_USER_NAME`, `NGINX_UI_PREDEFINED_USER_PASSWORD`, and
  `NGINX_UI_NODE_SECRET` in the env file to bypass the first-run web wizard.
  Without these, the container waits at the `/install` page and MCP is unavailable.
  Credentials are in the `nginx_ui` role's `.env` template (sourced from SOPS vars).

- **mcp-grafana joins observability_network as external network**: The observability
  stack creates `observability_network` (name: `observability_network`). The mcp-grafana
  compose declares it as `external: true` and joins it — this lets mcp-grafana reach
  `grafana:3000` by container name without port exposure. Start the observability stack
  before starting mcp-grafana or the network will not exist.

- **Claude Code MCP configuration** (add to `~/.claude/settings.json` on Mighty after
  target VMs are up and WireGuard mesh is verified):
  ```json
  "mcpServers": {
    "grafana": { "type": "sse", "url": "http://10.10.0.1:8000/sse" },
    "mariadb-target1": { "type": "sse", "url": "http://10.10.0.3:9001/sse" },
    "mariadb-target2": { "type": "sse", "url": "http://10.10.0.4:9001/sse" },
    "nginx-target1": { "type": "sse", "url": "http://10.10.0.3:9000/mcp?node_secret=<secret>" },
    "nginx-target2": { "type": "sse", "url": "http://10.10.0.4:9000/mcp?node_secret=<secret>" }
  }
  ```

- **ERPNext MCP (future)**: `Frappe_Assistant_Core` (buildswithpaul/promantia-ai) — bench app, OAuth 2.0, 20+ tools. Alt: `rakeshgangwar/erpnext-mcp-server` (TypeScript, no bench required). Add MCP endpoint to `~/.claude/settings.json` when ERPNext is deployed.

- **Cloudflare MCP (future)**: Assessed as worthwhile. Key caution: API token must be tightly scoped (read-only where possible, zone-locked for writes) — a broad token in an MCP container is high blast-radius.

- **`virsh snapshot-create-as` on libvirt 6.0.0 via SSH**: multi-word snapshot names are
  split at spaces when passed through SSH (argv is joined into a single shell string).
  Use `ssh host bash -c "virsh ... 'Name With Spaces' --atomic"` — not `remote virsh ...`.
  `bootstrap_saconsole.sh` uses this pattern in `take_snapshot()` and `snapshot_exists()`.

- **iptables FORWARD ordering on KVM hosts**: libvirt + Docker both add chains to FORWARD.
  The default FORWARD policy is DROP. Any custom ACCEPT rule appended with `-A` lands after
  libvirt's `LIBVIRT_FWI` chain (which REJECTs unmatched traffic to virbr0). Always insert
  with `-I FORWARD 1` to place the rule before libvirt/Docker chains.

- **toshiba WireGuard port-forward**: for Mighty's wg0 to reach saconsole's hub (virbr0
  192.168.122.10:51820) via toshiba (192.168.40.16), two iptables rules are required on
  toshiba — the DNAT in nat/PREROUTING and an ACCEPT inserted at position 1 in FORWARD:
    sudo iptables -t nat -A PREROUTING -i wlp2s0 -p udp --dport 51820 \
        -j DNAT --to-destination 192.168.122.10:51820
    sudo iptables -I FORWARD 1 -i wlp2s0 -o virbr0 -p udp \
        -d 192.168.122.10 --dport 51820 -j ACCEPT
  These rules are not persistent across reboots — see Stage 2.x for persistence plan.

- **Both controller and hypervisor virbr0 share 192.168.122.0/24**: every KVM host gets
  this subnet by default. Mighty's routing table claims 192.168.122.0/24 for its own
  virbr0, so it can never reach toshiba's 192.168.122.10 directly. ProxyJump through
  toshy is structurally required (not optional) for all Ansible and SSH access to
  toshiba-hosted VMs. Mighty's wg0 endpoint must always be toshiba's LAN IP, not virbr0.

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

- **SSH polling and autoinstall** (handled automatically): `provision_kvm.py` detects
  whether a VM is mid-autoinstall by probing SSH for 30s after `create_vms.sh`. If SSH
  is unreachable, it waits up to 30 min for the VM to power off (autoinstall complete),
  then starts it. Normal post-boot SSH is then ready in ~30s. Run `provision_kvm.py`
  immediately after `create_vms.sh` — no manual waiting required.

- **known_hosts must be cleared on VM rebuild**: after destroying and recreating VMs,
  the new host keys differ from the cached entries and SSH rejects connections.
  Clear with: `ssh-keygen -R saconsole && ssh-keygen -R target1 &&
  ssh-keygen -R 192.168.122.10 && ssh-keygen -R 192.168.122.11`

- **Secrets**: `ansible/group_vars/all.sops.yml` holds encrypted credentials
  (Telegram bot token, Grafana admin password). Requires SOPS + age key to decrypt.
  See `SETUP_GUIDE.md` for key setup.

- **`esacp.py snapShotVM` is KVM-only**: hardwired to `platforms/kvm/snapshot.py` → `virsh`.
  On VBox/WSL use `bash platforms/vbox/take_snapshots.sh "name"` instead.

- **Loki /ready returns 503 for ~30s after fresh provision**: Loki's ingester emits
  "waiting for 15s after being ready" on first startup. `validate_observability.py` will report
  a FAIL on the Loki health check if run immediately after `provision_targets.sh` completes.
  Wait ~30s and re-run — it resolves on its own.

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
