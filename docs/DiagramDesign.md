# ESACP — Cytoscape Control Plane Diagram Design

Design session: 2026-03-21
Status: Planning — implementation in progress

---

## Purpose

The diagram is a **business operations console**, not a network diagram for engineers.
The family asks: *Is the ERPNext site up? Is the right version running? Can I safely
deploy a change? How do I flip staging to production?* The diagram answers those
questions visually and enables those actions.

The AI agent (Claude) queries MCP connectors for deep technical detail — Loki config,
Prometheus scrape intervals, iptables rules. The diagram surfaces only what a family
member engaged in ERPNext development or maintenance needs to see and act on.

---

## VM Fleet Model

All environments use **paired VMs**:

| VM | Role | Services |
|---|---|---|
| `*-master` | Primary | ERPNext (frappe bench) + MariaDB (master) + Redis + Nginx |
| `*-slave`  | Replica | MariaDB (replica of master) only |

The replica provides read failover and backup without downtime. The ERPNext
application connects to the master; the slave is a hot standby and backup source.

Environments:

| Environment | Pair | Domain |
|---|---|---|
| Production  | `prod-master` + `prod-slave`     | `erp.company.com` |
| Staging     | `staging-master` + `staging-slave` | `staging.company.com` |
| Dev (N)     | `dev1`, `dev2`, …                | local only |

saconsole manages all environments. DNS flip (blue-green deployment) is the
mechanism for promoting staging to production.

---

## Diagram Hierarchy

### Level 0 — Topology (the map)

Machines as nodes, edges as WireGuard connections.

**Node colour by role:**

| Role | Colour | Notes |
|---|---|---|
| saconsole (control plane) | blue | hub node, always present |
| production-master | green | live ERPNext |
| production-slave  | green (lighter) | MariaDB replica |
| staging-master    | amber | candidate for next production |
| staging-slave     | amber (lighter) | MariaDB replica |
| dev               | grey | any number |
| controller        | dashed | Mighty or future controller |

**Edge health:** WireGuard handshake age — green < 3 min, yellow < 10 min, red otherwise.

**Node actions (visible on click):** snapshot, revert, provision, destroy.
Unprovisioned nodes (newly drawn) have a dashed amber border until provisioned.

---

### Level 1 — Services (click any machine)

Shows containers/services running on that machine. Grouped:

| Group | Services | Drill-down |
|---|---|---|
| **ERPNext stack** | bench, mariadb, redis, nginx | Yes — see Level 2 |
| **Observability** | prometheus, grafana, loki, alertmanager, promtail, cAdvisor | Status + version only — collapsed by default |
| **MCP layer** | mcp-grafana, dbhub, nginx-ui | Status + endpoint only |

The observability group is collapsed by default. Family members maintaining
ERPNext do not need to expand it; the AI agent queries it directly via MCP.

---

### Level 2 — ERPNext application state (bench service)

The heart of the console. Shows what matters for maintaining and enhancing ERPNext:

```
Site: erp.company.com
  Apps:   frappe 15.x.x    erpnext 15.x.x    custom_app 1.2.0
  Maintenance mode:  OFF                      [Toggle]
  Pending migrations: none
  Last bench update: 2026-03-18

Runtime:
  Python:   3.11.x  ✓
  Node.js:  18.x.x  ✓   (frappe v15 requires 18)
  yarn:     1.22.x  ✓

Database: erp_company  (mariadb, 2.3 GB)
  Last backup: 4h ago  ✓
```

**Node.js and Python versions** are shown with traffic-light indicators relative
to the known requirements for the installed frappe version. A wrong Node.js version
passes `bench start` but silently breaks `bench build-js` — this is a common silent
failure point that must be visible without SSH.

**Actions:**
- Toggle maintenance mode (on/off)
- Trigger bench update
- Run pending migrations
- Open site in browser

**MCP source:** ERPNext MCP (`Frappe_Assistant_Core` or equivalent) — **future**.
Until available: container status only; frappe-level fields are placeholders.

---

### Level 2 — Nginx (nginx service)

Active server configs in human terms:

```
erp.company.com     → bench:8000   SSL ✓  expires 2026-08-12  (157 days)
staging.company.com → bench:8000   SSL ✓  expires 2026-09-01  (176 days)
```

