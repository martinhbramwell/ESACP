# ESACP — Claude Code Project Context

---

## Mission & Vision

**Mission**: A family-owned manufacturing business runs a heavily customised ERPNext system
built by one developer who cannot be permanently available. A replacement cannot be hired or
trained. The mission is a self-repairing, AI-assisted platform that lets family members
maintain and enhance the ERP themselves — guided step by step, with graphical tutorials, by
an AI that has live access to every layer of the system via MCP connectors.

**Vision**: The system is never finished. It grows with the business — deepening its
understanding of operations, trajectory, and each person's role. The owner and family have
an advisor that knows their systems as well as the original developer did, is always available,
and compounds in value over time rather than walking out the door.

**What this means for every session**:
- The ERPNext MCP connector is the core deliverable. The VMs, observability stack, WireGuard
  mesh, and MCP framework all exist to make that connector reliable and permanently accessible.
- Every commit, doc, and CLAUDE.md update is a deposit into institutional memory. A future
  session on any machine must be able to sit beside a family member and be useful immediately.
- Self-repair means the system survives the absence of any single person — including the
  original developer and the current operator.
- The Cytoscape/Grafana control plane is the family's operational window into their business.
  It is not a network diagram for engineers.

---

## Session Protocol

**At the start of every session**, before doing anything else:

1. **Identify the platform** — which controller machine are you on?
2. **Run the sync check** for that platform:
   - KVM/Xubuntu (Mighty): `bash platforms/kvm/sync_check.sh`
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
| Stage 2.2 | ✅ Complete | Remote KVM hypervisor (toshiba): saconsole bootstraps target1+target2 with MariaDB+dbhub MCP+Nginx UI+node_exporter; mcp-grafana on saconsole; all 5 MCP servers configured in Claude Code settings |
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

**VPS Provider**: iwStack/cdStack (Prometeus, Milan/Rome) — CloudStack API via `CloudMonkey` or Python SDK; pay-as-you-go (€1 = 1 cdCredit); disk snapshots schedulable via API.

**macOS hosting** (Platform 4): MacStadium/Mac Mini Vault/MacinCloud — controller-only workload, lowest tier suffices.

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

**Alert profiles**: `alerts/` = production (`for:` 2–10m); `alerts-drill/` = drill (20–30s). KVM hosts land in `lab` group → drill. Ansible role refuses to run drill profile against `production` group.

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
    mariadb/                        # Docker Compose: MariaDB 10.11 + mysqld_exporter 0.15.1 + bytebase/dbhub MCP
                                    #   deploy_dir: /opt/mariadb; mysqld_exporter port: 9104; mcp port: 9001
                                    #   dbhub:0.18.0 published image (no local build); SSE at /sse on port 9001
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

`python tools/esacp.py <subcommand> [options]` — run from project root; `--help` lists all subcommands.

Non-obvious behaviours:
- `provisionVM` Ansible output filter: shows PLAY headers, ✓ ok, ★ changed, ❌ fatal, RECAP only.
- `validateObservability` credential order: `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD` env vars → SSH saconsole `/opt/observability/.env` → interactive prompt.

---

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

- **MariaDB MCP uses bytebase/dbhub (not MariaDB/mcp)**: `MariaDB/mcp` main branch now
  pulls `sentence-transformers` → PyTorch/CUDA (~3.5GB), causing `docker build` to fail
  on 20GB target VMs with "no space left on device". Switched to `bytebase/dbhub:0.18.0` —
  a lightweight published image (no local build). SSE transport on port 9001 (internal 8080,
  `--transport http`); endpoint `http://<target-wg-ip>:9001/sse` unchanged.
  UFW restricts port 9001 to saconsole's WireGuard IP (10.10.0.1) only.
  DSN passed via `--dsn mariadb://${MYSQL_USER}:${MYSQL_PASSWORD}@mariadb:3306/${MYSQL_DATABASE}`
  in the compose command (docker-compose expands `.env` vars before passing to container).

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

- **Play 5 (controller WireGuard) requires `wg_hub_endpoint` in site-kvm.yml vars**:
  Play 5 runs on `hosts: localhost` with `connection: local` and does not inherit
  `group_vars/kvm.yml` (which defines `wg_hub_endpoint: "192.168.122.10"`). The controller's
  hub endpoint is toshiba's LAN IP (`192.168.40.16`) — not saconsole's virbr0 IP — because
  Mighty's own virbr0 owns `192.168.122.0/24`. The var is now hardcoded in the Play 5 vars
  block in `site-kvm.yml`: `wg_hub_endpoint: "192.168.40.16"`.

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

- **cAdvisor Docker SDK**: `gcr.io/cadvisor/cadvisor:v0.47.2` and `v0.49.1` embed
  Docker SDK API v1.41; Docker CE 25+ requires v1.44 minimum. Use `v0.55.1`.
  `ghcr.io/google/cadvisor` tags do NOT exist despite the README claiming migration there —
  stay on `gcr.io/cadvisor/cadvisor`.

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

See `docs/ControlPlaneDesign.md` for full rationale (design session 2026-03-03).

- saconsole becomes control plane: manages VMs via `qemu+ssh://host/system`, CloudStack API, or VBoxWebSrv; `esacp.py` becomes its REST API pipeline engine
- Cloud-init → generated from `hosts_map.yml` via `tools/generate_cloud_init.py`; do not edit directly (same as inventory)
- Live-safe params (thresholds, dashboards): push in-place. Rebuild-required params (IPs, hostnames, WG subnet): trigger `destroyVM → buildVM → provisionVM`
- Grafana control plane: Canvas+HTML panel (immediate) → draw.io embedded → custom React+Cytoscape app plugin
- Platform 3 (Ubuntu+X2Go on CloudStack VPS), Platform 4 (macOS on hosted Mac)
- Chaos on KVM: port `run_scenario.py`+`scenarios.yml`; version watchdog: monitor pinned components, auto-rebuild staging on release
