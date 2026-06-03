#!/usr/bin/env python3
"""CLI arg parsing → VerifyContext for the per-stage verify scripts."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from tools.host_identity import DEFAULT_HYPERVISOR, ZONE_DOMAINS, operator_ssh_key
from tools.pipeline.stages.common.config_helpers import (
    _derive_zone,
    _read_erp_user,
    _ssh_transport,
)
from tools.pipeline.stages.common.verify_context import VerifyContext


def parse_verify_args() -> VerifyContext:
    """Parse CLI args and return a VerifyContext with all derived fields.

    Usage: <script> <hostname> [project_root] [--wg]
    """
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    use_wg = "--wg" in flags

    if len(args) < 1:
        print(f"Usage: {sys.argv[0]} <hostname> [project_root] [--wg]")
        sys.exit(2)

    hostname = args[0]
    proj = args[1] if len(args) > 1 else str(
        Path(__file__).resolve().parents[4])

    with open(Path(proj) / "hosts_map.yml") as f:
        host_cfg = yaml.safe_load(f)["groups"]["kvm"][hostname]

    target_ip, ssh_opts = _ssh_transport(host_cfg, use_wg)
    hypervisor = host_cfg.get("hypervisor") or DEFAULT_HYPERVISOR
    ssh_key = operator_ssh_key()
    erp_user = _read_erp_user(proj)
    nickname = host_cfg.get("nickname", hostname[:4])
    domain = ZONE_DOMAINS[_derive_zone(host_cfg.get("ansible_groups", []))]

    return VerifyContext(
        hostname=hostname,
        host_cfg=host_cfg,
        project_root=proj,
        use_wg=use_wg,
        target_ip=target_ip,
        ssh_opts=ssh_opts,
        ssh_key=ssh_key,
        hypervisor=hypervisor,
        virbr0_ip=host_cfg.get("virbr0_ip", ""),
        wg_ip=host_cfg.get("wg_ip", ""),
        erp_user=erp_user,
        nickname=nickname,
        bench_dir=f"/home/{erp_user}/frappe-bench-{nickname}",
        bench_dir_orig=f"/home/{erp_user}/frappe-bench",
        site_url=f"{hostname}.{domain}",
        domain=domain,
    )
