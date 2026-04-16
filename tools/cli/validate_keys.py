"""CLI: verify SOPS/age keys and WireGuard key structure."""

from __future__ import annotations

from pathlib import Path

from tools.cli._common import banner, console, hub_vm, kvm_hosts
from tools.pipeline.stages.preflight.check_keys import check_keys


def run(args, config: dict) -> int:
    banner("Validate Keys")
    project_root = str(Path(__file__).resolve().parent.parent.parent)
    expected = list(kvm_hosts(config).keys()) + ["controller"]
    result = check_keys(
        project_root=project_root,
        expected_hosts=expected,
        hub_name=hub_vm(config),
        emit=console.print,
    )
    console.print()
    if result.success:
        console.print("[green]✅  All WireGuard keys present and decryptable.[/green]")
        return 0
    console.print(f"[red]❌  {result.message} — re-run config/wireguard/generate_keys.sh[/red]")
    return 1
