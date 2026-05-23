"""CLI: apply a bespoke-app migration on a lab VM (#418).

Thin dispatcher: build Config from hosts_map, call the substrate_apply
primitive, format the result. Closes the bypass that caused LSKB#15 to
fail twice on dev02 in S54/S55. See ESACP#418.
"""

from __future__ import annotations

from tools.cli._common import banner, console, kvm_hosts, PROJECT_ROOT
from tools.pipeline.orchestration.substrate_apply import apply_substrate_migration
from tools.pipeline.stages.common.config import build_config


def add_subparser(sub) -> None:
    p = sub.add_parser(
        "applySubstrateMigration",
        help="Run g1+g2 protections then bench migrate on a lab VM",
    )
    p.add_argument("vm", help="Target VM (e.g. dev02)")


def run(args, config: dict) -> int:
    vm = args.vm
    host_cfg = kvm_hosts(config).get(vm) or {}
    if not host_cfg.get("wg_ip"):
        console.print(f"[red]No wg_ip for {vm} in hosts_map.yml — VM must be provisioned first.[/red]")
        return 1

    banner(f"Apply substrate migration: {vm}")
    cfg = build_config(vm, host_cfg, str(PROJECT_ROOT), use_wg=True)
    result = apply_substrate_migration(cfg, console.print)

    if result.success:
        console.print(f"[green]✅  {result.message}[/green]")
        return 0
    console.print(f"[red]❌  {result.message}[/red]")
    return 1
