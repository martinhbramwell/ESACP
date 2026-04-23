#!/usr/bin/env python3
"""Shared SSH helper for Stage 6 verify checks."""

from __future__ import annotations

import subprocess


def ssh_vm(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    cmd: str, timeout: int = 15,
):
    """Run a command on the VM via SSH; return completed process."""
    return subprocess.run(
        ["ssh", *ssh_opts, "-i", ssh_key, f"you@{target_ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )
