#!/usr/bin/env python3
"""Verify Stage 4 (Content Delivery) postconditions.

Each check returns (pass, description).  Importable for use as a pre-stage
idempotency gate: if all pass, Stage 4 can be skipped entirely.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _ssh_vm(target_ip: str, ssh_opts: list[str], ssh_key: str,
            cmd: str, timeout: int = 15):
    return subprocess.run(
        ["ssh", *ssh_opts, "-i", ssh_key, f"you@{target_ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def check_rendered_bundle(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """Rendered config bundle present on VM at /tmp/rendered/."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                "test -f /tmp/rendered/envars.sh"
                " && test -f /tmp/rendered/params.json"
                " && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "Rendered config bundle present"
    return False, "Rendered config bundle not found on VM"


def check_vm_scripts(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """vm_scripts directory present on VM."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                "test -d /tmp/vm_scripts && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "vm_scripts present"
    return False, "vm_scripts not found on VM"


def check_renderers(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """Renderers directory present on VM."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                "test -d /tmp/renderers && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "Renderers present"
    return False, "Renderers not found on VM"


def check_templates(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """Templates directory present on VM."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                "test -d /tmp/templates && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "Templates present"
    return False, "Templates not found on VM"


def check_install_specific(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """install_specific.py present on VM."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                "test -f /tmp/install_specific.py && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "install_specific.py present"
    return False, "install_specific.py not found on VM"


def verify_stage_4(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
) -> list[tuple[bool, str]]:
    """Run all Stage 4 postcondition checks.  Returns list of (pass, msg)."""
    return [
        check_rendered_bundle(target_ip, ssh_opts, ssh_key),
        check_vm_scripts(target_ip, ssh_opts, ssh_key),
        check_renderers(target_ip, ssh_opts, ssh_key),
        check_templates(target_ip, ssh_opts, ssh_key),
        check_install_specific(target_ip, ssh_opts, ssh_key),
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
    results = verify_stage_4(
        target_ip=ctx.target_ip,
        ssh_opts=ctx.ssh_opts,
        ssh_key=ctx.ssh_key,
    )
    print_results("Stage 4", ctx.hostname, results)
