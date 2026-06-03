"""Low-level hypervisor helpers — remote (SSH) and local (virsh) wrappers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.host_identity import GUEST_VM_USER


def vm_exists(vm: str, hypervisor: str | None = None) -> bool:
    """True if *vm* is defined (any state) on the hypervisor."""
    cmd = _virsh_cmd("dominfo", vm, hypervisor)
    return subprocess.run(cmd, capture_output=True).returncode == 0


def vm_state(vm: str, hypervisor: str | None = None) -> str | None:
    """Return domstate string (e.g. 'running', 'shut off') or None."""
    cmd = _virsh_cmd("domstate", vm, hypervisor)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip().lower() if r.returncode == 0 else None


def start_vm(vm: str, hypervisor: str | None = None) -> None:
    """Start a shut-off VM. Raises RuntimeError on failure."""
    cmd = _virsh_cmd("start", vm, hypervisor)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"virsh start {vm} failed: {r.stderr.strip()}")


def tcp_probe_via_hypervisor(
    virbr0_ip: str, hypervisor: str, user: str = "hasan",
) -> bool:
    """Probe TCP port 22 on a hypervisor-internal IP via ProxyJump."""
    r = subprocess.run(
        ["ssh",
         "-o", "ConnectTimeout=5",
         "-o", "StrictHostKeyChecking=no",
         "-o", "BatchMode=yes",
         "-J", f"{user}@{hypervisor}",
         f"{GUEST_VM_USER}@{virbr0_ip}", "true"],
        capture_output=True,
    )
    return r.returncode == 0


def ansible_ping(vm: str, project_root: str, ssh_key: str) -> bool:
    """Run ``ansible -m ping`` against *vm*. Returns True on SUCCESS."""
    ansible_dir = Path(project_root) / "ansible"
    env_extra = {
        "ANSIBLE_CONFIG": str(ansible_dir / "ansible.cfg"),
        "ANSIBLE_PRIVATE_KEY_FILE": ssh_key,
    }
    import os
    env = {**os.environ, **env_extra}
    r = subprocess.run(
        ["ansible", "all", "-i", "inventory/kvm.yml",
         "-m", "ping", "--one-line", "--limit", vm],
        capture_output=True, text=True, env=env, cwd=str(ansible_dir),
    )
    return r.returncode == 0 and "SUCCESS" in r.stdout


def _virsh_cmd(action: str, vm: str, hypervisor: str | None) -> list[str]:
    """Build a virsh command — local or via SSH."""
    if hypervisor:
        return ["ssh", hypervisor, "virsh", "--connect", "qemu:///system", action, vm]
    return ["virsh", action, vm]
