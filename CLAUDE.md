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

**One objective per session.** This is a hard rule.

**Bug workflow** — whenever a bug is found, regardless of what else is happening:
1. Open a GitHub issue immediately (`gh issue create --repo martinhbramwell/ESACP`)
2. Fix the code, committing with `fixes #N` in the message
3. Close the issue with the commit hash

Do this at the moment of discovery — not at session end. The issue must exist before the fix commit so the commit can reference it.

**Issues review** — at the start of any session where the objective involves bug fixing or infrastructure work, run `gh issue list --repo martinhbramwell/ESACP --state open` and close any issues that are already resolved but were not closed at the time. Context degrades across
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
| Stage 2.2 rebuild | ✅ Verified | `bash platforms/kvm/rebuild_lab.sh` proven end-to-end from bare disk; 3 cold-start bugs found and fixed (issues #6 #7 #8); estate rebuilt and **fully operational** (all 3 VMs running, all 5 MCP endpoints healthy) |
| Stage 2.3 | 🔧 In progress | Cytoscape control plane prototype: draw-to-provision UI + FastAPI backend; diagram design spec (master/slave pairs, blue-green DNS flip) captured in `docs/DiagramDesign.md` |
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
- **MCP endpoints**: mcp-grafana `http://10.10.0.1:8000/sse`; dbhub targets `http://10.10.0.{3,4}:9001/sse`; nginx-ui `http://10.10.0.{3,4}:9000/mcp?node_secret=<secret>`
- saconsole manages sibling VMs via `qemu+ssh://<hypervisor-alias>/system`

### Stage 2.1: Platform 2 (KVM/Xubuntu — superseded by toshiba path)
Mighty-local VMs at virbr0 192.168.122.10/11. Provisioned via `orchestration/provision_kvm.py` → `ansible/site-kvm.yml`. Superseded by Stage 2.2 remote-toshiba path; scripts preserved.

### Observability Stack (Docker Compose on saconsole)
All services in Docker at `/opt/observability/`. Ports: Prometheus 9090, Grafana 3000, Loki 3100, Alertmanager 9093, node_exporter 9100, cAdvisor 8080. Promtail 3.3.2 (3.x required — Docker CE 25+ needs SDK v1.44+). node_exporter runs `network_mode: host` + `pid: host`; Prometheus reaches it via `host.docker.internal:9100`. Alert profiles: `alerts/`=production (2–10m); `alerts-drill/`=drill (20–30s). KVM hosts → `lab` group → drill.

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
  prepare_hypervisor.sh             # Pre-bootstrap: check + apply controller prereqs; check hypervisor state
                                    #   Controller side auto-installs (cloud-image-utils, ansible, collections)
                                    #   Hypervisor side: check + fix guidance (no sudo over SSH)
                                    #   Run before bootstrap_saconsole.sh on any new hypervisor host
  rebuild_lab.sh                    # One-command full rebuild: destroy → bootstrap_saconsole → bootstrap_targets
                                    #   Phase 3 SSHes to saconsole (ProxyJump toshy) and runs bootstrap_targets.sh there
                                    #   Sends Telegram notification on success/failure
  destroy_vms.sh                    # Tear down all 3 VMs on toshiba (virsh destroy + undefine --remove-all-storage)
                                    #   Also removes local + remote seed ISOs and clears known_hosts
  utils.sh                          # Shared Telegram helper (tg_notify) — sourced by rebuild_lab.sh
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
    saconsole/{user-data,meta-data} # includes cloud-image-utils in packages (required by bootstrap_targets.sh)
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
  DiagramDesign.md                  # Cytoscape control plane diagram spec: 3-level hierarchy,
                                    #   master/slave VM pairs, blue-green DNS flip, MCP source mapping
  FailoverDesign.md                 # Production master failover design (artisan SLA, human-triggered)
                                    #   DRAFT — must be revised once ERPNext v13 is in staging
                                    #   Covers: topology, gaps, procedure, UI implications, open questions

tools/
  api.py                            # FastAPI control plane backend (port 8088) — prototype
                                    #   GET  /api/hosts              → kvm hosts + IP suggestions + default hypervisor
                                    #                                   (returns vm_role field: dev | master | slave)
                                    #   POST /api/hosts/add          → append to hosts_map.yml, regen inventory
                                    #                                   (accepts zone, vm_role; writes zone-based ansible_groups)
                                    #   POST /api/provision/{host}   → job: cloud-init + WG + buildVM + provisionVM
                                    #                                   + saconsole WireGuard hub update (Step 5)
                                    #   POST /api/provision/erpnext  → template-based deploy: vol-clone + --import + differentiation
                                    #                                   Steps 1-8: WG peer, seed ISO, vol-clone, boot, SSH wait, Baseline snapshot, saconsole WG
                                    #                                   Steps 9-18: WG spoke, envars.sh, bench new-site, rsync apps+BaRe+BKP,
                                    #                                     BaRe symlink, ddlViews.sql, installApps.sh, handleRestore.sh, bench restart,
                                    #                                     snapshot "ERPNext v13 Logichem DB Restored"
                                    #   POST /api/promote            → stub: Staging→Production initiation (Telegram approval deferred)
                                    #   GET  /api/jobs               → list all jobs (for page-refresh reconnect)
                                    #   GET  /api/jobs/{id}          → poll job status + log
                                    #   provisioned = VM has a snapshot containing "Baseline" (not just VM exists)
                                    #   Start: uvicorn tools.api:app --port 8088 --reload (from project root)
                                    #   Will move to saconsole when promoted from prototype

prototypes/
  cytoscape/                        # Cytoscape.js prototype (Vite + vanilla JS). Run: uvicorn tools.api:app --port 8088 + bash doCytoscape.sh → http://localhost:5173
                                    # 4-quadrant layout (Console/Dev/Staging/Prod), HTML zone overlays (not compound nodes — GH #15),
                                    # drag-to-rezone, stockroom templates, draw-to-provision end-to-end. See project_cytoscape_pending.md.
  cytoscape/src/api.js              # Fetch helpers for the FastAPI backend (/api proxy via Vite)
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

- **`bootstrap_targets.sh` runs FROM saconsole**: saconsole's `~/.ssh/id_ed25519` is the only key authorised in targets' cloud-init. Controller key has no access. Requires `cloud-image-utils` on saconsole (in saconsole/user-data packages). Entry point: `platforms/kvm/rebuild_lab.sh`.

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

- **GitHub MCP** (`github/github-mcp-server` v0.32.0): binary at `/usr/local/bin/github-mcp-server`;
  configured in `~/.claude/settings.json` as `type: stdio`. Uses `gh auth token` (gho_*) scoped to
  `repo, read:org, admin:public_key, gist`. Gives AI sessions direct query access to Issues, PRs,
  and repo content — the institutional memory query interface. Repo: `martinhbramwell/ESACP`.

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
  These rules are persistent: `iptables-persistent` is installed on toshiba and rules are
  saved to `/etc/iptables/rules.v4` via `netfilter-persistent save`. To reapply or update,
  run `platforms/kvm/persist_iptables_toshiba.sh` directly on toshiba (requires sudo TTY —
  use `scp` + `ssh -t`, not pipe via stdin).

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

- **ContainerRestartLoop alert**: `{name!=""}` filter excludes cAdvisor's root cgroup entry. (GH #39)

- **Promtail docker_sd_configs**: Docker socket mount required; logs appear under `container_name` not `job`. (GH #40)

- **Promtail systemd-journal**: 3 extra mounts required — `/run/log/journal`, `/var/log/journal`, `/etc/machine-id` (all `:ro`). (GH #41)

- **cAdvisor dashboard template variables**: use concrete metric names in `label_values()` — Grafana 10 blocks `{__name__=~"..."}` selectors. (GH #42)

- **Grafana provisioned dashboards**: `${DS_PROMETHEUS}` not resolved from files — replace with pinned UID `prometheus`, remove `__inputs` block. (GH #43)

- **cAdvisor Docker SDK**: pin `gcr.io/cadvisor/cadvisor:v0.55.1` — v0.47/v0.49 embed API v1.41, incompatible with Docker CE 25+. (GH #44)

- **generate_inventory.py backend filter**: Only hosts with `backend: kvm` (or no backend
  field) are written to `kvm.yml`. VBox and future CloudStack hosts are excluded via
  `attrs.get("backend", "kvm") != "kvm"` check. VBox hosts use `ansible/inventory/dev.yml`.

- **`hypervisor` field in hosts_map.yml**: Optional per-host field that controls where
  `esacp.py buildVM` creates the VM. `hypervisor: <hypervisor-alias>` routes to the remote
  KVM host via SSH (`scp` seed ISO, `ssh <hypervisor-alias> bash -c "virt-install --connect
  qemu:///system ..."`). No field → local controller KVM (Stage 2.1 path). All current
  remote-hosted VMs carry the appropriate hypervisor value.
  `generate_inventory.py` reads this field and injects
  `ansible_ssh_common_args: "-o ProxyJump=<user>@<hypervisor-alias>"` for all remote-hosted
  hosts — so Ansible reaches them via ProxyJump from the controller.

- **Remote-hosted VMs: SSH key authorisation split**: target1 and target2 were bootstrapped
  via saconsole (saconsole's pubkey in authorized_keys). Ansible from the controller reaches
  them via ProxyJump but cannot authenticate with the controller key — saconsole's key is
  required for those hosts. New VMs built through the Cytoscape prototype use the target1/
  cloud-init template which hardcodes the controller's pubkey, so the controller can
  provision them directly via ProxyJump. This split is intentional for the prototype stage.

- **`esacp.py buildVM`**: uses `virsh vol-create-as` + `virsh vol-upload` for seed ISO — not `sudo cp` (hangs in uvicorn threads). (GH #46)

- **MariaDB Docker Compose on targets**: Deployed to `/opt/mariadb/`. MariaDB port 3306 is
  Docker-internal only (not exposed to host). mysqld_exporter port 9104 is UFW-restricted to
  10.10.0.1 (saconsole). Credentials are in `/opt/mariadb/.env` (mode 0600).
  The compose file is templated — edit `ansible/roles/mariadb/templates/docker-compose.mariadb.yml.j2`.

- **mysqld_exporter v0.15.x**: `DATA_SOURCE_NAME` removed — use `--config.my-cnf=<absolute-path>`; file mode must be `0644` (runs as `nobody`). (GH #45)

- **known_hosts must be cleared on VM rebuild**: after destroying and recreating VMs,
  the new host keys differ from the cached entries and SSH rejects connections.
  Clear with: `ssh-keygen -R saconsole && ssh-keygen -R target1 &&
  ssh-keygen -R 192.168.122.10 && ssh-keygen -R 192.168.122.11`

- **Secrets**: `ansible/group_vars/all.sops.yml` holds encrypted credentials
  (Telegram bot token, Grafana admin password). Requires SOPS + age key to decrypt.
  See `SETUP_GUIDE.md` for key setup.

- **Cytoscape zone frames must be HTML overlays, not compound nodes** (GH #15): Cytoscape
  compound nodes cause three fatal bugs: (1) empty zones collapse to zero size at (0,0);
  (2) attribute selectors like `node[!provisioned]` bleed onto zone nodes (no VM data → falsy
  → matched); (3) phantom anchor selectors lose specificity battles against VM style rules.
  Use `<div id="zone-overlay">` with absolutely-positioned child panels instead. Position them
  via `_graphToScreen()` on every `pan zoom resize` event. Phantom anchors must have
  `provisioned: true` in data and use a class+attribute selector (`node.phantom[phantom="yes"]`,
  specificity 21) placed *after* the base VM style in the CY_STYLE array.

- **Cytoscape zone geometry single source of truth**: zone panels, the splitter handle, and
  `_zoneAtPos()` must all derive coordinates from the same `splitX/splitY` values via
  `_graphToScreen()`. Any divergence causes VMs to visually land in one zone while being
  assigned to another. `_updateQuadAnchors()` clamps and writes `splitX/splitY` then calls
  `_constrainVMsToZones()` — both the frames and the sheep move together.

- **`esacp.py snapShotVM` is KVM-only**: hardwired to `platforms/kvm/snapshot.py` → `virsh`.
  On VBox/WSL use `bash platforms/vbox/take_snapshots.sh "name"` instead.

- **Loki `/ready` returns 503 for ~30s** on first start — wait before running `validate_observability.py`. (GH #47)

---

## Stage 2.x Scope (next)

See `docs/ControlPlaneDesign.md`. Heterogeneous fleet: CloudStack backend, chaos on KVM, version watchdog, Platforms 3+4.
