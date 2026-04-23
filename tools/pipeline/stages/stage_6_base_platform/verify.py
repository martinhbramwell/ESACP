#!/usr/bin/env python3
"""Verify Stage 6 (Base Platform) postconditions.

Six checks covering sections A–C + B2b. Per-check logic lives in
``check_envars.py`` / ``check_apps.py`` / ``check_infra.py``; this
module is the orchestrator + CLI entry.

Behaviour diverges by ``provision_mode``:

  restore (default) — legacy bespoke bench layout:
    envars at /opt/ce_sri; ce_sri cloned in apps/; deploy keys present;
    BaRe/envars.sh -> /opt/ce_sri/envars.sh.

  generic — clean bench layout (#289):
    envars at /opt/generic; only BaRe cloned; no ce_sri/route_planner/
    returnable; Procfile clean; no you_gh_* keys;
    BaRe/envars.sh -> /opt/generic/envars.sh.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Direct ./verify.py invocation needs repo root on sys.path for absolute imports.
if __name__ == "__main__" and __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tools.pipeline.stages.stage_6_base_platform.check_apps import (
    check_app_cloned, check_deploy_keys,
)
from tools.pipeline.stages.stage_6_base_platform.check_envars import (
    check_bare_symlink, check_envars_deployed,
)
from tools.pipeline.stages.stage_6_base_platform.check_infra import (
    check_bench_symlink, check_supervisor_running,
)


def verify_stage_6(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
    erp_user: str,
    bench_dir: str,
    provision_mode: str = "restored",
) -> list[tuple[bool, str]]:
    """Run all Stage 6 postcondition checks for the given mode."""
    return [
        check_envars_deployed(target_ip, ssh_opts, ssh_key, provision_mode),
        check_bench_symlink(target_ip, ssh_opts, ssh_key, bench_dir),
        check_deploy_keys(target_ip, ssh_opts, ssh_key, erp_user,
                          provision_mode),
        check_app_cloned(target_ip, ssh_opts, ssh_key, bench_dir,
                         provision_mode),
        check_supervisor_running(target_ip, ssh_opts, ssh_key),
        check_bare_symlink(target_ip, ssh_opts, ssh_key, bench_dir,
                           provision_mode),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hostname> [project_root]"
              " [--wg] [--mode=generic|restored]")
        sys.exit(2)

    from tools.pipeline.stages.common.verify_cli import (
        parse_verify_args,
        print_results,
    )

    mode = next((a.split("=", 1)[1] for a in sys.argv[1:]
                 if a.startswith("--mode=")), "restored")
    ctx = parse_verify_args()
    results = verify_stage_6(
        target_ip=ctx.target_ip,
        ssh_opts=ctx.ssh_opts,
        ssh_key=ctx.ssh_key,
        erp_user=ctx.erp_user,
        bench_dir=ctx.bench_dir,
        provision_mode=mode,
    )
    print_results(f"Stage 6 ({mode})", ctx.hostname, results)
