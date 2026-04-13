#!/usr/bin/env python3
"""Verify Stage 2 (Network) postconditions.

Each check returns (pass, description).  Importable for use as a pre-stage
idempotency gate: if all pass, Stage 2 can be skipped entirely.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def _ssh_vm(virbr0_ip: str, hypervisor: str, ssh_key: str,
            cmd: str, timeout: int = 15):
    return subprocess.run(
        ["ssh",
         "-o", f"ProxyJump={hypervisor}",
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10",
         "-i", ssh_key,
         f"you@{virbr0_ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def _ssh_saconsole(hypervisor: str, ssh_key: str,
                   cmd: str, timeout: int = 15):
    return subprocess.run(
        ["ssh",
         "-o", f"ProxyJump={hypervisor}",
         "-o", "StrictHostKeyChecking=no",
         "-i", ssh_key,
         "you@192.168.122.10", cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def check_saconsole_wg_peer(
    hostname: str, project_root: str, hypervisor: str, ssh_key: str,
) -> tuple[bool, str]:
    """saconsole's wg show lists the peer public key for this host."""
    # Read the expected pubkey from group_vars
    gv = Path(project_root) / "ansible" / "group_vars" / "all.yml"
    with open(gv) as f:
        data = yaml.safe_load(f)
    pubkey = data.get(f"wg_pubkey_{hostname}", "")
    if not pubkey:
        return False, f"No wg_pubkey_{hostname} in group_vars — can't verify hub"

    r = _ssh_saconsole(hypervisor, ssh_key, "sudo wg show wg0")
    if r.returncode != 0:
        return False, f"Cannot run wg show on saconsole: {r.stderr.strip()}"
    if pubkey in r.stdout:
        return True, f"saconsole hub has peer {hostname} ({pubkey[:12]}…)"
    return False, f"saconsole hub missing peer for {hostname}"


def check_cloudflare_dns(hostname: str, wg_ip: str) -> tuple[bool, str]:
    """DNS A record resolves to expected WG IP."""
    fqdn = f"{hostname}.iridium.blue"
    r = subprocess.run(
        ["dig", "+short", fqdn, "A", "@1.1.1.1"],
        capture_output=True, text=True, timeout=10,
    )
    resolved = r.stdout.strip()
    if resolved == wg_ip:
        return True, f"DNS {fqdn} → {wg_ip}"
    if resolved:
        return False, f"DNS {fqdn} → {resolved} (expected {wg_ip})"
    return False, f"DNS {fqdn} has no A record"


def check_tls_cert_on_vm(
    virbr0_ip: str, hypervisor: str, ssh_key: str,
) -> tuple[bool, str]:
    """TLS cert files present on VM (final location or staging in /tmp/)."""
    # Check final location first
    r = _ssh_vm(virbr0_ip, hypervisor, ssh_key,
                "test -f /etc/nginx/certs/iridium.blue/fullchain.pem && echo final")
    if r.returncode == 0 and "final" in r.stdout:
        return True, "TLS cert installed at /etc/nginx/certs/"
    # Fall back to staging location
    r = _ssh_vm(virbr0_ip, hypervisor, ssh_key,
                "test -f /tmp/fullchain.pem && test -f /tmp/privkey.pem && echo staged")
    if r.returncode == 0 and "staged" in r.stdout:
        return True, "TLS cert staged in /tmp/ (pending install)"
    return False, "TLS cert not found on VM"


def check_vm_wg_interface(
    virbr0_ip: str, hypervisor: str, ssh_key: str,
) -> tuple[bool, str]:
    """VM has wg0 interface up."""
    r = _ssh_vm(virbr0_ip, hypervisor, ssh_key,
                "ip link show wg0 2>/dev/null | head -1")
    if r.returncode == 0 and "wg0" in r.stdout:
        if "UP" in r.stdout:
            return True, "VM wg0 interface is UP"
        return False, "VM wg0 exists but is not UP"
    return False, "VM wg0 interface not found"


def check_wg_mesh_ping(wg_ip: str) -> tuple[bool, str]:
    """Controller can ping VM on WireGuard mesh."""
    r = subprocess.run(
        ["ping", "-c", "2", "-W", "3", wg_ip],
        capture_output=True, text=True, timeout=15,
    )
    if r.returncode == 0:
        return True, f"WG mesh ping to {wg_ip} OK"
    return False, f"WG mesh ping to {wg_ip} failed"


def verify_stage_2(
    hostname: str,
    wg_ip: str,
    virbr0_ip: str,
    hypervisor: str,
    project_root: str,
    ssh_key: str | None = None,
) -> list[tuple[bool, str]]:
    """Run all Stage 2 postcondition checks.  Returns list of (pass, msg)."""
    if ssh_key is None:
        ssh_key = str(Path.home() / ".ssh" / "hasan_mighty")
    return [
        check_saconsole_wg_peer(hostname, project_root, hypervisor, ssh_key),
        check_cloudflare_dns(hostname, wg_ip),
        check_tls_cert_on_vm(virbr0_ip, hypervisor, ssh_key),
        check_vm_wg_interface(virbr0_ip, hypervisor, ssh_key),
        check_wg_mesh_ping(wg_ip),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


# ── CLI entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    from tools.pipeline.stages.common.verify_cli import (
        parse_verify_args,
        print_results,
    )

    ctx = parse_verify_args()
    results = verify_stage_2(
        hostname=ctx.hostname,
        wg_ip=ctx.wg_ip,
        virbr0_ip=ctx.virbr0_ip,
        hypervisor=ctx.hypervisor,
        project_root=ctx.project_root,
    )
    print_results("Stage 2", ctx.hostname, results)
