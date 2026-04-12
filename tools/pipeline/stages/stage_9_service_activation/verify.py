#!/usr/bin/env python3
"""Verify Stage 9 (Service Activation) postconditions.

Four checks covering sections H4a-sl, L0, L:
  1. HTTPS responding (Stage 5 + 9 together deliver working HTTPS)
  2. Social Login Key exists via API
  3. stop.py deployed to bench dir
  4. .bash_aliases rendered for erp_user
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _ssh_vm(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    cmd: str, timeout: int = 15,
):
    return subprocess.run(
        ["ssh", *ssh_opts, "-i", ssh_key, f"you@{target_ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def check_https(
    target_ip: str, ssh_opts: list[str], ssh_key: str, site_url: str,
) -> tuple[bool, str]:
    """HTTPS responds to /api/method/ping."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"curl -sf --insecure --max-time 5 https://{site_url}/api/method/ping"
                " >/dev/null && echo y",
                timeout=10)
    if r.returncode == 0 and "y" in r.stdout:
        return True, f"HTTPS responding at {site_url}"
    return False, f"HTTPS not responding at {site_url}"


def check_social_login(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    erp_user: str, bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Social Login Key 'google' exists (verified via DB, not API).

    Uses direct MySQL query because Frappe v13 /api/resource/ GETs are
    broken by missing apply_perm_level_on_api_calls field (#159).
    """
    cmd = (
        f"python3 -c \""
        f"import json, subprocess, sys; "
        f"c = json.load(open('{bench_dir}/sites/{site_url}/site_config.json')); "
        f"r = subprocess.run("
        f"['mysql', '-AD', c['db_name'], '-u' + c['db_name'], "
        f"'-p' + c.get('db_password',''), "
        f"'-e', 'SELECT name FROM \\`tabSocial Login Key\\` "
        f"WHERE name=\\\"google\\\"', '--skip-column-names'], "
        f"capture_output=True, text=True); "
        f"print(r.stdout.strip()) if r.returncode == 0 else sys.exit(1)\""
    )
    r = _ssh_vm(target_ip, ssh_opts, ssh_key, cmd, timeout=15)
    if r.returncode == 0 and "google" in r.stdout:
        return True, "Social Login Key 'google' present"
    return False, "Social Login Key 'google' not found"


def check_stop_py(
    target_ip: str, ssh_opts: list[str], ssh_key: str, bench_dir: str,
) -> tuple[bool, str]:
    """stop.py deployed to bench dir."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"sudo test -f {bench_dir}/stop.py && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "stop.py deployed"
    return False, "stop.py not found in bench dir"


def check_bash_aliases(
    target_ip: str, ssh_opts: list[str], ssh_key: str, erp_user: str,
) -> tuple[bool, str]:
    """.bash_aliases rendered for erp_user."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"sudo test -f /home/{erp_user}/.bash_aliases && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, f".bash_aliases present for {erp_user}"
    return False, f".bash_aliases not found for {erp_user}"


def verify_stage_9(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
    erp_user: str,
    bench_dir: str,
    site_url: str,
) -> list[tuple[bool, str]]:
    """Run all Stage 9 postcondition checks."""
    return [
        check_https(target_ip, ssh_opts, ssh_key, site_url),
        check_social_login(target_ip, ssh_opts, ssh_key, erp_user, bench_dir, site_url),
        check_stop_py(target_ip, ssh_opts, ssh_key, bench_dir),
        check_bash_aliases(target_ip, ssh_opts, ssh_key, erp_user),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


# ── CLI entry point ──────────────────────────────────────────────────
if __name__ == "__main__":
    from tools.pipeline.stages.common.verify_cli import (
        parse_verify_args,
        print_results,
    )

    ctx = parse_verify_args()
    results = verify_stage_9(
        target_ip=ctx.target_ip,
        ssh_opts=ctx.ssh_opts,
        ssh_key=ctx.ssh_key,
        erp_user=ctx.erp_user,
        bench_dir=ctx.bench_dir,
        site_url=ctx.site_url,
    )
    print_results("Stage 9", ctx.hostname, results)
