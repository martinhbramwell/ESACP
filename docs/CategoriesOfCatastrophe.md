# Categories of Catastrophe — Cytoscape Control Plane

*Design review session: 2026-03-21. Context: blue-green DNS-flip deployment UI with Telegram approval gates, MariaDB replication, CloudStack/KVM VMs, family operators.*

---

## Category 1: The DNS Swap Window — Data Written to the Wrong Place

- **TTL not pre-lowered**: If TTL is 3600s, users keep hitting old production for up to an hour after the swap. Writes during that window go to the server now labelled "Staging" — and will be destroyed or overwritten.
- **The gap between check and swap**: Replication lag is checked at T=0. Approval takes minutes. Users write to production throughout. The check is stale by the time the swap fires. Writes must be locked *before* the check, not after.
- **ERPNext file attachments are not in MariaDB**: Uploaded files live on disk. MariaDB replication does not replicate the filesystem. New production is missing every file uploaded since the last manual sync. Nobody notices until a user opens an invoice and the PDF is gone.
- **ERPNext background workers don't know DNS flipped**: Bench scheduler, Redis queue workers, and socketio processes on old production keep running against the old database. Jobs submitted just before the flip are processed by a dead server. Results are orphaned.
- **Old production keeps accepting connections during TTL bleed**: Any client with the IP cached (browser, mobile app, internal system integration) is still writing to old production. This window can be hours, not seconds.

---

## Category 2: Replication Is Not What You Think It Is

- **Replication lag passes the check, then diverges**: "Lag = 0s" at check time. 90 seconds pass during DNS propagation. 50 transactions hit old production master. New production master never receives them. Those 50 transactions are gone.
- **Staging master is a slave to dev master — dev is not clean**: Dev is where experiments happen. Broken migrations, test records, junk data — all replicate into "golden" staging. Staging is only as clean as dev discipline.
- **Severing the dev→staging replication chain at promotion**: When staging becomes production it must immediately stop being a slave to dev. If the automation fails, dev writes contaminate production. Not recoverable without a backup restore.
- **The production slave has never been tested for promotion to master**: An untested failover is not a failover. MariaDB slave-to-master promotion requires: stopping the slave thread, resetting slave status, confirming binary log position, reconfiguring the old master. Any misconfiguration during original setup causes silent data corruption on promotion.
- **GTID vs binlog position mismatch**: Servers provisioned at different times with different replication configs may have incompatible serial counts. Two servers can share a sequence number via different topologies and be completely out of sync.

---

## Category 3: The Telegram Approval Gate Is a Single Point of Failure and a Target

- **No timeout defined**: First approval received, safety checks running — nobody sends second approval. Process hangs in a half-armed state for hours or days. Are users locked out indefinitely during this window?
- **Telegram is down**: Both gates require Telegram. An outage blocks the system completely. Cannot promote, cannot abort, cannot communicate status.
- **Approval from a compromised phone**: Telegram accounts get hijacked. An attacker controlling a group member's account can approve a production DNS flip at 3am. No second factor on the approval itself.
- **Replay or race**: Two promotions triggered in quick succession. Second approval arrives out of order. System promotes, then immediately promotes again — swapping back, or landing in an inconsistent state.
- **Group membership not audited**: Former employees still in the Telegram group can approve. No mechanism to revoke individual approval authority short of removing them from Telegram.
- **Spurious alerts desensitise the group**: False alarms cause members to stop reading carefully. A real "approve this DNS flip" message gets approved reflexively. This is how catastrophic approved-by-accident deployments happen. (Validation gate before first button is the mitigation — see open questions.)

---

## Category 4: The UI Makes Destruction Look Routine

