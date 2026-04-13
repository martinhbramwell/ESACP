#!/usr/bin/env python3
"""Update saconsole WireGuard hub configuration via Ansible."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def _stream_lines(pipe) -> list[str]:
    """Read lines from a pipe, stripping trailing whitespace."""
    lines: list[str] = []
    for raw in pipe:
        line = raw.decode("utf-8", errors="replace").rstrip()
        lines.append(line)
    return lines


def update_saconsole_wg_hub(config: Config, emit: Emit) -> TaskResult:
    """Run ``ansible-playbook --limit saconsole --tags wireguard``.

    Tells saconsole about the new peer so the hub accepts WG handshakes.
    """
    ansible_dir = Path(config.project_root) / "ansible"
    proc = subprocess.Popen(
        [
            "ansible-playbook",
            "-i", "inventory/kvm.yml",
            "site-kvm.yml",
            "--limit", "saconsole",
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
    return TaskResult(True, True, "saconsole WireGuard hub updated")
