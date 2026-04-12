#!/usr/bin/env python3
"""Verify Stage 5 (TLS) postconditions.

Each check returns (pass, description).  Importable for use as a pre-stage
idempotency gate: if all pass, Stage 5 can be skipped entirely.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _ssh_vm(target_ip: str, ssh_opts: list[str], ssh_key: str,
            cmd: str, timeout: int = 15):
    return subprocess.run(
        ["ssh", *ssh_opts, "-i", ssh_key, f"you@{target_ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def check_cert_installed(
    target_ip: str, ssh_opts: list[str], ssh_key: str, domain: str,
) -> tuple[bool, str]:
    """TLS cert + key present at /etc/nginx/certs/{domain}/."""
    cert_dir = f"/etc/nginx/certs/{domain}"
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -f {cert_dir}/fullchain.pem"
                f" && test -f {cert_dir}/privkey.pem"
                " && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, f"TLS cert installed at {cert_dir}"
    return False, f"TLS cert not found at {cert_dir}"


def check_nginx_vhost(
    target_ip: str, ssh_opts: list[str], ssh_key: str, site_url: str,
) -> tuple[bool, str]:
    """nginx vhost symlinked in sites-enabled."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -f /etc/nginx/sites-enabled/{site_url} && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, f"nginx vhost enabled for {site_url}"
    return False, f"nginx vhost not enabled for {site_url}"


def check_dh_params(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
) -> tuple[bool, str]:
    """DH params file present."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                "test -f /etc/nginx/dhparam.pem && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "DH params present"
    return False, "DH params not found at /etc/nginx/dhparam.pem"


def verify_stage_5(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
    site_url: str,
    domain: str,
) -> list[tuple[bool, str]]:
    """Run all Stage 5 postcondition checks.  Returns list of (pass, msg)."""
    return [
        check_cert_installed(target_ip, ssh_opts, ssh_key, domain),
        check_nginx_vhost(target_ip, ssh_opts, ssh_key, site_url),
        check_dh_params(target_ip, ssh_opts, ssh_key),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


# ── CLI entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hostname> [project_root]")
        sys.exit(2)

    host = sys.argv[1]
    proj = sys.argv[2] if len(sys.argv) > 2 else str(
        Path(__file__).resolve().parents[4])

    import yaml

    hm = Path(proj) / "hosts_map.yml"
    with open(hm) as f:
        data = yaml.safe_load(f)
    host_cfg = data["groups"]["kvm"][host]

    hypervisor = host_cfg.get("hypervisor", "toshiba")
    virbr0_ip = host_cfg["virbr0_ip"]
    ssh_key = str(Path.home() / ".ssh" / "hasan_mighty")
    ssh_opts = [
        "-o", f"ProxyJump={hypervisor}",
        "-o", "StrictHostKeyChecking=no",
    ]

    # Derive domain from ansible_groups
    groups = host_cfg.get("ansible_groups", [])
    if "production" in groups:
        domain = "logichem.solutions"
    else:
        domain = "iridium.blue"
    site_url = f"{host}.{domain}"

    results = verify_stage_5(
        target_ip=virbr0_ip,
        ssh_opts=ssh_opts,
        ssh_key=ssh_key,
        site_url=site_url,
        domain=domain,
    )

    print(f"\n── Stage 5 verification: {host} ──")
    passed = failed = 0
    for ok, msg in results:
        tag = "\u2705" if ok else "\u274c"
        print(f"  {tag}  {msg}")
        if ok:
            passed += 1
        else:
            failed += 1
    print(f"\n  {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
