#!/usr/bin/env python3
"""
diagnose — Remote VM process diagnostics for ESACP lab.

Reusable functions for inspecting hung, stuck, or misbehaving processes
on KVM guest VMs via SSH.  Each function does one thing, returns structured
data, and prints a human-readable summary.

Usage:
    python tools/diagnose.py <host> <subcommand> [args]

Subcommands:
    hung-procs              List long-running bench/frappe/ce_sri processes
    proc-detail <pid>       Threads, wait channels, file descriptors, TCP sockets
    proc-output <pid>       Capture recent stdout/stderr (reads /proc pipes via GDB)
    bench-log <job_id>      Tail the job log for a background differentiation job
    site-health             Quick: currentsite.txt, gunicorn, supervisor, nginx
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent


# ── SSH transport ─────────────────────────────────────────────────────────────

def ssh(host: str, cmd: str, timeout: int = 15) -> tuple[int, str]:
    """Run a command on a remote host via SSH.  Returns (exit_code, output)."""
    result = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", host, cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def ssh_lines(host: str, cmd: str, timeout: int = 15) -> list[str]:
    """ssh() but split into non-empty lines."""
    _, out = ssh(host, cmd, timeout)
    return [l for l in out.splitlines() if l.strip()]


# ── Process discovery ─────────────────────────────────────────────────────────

PROC_PATTERNS = r"(bench|frappe|install\.py|after_restart|before_install|ce_sri)"


def hung_procs(host: str) -> list[dict]:
    """Find long-running bench/frappe/ce_sri processes on a VM."""
    lines = ssh_lines(
        host,
        f"ps -eo pid,etimes,user,args --no-headers"
        f" | grep -E '{PROC_PATTERNS}' | grep -v grep",
    )
    procs = []
    for line in lines:
        parts = line.split(None, 3)
        if len(parts) >= 4:
            procs.append({
                "pid": int(parts[0]),
                "elapsed_s": int(parts[1]),
                "user": parts[2],
                "cmd": parts[3],
            })
    procs.sort(key=lambda p: p["elapsed_s"], reverse=True)
    return procs


def print_hung_procs(procs: list[dict]) -> None:
    if not procs:
        print("  No matching processes found.")
        return
    for p in procs:
        mins = p["elapsed_s"] // 60
        print(f"  PID {p['pid']:>7}  {mins:>4}m  {p['user']:<10}  {p['cmd'][:90]}")


# ── Per-process detail ────────────────────────────────────────────────────────

def proc_threads(host: str, pid: int) -> list[dict]:
    """List threads for a PID with their wait channels."""
    tids = ssh_lines(host, f"ls /proc/{pid}/task/ 2>/dev/null")
    threads = []
    for tid in tids:
        tid = tid.strip()
        if not tid.isdigit():
            continue
        wchan_lines = ssh_lines(host, f"cat /proc/{tid}/wchan 2>/dev/null")
        wchan = wchan_lines[0] if wchan_lines else "?"
        stack_lines = ssh_lines(
            host, f"sudo cat /proc/{tid}/stack 2>/dev/null | head -3"
        )
        threads.append({"tid": int(tid), "wchan": wchan, "stack": stack_lines})
    return threads


def print_proc_threads(threads: list[dict]) -> None:
    for t in threads:
        label = "main" if t == threads[0] else "    "
        print(f"  {label} TID {t['tid']}  wchan={t['wchan']}")
        for s in t["stack"]:
            print(f"        {s.strip()}")


def proc_fds(host: str, pid: int) -> list[dict]:
    """List open file descriptors for a PID."""
    lines = ssh_lines(
        host,
        f"sudo ls -la /proc/{pid}/fd/ 2>/dev/null | tail -n +2",
    )
    fds = []
    for line in lines:
        parts = line.rsplit("->", 1)
        if len(parts) == 2:
            fd_num = parts[0].strip().split()[-1]
            target = parts[1].strip()
            fds.append({"fd": fd_num, "target": target})
    return fds


def print_proc_fds(fds: list[dict]) -> None:
    for f in fds:
        print(f"  fd {f['fd']:>3}  →  {f['target']}")


def proc_tcp(host: str, pid: int) -> list[dict]:
    """Show TCP connections belonging to a PID's network namespace."""
    lines = ssh_lines(
        host,
        f"sudo nsenter -t {pid} -n ss -tnp 2>/dev/null | tail -n +2",
    )
    conns = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 5:
            conns.append({
                "state": parts[0],
                "local": parts[3],
                "remote": parts[4],
                "detail": parts[5] if len(parts) > 5 else "",
            })
    return conns


