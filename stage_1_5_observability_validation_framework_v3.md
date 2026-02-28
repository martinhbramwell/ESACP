# Stage 1.5 -- Observability Validation & Management Console Framework (v3)

## 1. Purpose

Stage 1 established a functional observability stack consisting of:

-   Grafana
-   Prometheus
-   Alertmanager
-   Loki
-   Promtail
-   node_exporter
-   cAdvisor

Stage 1.5 formalizes the **validation, training, and governance** layer
for that stack.

Stage 1.5 does **not** replace Stage 1.\
It strengthens it.

This document is architectural and intended to endure.

------------------------------------------------------------------------

## 2. Long-Term Vision

The observability platform must serve a small but serious organization
that:

-   Requires actionable alerts rather than noise
-   Prefers stability over experimentation
-   Needs documentation that is accessible to a technically capable but
    inexperienced successor
-   Expects the system to operate reliably for many years
-   Treats the Grafana console as **living documentation** (the primary
    operational "map" and drill-down surface)

A monitoring system that cannot be validated under controlled stress
cannot be trusted in production.

------------------------------------------------------------------------

## 3. Architectural Principles

### 3.1 Extension, Not Replacement

Stage 1.5:

-   Extends existing configuration
-   Respects established repository structure
-   Avoids parallel configuration trees
-   Avoids speculative re-architecture

### 3.2 Actionable Alerting

Alerts must:

-   Represent conditions requiring action
-   Avoid unnecessary duplication
-   Be tuned for small-scale infrastructure

### 3.3 Community Maturity Over Reinvention

Where mature community dashboards exist (e.g., node_exporter, cAdvisor):

-   Prefer **stored JSON** checked into version control
-   Avoid "generate from scratch" approaches
-   Allow import-by-ID only as a temporary exploration aid (never the
    durable baseline)

Repeatability must not depend on internet access.

------------------------------------------------------------------------

## 4. Management Console Design

A dedicated Grafana "Management Console" dashboard shall be created.

Its purpose is executive visibility and operational clarity, not
engineering experimentation.

Minimum components:

1.  Scrape Health Overview (all jobs)
2.  Alert Status Summary (count + top firing alerts)
3.  CPU Utilization
4.  Memory Utilization
5.  Disk Utilization
6.  Container Restart Indicators
7.  Log Ingestion / Error Rate Indicators (if feasible)

The console must:

-   Be visually calm under normal operation
-   Clearly indicate abnormal states
-   Avoid excessive visual clutter
-   Present a coherent "instrument panel" view suitable for novices

------------------------------------------------------------------------

## 5. Controlled Failure Injection Framework

### 5.1 Intent

Controlled Failure Injection enables:

-   Validation of telemetry pathways
-   Validation of alert routing
-   Administrator training
-   Confidence building

Failure simulation is a governance mechanism.

### 5.2 Categories of Failure Scenarios

**Category A: Instrumented System Failures** (target workload/system
health)

Examples:

-   Disk pressure
-   CPU saturation
-   Bounded memory pressure (safe ceilings)
-   Log generation spikes
-   Container restart loops

**Category B: Monitoring Stack Failures** (target observability
components)

Examples:

-   Prometheus stopped
-   Alertmanager stopped
-   Loki stopped
-   Promtail stopped
-   Grafana stopped

The categories must remain **conceptually distinct**, where possible:

-   Category A scenarios must not intentionally target monitoring stack
    services.
-   It is acknowledged that severe Category A scenarios can indirectly
    degrade monitoring (e.g., disk fill impacting WAL). Such
    cross-effects should be documented as secondary outcomes, not
    primary intent.

------------------------------------------------------------------------

## 6. Safety and Governance Requirements

### 6.1 Snapshot-First Recovery Model (Primary)

All failure injection exercises are performed in a **disposable lab
context** and are finalized by **virtual machine snapshot reversion**.

-   Snapshot reversion is the primary recovery path.
-   The system must assume the environment will be reverted to a
    known-good snapshot at the end of an exercise.

This model intentionally favors repeatability and safety over in-guest
"surgical" restoration.

### 6.2 Host-Executed Control Plane (Required)

Failure injection tooling is executed as **Python scripts on the host**,
not inside the guest VM.

For each exercise, the host-runner scripts must:

1.  Display a warning that a snapshot will be created.
2.  Display the list of existing snapshots and recommend pruning be
    considered.
3.  Request explicit user confirmation.
4.  Create a snapshot named: **"Before `<TEST NAME>`{=html} test"**
5.  Inject the failure (via guest interaction and/or Docker control as
    appropriate).
