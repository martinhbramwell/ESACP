#!/usr/bin/env python3
"""Standalone job worker — spawned by api.py as an independent OS process.

Usage:
    python3 tools/job_worker.py <job_type> <job_id> '<json_args>'

Job types: provision, refresh, destroy, build_template

Writes timestamped lines to stdout (api.py redirects to /tmp/esacp-job-{id}.log).
Writes exit status to /tmp/esacp-job-{id}.status on completion.

Because this runs as a child process (not a thread), it survives uvicorn restarts.
This is the fix for GH #37.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent

# Ensure project root is on sys.path so `from tools.*` imports work
# when this script is spawned as an independent subprocess.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
HOSTS_MAP = PROJECT_ROOT / "hosts_map.yml"
GROUP_VARS_ALL = PROJECT_ROOT / "ansible" / "group_vars" / "all.yml"
KEYS_SOPS = PROJECT_ROOT / "config" / "wireguard" / "keys.sops.yml"
CLOUD_INIT_DIR = PROJECT_ROOT / "platforms" / "kvm" / "cloud-init"
PLATFORMS_PACKER = PROJECT_ROOT / "platforms" / "packer"

from tools.host_identity import HUB_KEY, HUB_VIRBR0_IP

TOSHIBA_ALIAS = "toshiba"
TOSHIBA_HYPERVISOR_USER = "hasan"
HUB_IP = HUB_VIRBR0_IP
HUB_SSH = [
    "ssh", "-o", f"ProxyJump={TOSHIBA_ALIAS}",
    "-o", "StrictHostKeyChecking=no",
    "-i", str(Path.home() / ".ssh" / "hasan_mighty"),
    f"you@{HUB_IP}",
]


def _ts():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def emit(line: str):
    print(f"[{_ts()}] {line}", flush=True)


def _stream_lines(pipe):
    """Yield lines from a binary pipe, handling \\r correctly."""
    buf = b""
    current = b""
    while True:
        chunk = pipe.read(256)
        if not chunk:
            break
        buf += chunk
        while buf:
            nl = buf.find(b"\n")
            cr = buf.find(b"\r")
            if nl == -1 and cr == -1:
                current += buf
                buf = b""
            elif nl != -1 and (cr == -1 or nl < cr):
                current += buf[:nl]
                yield current.decode("utf-8", errors="replace")
                current = b""
                buf = buf[nl + 1:]
            else:
                current = buf[cr + 1:]
                buf = b""
    if current:
        yield current.decode("utf-8", errors="replace")


# ── Job runners ──────────────────────────────────────────────────────────────

def run_provision(args: dict) -> None:
    from tools.pipeline.macro.provision import run
    run(
        hostname=args["hostname"],
        virbr0_ip=args["virbr0_ip"],
        project_root=str(PROJECT_ROOT),
        emit=emit,
        cleanup_cfg=args.get("cleanup_cfg"),
    )
    emit(f"── Provision complete — ERPNext at https://{args['hostname']}.iridium.blue ──")


def run_refresh(args: dict) -> None:
    from tools.pipeline.macro.refresh import run
    run(
        hostname=args["hostname"],
        host_cfg=args["host_cfg"],
        project_root=str(PROJECT_ROOT),
        emit=emit,
    )
    emit("── Refresh complete ──")


def run_destroy(args: dict) -> None:
    from tools.destroy_helpers import (
        destroy_vm,
        get_wg_pubkey,
        remove_from_group_vars_all,
        remove_from_hosts_map,
        remove_keys_from_sops,
        remove_wg_peer_live,
    )

    hostname = args["hostname"]
    host_cfg = args["host_cfg"]

    # Step 1: Remove live WireGuard peer
    emit("── Remove live WireGuard peer ──")
    pubkey = get_wg_pubkey(hostname, KEYS_SOPS, PROJECT_ROOT)
    if pubkey:
        remove_wg_peer_live(hostname, pubkey, HOSTS_MAP, emit)
    else:
        emit(f"  [WARN] No pubkey found for {hostname} — skipping live WG removal")

    # Step 2: Destroy VM on hypervisor
    emit("── Destroy VM ──")
    destroy_vm(hostname, host_cfg, emit)

    # Step 3: Remove from hosts_map.yml
    emit("── Update hosts_map.yml ──")
    remove_from_hosts_map(hostname, HOSTS_MAP, emit)

    # Step 4: Remove pubkey from group_vars/all.yml
    emit("── Update group_vars/all.yml ──")
    remove_from_group_vars_all(hostname, GROUP_VARS_ALL, emit)

    # Step 5: Regenerate inventory
    emit("── Regenerate inventory ──")
    result = subprocess.run(
        ["python3", "tools/generate_inventory.py"],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"generate_inventory.py failed:\n{result.stderr}")
    emit("  [OK] inventory regenerated")

    # Step 6: Update hub WireGuard config via Ansible
    emit("── Update hub WireGuard config (Ansible) ──")
    proc = subprocess.Popen(
        [
            "ansible-playbook",
            "-i", "inventory/kvm.yml",
            "site-kvm.yml",
            "--limit", HUB_KEY,
            "--tags", "wireguard",
        ],
        cwd=str(PROJECT_ROOT / "ansible"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for line in _stream_lines(proc.stdout):
        emit(line)
    proc.wait()
    if proc.returncode != 0:
        emit(f"  [WARN] Ansible wireguard update failed (exit {proc.returncode})")
    else:
        emit("  [OK] hub wg0.conf updated")

    # Step 7: Remove keys from keys.sops.yml
    emit("── Remove WireGuard keys ──")
    remove_keys_from_sops(hostname, KEYS_SOPS, PROJECT_ROOT, emit)

    # Step 8: Remove cloud-init dir if present
    ci_dir = CLOUD_INIT_DIR / hostname
    if ci_dir.exists():
        shutil.rmtree(ci_dir)
        emit(f"  [OK] Removed cloud-init dir {ci_dir}")

    emit("── Destroy complete ──")


def run_build_template(args: dict) -> None:
    ssh_opts = [
        "-o", f"ProxyJump={TOSHIBA_ALIAS}",
        "-o", "StrictHostKeyChecking=no",
        "-i", str(Path.home() / ".ssh" / "hasan_mighty"),
    ]

    _COMPACT_SUFFIXES = ("— waiting 30s ...",)
    _last_line = [None]  # mutable ref for compaction

    def emit_compact(line: str):
        stamped = f"[{_ts()}] {line}"
        if _last_line[0] and any(line.endswith(s) for s in _COMPACT_SUFFIXES):
            if any(_last_line[0].endswith(s) for s in _COMPACT_SUFFIXES):
                # Overwrite last line — write \r to signal compaction in log
                print(f"\r{stamped}", end="", flush=True)
                _last_line[0] = stamped
                return
        print(stamped, flush=True)
        _last_line[0] = stamped

    emit("── ERPNext v13 template build ──")

    # Sync packer directory to hub
    emit("Syncing platforms/packer/ to hub ...")
    rsync = subprocess.run(
        ["rsync", "-az", "--delete",
         "-e", "ssh " + " ".join(ssh_opts),
         str(PLATFORMS_PACKER) + "/",
         f"you@{HUB_IP}:/opt/esacp/platforms/packer/"],
        capture_output=True, text=True,
    )
    if rsync.returncode != 0:
        raise RuntimeError(f"rsync to hub failed: {rsync.stderr.strip()}")

    emit(f"Connecting to hub ({HUB_IP} via {TOSHIBA_ALIAS}) ...")

    REMOTE_LOG = "/tmp/packer-build-output.log"
    REMOTE_EXIT = "/tmp/packer-build-output.log.exit"

    subprocess.run(HUB_SSH + [f"rm -f {REMOTE_LOG} {REMOTE_EXIT}"],
                   capture_output=True)

    start_cmd = (
        f"nohup bash -c 'bash /opt/esacp/platforms/packer/build.sh"
        f" > {REMOTE_LOG} 2>&1; echo $? > {REMOTE_EXIT}'"
        f" > /dev/null 2>&1 & echo $!"
    )
    r = subprocess.run(HUB_SSH + [start_cmd], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Failed to start build on hub: {r.stderr.strip()}")
    emit(f"Build detached on hub (PID {r.stdout.strip()}) — polling log ...")

    offset = 0
    while True:
        time.sleep(5)
        r = subprocess.run(
            HUB_SSH + [f"tail -c +{offset + 1} {REMOTE_LOG} 2>/dev/null || true"],
            capture_output=True, text=True,
        )
        if r.stdout:
            for raw_line in r.stdout.splitlines():
                if raw_line.strip():
                    emit_compact(raw_line)
            offset += len(r.stdout.encode("utf-8"))

        r = subprocess.run(
            HUB_SSH + [f"cat {REMOTE_EXIT} 2>/dev/null || echo -1"],
            capture_output=True, text=True,
        )
        exit_str = r.stdout.strip()
        if exit_str != "-1":
            r = subprocess.run(
                HUB_SSH + [f"tail -c +{offset + 1} {REMOTE_LOG} 2>/dev/null || true"],
                capture_output=True, text=True,
            )
            for raw_line in r.stdout.splitlines():
                if raw_line.strip():
                    emit_compact(raw_line)
            exit_code = int(exit_str) if exit_str.isdigit() else 1
            if exit_code != 0:
                raise RuntimeError(f"build.sh exited with code {exit_code}")
            break

    emit("── Build complete — new image ready on toshiba ──")


# ── Dispatch ─────────────────────────────────────────────────────────────────

RUNNERS = {
    "provision": run_provision,
    "refresh": run_refresh,
    "destroy": run_destroy,
    "build_template": run_build_template,
}


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <job_type> <job_id> '<json_args>'", file=sys.stderr)
        sys.exit(2)

    job_type = sys.argv[1]
    job_id = sys.argv[2]
    args = json.loads(sys.argv[3])

    status_file = Path(f"/tmp/esacp-job-{job_id}.status")

    runner = RUNNERS.get(job_type)
    if not runner:
        print(f"[ERROR] Unknown job type: {job_type}", file=sys.stderr)
        status_file.write_text("error")
        sys.exit(1)

    try:
        runner(args)
        status_file.write_text("done")
    except Exception as exc:
        emit(f"[ERROR] {exc}")
        status_file.write_text("error")
        sys.exit(1)


if __name__ == "__main__":
    main()
