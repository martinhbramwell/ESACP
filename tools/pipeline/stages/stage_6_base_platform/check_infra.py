#!/usr/bin/env python3
"""Stage 6 infrastructure checks (bench symlink, supervisor)."""

from __future__ import annotations

from tools.pipeline.stages.stage_6_base_platform.check_ssh import ssh_vm


def check_bench_symlink(
    target_ip: str, ssh_opts: list[str], ssh_key: str, bench_dir: str,
) -> tuple[bool, str]:
    """Section A2: bench dir symlink exists."""
    r = ssh_vm(target_ip, ssh_opts, ssh_key,
               f"test -L {bench_dir} && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, f"Bench symlink {bench_dir} present"
    return False, f"Bench symlink {bench_dir} not found"


def check_supervisor_running(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """Sections A3 + A3b: supervisor has running bench processes."""
    r = ssh_vm(target_ip, ssh_opts, ssh_key,
               "sudo supervisorctl status 2>/dev/null | grep -c RUNNING",
               timeout=20)
    if r.returncode == 0:
        count = r.stdout.strip()
        if count.isdigit() and int(count) > 0:
            return True, f"Supervisor: {count} processes RUNNING"
    return False, "No supervisor processes running"
