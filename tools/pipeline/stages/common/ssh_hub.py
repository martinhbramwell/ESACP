"""Hub-transport SSH helper — ProxyJump through the hypervisor to the hub VM."""

from __future__ import annotations

import subprocess

from tools.host_identity import DEFAULT_HYPERVISOR, GUEST_VM_USER, HUB_VIRBR0_IP
from tools.pipeline.stages.common.types import Config


def hub_ssh_run(
    config: Config, cmd: str, *, timeout: int = 15,
) -> subprocess.CompletedProcess[str]:
    """Run *cmd* on the hub VM via ProxyJump through the hypervisor."""
    hyp = config.hypervisor or DEFAULT_HYPERVISOR
    return subprocess.run(
        ["ssh",
         "-o", f"ProxyJump={hyp}",
         "-o", "StrictHostKeyChecking=no",
         "-i", config.ssh_key,
         f"{GUEST_VM_USER}@{HUB_VIRBR0_IP}",
         cmd],
        capture_output=True, text=True, timeout=timeout,
    )


# Backward-compatible alias
saconsole_ssh_run = hub_ssh_run
