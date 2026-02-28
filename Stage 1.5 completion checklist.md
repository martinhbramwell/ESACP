# Stage 1.5 Completion Checklist

## Before Provisioning

- [ ] **Set environment variables** in your WSL terminal (needed by both the provisioning script and the chaos runner):
  ```bash
  export VM_IP=<your VM's IP address>
  export VM_HOSTNAME=<your VirtualBox VM name, e.g. esacp-dev>
  export SSH_KEY_PATH=~/.ssh/id_ed25519
  export SNAPSHOT_NAME="Stage 1 Complete"
  export VM_USER=ernest
  ```

- [ ] **Revert the VM** to your "Stage 1 Complete" snapshot so provisioning starts from a known-good state:
  ```bash
  python3 orchestration/revertToBaseline.py --vm $VM_HOSTNAME --snapshot "Stage 1 Complete"
  ```

## Provision

- [ ] **Run the provisioner** to push all the new files to the VM and restart the stack:
  ```bash
  python3 orchestration/provision.py --target dev
  ```
  Watch the Ansible output — you should see the task name say `Copy Prometheus alert rules (production profile)`.

## Verify After Provisioning

- [ ] **All 7 Prometheus targets UP** — open `http://<VM_IP>:9090/targets` and confirm all seven services (prometheus, node, cadvisor, alertmanager, grafana, loki, promtail) show state `UP`.

- [ ] **No active alerts** — open `http://<VM_IP>:9090/alerts` and confirm all alerts are in `inactive` state.

- [ ] **Three dashboards in Grafana** — open `http://<VM_IP>:3000`, go to Dashboards, and confirm you see "Node Exporter Full", "Cadvisor exporter", and "ESACP Management Console" all loaded with data.

- [ ] **Management Console has no empty panels** — click into the Management Console dashboard and check that all 7 panels show data (none should say "No data").

- [ ] **Loki ingesting logs** — in Grafana, go to Explore → select Loki datasource → run `{container_name=~".+"}` → confirm recent log entries appear.

## Commit

- [ ] **Create a signed commit** with the Stage 1.5 changes (you run this, as you handle signing):
  ```bash
  git add -A
  git commit -S -m "Stage 1.5: observability validation and management console framework"
  ```

## Snapshot

- [ ] **Take the Stage 1.5 Complete snapshot** after a successful provision and verify:
  ```bash
  VBoxManage snapshot $VM_HOSTNAME take "Stage 1.5 Complete"
  ```

## Optional: Run a Test Scenario

- [ ] **Smoke-test the chaos runner** with a low-risk scenario (e.g. `disk_pressure` or `prometheus_stopped`) to confirm the full 9-step lifecycle works end-to-end:
  ```bash
  python3 orchestration/chaos/run_scenario.py --scenario disk_pressure
  ```
