"""Colocated test for v16_post_migrate_fixups primitive (#498)."""

from __future__ import annotations

from subprocess import CompletedProcess
from unittest.mock import patch

from tools.pipeline.orchestration.v16_post_migrate_fixups import (
    apply_v16_post_migrate_fixups,
)
from tools.pipeline.stages.common.types import Config

MOD = "tools.pipeline.orchestration.v16_post_migrate_fixups"
EMIT = lambda _m: None  # noqa: E731


def _config() -> Config:
    return Config(
        hostname="dev02", nickname="D2IRBL", zone="development", backend="kvm",
        target_ip="10.10.0.17", wg_ip="10.10.0.17", virbr0_ip="192.168.122.17",
        site_url="dev02.iridium.blue", domain="iridium.blue",
        erp_user="erpadm", erp_user_pwd="x", db_root_pwd="x",
        bench_dir="/home/erpadm/frappe-bench-D2IRBL",
        bench_dir_orig="/home/erpadm/frappe-bench",
        provision_mode="restored", hypervisor="toshiba",
        ssh_key="/dev/null", ssh_opts=[], project_root="/tmp/proj",
    )


def _cp(rc=0, stdout="", stderr=""):
    return CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr=stderr)


def _run(rsync=_cp(), ssh=_cp()):
    with patch(f"{MOD}.rsync_to_vm", return_value=rsync), \
         patch(f"{MOD}.ssh_run", return_value=ssh) as s:
        return apply_v16_post_migrate_fixups(_config(), EMIT), s


def test_first_apply_sets_changed_true():
    out = "  [OK] disabled (was 0, now 1)\n  [PROBE] disabled=1\n"
    result, s = _run(ssh=_cp(stdout=out))
    assert result.success and result.changed and "disabled=1" in result.message
    cmd = s.call_args.args[1]
    assert "r3_disable_irs_1099_pf.py" in cmd
    assert "--bench-dir /home/erpadm/frappe-bench-D2IRBL" in cmd
    assert "--site dev02.iridium.blue" in cmd


def test_already_disabled_is_no_op():
    out = "  [OK] already disabled\n  [PROBE] disabled=1\n"
    result, _ = _run(ssh=_cp(stdout=out))
    assert result.success and not result.changed


def test_record_absent_is_no_op():
    out = "  [SKIP] not present\n  [PROBE] disabled=absent\n"
    result, _ = _run(ssh=_cp(stdout=out))
    assert result.success and not result.changed
    assert "disabled=absent" in result.message


def test_rsync_failure_aborts_before_ssh():
    result, s = _run(rsync=_cp(rc=1, stderr="boom"))
    assert not result.success and "rsync" in result.message and s.call_count == 0


def test_r3_ssh_failure_returns_fail():
    result, _ = _run(ssh=_cp(rc=1, stderr="mysql exploded"))
    assert not result.success and "R3" in result.message


def test_unexpected_probe_returns_fail():
    out = "  [PROBE] disabled=garbage\n"
    result, _ = _run(ssh=_cp(stdout=out))
    assert not result.success and "probe unexpected" in result.message
