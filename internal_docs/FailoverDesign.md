# Production Master Failover — Working Design Document

> **DRAFT — DO NOT USE AS AN OPERATIONAL RUNBOOK**
> This document is a design record based on knowledge of the current production system
> prior to local v13 staging. All steps marked "verify" are unconfirmed assumptions.
> This document must be revised in full once ERPNext v13 is available in staging and
> the failover sequence has been walked through against real software versions.

*Created: 2026-03-22. Status: Draft pending v13 staging validation.*

---

## Purpose

This document captures the agreed failover model for production master failure, the known
gaps that must be closed before it is reliable, and the design implications for the
Cytoscape control plane UI.

It covers **unplanned production master failure only** — hardware fault, disk failure,
or unrecoverable service crash. Planned software promotion (staging → production) is a
separate operation; see `internal_docs/DiagramDesign.md` (DNS flip workflow).

---

## SLA Context — Artisan Policy

This is a family-operated manufacturing business, not a commercial SaaS product.

- **Acceptable recovery time**: service restored by early the following business day
- **Failure mode**: users are informed, work is paused; no overnight panic escalation
- **Implication**: automated failover is not required; a reliable human-triggered
  runbook is sufficient and safer than automation misfiring on a partial failure
- **Implication**: replication lag of seconds or minutes at the moment of failure is
  acceptable — note the gap, document what (if anything) was lost, proceed

---

## Current Production Topology

```
prod-master   ERPNext (frappe bench) + MariaDB (master) + Redis + Nginx
              Hosted: Contabo.com, Missouri, USA

prod-slave    MariaDB (replica of prod-master) only
              Hosted: Prometeus.net, Netherlands
```

**ERPNext must not run on the slave.** ERPNext cron jobs write to the database. If bench
were started on the slave while MariaDB replication is active, those writes would
propagate back toward the master and corrupt the replication chain. This constraint
applies during normal operation only — once replication is stopped and the slave is
promoted to a standalone master, bench can and must be started there.

Geographic separation makes simultaneous hardware failure very unlikely. The credible
risk is logical corruption propagating through replication before it is detected.

---

## What Is Already in Place

| Mechanism | Status | Notes |
|---|---|---|
| MariaDB replication (master → slave) | Running | Standard binlog replication |
| inotify/rsync (file attachments) | Running | Syncs `sites/*/private/files/` and `sites/*/public/files/` master → slave |
| Replication health watchdog | Running | Master cron increments a watchdog table every ~10 min; both machines run `qmaria -e "select * from watchdog;"` and compare; discrepancy → Telegram group alert |
| Database backups | Running | Every 4 hours; retained 24 hours — **retention needs improvement** |
| Service health monitoring | Running | Prometheus / Alertmanager → Telegram (mysqld_up, node metrics) |
| Telegram approval gate | Agreed | Same gate used for planned DNS-flip promotions |
| Failover bash scripts | Existing | Scripts handle promotion steps and dump restore (with embedded URL rewriting) |

---

## Known Gaps — Must Be Closed or Assessed

### Gap 1 — Backup retention (24 hours is insufficient)

Current: backups taken every 4 hours, retained 24 hours. A corruption event discovered
after 24 hours has no clean restore point. The propagated-corruption risk profile
(master corrupts → replicates to slave) makes this the most important gap to close.

**Action**: evaluate retention policy when ERPNext v13 volume is known. Off-site storage
already exists (geographic separation); the question is frequency and retention window.

### Gap 2 — Replication health watchdog: what it covers and what it does not

The watchdog (DB table increment → replication → comparison) confirms that **database
replication is live**. It does not directly confirm that the inotify/rsync daemon for
file attachments is still running.

A more definitive database replication check is to compare binary log coordinates
(GTID position or binlog file + position) between master and slave directly. This
eliminates the need for a synthetic watchdog table and detects lag or split-brain
immediately.

**Action**: during v13 rebuild, determine whether binlog coordinate comparison can
replace or supplement the watchdog table approach. File attachment sync should have
its own independent health signal (e.g. a file-modification timestamp written by the
rsync daemon periodically, readable on the slave).

### Gap 3 — Archive compression / off-machine file backup

The rsync sync is master → slave (same estate, different continent). There is no
third-location archive of file attachments.

**Action**: assess priority relative to other gaps. Geographic separation mitigates
simultaneous loss. Logical corruption (propagated delete/corruption) is the real
exposure. Decide on archive frequency and destination when v13 file volume is known.

### Gap 4 — Failover procedure last tested 2+ years ago

The procedure works in principle (has been performed) but the exact steps have not
been verified against the current MariaDB version, bench version, or replication
configuration. A bash script handles key steps including the dump restore with
embedded URL rewriting.

**Action**: walk through the full sequence on local dev VMs during the v13 rebuild
session. Verify each step against current software versions. Update the runbook below
with exact commands.

---

## Failover Procedure (current best knowledge — verify against v13)

### Pre-conditions to check before starting

The master may be inaccessible, so all checks are slave-side or monitoring-side.

1. Slave MariaDB is running and healthy
2. Replication watchdog: check last known state from monitoring; note how stale it is
3. Binary log coordinates (if accessible): note the last replicated position
4. File attachment sync: check last modification timestamps on slave-side files to
   estimate how current the file state is
