# ESACP Observability Runbook

Stage 1.5 — Failure Injection & Observability Validation

> **RETIRED 2026-04-22.** This runbook describes the VBox-era chaos harness
> (`orchestration/chaos/run_scenario.py`, `revertToBaseline.py`). Both scripts
> were deleted in the #211 orphan audit — they were bound to VBoxManage on a
> platform permanently retired 2026-03-17. The ten chaos scenarios preserved
> here as historical reference are tracked for KVM re-implementation in
> **[#280](https://github.com/martinhbramwell/ESACP/issues/280)** (wire to
> `tools/pipeline/orchestration/snapshot_ops.py`; decide Cytoscape placement).
> Do not run the commands below — the scripts no longer exist.

---

## Table of Contents

1. [Host Prerequisites](#1-host-prerequisites)
2. [Baseline Readiness Checklist](#2-baseline-readiness-checklist)
3. [Scenario Procedures](#3-scenario-procedures)
   - [disk\_pressure](#disk_pressure)
   - [cpu\_saturation](#cpu_saturation)
   - [memory\_pressure](#memory_pressure)
   - [log\_storm](#log_storm)
   - [container\_restart\_loop](#container_restart_loop)
   - [prometheus\_stopped](#prometheus_stopped)
   - [alertmanager\_stopped](#alertmanager_stopped)
   - [loki\_stopped](#loki_stopped)
   - [promtail\_stopped](#promtail_stopped)
   - [grafana\_stopped](#grafana_stopped)
4. [Troubleshooting](#4-troubleshooting)
5. [Enrolling a Mobile / Satellite Terminal (WireGuard + tmux)](#5-enrolling-a-mobile--satellite-terminal-wireguard--tmux)
   - [Enroll a new WireGuard peer](#5a-enroll-a-new-wireguard-peer)
   - [Attach a satellite mirrored terminal](#5b-attach-a-satellite-mirrored-terminal)

---

## 1. Host Prerequisites

### Software

| Requirement | Install |
|---|---|
| Python 3.10+ | `sudo apt install python3` |
| `rich` library | `pip3 install rich` or `sudo apt install python3-rich` |
| `pyyaml` library | `pip3 install pyyaml` |
| VBoxManage | VirtualBox on host Windows; `VBoxManage.exe` auto-discovered via WSL path |
| `ssh` / `scp` | `sudo apt install openssh-client` |

All Python dependencies for the orchestration tools are listed in `orchestration/requirements.txt`.
Install with `pip3 install -r orchestration/requirements.txt`.

### VBoxManage Path

The runner auto-discovers VBoxManage in this order:
1. `VBoxManage` on `PATH` (native Linux)
2. `VBoxManage.exe` on `PATH` (WSL with Windows PATH passthrough)
3. `/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe` (WSL default)

If none of these apply, add the VirtualBox directory to `PATH` before running.

### SSH Key

The runner uses `$SSH_KEY_PATH` (default `~/.ssh/id_ed25519`) to authenticate to the VM.
Ensure the corresponding public key is installed on the VM:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub ernest@<VM_IP>
```

### Required Environment Variables

| Variable | Description | Example |
|---|---|---|
| `VM_IP` | IP address of the target VM | `192.168.40.101` |
| `VM_HOSTNAME` | VirtualBox VM name | `esacp-dev` |
| `SSH_KEY_PATH` | Path to SSH private key | `~/.ssh/id_ed25519` |
| `SNAPSHOT_NAME` | Snapshot to revert to on cleanup | `Stage 1.5 Complete` |
| `VM_USER` | SSH username on VM (default: `ernest`) | `ernest` |

Set these in your shell before running scenarios:

```bash
export VM_IP=192.168.40.101
export VM_HOSTNAME=esacp-dev
export SSH_KEY_PATH=~/.ssh/id_ed25519
export SNAPSHOT_NAME="Stage 1 Complete"
export VM_USER=ernest
```

---

## 2. Baseline Readiness Checklist

Verify all four conditions before running any scenario. Failing to establish a clean baseline
means scenario results will be ambiguous.

### Check 1 — All Prometheus targets UP

Navigate to `http://<VM_IP>:9090/targets`.

Expected: All 7 targets show state `UP`:
- `prometheus` (localhost:9090)
- `node` (node_exporter:9100)
- `cadvisor` (cadvisor:8080)
- `alertmanager` (alertmanager:9093)
- `grafana` (grafana:3000)
- `loki` (loki:3100)
- `promtail` (promtail:9080)

If any target is DOWN, check Docker container status:
```bash
ssh ernest@$VM_IP "docker ps -a"
```

### Check 2 — No active alerts firing

Navigate to `http://<VM_IP>:9090/alerts`.

Expected: All alerts in `inactive` state. If any alert is `pending` or `firing`, investigate
and resolve before proceeding.

### Check 3 — Grafana datasources responding

1. Open Grafana at `http://<VM_IP>:3000`.
2. Navigate to **Configuration → Data Sources**.
3. Click **Test** on both `Prometheus` and `Loki` datasources.
4. Expected: Both return a green "Data source is working" confirmation.

### Check 4 — Loki ingesting logs

1. In Grafana, navigate to **Explore**.
2. Select the **Loki** datasource.
3. Run the query: `{container_name=~".+"}`
4. Expected: Recent log entries from running containers appear within the last 5 minutes.

---

## 3. Scenario Procedures

All scenarios follow the same 9-step lifecycle managed by `run_scenario.py`.
The script prompts you at each decision point. Run from the repository root.

**General command form:**

```bash
python3 orchestration/chaos/run_scenario.py --scenario <name>
```

**What to expect in the terminal:**
- Rich panel showing VM and scenario details
- A table of existing VirtualBox snapshots with a pruning reminder
- Confirmation prompt before snapshot creation
- Scenario briefing (expected behaviour and Grafana manifestations rendered as Markdown)
- Injection status message
- A progress bar countdown for the observation window
- Revert confirmation prompt

---

### disk_pressure

**Objective:** Verify that disk consumption triggers `HighDiskUsage` and `CriticalDiskUsage` alerts
and that the Disk Utilization panel reflects real-time usage.

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario disk_pressure
```

**What the injection does:**
A 4 GB file is written to `/tmp/esacp_fill` via `dd`, rapidly consuming available disk space.

**Expected Grafana panel behaviour:**
- **Disk Utilization** gauge climbs toward the 80% threshold line.
- **Alert Status Summary** shows `HighDiskUsage` (warning) within ~30s of the threshold crossing,
  then `CriticalDiskUsage` (critical) if usage exceeds 90%.

**Loki query hint:**
```
{container_name="node_exporter"} |= "disk"
```

**Recovery verification:**
After snapshot revert, confirm `/tmp/esacp_fill` no longer exists and Disk Utilization panel
returns to pre-injection values within one scrape interval (15s).

---

### cpu_saturation

**Objective:** Verify that sustained CPU saturation triggers `HighCPUUsage` and that the CPU
Utilization panel tracks the spike accurately.

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario cpu_saturation
```

**What the injection does:**
4 `yes > /dev/null` processes are launched via SSH, consuming all CPU cores for 120 seconds.

**Expected Grafana panel behaviour:**
- **CPU Utilization** time series spikes sharply above 80%.
- **Alert Status Summary** shows `HighCPUUsage` (warning) after the `for:` duration elapses.

**Loki query hint:**
```
{container_name=~".+"} |= "cpu"
```

**Recovery verification:**
After revert, CPU Utilization panel returns to baseline. No `yes` processes remain:
```bash
ssh ernest@$VM_IP "pgrep yes || echo 'clean'"
```

---

### memory_pressure

**Objective:** Verify that memory allocation pressure triggers `HighMemoryUsage`.

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario memory_pressure
```

**What the injection does:**
A Python script is uploaded to the VM and run in the background. It reads `/proc/meminfo`,
allocates 40% of `MemAvailable` via a `bytearray`, and holds it for 240 seconds.

**Expected Grafana panel behaviour:**
- **Memory Utilization** time series rises as `MemAvailable` decreases.
- **Alert Status Summary** shows `HighMemoryUsage` (warning) after threshold is crossed.

**Loki query hint:**
```
{container_name="node_exporter"} |= "memory"
```

**Recovery verification:**
After revert, `/tmp/esacp_mem_pressure.py` is gone and Memory Utilization returns to baseline.

---

### log_storm

**Objective:** Verify that a high log ingestion rate is visible in Grafana's Log Ingestion Rate
panel and in Grafana Explore.

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario log_storm
```

**What the injection does:**
A throwaway Ubuntu container named `esacp-log-storm` runs `while true; do echo LOG_STORM; done`,
writing to stdout at maximum rate. Promtail picks these up and ships them to Loki.

**Expected Grafana panel behaviour:**
- **Log Ingestion Rate** time series shows a sharp spike in `promtail_sent_entries_total` rate.
- In **Grafana Explore** (Loki), `{container_name="esacp-log-storm"}` shows dense log entries.

**Loki query hint:**
```
{container_name="esacp-log-storm"} | line_format "{{.line}}"
```

**Recovery verification:**
After revert, `esacp-log-storm` container is gone and Log Ingestion Rate returns to baseline.

---

### container_restart_loop

**Objective:** Verify that a repeatedly-restarting container triggers `ContainerRestartLoop`.

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario container_restart_loop
```

**What the injection does:**
A container `esacp-restart-test` is started with `--restart=always` running `sh -c 'exit 1'`,
causing it to exit immediately and restart continuously.

**Expected Grafana panel behaviour:**
- **Container Restart Indicators** time series shows elevated `container_start_time_seconds` rate.
- **Alert Status Summary** shows `ContainerRestartLoop` (warning) after threshold elapses.

**Loki query hint:**
```
{container_name="esacp-restart-test"}
```

**Recovery verification:**
After revert, `esacp-restart-test` container is gone and restart rate drops to zero.

---

### prometheus_stopped

**Objective:** Verify that Prometheus unavailability is detectable via Alertmanager's own
self-monitoring and that Grafana datasource health degrades visibly.

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario prometheus_stopped
```

**What the injection does:**
`docker stop prometheus` terminates the Prometheus container. Port 9090 becomes unreachable.

**Expected Grafana panel behaviour:**
- **Scrape Health Overview** shows targets as stale or unknown (Grafana cannot query Prometheus).
- Prometheus datasource in Grafana Explore shows a connection error.
- `PrometheusDown` alert fires from Alertmanager's internal watchdog rule (if configured).

**Note:** Once Prometheus is down, panels backed by the Prometheus datasource will show
"No data" or errors. This is expected behaviour — the monitoring stack itself is the subject.

**Recovery verification:**
After revert, `http://<VM_IP>:9090/targets` returns all targets as UP within ~30s of boot.

---

### alertmanager_stopped

**Objective:** Verify that Alertmanager unavailability triggers `AlertmanagerDown` and that the
alert appears in Prometheus's own `/alerts` page.

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario alertmanager_stopped
```

**What the injection does:**
`docker stop alertmanager` terminates the Alertmanager container. Port 9093 becomes unreachable.

**Expected Grafana panel behaviour:**
- **Alert Status Summary** shows `AlertmanagerDown` firing.
- Navigate to `http://<VM_IP>:9090/alerts` to confirm the alert state in Prometheus directly.

**Recovery verification:**
After revert, Alertmanager UI at `http://<VM_IP>:9093` is accessible and `AlertmanagerDown`
clears within 2–3 scrape cycles.

---

### loki_stopped

**Objective:** Verify that Loki unavailability triggers `LokiDown` and that Grafana Explore
log queries fail with a datasource error.

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario loki_stopped
```

**What the injection does:**
`docker stop loki` terminates the Loki container. Port 3100 becomes unreachable.

**Expected Grafana panel behaviour:**
- **Alert Status Summary** shows `LokiDown` (warning) after the `for:` duration.
- In Grafana Explore, Loki queries return a datasource connection error.
- **Log Ingestion Rate** panel shows a drop to zero as Promtail can no longer deliver entries.

**Loki query hint (post-revert check):**
```
{container_name=~".+"} | line_format "{{.line}}"
```
Should return results immediately after Loki restarts.

**Recovery verification:**
After revert, Loki is reachable at `http://<VM_IP>:3100/ready` and log entries resume in Explore.

---

### promtail_stopped

**Objective:** Verify that Promtail unavailability triggers `PromtailDown` and stops log
ingestion visibly in Grafana.

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario promtail_stopped
```

**What the injection does:**
`docker stop promtail` terminates the Promtail container. Port 9080 becomes unreachable.

**Expected Grafana panel behaviour:**
- **Log Ingestion Rate** panel drops to zero.
- **Alert Status Summary** shows `PromtailDown` (warning) after the `for:` duration.
- Grafana Explore (Loki) shows no new log entries after injection — existing entries remain.

**Recovery verification:**
After revert, Promtail restarts and new log entries appear in Grafana Explore within ~60s.
Log Ingestion Rate panel recovers to its pre-injection level.

---

### grafana_stopped

**Objective:** Verify that Grafana unavailability triggers `GrafanaDown` and that the alert is
observable in Prometheus (since Grafana itself is unavailable).

**Command:**
```bash
python3 orchestration/chaos/run_scenario.py --scenario grafana_stopped
```

**What the injection does:**
`docker stop grafana` terminates the Grafana container. Port 3000 becomes unreachable.

**Expected behaviour:**
- Grafana UI returns HTTP connection refused.
- Navigate to `http://<VM_IP>:9090/alerts` — `GrafanaDown` appears as pending then firing.
- Alertmanager at `http://<VM_IP>:9093` shows the `GrafanaDown` notification received.

**Note:** Since Grafana is the UI, you must use Prometheus and Alertmanager UIs directly to
observe this alert. This tests that the monitoring stack operates independently of Grafana.

**Recovery verification:**
After revert, Grafana is accessible at `http://<VM_IP>:3000` and `GrafanaDown` clears.

---

## 4. Troubleshooting

### VBoxManage not found

**Symptom:** `❌ VBoxManage not found.`

**Fix:** Add the VirtualBox installation directory to `PATH`, or confirm the WSL path exists:
```bash
ls "/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"
```
If VirtualBox is installed in a non-default path, symlink `VBoxManage.exe` onto `PATH`.

---

### SSH connection refused

**Symptom:** Injection phase shows `⚠️ SSH connection refused — monitoring only.`

**Causes:**
- VM is not running: check `VBoxManage list runningvms`
- SSH service not started: boot into VM console, check `systemctl status sshd`
- Wrong IP: confirm `$VM_IP` matches the VM's current DHCP address

**Quick test:**
```bash
ssh -i $SSH_KEY_PATH ernest@$VM_IP "echo ok"
```

---

### Snapshot already exists

**Symptom:** `VBoxManage failed: Snapshot 'Before disk_pressure test' already exists`

**Fix:** Delete the old snapshot before re-running:
```bash
VBoxManage snapshot esacp-dev delete "Before disk_pressure test"
```
Or rename it to preserve the data point.

---

### Timer expired before alert fired

**Symptom:** Observation window ends but no alert appeared in Grafana.

**Diagnosis:**
1. Check `http://<VM_IP>:9090/alerts` — is the alert `pending`? If so, wait for the `for:` duration.
2. Check `http://<VM_IP>:9090/targets` — is the relevant scrape target `UP`?
3. Confirm you are using the `drill` alert profile if working in the lab group
   (drill profile has 20–30s `for:` durations vs. 2–10m production durations).

**Check active alert profile:**
```bash
ansible-inventory -i ansible/inventory/dev.yml --host console | grep alert_profile
```

---

### Container name conflict

**Symptom:** Injection fails with `docker: Error response from daemon: Conflict. The container name "/esacp-log-storm" is already in use.`

**Fix:** Remove the leftover container from a previous run:
```bash
ssh ernest@$VM_IP "docker rm -f esacp-log-storm esacp-restart-test 2>/dev/null; echo cleaned"
```
If the VM was not reverted after the last scenario, revert to the baseline snapshot first.

---

### Ansible check-mode failures

**Symptom:** `ansible-playbook --check` fails on the alert profile guard task.

**Cause:** `check_mode` does not evaluate conditionals the same way in all cases.
The guard task is a `fail` module with `when:` conditions — it only fires if the conditions are
true at runtime. In check mode against the `lab` group (where `alert_profile=drill`), the guard
will not fire because `'production' not in group_names`.

If a false positive occurs, verify group membership:
```bash
ansible-inventory -i ansible/inventory/dev.yml --list | python3 -m json.tool | grep -A5 '"production"'
```

---

## 5. Enrolling a Mobile / Satellite Terminal (WireGuard + tmux)

Mobile/roaming devices (a Windows tablet, a phone) join the mesh as **manual
spokes** — `ansible_managed: false` in `hosts_map.yml`, so `generate_inventory.py`
excludes them and Ansible never connects to them. The hub learns each one via the
`wg_external_peers` list in `ansible/group_vars/all.yml`. (ESACP#383)

### 5a. Enroll a new WireGuard peer

1. **Generate keys** (from project root):
   ```bash
   bash config/wireguard/add_peer.sh <name>      # e.g. iconia
   ```
   Note the printed `wg_pubkey_<name>`.
2. **Register the peer** in three files:
   - `hosts_map.yml` → add under the `mobile:` group (`wg_ip`, `wg_role: spoke`,
     `ansible_managed: false`). Pick a free `10.10.0.x` (≥ `.20` for mobile).
   - `ansible/group_vars/all.yml` → add `wg_pubkey_<name>` and an entry under
     `wg_external_peers` (`name` + `wg_ip`).
   - (no inventory edit — `generate_inventory.py` skips unmanaged hosts; the
     summary line confirms `[manual]`).
3. **Apply the hub config** (renders the new `[Peer]` into saconsole's `wg0.conf`):
   ```bash
   cd ansible
   ansible-playbook -i inventory/kvm.yml site-kvm.yml --limit saconsole --tags wireguard
   ```
4. **Build the client config** and transfer it securely to the device (it holds
   the private key — never commit it):
   ```bash
   # produces ~/<name>-wg0.conf (mode 0600); Endpoint = toshy.iridium.blue:51820
   ```
   On **Windows**: install *WireGuard for Windows*, "Add Tunnel" → import the
   `.conf`, activate. On the **home/office LAN** `toshy.iridium.blue` resolves
   directly; from a foreign network you need a public DDNS name with UDP/51820
   forwarded to the hypervisor (out of v1 scope).
5. **Verify**: on the device, the tunnel shows a recent handshake;
   `ping 10.10.0.1` (hub) and `ping 10.10.0.2` (controller) succeed. The standard
   spoke config (`AllowedIPs = 10.10.0.0/24` + hub forwarding) gives full-mesh
   reachability.

### 5b. Attach a satellite mirrored terminal

`Cld.sh` launches Claude Code inside a shared tmux session (`esacp`) by default.
A second terminal attaches to the **same live session** and can drive it:

```bash
ssh you@10.10.0.2 -t 'tmux attach -t esacp'      # from the tablet, over WireGuard
```

- Both terminals render the same output and accept input (turn-taking — one
  input stream).
- `window-size largest` (set by `Cld.sh`) keeps the controller terminal full-size
  when the smaller tablet attaches; the tablet shows a scrolled view of the larger
  geometry.
- `ESACP_NO_TMUX=1 ./Cld.sh` launches Claude Code directly, without the shared
  session.
- The tablet's SSH **public** key must be in the controller's
  `~/.ssh/authorized_keys`.
