# Claude Code Prompt: Observability Stack Automation + Chaos Test Suite

> **Purpose:** Have Claude Code generate a repeatable, minimal-UI setup for Grafana + Prometheus + Alertmanager + Loki + Promtail (plus node_exporter and cAdvisor), and create a set of small, shebang’d Python “break something” scripts to validate that dashboards, logs, and alerts light up the way we expect.

---

## 0) Operating Assumptions

- You are working in a repo that contains a Docker Compose deployment for these services (service names shown below):
  - `grafana` (port 3000)
  - `prometheus` (port 9090)
  - `alertmanager` (port 9093)
  - `loki` (port 3100)
  - `promtail`
  - `node_exporter` (port 9100)
  - `cadvisor` (port 8080)
- All inter-service networking uses **Docker Compose service DNS names** (e.g., `http://prometheus:9090`, not `localhost`).
- Goal is **file-based provisioning** (Grafana datasources/dashboards, Prometheus config/rules, Alertmanager routing), not fragile UI click automation.
- This is running inside a VM. We will intentionally break things inside that VM (or containers) in controlled ways.
- Prefer **idempotent** changes (can run repeatedly without harmful duplication).
- Do not expose services publicly or weaken security as a “solution”. Prefer local-only or VM-internal access.

---

## 1) Deliverables Summary

Generate:

1. **Grafana provisioning**
   - Datasources: Prometheus + Loki
   - Dashboards: Node exporter + cAdvisor/containers + “Chaos Overview” dashboard
   - Optional: a folder structure and org settings

2. **Prometheus**
   - `prometheus.yml` scrape config for: prometheus, node_exporter, cadvisor (and optionally alertmanager)
   - `rules/*.yml` alert rules for basic health + VM stress conditions

3. **Alertmanager**
   - `alertmanager.yml` routes/receivers with placeholders
   - A clear section marking where to insert real integrations (email/Telegram/webhook)

4. **Loki + Promtail**
   - Loki config if needed (often minimal)
   - Promtail config to scrape Docker logs (json-file) or host logs (syslog), with label hygiene

5. **Chaos test scripts**
   - A `chaos/` folder containing Python scripts (with shebang) to break and restore:
     - Disk usage
     - CPU load
     - Memory pressure
     - Network disruption (limited/safe)
     - Stop/restart key containers (grafana, prometheus, alertmanager, promtail, loki, node_exporter, cadvisor)
     - Create log storms for Loki validation
   - Scripts must print:
     - What they are about to do
     - What to expect in Grafana/Prometheus/Alertmanager/Loki
     - How to restore (or point to `restore_*.py`)

6. **Runbook**
   - A short `RUNBOOK.md` describing:
     - How to bring stack up
     - How to verify targets
     - How to run each chaos script and what panels/alerts to watch

---

## 2) Repository Layout (Target)

Create or use this structure:

```
.
├─ docker-compose.yml
├─ prometheus/
│  ├─ prometheus.yml
│  └─ rules/
│     ├─ basics.yml
│     └─ resources.yml
├─ alertmanager/
│  └─ alertmanager.yml
├─ loki/
│  └─ loki-config.yml              (only if needed)
├─ promtail/
│  └─ promtail-config.yml
├─ grafana/
│  ├─ dashboards/
│  │  ├─ node_exporter.json
│  │  ├─ cadvisor.json
│  │  └─ chaos_overview.json
│  └─ provisioning/
│     ├─ datasources/
│     │  └─ datasources.yml
│     └─ dashboards/
│        └─ dashboards.yml
├─ chaos/
│  ├─ README.md
│  ├─ break_disk.py
│  ├─ restore_disk.py
│  ├─ break_cpu.py
│  ├─ restore_cpu.py
│  ├─ break_memory.py
│  ├─ restore_memory.py
│  ├─ break_logs.py
│  ├─ restore_logs.py
│  ├─ break_container.py
│  ├─ restore_container.py
│  ├─ break_node_exporter.py
│  ├─ restore_node_exporter.py
│  ├─ break_cadvisor.py
│  ├─ restore_cadvisor.py
│  ├─ break_promtail.py
│  ├─ restore_promtail.py
│  ├─ break_loki.py
│  ├─ restore_loki.py
│  ├─ break_prometheus.py
│  ├─ restore_prometheus.py
│  ├─ break_alertmanager.py
│  ├─ restore_alertmanager.py
│  └─ break_network_safe.py        (optional)
└─ RUNBOOK.md
```

If the repo already has configs, update rather than replace. Keep diffs clean.

---

## 3) Docker Compose Wiring Requirements

Update `docker-compose.yml` to:

- Mount provisioning:
  - `./grafana/provisioning:/etc/grafana/provisioning`
  - `./grafana/dashboards:/var/lib/grafana/dashboards`
- Mount Prometheus:
  - `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro`
  - `./prometheus/rules:/etc/prometheus/rules:ro`
- Mount Alertmanager:
  - `./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro`
