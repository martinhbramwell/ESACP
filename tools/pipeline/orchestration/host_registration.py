#!/usr/bin/env python3
"""Register a new KVM host in hosts_map.yml and regenerate Ansible inventory.

Single source of truth for the YAML mutation previously duplicated across
three api.py endpoints. Raises ``HostRegistrationError`` (HTTP 400),
``HostConflictError`` (409), or ``RuntimeError`` (500); callers map those.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import yaml

from tools.pipeline.orchestration.host_registration_block import (
    MARKER, build_host_block,
)
from tools.pipeline.orchestration.inventory_regen import regenerate_inventory
from tools.pipeline.orchestration.known_hosts_cleanup import clear_known_hosts

Emit = Callable[[str], None]

_HOSTNAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class HostRegistrationError(ValueError):
    """Invalid input — user-correctable. Maps to HTTP 400."""


class HostConflictError(ValueError):
    """Resource already exists (hostname or IP). Maps to HTTP 409."""


def register_host(
    *,
    hostname: str, nickname: str, virbr0_ip: str, wg_ip: str,
    hypervisor: str, zone: str, vm_role: str, backend: str,
    project_root: str, emit: Emit,
) -> None:
    if not _HOSTNAME_RE.match(hostname):
        raise HostRegistrationError(
            "hostname: lowercase letters/digits/hyphens, must start with a letter"
        )
    root = Path(project_root)
    hosts_map_path = root / "hosts_map.yml"
    data = yaml.safe_load(hosts_map_path.read_text())
    kvm = data.get("groups", {}).get("kvm", {}) or {}

    if hostname in kvm:
        raise HostConflictError(f"'{hostname}' already exists in the kvm group")
    for name, h in kvm.items():
        if h.get("wg_ip") == wg_ip:
            raise HostConflictError(f"WireGuard IP {wg_ip} already used by '{name}'")
        if h.get("virbr0_ip") == virbr0_ip:
            raise HostConflictError(f"virbr0 IP {virbr0_ip} already used by '{name}'")

    text = hosts_map_path.read_text()
    if MARKER not in text:
        raise RuntimeError(f"Cannot find '{MARKER}' insertion point in hosts_map.yml")
    block = build_host_block(
        hostname=hostname, nickname=nickname, virbr0_ip=virbr0_ip, wg_ip=wg_ip,
        hypervisor=hypervisor, vm_role=vm_role, backend=backend, zone=zone,
    )
    hosts_map_path.write_text(text.replace(MARKER, block + MARKER))
    emit(f"  [OK] registered {hostname} in hosts_map.yml")

    # Defense-in-depth: clear stale known_hosts entries in case a prior VM
    # at these addresses was destroyed elsewhere or the controller was
    # different. destroy.py also runs this; the duplication is intentional.
    clear_known_hosts([hostname, wg_ip, virbr0_ip], emit)

    regenerate_inventory(root, emit)
