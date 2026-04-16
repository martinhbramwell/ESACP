"""Shared helpers for API route modules."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import HTTPException

from tools.api.jobs import PROJECT_ROOT

HOSTS_MAP      = PROJECT_ROOT / "hosts_map.yml"
GROUP_VARS_ALL = PROJECT_ROOT / "ansible" / "group_vars" / "all.yml"


def load_hosts_map() -> dict:
    with open(HOSTS_MAP) as f:
        return yaml.safe_load(f)


def kvm_hosts() -> dict:
    return load_hosts_map()["groups"].get("kvm", {})


def get_host_or_404(hostname: str) -> dict:
    hosts = kvm_hosts()
    if hostname not in hosts:
        raise HTTPException(404, f"'{hostname}' not found in hosts_map.yml")
    return hosts[hostname]


def last_octet(ip: str) -> int:
    try:
        return int(ip.split(".")[-1])
    except (ValueError, IndexError):
        return 0


def load_erp_user(default: str = "erpadm") -> str:
    try:
        with open(GROUP_VARS_ALL) as f:
            return yaml.safe_load(f).get("erp_user", default)
    except Exception:
        return default
