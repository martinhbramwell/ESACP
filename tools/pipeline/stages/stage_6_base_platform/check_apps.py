#!/usr/bin/env python3
"""Stage 6 app-clone and deploy-key checks (sections A2c/A2e/A2d)."""

from __future__ import annotations

from tools.pipeline.stages.stage_6_base_platform.check_ssh import ssh_vm


def check_deploy_keys(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    erp_user: str, provision_mode: str = "restored",
) -> tuple[bool, str]:
    """Sections A2c + A2e. Generic: no you_gh_* keys (absence)."""
    if provision_mode == "generic":
        r = ssh_vm(
            target_ip, ssh_opts, ssh_key,
            f"sudo bash -c 'ls /home/{erp_user}/.ssh/you_gh_* 2>/dev/null"
            " | wc -l'")
        count = r.stdout.strip() or "?"
        if r.returncode == 0 and count == "0":
            return True, "No you_gh_* keys (generic mode)"
        return False, f"Unexpected you_gh_* keys present (count={count})"
    r = ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"sudo test -f /home/{erp_user}/.ssh/you_gh_ce_sri"
        f" && sudo test -f /home/{erp_user}/.ssh/config"
        f" && sudo test -f /home/{erp_user}/.ssh/gh_askpass.sh && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "Deploy keys + SSH config present"
    return False, "Deploy keys or SSH config missing"


def check_app_cloned(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str, provision_mode: str = "restored",
) -> tuple[bool, str]:
    """Section A2d. Generic: BaRe clone + no bespoke apps + clean Procfile."""
    if provision_mode == "generic":
        r = ssh_vm(
            target_ip, ssh_opts, ssh_key,
            f"test -d {bench_dir}/BaRe/.git"
            f" && ! test -e {bench_dir}/apps/ce_sri"
            f" && ! test -e {bench_dir}/apps/route_planner"
            f" && ! test -e {bench_dir}/apps/returnable"
            f" && ! grep -q ce_sri {bench_dir}/Procfile 2>/dev/null"
            " && echo y")
        if r.returncode == 0 and "y" in r.stdout:
            return True, "BaRe cloned; no ce_sri/route_planner/returnable; Procfile clean"
        return False, "Generic-bench invariants violated"
    r = ssh_vm(target_ip, ssh_opts, ssh_key,
               f"test -d {bench_dir}/apps/ce_sri/.git && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "ce_sri app cloned"
    return False, "ce_sri app not found in apps/"
