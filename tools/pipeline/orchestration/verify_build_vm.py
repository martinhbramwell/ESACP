#!/usr/bin/env python3
"""Verify build_vm primitives — colocated acceptance test.

Usage: ./tools/pipeline/orchestration/verify_build_vm.py <hostname>
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Ensure project root is importable
sys.path.insert(0, str(PROJECT_ROOT))

from tools.pipeline.orchestration.hypervisor_helpers import (
    ansible_ping, tcp_probe_via_hypervisor, vm_exists, vm_state,
)
from tools.pipeline.stages.common.known_hosts import known_hosts_entries, tcp_port_open
from tools.pipeline.orchestration.load_host_config import load_host_config


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hostname>")
        return 1

    hostname = sys.argv[1]
    host_cfg = load_host_config(hostname, str(PROJECT_ROOT))
    hypervisor = host_cfg.get("hypervisor")
    virbr0_ip = host_cfg.get("virbr0_ip", "")
    results: list[tuple[bool, str]] = []

    # ── Hypervisor helpers ──
    exists = vm_exists(hostname, hypervisor)
    results.append((exists, f"vm_exists({hostname}) = {exists}"))

    state = vm_state(hostname, hypervisor)
    results.append((state is not None, f"vm_state({hostname}) = {state}"))

    if state == "running" and virbr0_ip:
        if hypervisor:
            tcp_ok = tcp_probe_via_hypervisor(virbr0_ip, hypervisor)
            results.append((tcp_ok, f"tcp_probe_via_hypervisor({virbr0_ip}) = {tcp_ok}"))
        else:
            tcp_ok = tcp_port_open(virbr0_ip)
            results.append((tcp_ok, f"tcp_port_open({virbr0_ip}) = {tcp_ok}"))

        ssh_key = str(Path.home() / ".ssh" / "hasan_mighty")
        ping_ok = ansible_ping(hostname, str(PROJECT_ROOT), ssh_key)
        results.append((ping_ok, f"ansible_ping({hostname}) = {ping_ok}"))

    # ── Known hosts helpers ──
    entries = known_hosts_entries(host_cfg)
    results.append((len(entries) > 0, f"known_hosts_entries: {entries}"))

    # ── File size checks ──
    orch = Path(__file__).resolve().parent
    for pattern in ("build_vm*.py", "hypervisor_helpers.py"):
        for py in sorted(orch.glob(pattern)):
            n = len(py.read_text().splitlines())
            results.append((n <= 80, f"{py.name}: {n} lines (limit 80)"))

    # ── Report ──
    all_ok = True
    for ok, msg in results:
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {msg}")
        if not ok:
            all_ok = False

    print()
    print(f"{'All checks passed' if all_ok else 'Some checks FAILED'} ({len(results)} checks)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
