# ESACP — Control Plane Architecture Design

Brainstorming session: 2026-03-03
Status: Draft — decisions pending implementation

---

## Problem Statement: Multiple Sources of Truth

The Stage 2.1 implementation exposed a structural tension: `hosts_map.yml` is the
intended single source of truth, but several generated or quasi-generated artifacts
duplicate its data independently:

- `ansible/inventory/kvm.yml` — generated from `hosts_map.yml` by `generate_inventory.py`
- `platforms/kvm/cloud-init/hub-autoinstall.*.j2` — Jinja2 templates rendered from
  `hosts_map.yml` by `tools/pipeline/orchestration/hub_seed_iso.py` (hub) and
  `tools/pipeline/stages/stage_1_vm_creation/seed_iso.py` (targets)
- `ansible/group_vars/kvm.yml` — contains `ansible_user` which must match the OS
  username in cloud-init

Resolution status: cloud-init dynamic generation landed via #202. All generated
artifacts now derive from `hosts_map.yml`:

```
hosts_map.yml
  │
  ├─► ansible/inventory/kvm.yml                  (generate_inventory.py)
  ├─► platforms/kvm/<hub>-seed.iso              (hub_seed_iso.py + hub-autoinstall.*.j2)
  └─► platforms/kvm/<target>-seed.iso           (seed_iso.py — inline cloud-config)
```

---

## Architectural Shift: saconsole as Control Plane

### The Bootstrap Division

The physical host's role is minimal and well-defined: **bootstrap saconsole, then
step back.** The bootstrap requires only a small, stable manifest:

| Parameter | Example | Notes |
|---|---|---|
| saconsole hostname | `saconsole` | Rarely changes |
| saconsole virbr0 IP | `192.168.122.10` | Fixed at virbr0 subnet allocation |
| saconsole WireGuard IP | `10.10.1.1` | Fixed as hub |
| WireGuard subnet | `10.10.1.0/24` | Defines the management network |
| Hypervisor type | `kvm` / `vbox` / `cloudstack` | Selects the backend driver |
| Hypervisor reach | SSH key + gateway IP (KVM); VBoxWebSrv URL (VBox); API key (CloudStack) | How saconsole calls back |
| Admin credentials | Grafana password, age key | Secrets only |

Everything else — sibling VM names, IPs, WireGuard spokes, alert configs, chaos
scenarios — is defined and managed from saconsole after bootstrap. The physical host
only re-runs `esacp.py buildVM saconsole` if the control plane itself needs rebuilding.

### Remote Hypervisor Management (not nested virtualisation)

saconsole manages sibling VMs by calling back to the host hypervisor over the
network. Each backend is well-supported:

| Hypervisor | Mechanism | Notes |
|---|---|---|
| KVM/libvirt | `qemu+ssh://host/system` remote URI; `libvirt-python` | Production-grade; full virsh lifecycle remotely |
| VirtualBox | VBoxWebSrv SOAP API (port 18083) or SSH → VBoxManage | VBoxWebSrv ships with VirtualBox; Python SDK available |
| CloudStack | CloudStack API over HTTPS | No host-level access needed; cleanest case |

For KVM: saconsole needs an SSH key trusted on the Xubuntu host and the host user in
the `libvirt` group. All virsh operations (create, start, stop, snapshot, revert,
destroy) then work remotely from saconsole.

**Practical note — seed ISOs:** `virt-install` requires seed ISOs in the host's
storage pool (`/var/lib/libvirt/images/`). saconsole generates the seed ISO and
SCPs it to the host before calling `virt-install` remotely. One extra step, fully
automatable.

**Trust boundary:** A guest VM with hypervisor management rights over the host is
a meaningful security boundary. For a lab this is acceptable; document it explicitly
and scope the SSH key to the minimum required (libvirt group only, no root).

---

## Production vs Lab/Dev: The Core Distinction

| Class | Parameters | Who manages | Mechanism |
|---|---|---|---|
| **Production / Live-safe** | Alert thresholds, scrape intervals, dashboard layouts, notification channels, Grafana provisioning | Grafana — edit and apply in-place | Ansible push to running system; no rebuild |
| **Lab/Dev / Rebuild-required** | Hostnames, virbr0 IPs, WireGuard IPs and subnet, OS username, VM disk/memory | Control plane pipeline | destroyVM → buildVM → provisionVM |

This distinction should be **explicit in `hosts_map.yml`** — rebuild-required
parameters annotated or grouped so a pipeline can detect that a proposed change
requires a rebuild rather than an in-place push.

Changing a live-safe parameter: Grafana UI → Ansible push → done.
Changing a rebuild-required parameter: edit `hosts_map.yml` → `generate_cloud_init.py`
→ `destroyVM` → `buildVM` → `provisionVM`.

