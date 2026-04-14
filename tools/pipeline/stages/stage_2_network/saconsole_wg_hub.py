#!/usr/bin/env python3
"""Update the hub WireGuard configuration via Ansible."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.host_identity import HUB_KEY
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def _stream_lines(pipe) -> list[str]:
    """Read lines from a pipe, stripping trailing whitespace."""
    lines: list[str] = []
    for raw in pipe:
        line = raw.decode("utf-8", errors="replace").rstrip()
        lines.append(line)
    return lines


def update_hub_wg(config: Config, emit: Emit) -> TaskResult:
    """Run ``ansible-playbook --limit <hub_key> --tags wireguard``.

    Tells the hub about the new peer so it accepts WG handshakes.
    """
    ansible_dir = Path(config.project_root) / "ansible"
    proc = subprocess.Popen(
        [
            "ansible-playbook",
            "-i", "inventory/kvm.yml",
            "site-kvm.yml",
            "--limit", HUB_KEY,
            "--tags", "wireguard",
        ],
        cwd=str(ansible_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for line in _stream_lines(proc.stdout):
        emit(f"  {line}")
    proc.wait()
    if proc.returncode != 0:
        return TaskResult(False, False,
                          f"Ansible wireguard hub failed (exit {proc.returncode})")
    return TaskResult(True, True, "Hub WireGuard updated")


# Backward-compatible alias
update_saconsole_wg_hub = update_hub_wg
