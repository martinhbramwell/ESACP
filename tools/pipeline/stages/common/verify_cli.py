#!/usr/bin/env python3
"""Shared CLI helper for verify scripts.

Parses args, loads hosts_map.yml, derives SSH transport and common fields.
Each verify script's __main__ calls parse_verify_args() + print_results().
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from tools.pipeline.stages.common.config import _ssh_transport


@dataclass(frozen=True)
class VerifyContext:
    hostname: str
    host_cfg: dict
    project_root: str
    use_wg: bool
    target_ip: str
    ssh_opts: list[str]
    ssh_key: str
    hypervisor: str
    virbr0_ip: str
    wg_ip: str
    erp_user: str
    nickname: str
    bench_dir: str
    bench_dir_orig: str
    site_url: str
    domain: str


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

    hm = Path(proj) / "hosts_map.yml"
    with open(hm) as f:
        data = yaml.safe_load(f)
    host_cfg = data["groups"]["kvm"][hostname]

    target_ip, ssh_opts = _ssh_transport(host_cfg, use_wg)
    hypervisor = host_cfg.get("hypervisor") or "toshiba"
    ssh_key = str(Path.home() / ".ssh" / "hasan_mighty")

    gv = Path(proj) / "ansible" / "group_vars" / "all.yml"
    with open(gv) as f:
        gv_data = yaml.safe_load(f)
    erp_user = gv_data.get("erp_user", "erpadm")

    nickname = host_cfg.get("nickname", hostname[:4])
    groups = host_cfg.get("ansible_groups", [])
    if "production" in groups:
        domain = "logichem.solutions"
    else:
        domain = "iridium.blue"
    site_url = f"{hostname}.{domain}"

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
        site_url=site_url,
        domain=domain,
    )


def print_results(
    stage_label: str,
    hostname: str,
    results: list[tuple[bool, str]],
) -> None:
    """Print verification results table and exit 0/1."""
    print(f"\n── {stage_label} verification: {hostname} ──")
    passed = failed = 0
    for ok, msg in results:
        tag = "\u2705" if ok else "\u274c"
        print(f"  {tag}  {msg}")
        if ok:
            passed += 1
        else:
            failed += 1
    print(f"\n  {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
