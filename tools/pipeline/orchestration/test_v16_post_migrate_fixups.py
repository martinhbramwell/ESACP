"""Colocated test for v16_post_migrate_fixups primitive (#498, #486)."""

from subprocess import CompletedProcess
from unittest.mock import patch

from tools.pipeline.orchestration.v16_post_migrate_fixups import (
    apply_v16_post_migrate_fixups,
)
from tools.pipeline.stages.common.types import Config

MOD = "tools.pipeline.orchestration.v16_post_migrate_fixups"
SSH = "tools.pipeline.orchestration.fix_script_runner.ssh_run"
EMIT = lambda _m: None  # noqa: E731
R1_CREATED = "  [OK] (was absent, now 1)\n  [PROBE] home=created\n"
R3_OK = "  [OK] (was 0, now 1)\n  [PROBE] disabled=1\n"


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


def _run(rsync=None, r1=None, r3=None):
    r1 = r1 or _cp(stdout="  [PROBE] home=present\n")
    r3 = r3 or _cp(stdout="  [PROBE] disabled=1\n")
    with patch(f"{MOD}.rsync_to_vm", return_value=rsync or _cp()), \
         patch(SSH, side_effect=[r1, r3]) as s:
        return apply_v16_post_migrate_fixups(_config(), EMIT), s


def test_both_fresh_apply_sets_changed():
    result, s = _run(r1=_cp(stdout=R1_CREATED), r3=_cp(stdout=R3_OK))
    assert result.success and result.changed
    assert "home=created" in result.message and "disabled=1" in result.message
    cmds = [c.args[1] for c in s.call_args_list]
    assert all(s in cmds[0] for s in ("r1_recreate_web_page_home.py", "sudo -u erpadm", "/sites &&"))
    assert all(s in cmds[1] for s in ("r3_disable_irs_1099_pf.py", "sudo -u erpadm", "/sites &&"))


def test_both_idempotent_skip_no_change():
    result, _ = _run()
    assert result.success and not result.changed


def test_r1_singleton_absent_is_no_op():
    result, _ = _run(r1=_cp(stdout="  [PROBE] homepage=absent\n"),
                     r3=_cp(stdout="  [PROBE] disabled=absent\n"))
    assert result.success and not result.changed
    assert "homepage=absent" in result.message


def test_rsync_failure_aborts_before_ssh():
    result, s = _run(rsync=_cp(rc=1, stderr="boom"))
    assert not result.success and "rsync" in result.message and s.call_count == 0


def test_r1_ssh_failure_short_circuits_r3():
    result, s = _run(r1=_cp(rc=1, stderr="boom"))
    assert not result.success and "R1" in result.message and s.call_count == 1
