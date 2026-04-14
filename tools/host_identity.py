#!/usr/bin/env python3
"""Resolve host identities from hosts_map.yml at import time.

Provides constants for the WireGuard hub and helper functions for
looking up any host by key or role.  All Python code that previously
hardcoded "saconsole" should import from here instead.

Usage:
    from tools.host_identity import HUB_KEY, HUB_VM_NAME, HUB_HOSTNAME
    from tools.host_identity import HUB_VIRBR0_IP, HUB_WG_IP
    from tools.host_identity import hub_vm, kvm_hosts
"""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
HOSTS_MAP_PATH = PROJECT_ROOT / "hosts_map.yml"


def _load_kvm() -> dict:
    with open(HOSTS_MAP_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("groups", {}).get("kvm", {})


def _find_hub(kvm: dict) -> tuple[str, dict]:
    for key, attrs in kvm.items():
        if attrs.get("wg_role") == "hub":
            return key, attrs
    return "", {}


_kvm = _load_kvm()
_hub_key, _hub_attrs = _find_hub(_kvm)

HUB_KEY: str = _hub_key
HUB_VM_NAME: str = _hub_attrs.get("vm_name", _hub_key)
HUB_HOSTNAME: str = _hub_attrs.get("hostname", _hub_key)
HUB_DISPLAY_NAME: str = _hub_attrs.get("display_name", _hub_key)
HUB_VIRBR0_IP: str = _hub_attrs.get("virbr0_ip", "")
HUB_WG_IP: str = _hub_attrs.get("wg_ip", "")
HUB_NICKNAME: str = _hub_attrs.get("nickname", "")


def hub_vm(config: dict | None = None) -> str:
    """Return the hosts_map key for the hub VM.

    Accepts an optional hosts_map config dict for compatibility with
    callers that already loaded it.  If *config* is None, uses the
    module-level constant.
    """
    if config is None:
        return HUB_KEY
    kvm = config.get("groups", {}).get("kvm", {})
    for key, attrs in kvm.items():
        if attrs.get("wg_role") == "hub":
            return key
    return ""


def kvm_hosts(config: dict | None = None) -> dict:
    """Return the KVM hosts dict from hosts_map data."""
    if config is None:
        return _kvm
    return config.get("groups", {}).get("kvm", {})


def host_field(key: str, field: str, default: str = "") -> str:
    """Look up a single field for a KVM host by its hosts_map key."""
    return _kvm.get(key, {}).get(field, default)
