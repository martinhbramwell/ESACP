#!/usr/bin/env python3
"""Colocated test for v16_post_migrate_fixups (#626, #498, #486, #617).

Covers the version-aware selection added for the staged upgrade leg: the V15
leg runs #626 + R3 + R8 (no R1); the default V16 path runs all four, with
#626 ordered before R8 (R8's invoice probe depends on server scripts enabled).
"""

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

C626_SET = "  [OK] server_script_enabled set (was absent, now 1)\n  [PROBE] server_scripts=enabled\n"
R3_OK = "  [OK] (was 0, now 1)\n  [PROBE] disabled=1\n"
# R8 is a probe: a successful run ALWAYS advances the series (creates one draft
# invoice), so it always carries the changed_marker.
R8_OK = "  [OK] (series advanced)\n  [PROBE] naming_series=ok\n"
R1_CREATED = "  [OK] (was absent, now 1)\n  [PROBE] home=created\n"


def _config() -> Config:
    return Config(
        hostname="dev01", nickname="D1IRBL", zone="development", backend="kvm",
        target_ip="10.10.0.11", wg_ip="10.10.0.11", virbr0_ip="192.168.122.11",
        site_url="dev01.iridium.blue", domain="iridium.blue", erp_user="erpadm",
        erp_user_pwd="x", db_root_pwd="x", provision_mode="restored",
        bench_dir="/home/erpadm/frappe-bench-D1IRBL",
        bench_dir_orig="/home/erpadm/frappe-bench", hypervisor="toshiba",
        ssh_key="/dev/null", ssh_opts=[], project_root="/tmp/proj",
    )


def _cp(rc=0, stdout="", stderr=""):
    return CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr=stderr)


def _run(target_version=16, rsync=None, c626=None, r3=None, r8=None, r1=None):
    """Drive the primitive with mocked ssh outputs in FIXUPS order."""
    c626 = c626 or _cp(stdout="  [PROBE] server_scripts=enabled\n")
    r3 = r3 or _cp(stdout="  [PROBE] disabled=1\n")
    r8 = r8 or _cp(stdout=R8_OK)
    r1 = r1 or _cp(stdout="  [PROBE] home=present\n")
    seq = [c626, r3, r8] + ([r1] if target_version >= 16 else [])
    with patch(f"{MOD}.rsync_to_vm", return_value=rsync or _cp()), \
         patch(SSH, side_effect=seq) as s:
        return apply_v16_post_migrate_fixups(_config(), EMIT, target_version), s


def test_v16_runs_all_four_in_dependency_order():
    result, s = _run(c626=_cp(stdout=C626_SET), r3=_cp(stdout=R3_OK),
                     r1=_cp(stdout=R1_CREATED))
    assert result.success and result.changed
    assert "v16" in result.message
    for probe in ("server_scripts=enabled", "disabled=1", "naming_series=ok", "home=created"):
        assert probe in result.message, f"{probe} missing from {result.message}"
    cmds = [c.args[1] for c in s.call_args_list]
    assert len(cmds) == 4
    assert "server_scripts_enable_626.py" in cmds[0]
    assert "r3_disable_irs_1099_pf.py" in cmds[1]
    assert "r8_naming_series_probe.py" in cmds[2]
    assert "r1_recreate_web_page_home.py" in cmds[3]
    # dependency contract: #626 runs strictly before R8
    assert cmds.index(next(c for c in cmds if "626" in c)) < \
           cmds.index(next(c for c in cmds if "r8_" in c))


def test_v15_leg_runs_only_626_r3_r8_no_r1():
    result, s = _run(target_version=15, c626=_cp(stdout=C626_SET), r3=_cp(stdout=R3_OK))
    assert result.success and result.changed
    assert "v15" in result.message
    assert "server_scripts=enabled" in result.message and "naming_series=ok" in result.message
    cmds = [c.args[1] for c in s.call_args_list]
    assert len(cmds) == 3
    assert not any("r1_recreate_web_page_home.py" in c for c in cmds)


def test_idempotent_but_r8_always_advances():
    # #626/R3/R1 no-ops here, but R8 advances the series on every success, so the
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


def test_626_ssh_failure_short_circuits_rest():
    result, s = _run(c626=_cp(rc=1, stderr="boom"))
    assert not result.success and "#626" in result.message and s.call_count == 1


def test_r8_mismatch_fails_the_run_on_v15_leg():
    # A broken naming series => probe prints naming_series=mismatch (not in
    # R8's expected) => the V15-leg run fails, after #626+R3+R8 all ran.
    result, s = _run(target_version=15, r8=_cp(stdout="  [PROBE] naming_series=mismatch\n"))
    assert not result.success and "R8" in result.message and s.call_count == 3


if __name__ == "__main__":
    from tools.testkit import run_module_tests
    raise SystemExit(run_module_tests(globals()))
