#!/usr/bin/env python3
"""Verify Stage 7 (Data Restoration) postconditions.

Five checks covering sections D–G2:
  1. currentsite.txt exists and contains site_url
  2. Site responds to bench doctor
  3. ddlViews.sql in site private/files
  4. erpnext app installed (apps.txt)
  5. Database restored (tabSales Invoice has rows)
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


def check_currentsite(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Section D1: currentsite.txt exists and contains site_url."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"cat {bench_dir}/sites/currentsite.txt 2>/dev/null",
    )
    if r.returncode == 0 and site_url in r.stdout.strip():
        return True, f"currentsite.txt contains {site_url}"
    return False, "currentsite.txt missing or wrong content"


def check_bench_doctor(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    erp_user: str, bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Section D: site responds to bench doctor."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"sudo -u {erp_user} bash -c 'cd {bench_dir} && bench --site {site_url} doctor'",
        timeout=30,
    )
    if r.returncode == 0:
        return True, f"bench doctor OK for {site_url}"
    return False, f"bench doctor failed for {site_url}"


def check_ddl_views(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Section E: ddlViews.sql in site private/files."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"test -f {bench_dir}/sites/{site_url}/private/files/ddlViews.sql && echo y",
    )
    if r.returncode == 0 and "y" in r.stdout:
        return True, "ddlViews.sql present in private/files"
    return False, "ddlViews.sql not found in private/files"


def check_erpnext_installed(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str,
) -> tuple[bool, str]:
    """Section D: erpnext listed in apps.txt."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"grep -q erpnext {bench_dir}/sites/apps.txt && echo y",
    )
    if r.returncode == 0 and "y" in r.stdout:
        return True, "erpnext installed (in apps.txt)"
    return False, "erpnext not found in apps.txt"


def check_db_restored(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    erp_user: str, bench_dir: str, site_url: str,
) -> tuple[bool, str]:
    """Section G: production data present (tabSales Invoice has rows)."""
    r = _ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"sudo -u {erp_user} bash -c '"
        f"cd {bench_dir} && bench --site {site_url} mariadb"
        f" -e \"SELECT COUNT(*) AS c FROM \\`tabSales Invoice\\`\""
        f" --skip-column-names 2>/dev/null'",
        timeout=30,
    )
    if r.returncode == 0:
        count = r.stdout.strip()
        if count.isdigit() and int(count) > 0:
            return True, f"DB restored ({count} Sales Invoices)"
    return False, "DB not restored (no Sales Invoice rows)"


def verify_stage_7(
    target_ip: str,
    ssh_opts: list[str],
    ssh_key: str,
    erp_user: str,
    bench_dir: str,
    site_url: str,
) -> list[tuple[bool, str]]:
    """Run all Stage 7 postcondition checks."""
    return [
        check_currentsite(target_ip, ssh_opts, ssh_key, bench_dir, site_url),
        check_bench_doctor(target_ip, ssh_opts, ssh_key, erp_user, bench_dir, site_url),
        check_ddl_views(target_ip, ssh_opts, ssh_key, bench_dir, site_url),
        check_erpnext_installed(target_ip, ssh_opts, ssh_key, bench_dir),
        check_db_restored(target_ip, ssh_opts, ssh_key, erp_user, bench_dir, site_url),
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

    results = verify_stage_7(
        target_ip=virbr0_ip,
        ssh_opts=ssh_opts,
        ssh_key=ssh_key,
        erp_user=erp_user,
        bench_dir=bench_dir,
        site_url=site_url,
    )

    print(f"\n── Stage 7 verification: {host} ──")
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
