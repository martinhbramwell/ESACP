"""Build a frozen Config from hosts_map.yml host entry."""

from __future__ import annotations

from pathlib import Path

from tools.host_identity import ZONE_DOMAINS
from tools.pipeline.stages.common.config_helpers import (
    _derive_zone,
    _read_erp_user,
    _ssh_transport,
)
from tools.pipeline.stages.common.types import Config
from tools.secrets import load_build_secrets


def build_config(
    hostname: str,
    host_cfg: dict,
    project_root: str,
    *,
    use_wg: bool = False,
    provision_mode: str = "restored",
    force_refresh: bool = False,
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
        force_refresh=force_refresh,
    )
