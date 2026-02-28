# Stage 1.5 -- Observability Validation & Management Console Framework (v5)

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
7. Log Ingestion / Error Rate Indicators, if feasible via Promtail
   metrics or a Loki range query

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

A single RUNBOOK shall be created with a dedicated section per scenario,
describing the steps to perform and the behaviour to expect.

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

Each failure scenario shall have a dedicated section in the failure
injection parameters YAML file specifying:

- `timeout_seconds`
- `estimated_consequence_delay_seconds`
- `expected_guest_behavior` (Markdown text)
- `expected_grafana_manifestations` (Markdown text)
- Case-specific parameters (e.g., `memory_ceiling_percent` for memory
  stress scenarios)

Fields not applicable to a scenario may be omitted.

An additional top-level section in the YAML specifies the path to the
Ansible inventory file used for target classification.

Example skeleton:

```yaml
ansible:
  inventory_file: ansible/inventory/dev.yml

scenarios:
  disk_pressure:
    timeout_seconds: 120
    estimated_consequence_delay_seconds: 30
    expected_guest_behavior: |
      Filesystem usage on the target volume rises rapidly.
      DiskSpaceLow alert enters pending state then fires.
    expected_grafana_manifestations: |
      Disk Utilization panel climbs toward threshold.
      Alert Status Summary shows DiskSpaceLow firing.

  memory_pressure:
    timeout_seconds: 300
    estimated_consequence_delay_seconds: 60
    memory_ceiling_percent: 40
    expected_guest_behavior: |
      MemAvailable drops. MemoryLow alert enters pending state then fires.
    expected_grafana_manifestations: |
      Memory Utilization panel rises.
      Alert Status Summary shows MemoryLow firing.

  prometheus_stopped:
    timeout_seconds: 180
    estimated_consequence_delay_seconds: 60
    expected_guest_behavior: |
      Prometheus process terminates. Port 9090 becomes unreachable.
    expected_grafana_manifestations: |
      Prometheus datasource shows error in Grafana.
      Scrape Health Overview shows target DOWN.
      InstanceDown alert fires for the Prometheus job.
```

### 5.3 RUNBOOK Structure

The RUNBOOK is the authoritative operational reference for this
framework. A novice operator must be able to execute any scenario
end-to-end using only the RUNBOOK.

The RUNBOOK shall contain at minimum:

1. **Host Prerequisites** — confirming Python environment, `rich`
   library, VBoxManage access, and SSH key availability.
2. **Baseline Readiness Checklist** — the specific checks to confirm
   before any exercise:
   - All Prometheus targets UP (verify at Prometheus /targets)
   - No active alerts firing
   - Grafana datasources responding (verify in Grafana datasource
     settings)
   - Loki ingesting logs (verify in Grafana Explore)
3. **Per-Scenario Sections** — one section per defined scenario, each
   containing:
   - Objective
   - Command to execute
   - Expected terminal output
   - Expected Grafana panel and alert behaviour
   - Loki query hints (where applicable)
   - Verification of clean recovery after snapshot revert
4. **Troubleshooting** — common failure modes and their resolution.

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
non-interactive authentication. Tests will be performed on fully
provisioned targets using existing pre-authorized SSH keys.

Host scripts require the `rich` Python library installed on the host.
Installation is documented in the SETUP_GUIDE.

For each exercise, the host-runner must:

1. Advise that a snapshot will be created.
2. Display existing snapshots and recommend pruning be considered.
3. Request explicit user confirmation.
4. Create a snapshot named: "Before {SCENARIO_NAME} test"
5. Print on the command line, using the `rich` Python library:
   - Expected guest behavior
   - Expected manifestations in Grafana and related systems
6. Inject the failure via SSH commands or, if appropriate, by installing
   functions via SCP and then executing them via SSH. Injected scripts
   may delete themselves after causing the intended condition. They will
   also disappear implicitly upon snapshot reversion. Self-deleting
   scripts are not expected to reverse their own effects; snapshot
   reversion is the sole cleanup path.
7. Display a visible countdown timer. Timer length: the greater of two
   minutes or four times the per-scenario `estimated_consequence_delay_seconds`
   from the parameters YAML file. If injection completes normally before
   the timer expires, clear the timer and prompt the user to proceed to
   snapshot revert.
8. If the timer expires before normal completion, prompt the user to
   continue waiting or trigger an immediate snapshot revert. The script
   must not exit without either completing normally or reverting the
   snapshot.
9. Revert to the snapshot upon user confirmation.

If SSH becomes unreachable post-injection, the script must continue
displaying status and allow snapshot reversion.

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

Memory pressure must be bounded using available memory at runtime
(MemAvailable), not total installed RAM.

Allocation must remain below a threshold to avoid unpredictable OOM
behavior. The specific ceiling shall be defined per scenario in the
parameters YAML file.

### 6.5 Prohibited Mechanisms

The following are disallowed:

- iptables manipulation
- SSH-disruptive operations
- Irreversible filesystem operations
- Actions risking loss of administrative access

These prohibitions exist to protect the host control plane and preserve
meaningful observation during drills. No failure injection may be
executed against the host machine. Failure injections that render the
target unresponsive are not useful.

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

Ansible automation must enforce production profile on production
inventory targets.

Drills must check the Ansible configuration files specified in §5.2 to
ensure they do not execute against production targets.

------------------------------------------------------------------------

## 9. Validation Cycle

1. Operator confirms baseline readiness: all Prometheus targets UP, no
   active alerts firing, Grafana datasources responding, Loki ingesting.
   The RUNBOOK baseline readiness checklist implements this definition.
2. Snapshot created ("Before {SCENARIO_NAME} test").
3. Terminal prints expected behavior (CLI-rendered Markdown from
   parameters YAML).
4. Controlled failure injected via SSH.
5. Operator observes expected changes while countdown timer runs.
6. Operator confirms revert.
7. Snapshot reverted.
8. Operator confirms clean recovery.

------------------------------------------------------------------------

## 10. Trust Model

The monitoring stack must continuously answer:

- Are metrics flowing?
- Are alerts routing?
- Are logs ingesting?
- Is the monitoring system operational?

Monitoring failures must be observable.

Stage 1.5 does not include file integrity or tamper detection
mechanisms. These may be considered in a later stage as part of
configuration governance or security hardening.

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
7. RUNBOOK documenting scenarios (structure defined in §5.3)
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
Framework (v5)
