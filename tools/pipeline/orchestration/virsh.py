"""Free-form virsh-over-SSH wrapper — shared by VM orchestration primitives."""

from __future__ import annotations

import subprocess


def virsh_ssh(
    hypervisor: str, virsh_cmd: str, timeout: int = 30,
) -> subprocess.CompletedProcess:
    """Run ``virsh --connect qemu:///system <cmd>`` on *hypervisor* via SSH."""
    return subprocess.run(
        ["ssh", hypervisor, f"virsh --connect qemu:///system {virsh_cmd}"],
        capture_output=True, text=True, timeout=timeout,
    )
