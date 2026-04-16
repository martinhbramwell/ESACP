"""Orchestrate Ansible provisioning for a VM.

Runs the provisionVM flow: SSH reachability check, pre-provision snapshot,
``ansible-playbook site-kvm.yml``, post-provision snapshot.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.orchestration.ansible_playbook_run import run_playbook
from tools.pipeline.orchestration.hypervisor_helpers import ansible_ping
from tools.pipeline.orchestration.snapshot_ops import (
    create_snapshot, list_snapshots,
)
from tools.pipeline.stages.common.types import Emit


def provision_vm(
    vm: str, hypervisor: str | None, project_root: str, ssh_key: str,
    emit: Emit, check: bool = False, skip_fresh_snapshot: bool = False,
) -> bool:
    """Run the full provisionVM flow. Returns True on success."""
    ansible_dir = Path(project_root) / "ansible"

    emit("[bold]Step 1/4:[/bold] Verify SSH reachable")
    if not ansible_ping(vm, project_root, ssh_key):
        emit(f"[red]❌  Cannot reach {vm} via SSH.[/red]")
        return False
    emit("  [green]✓[/green] SSH reachable")

    emit("")
    emit("[bold]Step 2/4:[/bold] Fresh Install snapshot")
    existing = list_snapshots(vm, hypervisor)
    if skip_fresh_snapshot or "Fresh Install" in existing:
        emit("  [dim]Skipping (already exists or --skip-fresh-snapshot)[/dim]")
    else:
        create_snapshot(vm, "Fresh Install", emit, hypervisor=hypervisor)

    emit("")
    emit("[bold]Step 3/4:[/bold] Ansible provisioning [dim](task names and changes only)[/dim]")
    emit("")
    if not run_playbook(vm, ansible_dir, ssh_key, emit, check=check):
        return False

    emit("")
    emit("  [green]✓[/green] Ansible complete")

    emit("")
    emit("[bold]Step 4/4:[/bold] Baseline snapshot")
    if check:
        emit("  [dim]Skipping (check mode)[/dim]")
    else:
        create_snapshot(vm, "Baseline", emit, hypervisor=hypervisor)
    return True
