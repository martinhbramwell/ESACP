#!/usr/bin/env python3
"""Verify Stage 7 (Data Restoration) postconditions.

Five checks covering sections D–G2:
  1. currentsite.txt exists and contains site_url
  2. Site responds to bench doctor
  3. ddlViews.sql in site private/files
  4. erpnext app installed (apps.txt)
  5. Database restored (tabSales Invoice has rows)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.host_identity import GUEST_VM_USER


def _ssh_vm(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    cmd: str, timeout: int = 15,
):
    return subprocess.run(
        ["ssh", *ssh_opts, "-i", ssh_key, f"{GUEST_VM_USER}@{target_ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def check_currentsite(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Section D1: currentsite.txt exists and contains site_url."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"cat {bench_dir}/sites/currentsite.txt 2>/dev/null",
    )
    if r.returncode == 0 and site_url in r.stdout.strip():
        return True, f"currentsite.txt contains {site_url}"
    return False, "currentsite.txt missing or wrong content"


def check_bench_doctor(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    erp_user: str, bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Section D: site responds to bench doctor."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"sudo -u {erp_user} bash -c 'cd {bench_dir} && bench --site {site_url} doctor'",
        timeout=30,
    )
    if r.returncode == 0:
        return True, f"bench doctor OK for {site_url}"
    return False, f"bench doctor failed for {site_url}"


def check_ddl_views(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Section E: ddlViews.sql in site private/files."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"test -f {bench_dir}/sites/{site_url}/private/files/ddlViews.sql && echo y",
    )
    if r.returncode == 0 and "y" in r.stdout:
        return True, "ddlViews.sql present in private/files"
    return False, "ddlViews.sql not found in private/files"


def check_erpnext_installed(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str,
) -> tuple[bool, str]:
    """Section D: erpnext listed in apps.txt."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"grep -q erpnext {bench_dir}/sites/apps.txt && echo y",
    )
    if r.returncode == 0 and "y" in r.stdout:
        return True, "erpnext installed (in apps.txt)"
    return False, "erpnext not found in apps.txt"


def check_db_restored(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    erp_user: str, bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Section G: production data present (tabSales Invoice has rows).

    Reads DB credentials from site_config.json and queries mysql directly
    (bench mariadb does not accept -e).
    """
    cmd = (
        f"python3 -c \""
        f"import json, subprocess, sys; "
        f"c = json.load(open('{bench_dir}/sites/{site_url}/site_config.json')); "
        f"r = subprocess.run("
        f"['mysql', '-AD', c['db_name'], '-u' + c['db_name'], '-p' + c.get('db_password',''), "
        f"'-e', 'SELECT COUNT(*) FROM \\`tabSales Invoice\\`', '--skip-column-names'], "
        f"capture_output=True, text=True); "
        f"print(r.stdout.strip()) if r.returncode == 0 else sys.exit(1)\""
    )
    r = _ssh_vm(target_ip, ssh_opts, ssh_key, cmd, timeout=30)
    if r.returncode == 0:
        count = r.stdout.strip()
        if count.isdigit() and int(count) > 0:
            return True, f"DB restored ({count} Sales Invoices)"
    return False, "DB not restored (no Sales Invoice rows)"


def verify_stage_7(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
    erp_user: str,
    bench_dir: str,
    site_url: str,
) -> list[tuple[bool, str]]:
    """Run all Stage 7 postcondition checks."""
    return [
        check_currentsite(target_ip, ssh_opts, ssh_key, bench_dir, site_url),
        check_bench_doctor(target_ip, ssh_opts, ssh_key, erp_user, bench_dir, site_url),
        check_ddl_views(target_ip, ssh_opts, ssh_key, bench_dir, site_url),
        check_erpnext_installed(target_ip, ssh_opts, ssh_key, bench_dir),
        check_db_restored(target_ip, ssh_opts, ssh_key, erp_user, bench_dir, site_url),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


# ── CLI entry point ──────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hostname> [project_root]")
        sys.exit(2)

    from tools.pipeline.stages.common.verify_cli import (
        parse_verify_args,
        print_results,
    )

    ctx = parse_verify_args()
    results = verify_stage_7(
        target_ip=ctx.target_ip,
        ssh_opts=ctx.ssh_opts,
        ssh_key=ctx.ssh_key,
        erp_user=ctx.erp_user,
        bench_dir=ctx.bench_dir,
        site_url=ctx.site_url,
    )
    print_results("Stage 7", ctx.hostname, results)
