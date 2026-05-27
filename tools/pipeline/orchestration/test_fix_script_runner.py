"""Colocated test for fix_script_runner protocol (#486)."""

from subprocess import CompletedProcess
from unittest.mock import patch

from tools.pipeline.orchestration.fix_script_runner import run_fix_script
from tools.pipeline.stages.common.types import Config

SSH = "tools.pipeline.orchestration.fix_script_runner.ssh_run"
EMIT = lambda _m: None  # noqa: E731
EXPECTED = {"foo=1", "foo=absent"}
MARKER = "(was 0, now 1)"


def _config() -> Config:
    return Config(
        hostname="dev02", nickname="D2IRBL", zone="development", backend="kvm",
        target_ip="10.10.0.17", wg_ip="10.10.0.17", virbr0_ip="192.168.122.17",
        site_url="dev02.iridium.blue", domain="iridium.blue", erp_user="erpadm",
        erp_user_pwd="x", db_root_pwd="x", provision_mode="restored",
        bench_dir="/home/erpadm/frappe-bench-D2IRBL",
        bench_dir_orig="/home/erpadm/frappe-bench", hypervisor="toshiba",
        ssh_key="/dev/null", ssh_opts=[], project_root="/tmp/proj",
    )


def _cp(rc=0, stdout="", stderr=""):
    return CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr=stderr)


def _run(cp):
    with patch(SSH, return_value=cp):
        return run_fix_script(_config(), EMIT, "X", "cmd", EXPECTED, MARKER)


def test_changed_marker_detected():
    out = "  [OK] (was 0, now 1)\n  [PROBE] foo=1\n"
    result = _run(_cp(stdout=out))
    assert result.success and result.changed and "foo=1" in result.message


def test_no_change_marker_means_changed_false():
    result = _run(_cp(stdout="  [PROBE] foo=1\n"))
    assert result.success and not result.changed


def test_absent_probe_succeeds_unchanged():
    result = _run(_cp(stdout="  [PROBE] foo=absent\n"))
    assert result.success and not result.changed


def test_unexpected_probe_fails():
    result = _run(_cp(stdout="  [PROBE] foo=garbage\n"))
    assert not result.success and "probe unexpected" in result.message


def test_ssh_failure_emits_tails():
    emitted = []
    with patch(SSH, return_value=_cp(rc=1, stdout="STDO", stderr="STDE")):
        r = run_fix_script(_config(), emitted.append, "X", "cmd", EXPECTED, MARKER)
    assert not r.success and "X" in r.message
    assert any("STDO" in line for line in emitted)
    assert any("STDE" in line for line in emitted)
