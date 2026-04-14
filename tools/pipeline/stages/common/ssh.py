"""SSH / SCP / rsync helpers — build subprocess commands from Config."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.host_identity import HUB_VIRBR0_IP
from tools.pipeline.stages.common.types import Config


def _ssh_base(config: Config) -> list[str]:
    """Common SSH prefix for the target VM."""
    return [
        "ssh",
        *config.ssh_opts,
        "-i", config.ssh_key,
        f"you@{config.target_ip}",
    ]


def ssh_run(
    config: Config, cmd: str, *, timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """Run *cmd* on the target VM over SSH."""
    return subprocess.run(
        _ssh_base(config) + [cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def scp_to_vm(
    config: Config,
    local_files: list[str],
    remote_dest: str,
    *,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """SCP one or more local files to *remote_dest* on the target VM."""
    return subprocess.run(
        ["scp", *config.ssh_opts, "-i", config.ssh_key,
         *local_files, f"you@{config.target_ip}:{remote_dest}"],
        capture_output=True, text=True, timeout=timeout,
    )


def rsync_to_vm(
    config: Config,
    local_path: str,
    remote_path: str,
    *,
    timeout: int = 30,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Rsync *local_path* to *remote_path* on the target VM."""
    rsh = (
        f"ssh {' '.join(config.ssh_opts)} -i {config.ssh_key}"
    )
    cmd = ["rsync", "-a", "-e", rsh, *(extra_args or []),
           local_path, f"you@{config.target_ip}:{remote_path}"]
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
    )


def hub_ssh_run(
    config: Config, cmd: str, *, timeout: int = 15,
) -> subprocess.CompletedProcess[str]:
    """Run *cmd* on the hub VM via ProxyJump through the hypervisor."""
    hyp = config.hypervisor or "toshiba"
    return subprocess.run(
        ["ssh",
         "-o", f"ProxyJump={hyp}",
         "-o", "StrictHostKeyChecking=no",
         "-i", config.ssh_key,
         f"you@{HUB_VIRBR0_IP}",
         cmd],
        capture_output=True, text=True, timeout=timeout,
    )


# Backward-compatible alias
saconsole_ssh_run = hub_ssh_run
