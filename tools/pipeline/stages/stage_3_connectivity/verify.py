#!/usr/bin/env python3
"""Verify Stage 3 (Connectivity) postconditions.

Each check returns (pass, description).  Importable for use as a pre-stage
idempotency gate: if all pass, Stage 3 can be skipped entirely.
"""

from __future__ import annotations

import subprocess
import sys

from tools.host_identity import operator_pubkey


def _ssh_vm(target_ip: str, ssh_opts: list[str], ssh_key: str,
            cmd: str, timeout: int = 15):
    return subprocess.run(
        ["ssh", *ssh_opts, "-i", ssh_key, f"you@{target_ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def check_deploy_keys(
    target_ip: str, ssh_opts: list[str], ssh_key: str, erp_user: str,
) -> tuple[bool, str]:
    """Deploy keys present on VM (final or staging location)."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -f /home/{erp_user}/.ssh/you_gh_ce_sri && echo final"
                " || (test -f /tmp/you_gh_ce_sri && echo staged)")
    if "final" in r.stdout:
        return True, "Deploy keys installed"
    if "staged" in r.stdout:
        return True, "Deploy keys staged in /tmp/"
    return False, "Deploy keys not found on VM"


def check_controller_pubkey(
    target_ip: str, ssh_opts: list[str], ssh_key: str, erp_user: str,
) -> tuple[bool, str]:
    """Controller pubkey in erpadm authorized_keys (or staged in /tmp/)."""
    pubkey_path = operator_pubkey()
    if not pubkey_path.exists():
        return False, "Controller pubkey not found locally"
    key_blob = pubkey_path.read_text().strip().split()[1]
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"grep -qF '{key_blob}' "
                f"/home/{erp_user}/.ssh/authorized_keys 2>/dev/null "
                "&& echo installed"
                f" || (test -f /tmp/{pubkey_path.name} && echo staged)")
    if "installed" in r.stdout:
        return True, "Controller pubkey in authorized_keys"
    if "staged" in r.stdout:
        return True, "Controller pubkey staged in /tmp/"
    return False, "Controller pubkey not on VM"


def check_cesri_secrets(
    target_ip: str, ssh_opts: list[str], ssh_key: str, erp_user: str,
) -> tuple[bool, str]:
    """ce_sri parms JSON present on VM (final or staging location)."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -f /home/{erp_user}/.ssh/secrets/ce_sri_parms.json"
                " && echo final"
                " || (ls /tmp/ce_sri_parms_*.json 2>/dev/null && echo staged)")
    if "final" in r.stdout:
        return True, "ce_sri secrets installed"
    if "staged" in r.stdout:
        return True, "ce_sri secrets staged in /tmp/"
    return False, "ce_sri secrets not found on VM"


def check_backup(
    target_ip: str, ssh_opts: list[str], ssh_key: str, bench_dir_orig: str,
) -> tuple[bool, str]:
    """Database backup present on VM."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"sudo test -f {bench_dir_orig}/BKP/BACKUP.txt && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "Database backup present"
    return False, "Database backup not found on VM"


def check_ddl_views(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """ddlViews.sql present on VM."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                "test -f /tmp/ddlViews.sql && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "ddlViews.sql present"
    return False, "ddlViews.sql not found on VM"


def verify_stage_3(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
    erp_user: str,
    bench_dir_orig: str,
) -> list[tuple[bool, str]]:
    """Run all Stage 3 postcondition checks.  Returns list of (pass, msg)."""
    return [
        check_deploy_keys(target_ip, ssh_opts, ssh_key, erp_user),
        check_controller_pubkey(target_ip, ssh_opts, ssh_key, erp_user),
        check_cesri_secrets(target_ip, ssh_opts, ssh_key, erp_user),
        check_backup(target_ip, ssh_opts, ssh_key, bench_dir_orig),
        check_ddl_views(target_ip, ssh_opts, ssh_key),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


# ── CLI entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hostname> [project_root]")
        sys.exit(2)

    from tools.pipeline.stages.common.verify_cli import (
        parse_verify_args,
        print_results,
    )

    ctx = parse_verify_args()
    results = verify_stage_3(
        target_ip=ctx.target_ip,
        ssh_opts=ctx.ssh_opts,
        ssh_key=ctx.ssh_key,
        erp_user=ctx.erp_user,
        bench_dir_orig=ctx.bench_dir_orig,
    )
    print_results("Stage 3", ctx.hostname, results)
