#!/usr/bin/env python3
"""Verify Stage 9 (Service Activation) postconditions.

Four checks covering sections H4a-sl, L0, L:
  1. HTTPS responding (Stage 5 + 9 together deliver working HTTPS)
  2. Social Login Key exists via API
  3. stop.py deployed to bench dir
  4. .bash_aliases rendered for erp_user
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _ssh_vm(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    cmd: str, timeout: int = 15,
):
    return subprocess.run(
        ["ssh", *ssh_opts, "-i", ssh_key, f"you@{target_ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def check_https(
    target_ip: str, ssh_opts: list[str], ssh_key: str, site_url: str,
) -> tuple[bool, str]:
    """HTTPS responds to /api/method/ping."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"curl -sf --insecure --max-time 5 https://{site_url}/api/method/ping"
                " >/dev/null && echo y",
                timeout=10)
    if r.returncode == 0 and "y" in r.stdout:
        return True, f"HTTPS responding at {site_url}"
    return False, f"HTTPS not responding at {site_url}"


def check_social_login(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    erp_user: str, bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Social Login Key 'google' exists via API."""
    apikey_sh = f"{bench_dir}/sites/{site_url}/private/files/apikey.sh"
    cmd = (
        f"sudo -u {erp_user} bash -c '"
        f"if [ -f {apikey_sh} ]; then"
        f"  source {apikey_sh};"
        f"  curl -sf --insecure --max-time 5"
        f"  --header \"Authorization: token $KEYS\""
        f"  https://{site_url}/api/resource/Social%20Login%20Key/google"
        f"  >/dev/null && echo y;"
        f"else echo n; fi'"
    )
    r = _ssh_vm(target_ip, ssh_opts, ssh_key, cmd, timeout=10)
    if r.returncode == 0 and "y" in r.stdout:
        return True, "Social Login Key 'google' present"
    return False, "Social Login Key 'google' not found"


def check_stop_py(
    target_ip: str, ssh_opts: list[str], ssh_key: str, bench_dir: str,
) -> tuple[bool, str]:
    """stop.py deployed to bench dir."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"sudo test -f {bench_dir}/stop.py && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "stop.py deployed"
    return False, "stop.py not found in bench dir"


def check_bash_aliases(
    target_ip: str, ssh_opts: list[str], ssh_key: str, erp_user: str,
) -> tuple[bool, str]:
    """.bash_aliases rendered for erp_user."""
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"sudo test -f /home/{erp_user}/.bash_aliases && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, f".bash_aliases present for {erp_user}"
    return False, f".bash_aliases not found for {erp_user}"


def verify_stage_9(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
    erp_user: str,
    bench_dir: str,
    site_url: str,
) -> list[tuple[bool, str]]:
    """Run all Stage 9 postcondition checks."""
    return [
        check_https(target_ip, ssh_opts, ssh_key, site_url),
        check_social_login(target_ip, ssh_opts, ssh_key, erp_user, bench_dir, site_url),
        check_stop_py(target_ip, ssh_opts, ssh_key, bench_dir),
        check_bash_aliases(target_ip, ssh_opts, ssh_key, erp_user),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


# ── CLI entry point ──────────────────────────────────────────────────
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

    erp_user = "erpadm"
    nickname = host_cfg.get("nickname", host[:4])
    bench_dir = f"/home/{erp_user}/frappe-bench-{nickname}"
    site_url = host_cfg.get("site_url", f"{host}.iridium.blue")

    results = verify_stage_9(
        target_ip=virbr0_ip,
        ssh_opts=ssh_opts,
        ssh_key=ssh_key,
        erp_user=erp_user,
        bench_dir=bench_dir,
        site_url=site_url,
    )

    print(f"\n── Stage 9 verification: {host} ──")
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
