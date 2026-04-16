"""CLI: run Ansible provisioning for a VM (task names + changes only)."""

from __future__ import annotations

from pathlib import Path

from tools.cli._common import banner, console, kvm_hosts, ssh_key_path
from tools.pipeline.orchestration.ansible_provision import provision_vm


def run(args, config: dict) -> int:
    vm = args.vm
    vm_info = kvm_hosts(config).get(vm, {})
    hypervisor = vm_info.get("hypervisor") or None
    project_root = str(Path(__file__).resolve().parent.parent.parent)

    banner(f"Provision VM: {vm}")
    ok = provision_vm(
        vm, hypervisor, project_root, ssh_key_path(config),
        console.print, check=args.check,
        skip_fresh_snapshot=args.skip_fresh_snapshot,
    )
    if not ok:
        return 1

    console.print()
    console.print(f"[green]✅  {vm} provisioned.[/green]")
    return 0
