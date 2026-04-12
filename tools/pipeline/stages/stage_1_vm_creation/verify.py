#!/usr/bin/env python3
"""Verify Stage 1 (VM Creation) postconditions.

Each check returns (pass, description).  The runner prints a summary and
exits non-zero if any check fails.  Importable for use as a pre-stage
idempotency gate: if all pass, Stage 1 can be skipped entirely.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def _ssh_hyp(hypervisor: str, cmd: str, timeout: int = 15):
    return subprocess.run(
        ["ssh", hypervisor, cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def check_wg_key_in_sops(hostname: str, project_root: str) -> tuple[bool, str]:
    """WireGuard keypair exists in keys.sops.yml."""
    sops_file = Path(project_root) / "config" / "wireguard" / "keys.sops.yml"
    r = subprocess.run(
        ["sops", "-d", str(sops_file)],
        cwd=project_root, capture_output=True, text=True,
    )
    if r.returncode != 0:
        return False, f"sops decrypt failed: {r.stderr.strip()}"
    if hostname in r.stdout:
        return True, f"WG keypair for '{hostname}' in keys.sops.yml"
    return False, f"No WG keypair for '{hostname}' in keys.sops.yml"


def check_wg_pubkey_in_groupvars(hostname: str, project_root: str) -> tuple[bool, str]:
    """wg_pubkey_{hostname} present in group_vars/all.yml."""
    gv = Path(project_root) / "ansible" / "group_vars" / "all.yml"
    content = gv.read_text()
    key_name = f"wg_pubkey_{hostname}"
    if key_name in content:
        return True, f"{key_name} in group_vars/all.yml"
    return False, f"{key_name} NOT in group_vars/all.yml"


def check_vm_exists(hostname: str, hypervisor: str) -> tuple[bool, str]:
    """VM domain exists on hypervisor."""
    r = _ssh_hyp(hypervisor,
                 f"virsh --connect qemu:///system dominfo {hostname}")
    if r.returncode == 0:
        return True, f"VM '{hostname}' exists on {hypervisor}"
    return False, f"VM '{hostname}' not found on {hypervisor}"


def check_vm_running(hostname: str, hypervisor: str) -> tuple[bool, str]:
    """VM is in 'running' state."""
    r = _ssh_hyp(hypervisor,
                 f"virsh --connect qemu:///system domstate {hostname}")
    state = r.stdout.strip()
    if state == "running":
        return True, f"VM '{hostname}' is running"
    return False, f"VM '{hostname}' state: {state}"


def check_ssh_reachable(
    virbr0_ip: str, hypervisor: str, ssh_key: str,
) -> tuple[bool, str]:
    """SSH reachable on virbr0_ip via ProxyJump."""
    r = subprocess.run(
        ["ssh",
         "-o", f"ProxyJump={hypervisor}",
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10",
         "-i", ssh_key,
         f"you@{virbr0_ip}", "echo ready"],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode == 0 and "ready" in r.stdout:
        return True, f"SSH to {virbr0_ip} via {hypervisor} OK"
    return False, f"SSH to {virbr0_ip} failed: {r.stderr.strip()}"


def check_baseline_snapshot(hostname: str, hypervisor: str) -> tuple[bool, str]:
    """'Baseline' snapshot exists."""
    r = _ssh_hyp(hypervisor,
                 f"virsh --connect qemu:///system snapshot-list {hostname} --name")
    if r.returncode == 0 and "Baseline" in r.stdout:
        return True, f"Baseline snapshot exists for '{hostname}'"
    return False, f"No Baseline snapshot for '{hostname}'"


def verify_stage_1(
    hostname: str,
    virbr0_ip: str,
    hypervisor: str,
    project_root: str,
    ssh_key: str | None = None,
) -> list[tuple[bool, str]]:
    """Run all Stage 1 postcondition checks.  Returns list of (pass, msg)."""
    if ssh_key is None:
        ssh_key = str(Path.home() / ".ssh" / "hasan_mighty")
    return [
        check_wg_key_in_sops(hostname, project_root),
        check_wg_pubkey_in_groupvars(hostname, project_root),
        check_vm_exists(hostname, hypervisor),
        check_vm_running(hostname, hypervisor),
        check_ssh_reachable(virbr0_ip, hypervisor, ssh_key),
        check_baseline_snapshot(hostname, hypervisor),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


# ── CLI entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hostname> [project_root]")
        sys.exit(2)

    host = sys.argv[1]
    proj = sys.argv[2] if len(sys.argv) > 2 else str(Path(__file__).resolve().parents[4])

    # Load host config from hosts_map.yml
    hm = Path(proj) / "hosts_map.yml"
    with open(hm) as f:
        data = yaml.safe_load(f)
    host_cfg = data["groups"]["kvm"][host]

    results = verify_stage_1(
        hostname=host,
        virbr0_ip=host_cfg["virbr0_ip"],
        hypervisor=host_cfg.get("hypervisor", "toshiba"),
        project_root=proj,
    )

    print(f"\n── Stage 1 verification: {host} ──")
    passed = failed = 0
    for ok, msg in results:
        tag = "✅" if ok else "❌"
        print(f"  {tag}  {msg}")
        if ok:
            passed += 1
        else:
            failed += 1
    print(f"\n  {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
