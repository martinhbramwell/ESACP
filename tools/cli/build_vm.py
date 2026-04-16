"""CLI: build seed ISO, create VM, wait for autoinstall."""

from __future__ import annotations

from pathlib import Path

from tools.cli._common import banner, console, kvm_hosts, ssh_key_path
from tools.pipeline.orchestration.build_vm import build_vm


def run(args, config: dict) -> int:
    vm = args.vm
    vm_info = kvm_hosts(config).get(vm, {})
    project_root = str(Path(__file__).resolve().parent.parent.parent)
    banner(f"Build VM: {vm}")

    try:
        build_vm(vm, vm_info, project_root, ssh_key_path(config), console.print)
    except RuntimeError as exc:
        console.print(f"[red]❌  {exc}[/red]")
        return 1

    console.print()
    console.print(f"[green]✅  {vm} is built and SSH-ready.[/green]")
    console.print(f"    Next: [cyan]./tools/esacp.py provisionVM {vm}[/cyan]")
    return 0
