# Stage 1.5 -- Observability Validation & Management Console Framework (v4)

## 1. Purpose

Stage 1 established a functional observability stack consisting of:

- Grafana
- Prometheus
- Alertmanager
- Loki
- Promtail
- node_exporter
- cAdvisor

Stage 1.5 formalizes the validation, training, and governance layer for
that stack.

Stage 1.5 extends Stage 1. It does not replace it.

This document is architectural and intended to endure.

------------------------------------------------------------------------

## 2. Long-Term Vision

The observability platform must serve a small but serious organization
that:

- Requires actionable alerts rather than noise
- Prefers stability over experimentation
- Needs documentation accessible to a technically capable but
  inexperienced successor
- Expects reliable operation over many years
- Treats the Grafana console as living documentation (the primary
  operational map)

A monitoring system that cannot be validated under controlled stress
cannot be trusted in production.

------------------------------------------------------------------------

## 3. Architectural Principles

### 3.1 Extension, Not Replacement

Stage 1.5:

- Extends existing configuration
- Respects established repository structure
- Avoids parallel configuration trees
- Avoids speculative re-architecture

### 3.2 Actionable Alerting

Alerts must:

- Represent conditions requiring action
- Avoid duplication
- Be tuned for small-scale infrastructure

### 3.3 Community Maturity Over Reinvention

Where mature community dashboards exist:

- Stored JSON checked into version control is mandatory
- Import-by-ID is allowed only during exploration
- Internet access must not be required for repeatable deployment

------------------------------------------------------------------------

## 4. Management Console Design

A dedicated Grafana "Management Console" dashboard shall be created.

Minimum components:

1. Scrape Health Overview
2. Alert Status Summary
3. CPU Utilization
4. Memory Utilization
5. Disk Utilization
6. Container Restart Indicators
7. Log Ingestion / Error Rate Indicators, if feasible via Promtail metrics or a Loki range query

The console must:

- Be visually calm under normal operation
- Clearly indicate abnormal states
- Avoid clutter
- Be understandable by a novice administrator

------------------------------------------------------------------------

## 5. Controlled Failure Injection Framework

### 5.1 Intent

Controlled Failure Injection enables:

- Telemetry validation
- Alert routing validation
- Administrator training
- Confidence in observability integrity

A per-scenario RUNBOOK shall be created that describes the steps to perform and the behaviour to expect.

### 5.2 Categories of Failure Scenarios

Category A: Instrumented System Failures (target workload/system health)

Examples:

- Disk pressure
- CPU saturation
- Bounded memory pressure
- Log generation spikes
- Container restart loops (non-monitoring containers)

Category B: Monitoring Stack Failures (target observability components)

Examples:

- Prometheus stopped
- Alertmanager stopped
- Loki stopped
- Promtail stopped
- Grafana stopped

Category boundaries are defined by intent and target component, not by
injection mechanism.

Category A scenarios must not intentionally target monitoring stack
services. Cross-effects are secondary outcomes and should be documented.

Each failure scenario should have its own section in a failure injection parameters YAML file which specifies :

- timeouts

- Expected guest behavior (as Markdown)

- Expected manifestations in Grafana and related systems (as Markdown)

- Case specific behaviour, such as thresholds on memory stress tests.

An additional section in the YAML specifies the Ansible file containing the characteristics of targets .  

------------------------------------------------------------------------

## 6. Safety and Governance Requirements

### 6.1 Snapshot-First Recovery Model

Failure injection exercises require hypervisor snapshot capability and
are limited to environments where snapshot control is available (e.g.,
lab and staging VMs).

Production VMs without snapshot capability are not eligible targets for
this framework.

Snapshot reversion is the primary recovery path.

### 6.2 Host-Executed Control Plane

Failure injection tooling is executed as Python scripts on the host.

Injection into the guest shall be performed via SSH using key-based,
non-interactive authentication.

For each exercise, the host-runner must:

1. Advise that a snapshot will be created.
2. Display existing snapshots and recommend pruning be considered.
3. Request explicit user confirmation.
4. Create a snapshot named: "Before {SCENARIO_NAME} test"
5. Print on the command line, using `rich`Python Markdown library:
   - Expected guest behavior
   - Expected manifestations in Grafana and related systems
