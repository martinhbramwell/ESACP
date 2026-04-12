#!/usr/bin/env python3
"""Verify Stage 8 (App Config) postconditions.

Eight checks covering sections H–H4g:
  1. site_url in /etc/hosts
  2. apikey.sh exists (H4a)
  3. ce_sri_parms.json in secrets (H4b)
  4. config/nginx.conf generated (H4c)
  5. before-install artifacts: ce_sri.conf (H4d)
  6. .env exists for ce_sri_svc (H4e)
  7. gunicorn responds to /api/method/ping (H4f-poll)
  8. after-restart: Custom Script doctypes present (H4g)
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


def check_etc_hosts(
    target_ip: str, ssh_opts: list[str], ssh_key: str, site_url: str,
) -> tuple[bool, str]:
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"grep -q {site_url} /etc/hosts && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, f"{site_url} in /etc/hosts"
    return False, f"{site_url} not in /etc/hosts"


def check_apikey(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    path = f"{bench_dir}/sites/{site_url}/private/files/apikey.sh"
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -f {path} && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "apikey.sh present"
    return False, "apikey.sh missing"


def check_secrets(
    target_ip: str, ssh_opts: list[str], ssh_key: str, erp_user: str,
) -> tuple[bool, str]:
    path = f"/home/{erp_user}/.ssh/secrets/ce_sri_parms.json"
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"sudo test -f {path} && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "ce_sri_parms.json in secrets"
    return False, "ce_sri_parms.json missing from secrets"


def check_nginx_conf(
    target_ip: str, ssh_opts: list[str], ssh_key: str, bench_dir: str,
) -> tuple[bool, str]:
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -f {bench_dir}/config/nginx.conf && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "config/nginx.conf generated"
    return False, "config/nginx.conf missing"


def check_before_install(
    target_ip: str, ssh_opts: list[str], ssh_key: str, bench_dir: str,
) -> tuple[bool, str]:
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -f {bench_dir}/config/ce_sri.conf && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, "before-install artifact (ce_sri.conf) present"
    return False, "ce_sri.conf missing — before-install not run"


def check_dotenv(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str,
) -> tuple[bool, str]:
    path = f"{bench_dir}/apps/ce_sri/services/ce_sri_svc/.env"
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"test -f {path} && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, ".env present for ce_sri_svc"
    return False, ".env missing for ce_sri_svc"


def check_gunicorn(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    site_url: str, gunicorn_port: int,
) -> tuple[bool, str]:
    url = f"http://{site_url}:{gunicorn_port}/api/method/ping"
    r = _ssh_vm(target_ip, ssh_opts, ssh_key,
                f"curl -sf --max-time 5 {url} >/dev/null && echo y",
                timeout=10)
    if r.returncode == 0 and "y" in r.stdout:
        return True, "gunicorn responding to /api/method/ping"
    return False, "gunicorn not responding"


def check_after_restart(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    erp_user: str, bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    cmd = (
        f"sudo -u {erp_user} bash -c "
        f"'cd {bench_dir} && bench --site {site_url} list-apps'"
    )
    r = _ssh_vm(target_ip, ssh_opts, ssh_key, cmd, timeout=30)
    if r.returncode == 0 and "ce_sri" in r.stdout:
        return True, "after-restart: ce_sri app confirmed"
    return False, "after-restart: ce_sri app not found in list-apps"


def verify_stage_8(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
    erp_user: str,
    bench_dir: str,
    site_url: str,
    gunicorn_port: int = 8000,
) -> list[tuple[bool, str]]:
    """Run all Stage 8 postcondition checks."""
    return [
        check_etc_hosts(target_ip, ssh_opts, ssh_key, site_url),
        check_apikey(target_ip, ssh_opts, ssh_key, bench_dir, site_url),
        check_secrets(target_ip, ssh_opts, ssh_key, erp_user),
        check_nginx_conf(target_ip, ssh_opts, ssh_key, bench_dir),
        check_before_install(target_ip, ssh_opts, ssh_key, bench_dir),
        check_dotenv(target_ip, ssh_opts, ssh_key, bench_dir),
        check_gunicorn(target_ip, ssh_opts, ssh_key, site_url, gunicorn_port),
        check_after_restart(target_ip, ssh_opts, ssh_key, erp_user, bench_dir, site_url),
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

    results = verify_stage_8(
        target_ip=virbr0_ip,
        ssh_opts=ssh_opts,
        ssh_key=ssh_key,
        erp_user=erp_user,
        bench_dir=bench_dir,
        site_url=site_url,
    )

    print(f"\n── Stage 8 verification: {host} ──")
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
