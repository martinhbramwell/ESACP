#!/usr/bin/env python3
"""Colocated test for v16_post_migrate_fixups primitive (#498, #486, #617)."""

import sys
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.pipeline.orchestration.v16_post_migrate_fixups import (  # noqa: E402
    apply_v16_post_migrate_fixups,
)
from tools.pipeline.stages.common.types import Config  # noqa: E402

MOD = "tools.pipeline.orchestration.v16_post_migrate_fixups"
SSH = "tools.pipeline.orchestration.fix_script_runner.ssh_run"
EMIT = lambda _m: None  # noqa: E731
R1_CREATED = "  [OK] (was absent, now 1)\n  [PROBE] home=created\n"
R3_OK = "  [OK] (was 0, now 1)\n  [PROBE] disabled=1\n"
# R8 is a probe: a successful run ALWAYS advances the series (creates one draft
# invoice), so it always carries the changed_marker.
R8_OK = "  [OK] (series advanced)\n  [PROBE] naming_series=ok\n"


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


def _run(rsync=None, r1=None, r3=None, r8=None):
    r1 = r1 or _cp(stdout="  [PROBE] home=present\n")
    r3 = r3 or _cp(stdout="  [PROBE] disabled=1\n")
    r8 = r8 or _cp(stdout=R8_OK)
    with patch(f"{MOD}.rsync_to_vm", return_value=rsync or _cp()), \
         patch(SSH, side_effect=[r1, r3, r8]) as s:
        return apply_v16_post_migrate_fixups(_config(), EMIT), s


def test_all_three_run_and_set_changed():
    result, s = _run(r1=_cp(stdout=R1_CREATED), r3=_cp(stdout=R3_OK))
    assert result.success and result.changed
    assert "home=created" in result.message and "disabled=1" in result.message
    assert "naming_series=ok" in result.message
    cmds = [c.args[1] for c in s.call_args_list]
    assert all(x in cmds[0] for x in ("r1_recreate_web_page_home.py", "sudo -u erpadm", "/sites &&"))
    assert all(x in cmds[1] for x in ("r3_disable_irs_1099_pf.py", "sudo -u erpadm", "/sites &&"))
    assert all(x in cmds[2] for x in ("r8_naming_series_probe.py", "sudo -u erpadm", "/sites &&"))


def test_r1_r3_idempotent_but_r8_always_advances():
    # R1/R3 are no-ops here, but R8 advances the series on every success, so the
    # aggregate is always `changed` once R8 is in the loop. Documented behaviour.
    result, _ = _run()
    assert result.success and result.changed
    assert "naming_series=ok" in result.message


def test_r1_singleton_absent_path_reports_message():
    result, _ = _run(r1=_cp(stdout="  [PROBE] homepage=absent\n"),
                     r3=_cp(stdout="  [PROBE] disabled=absent\n"))
    assert result.success and "homepage=absent" in result.message


def test_rsync_failure_aborts_before_ssh():
    result, s = _run(rsync=_cp(rc=1, stderr="boom"))
    assert not result.success and "rsync" in result.message and s.call_count == 0


def test_r1_ssh_failure_short_circuits_rest():
    result, s = _run(r1=_cp(rc=1, stderr="boom"))
    assert not result.success and "R1" in result.message and s.call_count == 1


def test_r8_mismatch_fails_the_run():
    # A broken naming series => probe prints naming_series=mismatch (not in
    # R8_EXPECTED) => the whole fixups run fails, after R1+R3+R8 all ran.
    result, s = _run(r8=_cp(stdout="  [PROBE] naming_series=mismatch\n"))
    assert not result.success and "R8" in result.message and s.call_count == 3


if __name__ == "__main__":
    from tools.testkit import run_module_tests
    raise SystemExit(run_module_tests(globals()))
