"""Field-derivation helpers for build_config (split from config.py, #521)."""

from __future__ import annotations

from pathlib import Path

import yaml

from tools.host_identity import DEFAULT_HYPERVISOR


def _derive_zone(ansible_groups: list[str]) -> str:
    """Priority: production > staging > development."""
    for zone in ("production", "staging", "development"):
        if zone in ansible_groups:
            return zone
    return "development"


def _ssh_transport(
    host_cfg: dict, use_wg: bool,
) -> tuple[str, list[str]]:
    """Return (target_ip, ssh_opts) based on transport mode."""
    if use_wg:
        return host_cfg.get("wg_ip", ""), [
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
        ]
    hyp = host_cfg.get("hypervisor") or DEFAULT_HYPERVISOR
    return host_cfg.get("virbr0_ip", ""), [
        "-o", f"ProxyJump={hyp}",
        "-o", "StrictHostKeyChecking=no",
    ]


def _read_erp_user(project_root: str) -> str:
    gv = Path(project_root) / "ansible" / "group_vars" / "all.yml"
    with open(gv) as fh:
        return yaml.safe_load(fh).get("erp_user", "erpadm")