def print_proc_tcp(conns: list[dict]) -> None:
    if not conns:
        print("  No TCP connections.")
        return
    for c in conns:
        print(f"  {c['state']:<14} {c['local']:<25} → {c['remote']:<25} {c['detail']}")


# ── Site health ───────────────────────────────────────────────────────────────

def site_health(host: str) -> dict:
    """Quick health check: currentsite.txt, gunicorn, supervisor, nginx."""
    checks = {}

    # currentsite.txt
    rc, out = ssh(host, "cat /home/erpadm/frappe-bench/sites/currentsite.txt 2>&1")
    checks["currentsite_txt"] = {"ok": rc == 0, "value": out.strip()}

    # gunicorn
    rc, out = ssh(host, "pgrep -c gunicorn 2>/dev/null || echo 0")
    count = int(out.strip()) if out.strip().isdigit() else 0
    checks["gunicorn"] = {"ok": count > 0, "workers": count}

    # supervisor
    rc, out = ssh(
        host,
        "sudo supervisorctl status 2>/dev/null"
        " | awk '{print $1, $2}' | head -15",
    )
    checks["supervisor"] = {"ok": rc == 0, "services": out}

    # nginx
    rc, out = ssh(host, "systemctl is-active nginx 2>/dev/null")
    checks["nginx"] = {"ok": out.strip() == "active"}

    return checks


def print_site_health(checks: dict) -> None:
    for name, info in checks.items():
        status = "OK" if info["ok"] else "FAIL"
        detail = ""
        if "value" in info:
            detail = info["value"][:60]
        elif "workers" in info:
            detail = f"{info['workers']} workers"
        elif "services" in info:
            detail = info["services"].replace("\n", " | ")[:80]
        print(f"  [{status:>4}]  {name:<20}  {detail}")


# ── Job log ───────────────────────────────────────────────────────────────────

def bench_log(host: str, job_id: str, lines: int = 40) -> str:
    """Tail the differentiation job log on saconsole."""
    _, out = ssh(host, f"tail -n {lines} /tmp/job-{job_id}.log 2>/dev/null")
    return out


# ── API job polling ───────────────────────────────────────────────────────────

API_URL = os.environ.get("API_URL", "http://localhost:8088")


def await_job(job_id: str, interval: int = 30, timeout: int = 900) -> dict:
    """Poll the FastAPI /api/jobs endpoint until the job is done or failed."""
    import urllib.request
    elapsed = 0
    while elapsed < timeout:
        try:
            resp = urllib.request.urlopen(f"{API_URL}/api/jobs", timeout=5)
            jobs = json.loads(resp.read())
            job = jobs.get(job_id)
            if job is None:
                print(f"  {elapsed:>4}s  job {job_id} not found (cleaned up = done)")
                return {"status": "done"}
            status = job.get("status", "unknown")
            print(f"  {elapsed:>4}s  {status}")
            if status in ("done", "failed"):
                return job
        except Exception as e:
            print(f"  {elapsed:>4}s  error: {e}")
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="diagnose", description="Remote VM process diagnostics"
    )
    parser.add_argument("host", help="SSH host alias (e.g. dev02)")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("hung-procs", help="List long-running bench/frappe processes")

    p_detail = sub.add_parser("proc-detail", help="Full detail for one PID")
    p_detail.add_argument("pid", type=int)

    p_health = sub.add_parser("site-health", help="Quick site health check")

    p_log = sub.add_parser("bench-log", help="Tail a job log on saconsole")
    p_log.add_argument("job_id")
    p_log.add_argument("-n", type=int, default=40)

    p_await = sub.add_parser("await-job", help="Poll API until job completes")
    p_await.add_argument("job_id")
    p_await.add_argument("--interval", type=int, default=30)
    p_await.add_argument("--timeout", type=int, default=900)

    args = parser.parse_args()

    if args.cmd == "hung-procs":
        procs = hung_procs(args.host)
        print_hung_procs(procs)

    elif args.cmd == "proc-detail":
        print("── Threads ──")
        threads = proc_threads(args.host, args.pid)
        print_proc_threads(threads)
        print("\n── File descriptors ──")
        fds = proc_fds(args.host, args.pid)
        print_proc_fds(fds)
        print("\n── TCP connections ──")
        conns = proc_tcp(args.host, args.pid)
        print_proc_tcp(conns)

    elif args.cmd == "site-health":
        checks = site_health(args.host)
        print_site_health(checks)

    elif args.cmd == "bench-log":
        print(bench_log(args.host, args.job_id, args.n))

    elif args.cmd == "await-job":
        job = await_job(args.job_id, args.interval, args.timeout)
        print(f"\n  Final: {job.get('status')}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
