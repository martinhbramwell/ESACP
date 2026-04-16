"""Observability validation primitives — Grafana credential sourcing and validation.

Credential sourcing is non-interactive (env → SSH to hub). If neither source
yields a password, ``source_grafana_creds`` returns ``(user, None)`` and the
caller decides whether to prompt. This keeps the primitive usable from any
non-TTY context (API, worker) without breaking CLI interactivity.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from tools.host_identity import HUB_KEY, HUB_WG_IP
from tools.pipeline.stages.common.types import Emit


def _ssh(host_ip: str, user: str, key: str, cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-i", key,
         "-o", "StrictHostKeyChecking=accept-new",
         "-o", "ConnectTimeout=10",
         f"{user}@{host_ip}", cmd],
        capture_output=True, text=True,
    )


def source_grafana_creds(
    vm_user: str,
    ssh_key: str,
    emit: Emit,
) -> tuple[str, Optional[str]]:
    """Return (user, password) from env or hub .env, or (user, None) if neither."""
    user = os.environ.get("GRAFANA_ADMIN_USER", "admin")
    password = os.environ.get("GRAFANA_ADMIN_PASSWORD", "")

    if password:
        emit("  [dim]Grafana credentials from environment[/dim]")
        return user, password

    if HUB_KEY and HUB_WG_IP:
        r = _ssh(
            HUB_WG_IP, vm_user, ssh_key,
            "sudo grep GRAFANA_ADMIN_PASSWORD /opt/observability/.env 2>/dev/null",
        )
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                if "GRAFANA_ADMIN_PASSWORD=" in line:
                    password = line.split("=", 1)[1].strip()
                    emit(f"  [dim]Grafana credentials retrieved from {HUB_KEY}[/dim]")
                    return user, password

    emit("[yellow]Grafana password not found in env or on hub.[/yellow]")
    return user, None


def validate_observability(
    user: str,
    password: str,
    script_path: str,
    verbose: bool = False,
) -> int:
    """Invoke the 27-check validation script with creds injected into env."""
    env = os.environ.copy()
    env["GRAFANA_ADMIN_USER"] = user
    env["GRAFANA_ADMIN_PASSWORD"] = password

    cmd = ["python3", script_path]
    if verbose:
        cmd.append("--verbose")

    return subprocess.run(cmd, env=env).returncode