6. Inject the failure via SSH commands or, if appropriate, by installing functions via SCP and then executed via SSH. They can delete themselves when they have caused the damage they are meant to create. They will disappear implicitly upon snapshot reversion. Self-deleting scripts are not expected to reverse their own effects; snapshot reversion is the sole cleanup path.
7. Display a visible countdown timer as protection against at task that never completes.  Timer length to be two minutes (default) or four times an estimated delay before failure consequences can be expected to appear. Estimates should be on a per case basis from values in the above mentioned parameters YAML file (git recorded)
8. If the task fails to complete normally after the timeout, allow the user to continue waiting or cancel.
9. Revert to the snapshot upon user confirmation.

If SSH becomes unreachable post-injection, the script must continue
displaying status and allow snapshot reversion.

These tests will be performed on fully provisioned targets using existing pre-authorized SSH keys.

### 6.3 Production Safeguards (Fail Closed)

Failure injection must never run against production or protected
targets.

Untouchable targets:

- Hosts in Ansible inventory groups: production or protected

Touchable targets:

- Hosts in Ansible inventory groups: lab or staging

If inventory is unreadable, ambiguous, or the host is unclassified:
refuse to run (fail closed).

No override flags are permitted.

### 6.4 Resource Safety Rules

Memory pressure must be bounded using available memory at runtime (MemAvailable), not total installed RAM.

Allocation must remain below a threshold to avoid unpredictable OOM behavior.

The specific ceiling shall be defined per scenario in the parameters YAML file.

### 6.5 Prohibited Mechanisms

The following are disallowed:

- iptables manipulation
- SSH-disruptive operations
- Irreversible filesystem operations
- Actions risking loss of administrative access

These prohibitions exist to protect the host control plane and preserve meaningful observation during drills.  NO failure injection may be executed against the host machine!  Failure injections that render the target unresponsive aren't useful.

------------------------------------------------------------------------

## 7. Logging Ingestion Baseline

Promtail shall scrape Docker container json-file logs:

/var/lib/docker/containers/*/*.log

Log storm scenarios shall use controlled throwaway containers.

Host log ingestion may be added later but is not required for Stage 1.5.

------------------------------------------------------------------------

## 8. Alerting Profiles

Two alert profiles are mandatory:

- Production profile: conservative durations and thresholds
- Drill profile: shortened durations for training feedback

Ansible automation must enforce production profile on production inventory targets.

Drills must check the Ansible configuration files specified in 5.2 to ensure they do not execute against production targets.

------------------------------------------------------------------------

## 9. Validation Cycle

1. Operator confirms baseline readiness manually as defined in the RUNBOOK baseline readiness checklist.
2. Snapshot created ("Before {SCENARIO_NAME} test").
3. Terminal prints out test behaviour expectations (CLI rendered Markdown) and operator observes those expected changes.
4. Controlled failure injected, if safety conditions are met.
5. Operator confirms revert.
6. Snapshot reverted.
7. Operator confirms clean recovery.

------------------------------------------------------------------------

## 10. Trust Model

The monitoring stack must continuously answer:

- Are metrics flowing?
- Are alerts routing?
- Are logs ingesting?
- Is the monitoring system operational?

Monitoring failures must be observable.

Stage 1.5 does not include file integrity or tamper detection mechanisms. These may be considered in a later stage as part of configuration governance or security hardening.

------------------------------------------------------------------------

## 11. Stage Roadmap

Stage 2:

- Multi-node topology (WireGuard mesh, remote VM/VPS integration)
- Expansion of the living Grafana console

Stage 3:

- Formal onboarding documentation
- Drill playbooks
- Response playbooks
- File integrity, tamper detection and periodic security audits

------------------------------------------------------------------------

## 12. Deliverables of Stage 1.5

1. Refined configuration extending Stage 1
2. Community dashboards stored as JSON
3. Custom Management Console dashboard
4. Two alerting profiles (drill and production)
5. Host-runner failure injection scripts (snapshot-based lifecycle)
6. Failure injection scripts' parameters YAML file
7. RUNBOOK documenting scenarios
8. Ansible enforcement of:
   - Touchable/untouchable classification
   - Production profile lock-in
   - Prevention of drill profile on production

------------------------------------------------------------------------

## 13. Success Criteria

Stage 1.5 is successful when:

- Each defined scenario can be executed end-to-end using only the
  RUNBOOK
- Alerts fire appropriately under the drill profile
- Snapshot reversion reliably restores the environment
- No production or protected target can be subjected to injection



------------------------------------------------------------------------

End of Stage 1.5 -- Observability Validation & Management Console
Framework (v4)