6.  Print:
    -   Expected guest behavior
    -   Expected manifestations in Grafana/Prometheus/Alertmanager/Loki
7.  Wait for explicit user confirmation to revert.
8.  Revert to the snapshot.

This ensures recoverability even if the guest becomes unstable or
unreachable.

### 6.3 Production Safeguards (Fail Closed)

Failure injection must never run against production or protected
targets.

Enforcement rule:

-   "Untouchable" targets are hosts classified in Ansible inventory
    groups: `production` or `protected`.
-   "Touchable" targets are hosts classified in Ansible inventory
    groups: `lab` or `staging`.
-   If inventory is unreadable, ambiguous, or host is unclassified:
    **refuse to run** (fail closed).

No override flags are permitted.

The Ansible automation that stands up a new production server must
ensure these classifications exist and remain correct.

### 6.4 Resource Safety Rules

**Memory pressure must be bounded using available memory at runtime**,
not total installed RAM.

Example policy (implementation may refine):

-   Allocate no more than a conservative percentage of `MemAvailable` at
    script start.
-   Prevent triggering unpredictable OOM behavior.

### 6.5 Prohibited Mechanisms

The following are explicitly disallowed:

-   iptables manipulation
-   SSH-disruptive operations
-   Irreversible filesystem operations
-   Actions that risk loss of administrative access

------------------------------------------------------------------------

## 7. Logging Ingestion Baseline (Repeatable Default)

Default log ingestion is based on **Docker container json-file logs** to
maximize observability of the actual stack behavior during drills.

Promtail should scrape:

-   `/var/lib/docker/containers/*/*.log` (read-only mount)

The log storm scenario should be generated via a controlled throwaway
container that spams stdout/stderr, so Loki ingestion is visibly
exercised.

Host log ingestion may be added later, but container logs are the
durable baseline for Stage 1.5.

------------------------------------------------------------------------

## 8. Alerting Profiles: Drill vs Production

Production-grade alerting typically uses longer durations to reduce
flapping. Training drills require fast feedback.

Stage 1.5 mandates two profiles:

-   **Production profile**: conservative thresholds and longer `for:`
    durations
-   **Drill profile**: shorter `for:` durations suitable for validation
    exercises

Implementation requirement:

-   Profiles must be selectable via configuration at deploy time.
-   This selection must be supported and enforced by the Ansible
    automation that stands up production servers (production profile
    must be the default/locked-in choice for production inventory
    targets).

------------------------------------------------------------------------

## 9. Validation Cycle

Each scenario must support a structured learning cycle:

1.  Confirm baseline readiness (stack healthy, targets UP)
2.  Snapshot creation ("Before `<TEST NAME>`{=html} test")
3.  Controlled failure injection
4.  Observation of:
    -   Prometheus targets
    -   Alert firing state
    -   Grafana management console indicators
    -   Loki log behavior (if applicable)
5.  Operator confirmation
6.  Snapshot reversion
7.  Confirmation of clean recovery

Documentation must describe expected signals for each scenario.

------------------------------------------------------------------------

## 10. Trust Model

The monitoring stack must continuously answer:

-   Are metrics flowing?
-   Are alerts routing?
-   Are logs ingesting?
-   Is the monitoring system itself operational?

Monitoring failures must be observable.

A silent monitoring failure is unacceptable.

------------------------------------------------------------------------

## 11. Stage Roadmap Clarification

-   **Stage 2**: Multi-node topology (WireGuard mesh networking, remote
    VPS/VM integration) and expansion of the Grafana living console to
    represent and drill into that topology.
-   **Stage 3**: Formal onboarding documentation, drill playbooks, and
    response playbooks that teach and reinforce operation of the living
    console and validation framework.

Documentation is not separate from the console; it is anchored around
it.

------------------------------------------------------------------------

## 12. Deliverables of Stage 1.5

1.  Refined configuration extending Stage 1
2.  Community dashboards stored as JSON and integrated
3.  Custom Management Console dashboard
4.  Two alerting profiles (drill and production) with enforceable
    selection
5.  Host-runner failure injection script suite (snapshot-based
    lifecycle)
6.  RUNBOOK documenting scenarios and expected behavior

------------------------------------------------------------------------

## 13. Success Criteria

Stage 1.5 is successful when:

-   A technically capable but inexperienced administrator can run a
    failure scenario safely
-   The management console clearly reflects the induced condition
-   Alerts fire appropriately under the drill profile
-   The environment is reliably restored via snapshot reversion
-   Confidence in the monitoring system increases through repeated
    validation

------------------------------------------------------------------------

End of Stage 1.5 -- Observability Validation & Management Console
Framework (v3)
