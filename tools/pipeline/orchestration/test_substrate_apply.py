"""Colocated test for substrate_apply primitive (#418)."""

from __future__ import annotations

from dataclasses import replace
from subprocess import CompletedProcess
from unittest.mock import patch

from tools.pipeline.orchestration.substrate_apply import apply_substrate_migration
from tools.pipeline.stages.common.types import Config


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


def _ok(stdout: str = "ok") -> CompletedProcess:
    return CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def _fail(stderr: str = "boom", code: int = 1) -> CompletedProcess:
    return CompletedProcess(args=[], returncode=code, stdout="", stderr=stderr)


def test_happy_path_runs_all_four_steps():
    config = _config()
    emitted: list[str] = []
    with patch("tools.pipeline.orchestration.substrate_apply.rsync_to_vm", return_value=_ok()) as r, \
         patch("tools.pipeline.orchestration.substrate_apply.ssh_run", return_value=_ok()) as s:
        result = apply_substrate_migration(config, emitted.append)
    assert result.success and result.changed
    assert r.call_count == 1
    assert s.call_count == 3  # g1, g2, bench migrate
    cmds = [c.args[1] for c in s.call_args_list]
    assert "g1_seed_patch_log.py" in cmds[0]
    assert "g2_clear_fixture_custom_fields.py" in cmds[1]
    assert "bench --site dev02.iridium.blue migrate" in cmds[2]
    assert f"sudo -u {config.erp_user}" in cmds[2]


def test_rsync_failure_aborts_before_ssh():
    config = _config()
    emitted: list[str] = []
    with patch("tools.pipeline.orchestration.substrate_apply.rsync_to_vm", return_value=_fail()) as r, \
         patch("tools.pipeline.orchestration.substrate_apply.ssh_run") as s:
        result = apply_substrate_migration(config, emitted.append)
    assert not result.success
    assert "rsync" in result.message
    assert r.call_count == 1 and s.call_count == 0


def test_g2_failure_aborts_before_migrate():
    config = _config()
    emitted: list[str] = []
    responses = [_ok(), _fail("g2 boom")]
    with patch("tools.pipeline.orchestration.substrate_apply.rsync_to_vm", return_value=_ok()), \
         patch("tools.pipeline.orchestration.substrate_apply.ssh_run", side_effect=responses) as s:
        result = apply_substrate_migration(config, emitted.append)
    assert not result.success
    assert "g2" in result.message
    assert s.call_count == 2  # g1 ran, g2 failed, migrate did NOT run


def test_uses_bench_dir_not_bench_dir_orig():
    config = replace(_config(), bench_dir="/home/erpadm/frappe-bench-D2IRBL")
    emitted: list[str] = []
    with patch("tools.pipeline.orchestration.substrate_apply.rsync_to_vm", return_value=_ok()), \
         patch("tools.pipeline.orchestration.substrate_apply.ssh_run", return_value=_ok()) as s:
        apply_substrate_migration(config, emitted.append)
    for call in s.call_args_list:
        assert "/home/erpadm/frappe-bench-D2IRBL" in call.args[1]
