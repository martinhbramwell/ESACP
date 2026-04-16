"""CLI: full provisioning pipeline (stages 1–9) for a VM."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.cli._common import banner, console, kvm_hosts
from tools.host_identity import ZONE_DOMAINS
from tools.pipeline.macro.provision import run as run_macro


def run(args, config: dict) -> int:
    hostname = args.vm
    banner(f"Provision (full pipeline): {hostname}")

    vm_info = kvm_hosts(config).get(hostname, {})
    virbr0_ip = vm_info.get("virbr0_ip")
    if not virbr0_ip:
        console.print(f"[red]No virbr0_ip for '{hostname}' in hosts_map.yml[/red]")
        return 1
    if vm_info.get("wg_role") == "hub":
        console.print(f"[red]Cannot provision hub node '{hostname}' — use rebuild_lab.sh[/red]")
        return 1

    project_root = str(Path(__file__).resolve().parent.parent.parent)
    try:
        run_macro(
            hostname=hostname, virbr0_ip=virbr0_ip,
            project_root=project_root, emit=console.print,
        )
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        console.print(f"[red]Pipeline failed: {exc}[/red]")
        return 1

    zone = next(
        (g for g in vm_info.get("ansible_groups", [])
         if g in ("production", "staging", "development")),
        "development",
    )
    domain = ZONE_DOMAINS.get(zone, "iridium.blue")
    console.print()
    console.print(f"[green]Provision complete — ERPNext at https://{hostname}.{domain}[/green]")
    return 0
