# ESACP — System Overview

Enterprise System Administration & Chaos Planning

---

## What This System Does

ESACP is a training lab that teaches real-world server administration skills by
doing them for real. It sets up a small network of virtual servers, monitors
everything those servers are doing, and deliberately breaks things so you can
practise diagnosing and fixing problems — all in a safe, repeatable environment
that can be reset and rebuilt at any time.

---

## The Two Servers

The lab runs two virtual servers on your workstation:

**saconsole** is the monitoring hub. It collects metrics and logs from every
machine in the network and displays them on a web dashboard (Grafana). It also
sends alerts to Telegram when something goes wrong. Every service on this
machine — the dashboard, the metric database, the log storage, the alert router
— runs inside Docker containers that are automatically started, configured, and
updated by the build scripts.

**target1** is the monitored machine. It runs a lightweight agent
(node_exporter) that reports CPU, memory, disk, and network statistics back to
saconsole every 15 seconds. It is the intended subject of the failure-injection
exercises.

The two servers communicate over an encrypted private network (WireGuard) that
is built and configured automatically as part of the build process.

---

## What You Can See

Once the lab is running, a web browser pointed at saconsole shows:

- **Live metrics** — CPU load, memory usage, disk space, network traffic, and
  container resource consumption for both servers, updated in real time.
- **Logs** — a searchable stream of system events from both machines.
- **Alerts** — configured thresholds that fire Telegram notifications when, for
  example, disk usage exceeds 85 %, or a container keeps crashing.

A validation script (`validate_observability.py`) runs 27 automated checks
and confirms in seconds that every component is working end-to-end.

---

## How It Is Built

The entire lab — from blank virtual machine to fully running monitoring stack —
is built by running three commands:

```
bash platforms/kvm/rebuild_lab.sh      # hub-only rebuild (saconsole + WireGuard)
./tools/esacp.py provision <hostname>  # provision a dev-quadrant VM through the pipeline
```

The provisioner handles the rest automatically: it waits for the OS to install
itself, takes a snapshot at each milestone, applies all configuration through
Ansible, and ends with a working, verified system. The only manual step is
typing a sudo password once for the local WireGuard setup.

All passwords and encryption keys are stored in encrypted files inside the
repository and are never visible in plain text.

---

## Repeatable by Design

Every configuration decision is captured in code. To start over:

1. Revert both virtual machines to a saved snapshot.
2. Re-run the provisioner.

This makes it practical to run the same failure scenarios repeatedly, try
different alert configurations, or hand the lab to someone else to use on
their own machine.

---

## Where the Controller Can Run

The build scripts are designed to run from four different types of controller
machine, making the lab accessible regardless of what hardware you have:

| Controller | How it works |
|---|---|
| Windows 11 laptop (WSL2) | Runs Ansible inside Linux-on-Windows; manages VirtualBox VMs |
| Xubuntu workstation | Runs Ansible natively; manages KVM virtual machines directly |
| Ubuntu server (remote) | Connects over SSH via a graphical remote session (X2Go); manages cloud VPS instances |
| Mac laptop or desktop | Runs Ansible natively via Homebrew; manages cloud VPS instances |

The cloud VPS option (for the Ubuntu server and Mac platforms) uses a
pay-as-you-go European provider (iwStack/Prometeus) so no local hypervisor is
needed — the lab runs entirely in the cloud from those controllers.
