"""CLI: full teardown of a VM (WG + VM + hosts_map + SOPS keys)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.cli._common import banner, confirm, console, kvm_hosts
from tools.pipeline.macro.destroy import run as run_destroy


def run(args, config: dict) -> int:
    hostname = args.vm
    banner(f"Destroy (full teardown): {hostname}")

    vm_info = kvm_hosts(config).get(hostname, {})
    if not vm_info:
        console.print(f"[red]'{hostname}' not found in hosts_map.yml[/red]")
        return 1
    if vm_info.get("wg_role") == "hub":
        console.print(f"[red]Cannot destroy hub node '{hostname}' — this would break the entire mesh[/red]")
        return 1

    console.print("[bold red]This permanently destroys the VM, all snapshots, WireGuard keys,[/bold red]")
    console.print("[bold red]and removes the host from all configuration files.[/bold red]")
    if not confirm(f"Destroy {hostname}?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return 0

    project_root = str(Path(__file__).resolve().parent.parent.parent)
    try:
        run_destroy(hostname, vm_info, project_root, console.print)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        console.print(f"[red]Destroy failed: {exc}[/red]")
        return 1

    console.print()
    console.print(f"[green]Destroy complete — {hostname} fully removed.[/green]")
    return 0
