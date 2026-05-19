# Planning Notes — DNS & Certificate Architecture
## Session: 2026-03-28 ~08:00

---

## Domain Assignments (confirmed)

| Domain | Purpose |
|--------|---------|
| `logichem.solutions` | Production ERPNext — public-facing, staff/customer access |
| `iridium.blue` | Control plane + all dev/staging environments |

Rationale: production traffic never crosses the same domain as lab/development work.
A mistake in a dev VM cannot accidentally reach a production-facing URL.

---

## Certificate Strategy

**No saconsole nginx proxy.** Each VM's ERPNext nginx stack terminates HTTPS directly.

**Wildcard cert `*.iridium.blue`** issued once on saconsole via acme.sh + DNS-01 challenge
(Cloudflare API). Distributed to target VMs via Ansible post-renewal hook.

Why not per-VM certbot: DNS-01 allows wildcard issuance without exposing each VM to the
internet. One cert covers every current and future dev/staging hostname.

**Production (`logichem.solutions`)**: existing cert management stays as-is until
the v13 migration is ready. Not in scope for this session.

---

## DNS Routing Model

Cloudflare DNS maps each VM's hostname directly to its WireGuard IP:
```
lab.target3.iridium.blue  →  10.10.0.6
stg.target2.iridium.blue  →  10.10.0.4
(etc.)
```

Clients reaching these hostnames must be on the WireGuard mesh (staff laptops, VPS, saconsole).
No public internet exposure of ERPNext dev/staging instances.

**DDNS for hub**: saconsole's WireGuard hub is reachable at toshiba's router WAN IP.
That IP is dynamic (home ISP). A cron on saconsole or toshiba will poll `ifconfig.me`
and update a Cloudflare A record (e.g. `hub.iridium.blue`) when the IP changes.
WireGuard spoke configs on remote VPS use this hostname as their endpoint.

---

## Subdomain Naming Scheme — UNDECIDED

Bakes permanently into `bench new-site` name and Cloudflare DNS records.
Hard to change after VMs are provisioned.

Options under consideration:
- `lab.target3.iridium.blue` — site.vm.domain (mirrors ERPNext multi-site mental model)
- `target3.dev.iridium.blue` — vm.zone.domain (matches Cytoscape zone language)
- `lab.iridium.blue` — site.domain (simplest; nginx routes to correct bench by site name)

**Decision required before any DNS record creation or acme.sh role.**

---

## Production VPS Fleet (confirmed 2026-03-28)

4 VPS to support blue-green promotion without downtime:

| Provider | Location | Count | Role |
|----------|---------|-------|------|
| Contabo | USA / Missouri | 2 | Production master (1 active, 1 spare/handover) |
| Prometeus | Netherlands | 2 | Production slave (1 active, 1 spare/handover) |

Promotion flow: staging VM (iwStack CloudStack, ephemeral) → certified → DB sync + rsync
→ spare VPS → DNS flip (Cloudflare API) → spare becomes new production → old becomes spare.

Both Contabo and Prometeus: plain SSH backend. No confirmed programmatic lifecycle API
for either provider's control plane — may require screen-scraping for resize/snapshot/rebuild
admin tasks. For current scope (Ansible over WireGuard SSH), no lifecycle API needed.

**iwStack** (CDLan / Prometeus parent company): this IS the CloudStack API path for
ephemeral staging VMs. Separate service, separate credentials.

---

## acme.sh Ansible Role (planned — not yet built)

Tasks:
1. Install acme.sh on saconsole
2. Configure with `cloudflare_acme_token` (from SOPS)
3. Issue `*.iridium.blue` via DNS-01
4. Cron for auto-renewal
5. Post-renewal hook: push cert to all target VMs via Ansible

---

## Registrar Continuity (GH #48)

Concern raised: if the operator who holds the domain registrar login is unavailable,
renewal, DNS changes, and failover are blocked.
Resolution: document registrar credentials in SOPS (or equivalent secure store)
accessible to a trusted second person. GitHub issue #48 tracks this.
