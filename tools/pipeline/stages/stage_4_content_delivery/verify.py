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

    results = verify_stage_4(
        target_ip=virbr0_ip,
        ssh_opts=ssh_opts,
        ssh_key=ssh_key,
    )

    print(f"\n\u2500\u2500 Stage 4 verification: {host} \u2500\u2500")
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