- Mount Promtail:
  - `./promtail/promtail-config.yml:/etc/promtail/config.yml:ro`
  - Docker logs mount as needed (choose one approach and document):
    - **Option A (Docker json logs):**
      - `/var/lib/docker/containers:/var/lib/docker/containers:ro`
      - `/var/run/docker.sock:/var/run/docker.sock:ro` (optional, only if needed)
    - **Option B (host logs):**
      - `/var/log:/var/log:ro`
- Ensure Prometheus has a `--web.enable-lifecycle` flag only if you want runtime reloads (optional).

Do **not** publish additional ports beyond what’s already published unless explicitly required.

---

## 4) Grafana Provisioning Spec

### 4.1 Datasources

Create `grafana/provisioning/datasources/datasources.yml` with:

- Prometheus datasource:
  - name: `Prometheus`
  - url: `http://prometheus:9090`
  - isDefault: true
- Loki datasource:
  - name: `Loki`
  - url: `http://loki:3100`

Use apiVersion 1 and ensure updates are allowed on restart (overwrite).

### 4.2 Dashboards

Create `grafana/provisioning/dashboards/dashboards.yml` that loads JSON dashboards from `/var/lib/grafana/dashboards`.

Dashboards required:
- **Node exporter host dashboard** (must work with `node_exporter` target)
- **cAdvisor/container dashboard** (must work with `cadvisor` target)
- **Chaos Overview dashboard** (custom, see below)

Avoid dashboards that depend on exporters not present.

### 4.3 Chaos Overview Dashboard (Custom)

Create a dashboard that includes these panels (at minimum):

1. **Scrape Health**
   - Query: `up` by job/instance
2. **Firing Alerts Count**
   - Query: `count(ALERTS{alertstate="firing"})`
3. **Node CPU Load / Usage**
   - Load average or CPU usage from node_exporter
4. **Disk Usage**
   - Use node_exporter filesystem metrics
5. **Container Restarts**
   - From cAdvisor metrics if available
6. **Loki Log Volume**
   - If Loki metrics or a log-rate query is feasible, include a basic panel or instructions to use Explore

Make panels obvious, readable, and easy to correlate during chaos runs.

---

## 5) Prometheus Spec

### 5.1 Scrape Config

Create/update `prometheus/prometheus.yml` with scrape jobs:

- `prometheus`: target `prometheus:9090`
- `node_exporter`: target `node_exporter:9100`
- `cadvisor`: target `cadvisor:8080`
- optional `alertmanager`: target `alertmanager:9093`

Set scrape interval to something reasonable for a VM lab (e.g., 15s).

### 5.2 Rules

Create `prometheus/rules/basics.yml` including:

- **InstanceDown**
  - `up == 0` for > 1m
- **PrometheusTargetMissing** (optional variant)
  - Detect missing expected jobs or a sudden drop in `up` count

Create `prometheus/rules/resources.yml` including:

- **DiskSpaceLow**
  - Trigger when filesystem usage > 90% (exclude tmpfs, etc.)
- **HighCPUUsage**
  - Trigger when CPU usage > 90% for > 5m (or load avg too high)
- **MemoryLow**
  - Trigger when available memory < 10% for > 5m

Rules should include:
- `severity` label (e.g., warning/critical)
- Helpful annotations:
  - Summary
  - Description with the relevant labels

---

## 6) Alertmanager Spec

Create `alertmanager/alertmanager.yml`:

- Default route groups alerts by:
  - `alertname`, `job`, `instance`
- Use a short group wait and group interval suitable for lab testing.
- Include a placeholder receiver such as:
  - `null_receiver` (no-op) or
  - `webhook_receiver` with a dummy URL

Make it explicit where to insert:
- email SMTP config
- Telegram bot webhook
- generic webhook URL

Also include inhibition rules (optional) so that e.g. “InstanceDown” inhibits more granular alerts.

---

## 7) Loki + Promtail Spec

### 7.1 Loki

If Loki is already running with a known config, keep it. Otherwise provide a minimal `loki-config.yml`.

### 7.2 Promtail

Create `promtail/promtail-config.yml` that can ingest logs from either:

- Docker container json logs (preferred for container-level chaos):
  - Path: `/var/lib/docker/containers/*/*.log`
  - Labels: `container`, `compose_service`, `host` (if possible)
- Or host logs if Docker logs aren’t mounted.

Ensure:
- Promtail sends to: `http://loki:3100/loki/api/v1/push`
- Label cardinality stays sane. Avoid per-line unique labels.

---

## 8) Chaos Scripts Specification (Python, Shebang’d)

### 8.1 General Rules

All scripts in `chaos/` must:

- Begin with: `#!/usr/bin/env python3`
- Be safe-by-default:
  - Clearly print what will happen
  - Avoid irreversible actions
  - Keep actions scoped (e.g., use `/tmp/` for files)
