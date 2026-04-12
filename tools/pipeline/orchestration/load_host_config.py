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
