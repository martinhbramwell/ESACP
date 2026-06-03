"""Shared helpers for upgrade_v14 unit tests — Config factory + ssh_run patch.

Per `feedback_tests_with_code.md`, kept colocated with the units. Underscore
prefix marks it as test infrastructure, not a stage."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.host_identity import operator_ssh_key  # noqa: E402


def make_config(**overrides):
    base = dict(
        hostname="dev01", nickname="dev01", zone="development", backend="kvm",
        target_ip="10.10.0.16", wg_ip="10.10.0.16", virbr0_ip="192.168.122.16",
        site_url="dev01.iridium.blue", domain="iridium.blue",
        erp_user="erpadm", erp_user_pwd="x", db_root_pwd="x",
        bench_dir="/home/erpadm/frappe-bench", bench_dir_orig="/home/erpadm/frappe-bench",
        provision_mode="restored", hypervisor="toshiba",
        ssh_key=operator_ssh_key(),
        ssh_opts=["-o", "StrictHostKeyChecking=no"],
        project_root=str(REPO_ROOT),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def patch_ssh(module, fake):
    original = module.ssh_run
    module.ssh_run = fake
    return original


def ok(stdout: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")
