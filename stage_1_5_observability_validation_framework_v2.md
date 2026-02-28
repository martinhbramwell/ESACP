# Stage 1.5 -- Observability Validation & Management Console Framework

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

This stage does not replace Stage 1.\
It strengthens it.

The objective is to ensure the monitoring system is:

- Trustworthy
- Testable
- Maintainable
- Transferable to a future administrator

This document is architectural in nature and intended to endure.

------------------------------------------------------------------------

## 2. Long-Term Vision

The observability platform must serve a small but serious organization
that:

- Requires actionable alerts rather than noise
- Prefers stability over experimentation
- Needs documentation that is accessible to a technically capable but
  inexperienced successor
- Expects the system to operate reliably for many years

The system must make its own health visible.

A monitoring system that cannot be validated under stress cannot be
trusted in production.

------------------------------------------------------------------------

## 3. Architectural Principles

### 3.1 Extension, Not Replacement

Stage 1.5:

- Extends existing configuration
- Respects established repository structure
- Avoids duplication of configuration trees
- Introduces no speculative re-architecture

### 3.2 Actionable Alerting

Alerts must:

- Represent conditions requiring action
- Avoid unnecessary duplication
- Be tuned for small-scale infrastructure

During validation drills, shorter alert durations may be used.\
Production thresholds should remain conservative.

### 3.3 Community Maturity Over Reinvention

Where stable community dashboards exist (e.g., node_exporter, cAdvisor):

- Use maintained dashboards
- Import by ID or stored JSON
- Avoid regenerating large, complex dashboards

Custom dashboards are limited to governance and management purposes.

------------------------------------------------------------------------

## 4. Management Console Design

A dedicated "Management Console" dashboard shall be created.

Its purpose is executive visibility and operational clarity.

Minimum components:

1. Scrape Health Overview
2. Alert Status Summary
3. CPU Utilization
4. Memory Utilization
5. Disk Utilization
6. Container Restart Indicators
7. Log Ingestion or Error Rate Indicators (if feasible)

The console must:

- Be visually calm under normal operation
- Clearly indicate abnormal states
- Avoid excessive visual clutter

The console is not an engineering playground.\
It is an operational instrument panel.

------------------------------------------------------------------------

## 5. Controlled Failure Injection Framework

### 5.1 Purpose

Controlled Failure Injection enables:

- Validation of telemetry pathways
- Validation of alert routing
- Administrator training
- Confidence building

Failure simulation is not for entertainment.\
It is a governance mechanism.

The injection exercises will necessarily be aimed at development or staging virtual machine targets with snapshot capability.  Snapshot reversion will be the expected behaviour to finalize each exercise.  Strong obstacles against targetting production machines are obligatory.

### 5.2 Categories of Failure Scenarios

#### A. Instrumented System Failures

Examples:

- Disk pressure
- CPU saturation
- Bounded memory pressure
- Log generation spikes
- Container restart loops

These validate telemetry accuracy.

#### B. Monitoring Stack Failures

Examples:

- Prometheus stopped
- Alertmanager stopped
- Loki stopped
- Promtail stopped
- Grafana stopped

These validate observability resilience and failure visibility.

These two categories must remain conceptually distinct.

------------------------------------------------------------------------

## 6. Safety Requirements for Failure Simulation

All failure simulation scripts must:

- Use shebang Python (`#!/usr/bin/env python3`)
- Support a required `--duration` parameter
- Automatically restore system state after duration expires
- Track and terminate only processes they initiate
- Enforce explicit resource ceilings

### 6.1 Memory Ceiling

Memory pressure must not exceed a defined safe percentage of system RAM
(e.g., 50% maximum).

The simulation must not trigger unpredictable OOM behavior.

### 6.2 Prohibited Mechanisms

The following are explicitly disallowed:

- iptables manipulation
- SSH-disruptive operations
- Irreversible filesystem operations
- Actions that risk loss of administrative access

The validation framework must never endanger recoverability.

------------------------------------------------------------------------

## 7. Validation Cycle

Each scenario must support a structured learning cycle:

1. Record baseline state
2. Trigger controlled failure
3. Observe changes in:
   - Prometheus targets
   - Alert firing state
   - Grafana dashboard indicators
   - Loki log behavior (if applicable)
4. Automatic restoration
5. Confirmation of clean recovery

Documentation must describe expected signals for each scenario.

------------------------------------------------------------------------

## 8. Trust Model

The monitoring stack must continuously answer:

- Are metrics flowing?
- Are alerts routing?
- Are logs ingesting?
- Is the monitoring system itself operational?

Monitoring failures must be observable.

A silent monitoring failure is unacceptable.

------------------------------------------------------------------------

## 9. Deliverables of Stage 1.5

1. Refined configuration extending Stage 1
2. Community dashboards integrated
3. Custom Management Console dashboard
4. Alert tuning adjustments suitable for validation drills
5. Controlled Failure Injection script suite
6. RUNBOOK documenting scenarios and expected behavior

------------------------------------------------------------------------

## 10. Preparation for Stage 2

Stage 2 will produce formal documentation including:

- Administrator User Guide
- Chaos Drill Playbook
- Alert Response Playbook
- Onboarding materials

Stage 1.5 establishes the structural and conceptual foundation for that
documentation.

------------------------------------------------------------------------

## 11. Success Criteria

Stage 1.5 is successful when:

- A technically capable but inexperienced administrator can run a
  failure scenario
- The management console clearly reflects the induced condition
- Alerts fire appropriately
- The system restores automatically
- Confidence in the monitoring system increases

------------------------------------------------------------------------

End of Stage 1.5 -- Observability Validation & Management Console
Framework