**The Grafana UI should not expose rebuild-required parameters for in-place edit.**
Topology changes are code changes that go through the pipeline.

---

## Grafana as Operational Control Plane

### The Vision

The topology diagram IS the operational view: nodes show live VM status (running /
stopped / degraded), edges show WireGuard connectivity, clicking a node exposes
actions (snapshot, revert, destroy, provision). Committing topology changes
(rebuild-required) triggers the pipeline. Adjusting live-safe parameters applies
immediately.

### Why PlantUML Is the Wrong Tool

PlantUML is a rendering engine: write DSL → get static SVG. It supports `[[URL]]`
hyperlinks (open a browser tab on click). It cannot:
- Bind node colour to live metric data
- POST to an API with a request body
- Show async job progress
- Support topology editing

Mermaid.js has the same limitation. Both are appropriate for architecture
documentation embedded in Grafana Text panels — not for operational control.

### Viable Technology Stack

**Visualisation layer (in priority order):**

1. **Grafana Canvas** (built-in, Grafana 9+) — shapes bindable to metrics,
   click → navigate to URL. Good starting point for topology visualisation;
   actions limited to navigation. Zero additional dependencies.

2. **draw.io (diagrams.net) self-hosted on saconsole** — full topology editor,
   shape right-click actions can POST to saconsole's API, XML diagram format
   can map directly to `hosts_map.yml` structure. Pragmatic middle ground with
   a real editor UI.

3. **Cytoscape.js inside a custom Grafana app plugin** — designed for
   network/graph topology, full click/hover events → API calls, live metric
   overlays on nodes, layout algorithms. Correct long-term answer. Higher
   development effort.

**Action layer (the essential piece):**

A lightweight REST API on saconsole (FastAPI, ~300 lines) that wraps `esacp.py`:

```
POST /api/vm/create        { vm, template }    → { job_id }
POST /api/vm/snapshot      { vm, name }        → { job_id }
POST /api/vm/revert        { vm, snapshot }    → { job_id }
POST /api/vm/destroy       { vm }              → { job_id }
GET  /api/vm/status                            → { vm: state, ... }
GET  /api/jobs/{id}                            → { status, progress, log }
```

Commands that take time return a job ID immediately. The diagram polls
`/api/jobs/{id}` and reflects progress on the relevant node. This is standard
async job pattern — no special Grafana features needed.

`esacp.py` is already the pipeline engine. The API is an HTTP wrapper around it.
The diagram is a UI on top of the API.

### Staged Implementation

**Stage A — Visualisation + manual actions:**
Grafana Canvas for topology (nodes coloured by live VM status from `/api/vm/status`).
Separate HTML panel with action buttons POSTing to the API. Not elegant, functional,
buildable in a day.

**Stage B — Integrated editor:**
draw.io self-hosted on saconsole, embedded via iframe in Grafana. Shape context menus
POST to the API. The draw.io XML schema mirrors `hosts_map.yml` — the diagram and
the config converge toward the same data model.

**Stage C — Custom control panel:**
Grafana app plugin (React + Cytoscape.js). Live metric overlays on nodes, inline
job progress, integrated action menus. The complete operational control plane.

---

## Impact on esacp.py

`esacp.py` remains essential at two levels:

1. **Bootstrap CLI** — runs on the physical host to build saconsole. Always required
   for initial setup and for saconsole self-rebuild.

2. **Pipeline engine** — called by the saconsole REST API to execute VM lifecycle
   operations. Each subcommand should therefore work well when called
   non-interactively (clean stdout, meaningful exit codes, no TTY prompts).

Design principle: `esacp.py` is the engine; Grafana + the API is the cockpit.

---

## Deferred: Cloud-init Generation

The immediate fix for the source-of-truth problem:

- Add `vm_user` to `hosts_map.yml` (per host or as a KVM default)
- Create `tools/generate_cloud_init.py` — renders `user-data.j2` templates per VM
- Cloud-init files become generated artifacts: do not edit directly
- `esacp.py generateConfig` (new subcommand) runs both generators

This resolves the `ansible_user` vs cloud-init `username` divergence that surfaced
during Stage 2.1 as a VM buildVM failure.

---

## Open Decisions

| Decision | Options | Status |
|---|---|---|
| Grafana control panel technology | Canvas → draw.io → Cytoscape.js plugin | Staged; start with Canvas |
| REST API framework | FastAPI / Flask | Undecided; FastAPI preferred (async, OpenAPI docs) |
| draw.io embedding | iframe in Grafana / separate port on saconsole | Undecided |
| `hosts_map.yml` schema for rebuild-required annotation | Comment convention / explicit field / separate section | Undecided |
| saconsole hypervisor access grant | esacp.py subcommand (`grantHypervisorAccess`) / manual SSH key + libvirt group | Undecided |
