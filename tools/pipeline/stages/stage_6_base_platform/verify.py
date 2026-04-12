#!/usr/bin/env python3
"""Verify Stage 6 (Base Platform) postconditions.

Six checks covering sections A–C + B2b:
  1. /opt/ce_sri/envars.sh deployed
  2. Bench symlink present
  3. Deploy keys in ~erpadm/.ssh/
  4. At least one app cloned (ce_sri in apps/)
  5. Supervisor running bench processes
  6. BaRe/envars.sh symlink present
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


def check_envars_deployed(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """Section A: /opt/ce_sri/envars.sh exists."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                "test -f /opt/ce_sri/envars.sh && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "/opt/ce_sri/envars.sh deployed"
    return False, "/opt/ce_sri/envars.sh not found"


def check_bench_symlink(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str,
) -> tuple[bool, str]:
    """Section A2: bench dir symlink exists."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -L {bench_dir} && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, f"Bench symlink {bench_dir} present"
    return False, f"Bench symlink {bench_dir} not found"


def check_deploy_keys(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    erp_user: str,
) -> tuple[bool, str]:
    """Sections A2c + A2e: deploy keys and SSH config present."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"sudo test -f /home/{erp_user}/.ssh/you_gh_ce_sri"
        f" && sudo test -f /home/{erp_user}/.ssh/config"
        f" && sudo test -f /home/{erp_user}/.ssh/gh_askpass.sh"
        " && echo y",
    )
    if r.returncode == 0 and "y" in r.stdout:
        return True, "Deploy keys + SSH config present"
    return False, "Deploy keys or SSH config missing"


def check_app_cloned(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str,
) -> tuple[bool, str]:
    """Section A2d: at least ce_sri cloned in apps/."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -d {bench_dir}/apps/ce_sri/.git && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "ce_sri app cloned"
    return False, "ce_sri app not found in apps/"


def check_supervisor_running(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """Sections A3 + A3b: supervisor has running bench processes."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        "sudo supervisorctl status 2>/dev/null | grep -c RUNNING",
        timeout=20,
    )
    if r.returncode == 0:
        count = r.stdout.strip()
        if count.isdigit() and int(count) > 0:
            return True, f"Supervisor: {count} processes RUNNING"
    return False, "No supervisor processes running"


def check_bare_symlink(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str,
) -> tuple[bool, str]:
    """Section C: BaRe/envars.sh symlink to /opt/ce_sri/envars.sh."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"test -L {bench_dir}/BaRe/envars.sh && echo y",
    )
    if r.returncode == 0 and "y" in r.stdout:
        return True, "BaRe/envars.sh symlink present"
    return False, "BaRe/envars.sh symlink not found"


def verify_stage_6(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
    erp_user: str,
    bench_dir: str,
) -> list[tuple[bool, str]]:
    """Run all Stage 6 postcondition checks."""
    return [
        check_envars_deployed(target_ip, ssh_opts, ssh_key),
        check_bench_symlink(target_ip, ssh_opts, ssh_key, bench_dir),
        check_deploy_keys(target_ip, ssh_opts, ssh_key, erp_user),
        check_app_cloned(target_ip, ssh_opts, ssh_key, bench_dir),
        check_supervisor_running(target_ip, ssh_opts, ssh_key),
        check_bare_symlink(target_ip, ssh_opts, ssh_key, bench_dir),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


# ── CLI entry point ──────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hostname> [project_root]")
        sys.exit(2)

    host = sys.argv[1]
    proj = sys.argv[2] if len(sys.argv) > 2 else str(
        Path(__file__).resolve().parents[4])

    import yaml

    hm = Path(proj) / "hosts_map.yml"
    with open(hm) as f:
        data = yaml.safe_load(f)
    host_cfg = data["groups"]["kvm"][host]

    hypervisor = host_cfg.get("hypervisor", "toshiba")
    virbr0_ip = host_cfg["virbr0_ip"]
    ssh_key = str(Path.home() / ".ssh" / "hasan_mighty")
    ssh_opts = [
        "-o", f"ProxyJump={hypervisor}",
        "-o", "StrictHostKeyChecking=no",
    ]

    groups = host_cfg.get("ansible_groups", [])
    erp_user = "erpadm"
    nickname = host_cfg.get("nickname", host[:4])
    bench_dir = f"/home/{erp_user}/frappe-bench-{nickname}"

    results = verify_stage_6(
        target_ip=virbr0_ip,
        ssh_opts=ssh_opts,
        ssh_key=ssh_key,
        erp_user=erp_user,
        bench_dir=bench_dir,
    )

    print(f"\n── Stage 6 verification: {host} ──")
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
