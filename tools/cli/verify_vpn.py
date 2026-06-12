"""CLI: verify WireGuard VPN mesh connectivity."""

from __future__ import annotations

from tools.cli._common import banner, console, kvm_hosts, ssh_key_path, vm_user
from tools.pipeline.orchestration.verify_vpn import verify_vpn


def run(args, config: dict) -> int:
    banner("Verify WireGuard VPN")
    all_ok = verify_vpn(
        hosts=kvm_hosts(config),
        vm_user=vm_user(config),
        ssh_key=ssh_key_path(),
        emit=console.print,
    )
    console.print()
    if all_ok:
        console.print("[green]✅  All WireGuard connectivity checks passed.[/green]")
    else:
        console.print("[red]❌  Some connectivity checks failed.[/red]")
    return 0 if all_ok else 1
