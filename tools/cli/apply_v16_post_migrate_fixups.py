"""CLI: apply V13->V16 post-migrate fixups on a lab VM (#480 umbrella).

Thin dispatcher: build Config from hosts_map, call the primitive, format
the result. Catalogue: R1 Web Page 'home' (#486); R3 IRS 1099 PF disable
(#498). R6e.2 (#496) + future #480 children plug into the same primitive.
"""

from __future__ import annotations

from tools.cli._common import banner, console, kvm_hosts, PROJECT_ROOT
from tools.pipeline.orchestration.v16_post_migrate_fixups import (
    apply_v16_post_migrate_fixups,
)
from tools.pipeline.stages.common.config import build_config


def add_subparser(sub) -> None:
    p = sub.add_parser(
        "applyV16PostMigrateFixups",
        help="Run V13->V16 post-migrate fix-scripts (R1+R3; extensible)",
    )
    p.add_argument("vm", help="Target VM (e.g. dev02)")


def run(args, config: dict) -> int:
    vm = args.vm
    host_cfg = kvm_hosts(config).get(vm) or {}
    if not host_cfg.get("wg_ip"):
        console.print(
            f"[red]No wg_ip for {vm} in hosts_map.yml — "
            "VM must be provisioned first.[/red]"
        )
        return 1

    banner(f"Apply V16 post-migrate fixups: {vm}")
    cfg = build_config(vm, host_cfg, str(PROJECT_ROOT), use_wg=True)
    result = apply_v16_post_migrate_fixups(cfg, console.print)

    if result.success:
        marker = "(changed)" if result.changed else "(no-op)"
        console.print(f"[green]OK  {result.message} {marker}[/green]")
        return 0
    console.print(f"[red]FAIL  {result.message}[/red]")
    return 1