- Use `subprocess.run(..., check=True)` for commands where failure matters
- Print “Expected Observability Signals”:
  - Prometheus target status impact
  - Expected alert name (if applicable)
  - Expected Grafana dashboard/panel reaction
  - Loki log query hints if applicable
- Provide a paired restore script where possible.

Also include `chaos/README.md` describing usage.

### 8.2 Scripts Required (Break + Restore)

#### Disk Stress

- `break_disk.py`
  - Create a large file in `/tmp` (size configurable), e.g. `/tmp/chaos_bigfile`
- `restore_disk.py`
  - Remove that file
- Expected signals:
  - Grafana disk usage panel spikes
  - `DiskSpaceLow` alert fires when threshold crossed

#### CPU Stress

- `break_cpu.py`
  - Spawn N `yes` processes (default 4) with output suppressed
- `restore_cpu.py`
  - Kill `yes` processes (pkill)
- Expected signals:
  - Grafana CPU usage spikes
  - `HighCPUUsage` alert fires if enabled

#### Memory Pressure

- `break_memory.py`
  - Use `stress` if installed; otherwise allocate memory in Python carefully (avoid crashing VM)
  - Prefer `stress --vm 1 --vm-bytes <percent>` if available
- `restore_memory.py`
  - Stop stress process
- Expected signals:
  - Available memory drops
  - `MemoryLow` alert fires if enabled

#### Log Storm (Loki)

- `break_logs.py`
  - Emit high-rate log lines to a chosen file (e.g., `/tmp/chaos.log`) OR to syslog if mounted
  - If promtail is configured for Docker logs, alternatively run a temporary container that spams logs
- `restore_logs.py`
  - Stop spammer and/or truncate/delete the temp log file
- Expected signals:
  - Loki Explore shows burst
  - If log-rate panel exists, it spikes

#### Container Disruption (Generic)

- `break_container.py`
  - Argument: container name (default `grafana`)
  - Action: `docker kill <name>` or `docker stop <name>` (choose one and document)
- `restore_container.py`
  - `docker start <name>`
- Expected signals:
  - cAdvisor restart metrics change
  - Prometheus `up{job=...}` may go down if the exporter stops
  - Grafana UI becomes unavailable if `grafana` is stopped

#### Exporter/Service Target Down Scripts

Create explicit convenience scripts:

- `break_node_exporter.py` / `restore_node_exporter.py`
- `break_cadvisor.py` / `restore_cadvisor.py`
- `break_promtail.py` / `restore_promtail.py`
- `break_loki.py` / `restore_loki.py`
- `break_prometheus.py` / `restore_prometheus.py`
- `break_alertmanager.py` / `restore_alertmanager.py`

Expected signals:
- Prometheus targets flip UP/DOWN
- `InstanceDown` alert fires for the affected job/instance
- Loki ingestion stops (if promtail or loki is stopped)
- Alert routing stops (if alertmanager is stopped)

#### Safe Network Break (Optional)

- `break_network_safe.py`
  - Must be conservative:
    - Prefer temporarily blocking egress to one container via Docker network commands or iptables rules *that are easily reverted*
    - Avoid taking the VM offline entirely
- Provide `restore_network_safe.py`
- Expected signals:
  - A chosen target’s scrape fails or Loki push fails

If this is too risky, omit it and document why.

---

## 9) RUNBOOK Requirements

Create `RUNBOOK.md` that includes:

1. **Bring-up**
   - `docker compose up -d`
2. **Verify**
   - Prometheus targets page checks
   - Grafana datasources “OK”
   - Dashboards show data
3. **Chaos drills**
   - For each break script:
     - Command to run
     - Expected dashboard/alert/log behavior
     - Restore command
4. **Troubleshooting**
   - Where to check logs: `docker logs <service>`

---

## 10) Output Format Requirements (Critical)

When you respond:

- Provide **files created/modified** and their paths
- Provide **diffs** or full file contents where appropriate
- Provide **exact commands** to apply changes and restart the stack
- Do not invent services not present
- Do not assume external internet access
- Prefer small, understandable changes over “wizardry”

---

## 11) Validation Checklist

A solution is complete when:

- Grafana shows:
  - Datasources: Prometheus + Loki = OK
  - Dashboards: Node exporter + cAdvisor + Chaos Overview
- Prometheus shows:
  - Targets: prometheus, node_exporter, cadvisor = UP
  - Rules loaded and alerts appear when chaos triggers occur
- Alertmanager shows:
  - Alerts received and routed (even if to a placeholder receiver)
- Loki shows:
  - Logs ingested and visible in Grafana Explore during log storms
- Chaos scripts:
  - Run without crashing the VM
  - Produce the expected observable signals
  - Restore scripts return system to baseline

---

## 12) Nice-to-Haves (Only If Easy)

- Add `--dry-run` to chaos scripts
- Add a “marker log line” emitted at start/end of each chaos script to help correlate timelines in Loki
- Add `chaos_runner.py` to run a scenario sequence (disk -> cpu -> logs -> restore)
