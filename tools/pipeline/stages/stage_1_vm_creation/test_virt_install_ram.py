#!/usr/bin/env python3
"""Test: virt_install_import emits ``--ram 6144``.

Run directly: ``./tools/pipeline/stages/stage_1_vm_creation/test_virt_install_ram.py``
Exit 0 on pass, 1 on fail. No pytest dependency.

Regression guard for #308: dev VMs need 6 GiB to survive ERPNext build phases
(yarn / asset compilation OOM at 4 GiB on V14 ladder).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from tools.pipeline.stages.env_kvm import KvmEnv  # noqa: E402
from tools.pipeline.stages.stage_1_vm_creation import virt_install  # noqa: E402


def test_virt_install_emits_6144_mib_ram() -> bool:
    captured: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        captured.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    original = virt_install.subprocess.run
    virt_install.subprocess.run = fake_run
    try:
        virt_install.virt_install_import(
            hostname="dev03",
            remote_seed="/tmp/seed-dev03.iso",
            env=KvmEnv.from_project_root(REPO_ROOT),
            emit=lambda _msg: None,
        )
    finally:
        virt_install.subprocess.run = original

    if not captured:
        print("FAIL: subprocess.run was not invoked")
        return False
    ssh_argv = captured[0]
    if len(ssh_argv) < 3:
        print(f"FAIL: ssh argv malformed: {ssh_argv!r}")
        return False
    virt_cmd = ssh_argv[2]
    if "--ram 6144" not in virt_cmd:
        print(f"FAIL: expected '--ram 6144' in virt-install command, got:\n{virt_cmd}")
        return False
    if "--ram 4096" in virt_cmd:
        print(f"FAIL: stale '--ram 4096' still present:\n{virt_cmd}")
        return False
    print("PASS: virt-install command emits --ram 6144")
    return True


if __name__ == "__main__":
    sys.exit(0 if test_virt_install_emits_6144_mib_ram() else 1)
