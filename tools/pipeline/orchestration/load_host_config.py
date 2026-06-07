"""Load a single host's configuration from hosts_map.yml."""

from __future__ import annotations

from pathlib import Path

import yaml


def load_host_config(hostname: str, project_root: str | Path) -> dict:
    """Return the host entry dict from hosts_map.yml, or raise if not found."""
    hosts_map = Path(project_root) / "hosts_map.yml"
    with open(hosts_map) as f:
        data = yaml.safe_load(f)
    kvm = data.get("groups", {}).get("kvm", {})
    if hostname not in kvm:
        raise KeyError(f"'{hostname}' not found in the kvm group of hosts_map.yml")
    return kvm[hostname]


# Default frappe major when a host entry omits target_frappe_major — matches the
# packer-baked v13-era image (see hosts_map.yml header). Dual-template: a host
# clones the template for the major it targets (ESACP #631).
DEFAULT_FRAPPE_MAJOR = 13


def target_frappe_major(host_cfg: dict) -> int:
    """Return a host's target frappe major (``target_frappe_major``, default 13)."""
    return int(host_cfg.get("target_frappe_major", DEFAULT_FRAPPE_MAJOR))