- **Visual clarity is a false safety signal**: A clean diagram with colour-coded frames makes dangerous operations feel managed and safe. The more polished the UI, the more confidently a family member clicks through a workflow they don't fully understand.
- **Drag-and-drop is irreversible**: Dragging the wrong VM from Dev to Staging initiates a clone/build. Undoing it means destroying the staging VM and starting over. No "oops" path exists.
- **Quadrant relabeling surprises**: After promotion, what was "Staging" is now labelled "Production." A family member who wasn't present opens the UI the next day and sees unexpected labels. They assume the labels are wrong and try to "fix" it.
- **UI state not matching reality**: The diagram shows 3 healthy green nodes. One has been down for 6 hours because the health-check loop crashed. The UI is lying with confidence — the most dangerous failure mode in any control plane.

---

## Category 5: The "Golden Staging" Model Is Architecturally Confused

The design conflates two different requirements:

| Requirement | Solution |
|---|---|
| Zero-downtime software deployment | Blue-green DNS flip |
| Fast failover if production master dies | Hot standby slave *in production* |

A staging environment that is simultaneously a test bed, a hot standby, and a continuous replication slave to dev cannot do any of those reliably. It is always wrong for at least two of the three purposes.

**Recommended separation:**

- **Production**: Master + Slave. Slave follows production master only. Never touched by dev.
- **Staging**: Ephemeral. Created fresh per release cycle from a dev snapshot. Tested. Promoted via DNS flip. Then destroyed or briefly retained for rollback.
- **Dev**: Free, experimental, may be broken. Master only (or dev-only slave if replication itself must be tested).

The "golden pair always in staging" model only makes sense if RTO (recovery time from a production failure) is shorter than the time to build and test new staging VMs. For a family business ERP this is unlikely to be the case.

---

## Category 6: CloudStack-Specific

- **Template merge is not a CloudStack primitive**: CloudStack has VM templates (full disk images) and service offerings (compute specs). "Merging" a machine template with a content template means: pick a disk image, apply a service offering at deployment time. The content template IS the disk image. Workable, but the "stockroom merge" metaphor slightly misleads — these are not two independent objects being combined, they are one parameterised deployment.
- **Template freshness**: A content template (ERPNext disk image) baked last month contains last month's software. Deploying it to staging produces stale ERPNext. Templates must be rebuilt regularly or the pipeline silently produces outdated deployments.
- **API credentials in the backend**: The FastAPI process holds CloudStack credentials capable of provisioning and destroying VMs. If the backend is compromised (SSRF, path traversal, dependency vulnerability), an attacker can destroy the entire estate.

---

## The Meta-Catastrophe

This system is a **force multiplier for whoever operates it** — that is its entire value, and its primary risk. A careful operator is ten times more effective. A confused family member on a bad day is ten times more destructive than if they had no tools at all.

The most important safety mechanism is not in the code. It is the **runbook**: a plain-language document stating "before pressing this button, you must have done these 7 things and confirmed these 5 facts." The UI should surface that checklist inline, not assume the operator knows it.

---

## Open Questions (carry forward to next session)

1. What is the RTO requirement for production failure? This determines whether a hot standby slave in production is sufficient or whether a pre-built golden staging pair is also needed.
2. CloudStack template model — what operations are supported via API? Can a template be built from a running VM snapshot? Can it be parameterised with a service offering at deploy time?
3. What DNS TTL is currently set on the ERPNext domain? When was it last changed?
4. Is there a tested MariaDB slave-to-master promotion procedure? If not, this must be written and tested before the UI is built.
5. What defines "an authorised approver"? Is this a fixed list, or does it change? Who maintains it?
6. ERPNext file attachments — are they backed up separately from the database? Where do they live?

---

## Implementation Options (carry forward — choose one objective per session)

- **A** — Quadrant layout with coloured frames + placeholder nodes (no workflow)
- **B** — Stockroom + drag-to-Dev mechanics
- **C** — Master/Slave/Console custom icons (SVG shapes in Cytoscape)
- **D** — Promotion button + Telegram approval state machine (backend-heavy)
- **E** — Architectural model decision first (golden staging vs ephemeral staging) before any UI work
