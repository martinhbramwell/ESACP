"""WireGuard VPN verification primitive.

Pings each VM from the controller, runs `sudo wg show` on the hub, and
pings every VM from every other VM. Emits progress lines for the CLI to
render; returns True if all checks passed.
"""

from __future__ import annotations

import subprocess

from tools.host_identity import HUB_KEY, HUB_WG_IP
from tools.pipeline.stages.common.types import Emit


def _ssh(host_ip: str, user: str, key: str, cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-i", key,
         "-o", "StrictHostKeyChecking=accept-new",
         "-o", "ConnectTimeout=10",
         f"{user}@{host_ip}", cmd],
        capture_output=True, text=True,
    )


def verify_vpn(hosts: dict, vm_user: str, ssh_key: str, emit: Emit) -> bool:
    all_ok = True

    emit("[bold]Controller → VM (ping):[/bold]")
    for name, info in hosts.items():
        wg_ip = info.get("wg_ip")
        if not wg_ip:
            continue
        r = subprocess.run(
            ["ping", "-c", "3", "-W", "2", wg_ip],
            capture_output=True, text=True,
        )
        ok = r.returncode == 0
        icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
        emit(f"  {icon} ping {name} ({wg_ip})")
        if ok:
            for line in r.stdout.splitlines():
                if "rtt" in line or "round-trip" in line:
                    emit(f"    [dim]{line.strip()}[/dim]")
        all_ok = all_ok and ok

    emit("")
    if HUB_KEY and HUB_KEY in hosts:
        emit(f"[bold]WireGuard peers on {HUB_KEY} (sudo wg show):[/bold]")
        r = _ssh(HUB_WG_IP, vm_user, ssh_key, "sudo wg show")
        if r.returncode == 0:
            for line in r.stdout.strip().splitlines():
                emit(f"  [dim]{line}[/dim]")
        else:
            emit(f"  [red]SSH failed: {r.stderr.strip()}[/red]")
            all_ok = False

    emit("")
    emit("[bold]Cross-VM ping (via WireGuard):[/bold]")
    vm_list = list(hosts.items())
    for src_name, src_info in vm_list:
        src_ip = src_info.get("wg_ip")
        if not src_ip:
            continue
        for dst_name, dst_info in vm_list:
            if src_name == dst_name:
                continue
            dst_ip = dst_info.get("wg_ip")
            if not dst_ip:
                continue
            r = _ssh(src_ip, vm_user, ssh_key, f"ping -c 1 -W 2 {dst_ip}")
            ok = r.returncode == 0
            icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            emit(f"  {icon} {src_name} → {dst_name} ({dst_ip})")
            all_ok = all_ok and ok

    return all_ok