5. Accept the data state as-is — note any estimated gap, proceed

### Step 1 — Telegram approval

Notify the authorised group: master is down, proposing failover to slave.
One approval required to proceed. Record approver and timestamp.

### Step 2 — Stop replication on the slave and promote to standalone master

```sql
STOP SLAVE;
RESET SLAVE ALL;
```

Verify `read_only` is OFF. The slave is now an independent MariaDB instance.
The existing bash script handles this step — *verify script path during v13 rebuild*.

### Step 3 — Start ERPNext on the slave

Bench has not been running on the slave (must not run while replication was active).
Start it now.

*Verify*: whether any configuration change is needed before `bench start`, or whether
the slave's bench config already points at `localhost` MariaDB and can start directly.
The existing failover bash scripts may handle any required config changes — confirm
during v13 rebuild.

### Step 4 — Confirm the site loads

Log in, navigate to a known record, verify attachments are present. Check that
background workers and the scheduler have started cleanly.

### Step 5 — Notify users

Inform users of the URL. This is either:
- The existing production domain (if DNS is updated to the slave IP), or
- A direct IP or alternate hostname as a temporary measure

DNS update is optional at this stage — restoring access takes priority.

### Step 6 — Document the incident

Record: time of failure, time of recovery, estimated data gap (replication lag at
failover time), file sync staleness, and any transactions that may have been lost.
File in the Telegram group. This record is needed when rebuilding the old master.

---

## Recovery — Rebuilding the Old Master as a New Slave

When the original master machine is repaired:

1. **Do not start MariaDB as a master** — its data is stale relative to the promoted
   slave. Starting it immediately would create two diverged masters.

2. Take a dump from the current master (promoted slave). The existing bash script
   handles this, including editing embedded site URLs in the text dump to match the
   correct hostname.

3. Restore the dump to the old master and configure it as a replica of the current
   master.

4. Verify replication catches up and the watchdog comparison passes.

5. Resume inotify/rsync file sync: flow is now from new master (promoted slave) to
   old master (new slave). Verify attachment timestamps.

6. The estate is restored to a healthy master + slave pair with swapped roles.
   This is intentional — no further rename required unless specific tooling depends
   on fixed hostnames.

---

## Design Implications for the Cytoscape UI

### Production quadrant — what to show

| Element | Source | Status |
|---|---|---|
| Master: MariaDB running | Prometheus `mysqld_up` | Live now |
| Master: ERPNext bench running | Process / Prometheus | Needs endpoint |
| Slave: replication lag | Prometheus `mysqld_exporter` (`Seconds_Behind_Master`) | Live now |
| Slave: replication position vs master | Binlog coordinates | Verify feasibility |
| Slave: last watchdog match | Watchdog cron result | Live now |
| Slave: file attachment sync heartbeat | To be defined (Gap 2) | Not yet |

### Failover button behaviour

- Visible on the Slave node in **both Production and Staging quadrants** — the same
  Master/Slave pair model applies in both, and the same failover mechanics apply
- **Inactive** (greyed) when Master is healthy
- **Arms** (becomes clickable) when Master is detected unreachable, or when manually
  armed by an authorised operator (maintenance window scenario)
- Clicking opens a checklist panel, not a one-click action: shows pre-condition
  states from the table above, asks operator to acknowledge each
- On proceed: triggers Telegram approval gate → on approval, executes Steps 2–4
  via saconsole API
- Post-failover: node roles swap in the diagram; Slave node relabelled "Master
  (failover active)"; former Master node shown as "Unreachable / Standby"

### What the UI must not do

- Auto-trigger failover without operator initiation
- Show a green master node when health data is stale (stale = worse than unknown)
- Allow failover to proceed if slave MariaDB is itself unhealthy

---

## Open Questions — Verify During ERPNext v13 Rebuild Session

Many of these will be answered by reading the existing failover bash scripts.

1. **Failover script inventory**: what scripts exist, what each one does, and what
   sequence they are run in. Map these to the steps in this document.

2. **Bench config on the slave**: does the slave VM have bench installed? Is it
   configured to connect to `localhost` MariaDB, or does it need a config edit on
   promotion? The scripts likely answer this.

3. **Bench service management on v13**: `supervisord`, `systemd`, or manual `bench
   start`? Determines Step 3 commands.

4. **Binlog coordinate check**: can binary log position be compared between master
   and slave without a running master? (Slave stores last known master position in
   relay log metadata.) Assess as replacement for watchdog table.

5. **Backup retention**: what is the right retention window for this business? What
   storage cost is acceptable? Resolve once v13 data volume is known.

6. **DNS TTL** on the production domain. Relevant to recovery Step 6 and to the
   DNS-flip planned promotion workflow. Should be pre-lowered before any promotion.

---

## Relationship to Other Documents

| Document | Relationship |
|---|---|
| `internal_docs/DiagramDesign.md` | DNS-flip / planned promotion workflow; Production quadrant layout spec |
| `internal_docs/CategoriesOfCatastrophe.md` | Risk inventory that motivated this document; Categories 2 and 5 most relevant |
| `internal_docs/RUNBOOK.md` | Operational runbook; verified failover steps should be added as a scenario here |
| `ansible/roles/mariadb/` | MariaDB deployment config; replication setup lives here |
