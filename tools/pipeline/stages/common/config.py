"""Build a frozen Config from hosts_map.yml host entry."""

from __future__ import annotations

from pathlib import Path

import yaml

from tools.host_identity import DEFAULT_HYPERVISOR, ZONE_DOMAINS
from tools.pipeline.stages.common.types import Config
from tools.secrets import load_build_secrets


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


def build_config(
    hostname: str,
    host_cfg: dict,
    project_root: str,
    *,
    use_wg: bool = False,
    provision_mode: str = "restored",
) -> Config:
    """Construct an immutable Config for a pipeline run.

    *use_wg=False* (provision): target via virbr0_ip + ProxyJump.
    *use_wg=True*  (refresh):  target via wg_ip, direct SSH.
    """
    groups = host_cfg.get("ansible_groups", [])
    zone = _derive_zone(groups)
    domain = ZONE_DOMAINS[zone]
    nickname = host_cfg.get("nickname", hostname[:4])
    erp_user = _read_erp_user(project_root)
    target_ip, ssh_opts = _ssh_transport(host_cfg, use_wg)
    secrets = load_build_secrets(project_root)

    return Config(
        hostname=hostname,
        nickname=nickname,
        zone=zone,
        backend=host_cfg.get("backend", "kvm"),
        target_ip=target_ip,
        wg_ip=host_cfg.get("wg_ip", ""),
        virbr0_ip=host_cfg.get("virbr0_ip", ""),
        site_url=f"{hostname}.{domain}",
        domain=domain,
        erp_user=erp_user,
        erp_user_pwd=secrets["erp_user_pwd"],
        db_root_pwd=secrets["db_root_pwd"],
        bench_dir=f"/home/{erp_user}/frappe-bench-{nickname}",
        bench_dir_orig=f"/home/{erp_user}/frappe-bench",
        provision_mode=provision_mode,
        hypervisor=host_cfg.get("hypervisor"),
        ssh_key=str(Path.home() / ".ssh" / "hasan_mighty"),
        ssh_opts=ssh_opts,
        project_root=project_root,
    )
