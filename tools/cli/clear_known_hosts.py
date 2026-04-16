"""CLI: remove stale SSH known_hosts entries for ESACP VMs."""

from __future__ import annotations

from tools.cli._common import banner, console, kvm_hosts
from tools.pipeline.stages.common.known_hosts import (
    known_hosts_entries, remove_known_hosts,
)


def run(args, config: dict) -> int:
    banner("Clear Known Hosts")

    all_entries: list[str] = []
    for info in kvm_hosts(config).values():
        for entry in known_hosts_entries(info):
            if entry not in all_entries:
                all_entries.append(entry)

    console.print(f"Removing up to {len(all_entries)} entries from ~/.ssh/known_hosts:")
    for entry in all_entries:
        console.print(f"  [dim]{entry}[/dim]")
    console.print()

    removed = remove_known_hosts(all_entries, lambda _m: None)
    console.print(f"[green]✅  Done ({removed} removed, rest were not present).[/green]")
    return 0
