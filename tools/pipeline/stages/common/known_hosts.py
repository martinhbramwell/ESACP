"""Known-hosts helpers — entries, remove, populate, TCP probe."""

from __future__ import annotations

import socket
import subprocess
from pathlib import Path

from tools.pipeline.stages.common.types import Emit


def known_hosts_entries(info: dict) -> list[str]:
    """All SSH known_hosts identifiers for one host (hostname, nickname, IPs)."""
    seen: list[str] = []
    for field in ("hostname", "nickname", "virbr0_ip", "wg_ip"):
        val = info.get(field)
        if val and val not in seen:
            seen.append(val)
    return seen


def remove_known_hosts(entries: list[str], emit: Emit) -> int:
    """Remove entries from ~/.ssh/known_hosts. Returns count removed."""
    removed = 0
    for entry in entries:
        r = subprocess.run(["ssh-keygen", "-R", entry], capture_output=True, text=True)
        if r.returncode == 0 and "not found" not in r.stderr:
            removed += 1
    if removed:
        emit(f"  Cleared {removed} stale known_hosts entry/entries")
    return removed


def populate_known_hosts(entries: list[str], emit: Emit) -> None:
    """ssh-keyscan each entry and append to ~/.ssh/known_hosts."""
    kh = Path.home() / ".ssh" / "known_hosts"
    for entry in entries:
        r = subprocess.run(
            ["ssh-keyscan", "-H", "-T", "5", entry],
            capture_output=True, text=True,
        )
        if r.stdout.strip():
            with open(kh, "a") as fh:
                fh.write(r.stdout)
            emit(f"  Host key added for {entry}")


def populate_known_hosts_via_hypervisor(
    virbr0_ip: str, hypervisor: str, emit: Emit,
) -> None:
    """Collect host key via the hypervisor and append to local known_hosts."""
    kh = Path.home() / ".ssh" / "known_hosts"
    r = subprocess.run(
        ["ssh", hypervisor, "ssh-keyscan", "-H", "-T", "5", virbr0_ip],
        capture_output=True, text=True,
    )
    if r.stdout.strip():
        with open(kh, "a") as fh:
            fh.write(r.stdout)
        emit(f"  Host key for {virbr0_ip} added via {hypervisor}")


def tcp_port_open(host: str, port: int = 22, timeout: int = 5) -> bool:
    """True if a TCP connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
