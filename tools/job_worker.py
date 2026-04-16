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

from tools.host_identity import ZONE_DOMAINS


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
    domain = ZONE_DOMAINS.get(args.get("zone", "development"), "iridium.blue")
    emit(f"── Provision complete — ERPNext at https://{args['hostname']}.{domain} ──")


def run_provision_generic(args: dict) -> None:
    from tools.pipeline.macro.provision_generic import run
    run(
        hostname=args["hostname"],
        virbr0_ip=args["virbr0_ip"],
        project_root=str(PROJECT_ROOT),
        emit=emit,
        cleanup_cfg=args.get("cleanup_cfg"),
    )
    domain = ZONE_DOMAINS.get(args.get("zone", "development"), "iridium.blue")
    site_url = f"https://{args['hostname']}.{domain}"

    wizard_mode = args.get("wizard_mode", "record")
    if wizard_mode == "record":
        _wizard_record(args["hostname"], site_url)
    elif wizard_mode == "replay":
        _wizard_replay(args["hostname"], site_url, args.get("wizard_arg", ""))
    elif wizard_mode == "existing":
        _wizard_existing(args["hostname"], args.get("wizard_arg", ""))
    else:
        emit(f"  [WARN] Unknown wizard_mode '{wizard_mode}' — skipping wizard")

    emit(f"── Generic provision complete — {site_url} ──")


def _wizard_record(hostname: str, site_url: str) -> None:
    """Launch Playwright codegen to record the setup wizard."""
    emit(f"── Wizard ready — recording browser at {site_url} ──")
    emit("  Close the browser when wizard is complete.")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output = PROJECT_ROOT / "prototypes" / "cytoscape" / "recordings" / "wizard" / f"{hostname}-{ts}.spec.js"
    output.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["node", str(PROJECT_ROOT / "prototypes" / "cytoscape" / "recordings" / "record_wizard.js"),
         "--url", site_url, "--output", str(output)],
        cwd=str(PROJECT_ROOT / "prototypes" / "cytoscape"),
        timeout=2400,
    )
    if r.returncode != 0:
        emit(f"  [WARN] Recorder exited with code {r.returncode}")
    else:
        emit(f"  [OK] Recording saved: {output.name}")
    _capture_golden_backup(hostname)


def _wizard_replay(hostname: str, site_url: str, script_name: str) -> None:
    """Replay a previously recorded wizard script."""
    emit(f"── Replaying wizard recording: {script_name} ──")
    script = PROJECT_ROOT / "prototypes" / "cytoscape" / "recordings" / "wizard" / script_name
    if not script.exists():
        raise RuntimeError(f"Recording not found: {script}")
    r = subprocess.run(
        ["node", str(PROJECT_ROOT / "prototypes" / "cytoscape" / "recordings" / "replay_wizard.js"),
         "--script", str(script), "--url", site_url],
        cwd=str(PROJECT_ROOT / "prototypes" / "cytoscape"),
        timeout=600,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Replay failed (exit {r.returncode})")
    emit("  [OK] Wizard replay complete")
    _capture_golden_backup(hostname)


def _wizard_existing(hostname: str, backup_name: str) -> None:
    """Restore from an existing golden backup."""
    emit(f"── Restoring from golden backup: {backup_name} ──")
    from tools.pipeline.stages.wizard_completion.restore_backup import (
        restore_golden_backup,
    )
    restore_golden_backup(hostname, backup_name, str(PROJECT_ROOT), emit)
    emit("  [OK] Golden backup restored")


def _capture_golden_backup(hostname: str) -> None:
    """Capture a golden backup after wizard completion."""
    emit("── Capturing golden backup ──")
    from tools.pipeline.stages.wizard_completion.capture_backup import (
        capture_golden_backup,
    )
    capture_golden_backup(hostname, str(PROJECT_ROOT), emit)


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
    from tools.pipeline.macro.destroy import run
    run(args["hostname"], args["host_cfg"], str(PROJECT_ROOT), emit)


def run_build_template(args: dict) -> None:
    from tools.pipeline.orchestration.build_template import build_template
    build_template(emit)


# ── Dispatch ─────────────────────────────────────────────────────────────────

RUNNERS = {
    "provision": run_provision,
    "provision_generic": run_provision_generic,
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