SSL expiry colorised: green → yellow at 30 days → red at 7 days.

**MCP source:** nginx-ui MCP — **live now**.

---

### Level 2 — MariaDB (mariadb service)

```
erp_company   2.3 GB   last backup: 4h ago  ✓   role: master
_sys           12 MB

Replication:
  slave:  prod-slave   lag: 0.3s  ✓
```

**Actions:** trigger backup, open Grafana dashboard.
On the slave node, shows replication lag and master identity.

**MCP source:** dbhub MCP — **live now** (schema/query); backup status via node_exporter
filesystem metrics.

---

## Blue-Green / DNS Flip

First-class operation — not buried in a node detail view.

A **Deployments panel** (sidebar or tab) shows the current mapping:

```
Production  ──►  prod-master      erp.company.com → 1.2.3.4    erpnext 15.28.0
Staging     ──►  staging-master   staging.company.com → 5.6.7.8  erpnext 15.29.1

             [  Promote Staging → Production  ]
```

The promote operation:
1. Confirms: "You are about to make staging-master (15.29.1) the live production
   server. The current production server (15.28.0) will become staging. Continue?"
2. Updates DNS A record for `erp.company.com` → staging-master IP
3. Updates DNS A record for `staging.company.com` → prod-master IP
4. Swaps node role colours in the diagram

**MCP source:** Cloudflare MCP — **future** (when DNS is on Cloudflare).
Until available: shows current state as read-only; flip requires manual DNS change.

---

## What Needs MCP vs What Is Already Available

| Diagram panel | MCP source | Status |
|---|---|---|
| Container status / versions | saconsole REST API (tools/api.py) | **Partial — job runner live** |
| Nginx config + SSL expiry | nginx-ui MCP | **Live now** |
| MariaDB databases / sizes | dbhub MCP | **Live now** |
| Observability health | mcp-grafana | **Live now** |
| Frappe site list, apps, versions | ERPNext MCP | **Future — core deliverable** |
| Node.js / Python / yarn versions | ERPNext MCP or SSH | **Future** |
| Maintenance mode toggle | ERPNext MCP | **Future** |
| Bench update trigger | ERPNext MCP | **Future** |
| MariaDB replication lag | Prometheus / mysqld_exporter | Available via Grafana |
| DNS A records (live) | Cloudflare MCP | **Future** |
| DNS flip (blue-green) | Cloudflare MCP | **Future** |

---

## What NOT to Show in the Diagram

The AI agent queries these via MCP in conversation — they do not need diagram panels:

- Loki / Promtail internal configuration
- Prometheus scrape intervals and alert rule bodies
- iptables rules and WireGuard key material
- Docker network bridge details
- cAdvisor or node_exporter internals
- Ansible role variables

---

## Implementation Sequence (ordered by family value)

1. ✅ **Topology from live data** — machines, roles, WireGuard mesh (done)
2. ✅ **Draw + provision a target** — right-click → configure → buildVM + provisionVM (done)
3. **Nginx drill-down** — use live nginx-ui MCP; show domains, SSL expiry
4. **MariaDB drill-down** — use live dbhub MCP; show databases, sizes, replication state
5. **Master/Slave topology** — paired VM model; slave nodes shown with replication edge
6. **Deployments panel** — static DNS state first; wired to Cloudflare MCP when ready
7. **ERPNext MCP** — bench state, app versions, Node.js/Python check, maintenance mode
8. **Production/staging promotion** — DNS flip with confirmation dialog

---

## Open Decisions

| Decision | Options | Status |
|---|---|---|
| ERPNext MCP | `Frappe_Assistant_Core` (bench app, OAuth2) vs `rakeshgangwar/erpnext-mcp-server` (TypeScript, no bench needed) | Undecided — evaluate against actual ERPNext deployment |
| DNS provider | Cloudflare (has MCP) vs manual | Undecided |
| Replication monitoring | Prometheus mysqld_exporter `Seconds_Behind_Master` metric vs dbhub query | Undecided |
| Diagram persistence | Topology from `hosts_map.yml` only (current) vs diagram state saved separately | `hosts_map.yml` is authoritative; diagram is a view, not a store |
