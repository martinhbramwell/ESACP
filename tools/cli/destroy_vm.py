"""CLI: destroy a KVM VM on the local libvirt daemon (legacy, interactive)."""

from __future__ import annotations

from tools.cli._common import banner, confirm, console
from tools.pipeline.orchestration.local_vm_teardown import (
    destroy_local_vm, inspect_local_vm,
)


def run(args, config: dict) -> int:
    vm = args.vm
    banner(f"Destroy VM: {vm}")

    info = inspect_local_vm(vm)
    if not info.exists:
        console.print(f"[yellow]VM '{vm}' does not exist — nothing to do.[/yellow]")
        return 0

    console.print(f"  State     : [cyan]{info.state}[/cyan]")
    if info.snapshots:
        console.print(f"  Snapshots : [yellow]{len(info.snapshots)}[/yellow]")
        for s in info.snapshots:
            console.print(f"    [dim]• {s}[/dim]")
    for f in (info.disk, info.seed):
        if f is not None:
            size = f.stat().st_size // (1024 * 1024)
            console.print(f"  Disk      : [dim]{f}[/dim] ({size} MiB)")

    console.print()
    console.print("[bold red]This permanently destroys the VM, all snapshots, and all storage.[/bold red]")
    if not confirm(f"Destroy {vm}?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return 0

    try:
        destroy_local_vm(vm, info.state, console.print)
    except RuntimeError as exc:
        console.print(f"[red]❌  {exc}[/red]")
        return 1

    console.print(f"[green]✅  {vm} destroyed.[/green]")
    return 0
