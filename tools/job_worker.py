#!/usr/bin/env python3
"""Standalone job worker — spawned by ``tools/api`` as an independent OS process.

Thin dispatch: parses argv + JSON args, looks up a runner, writes status. Job
implementations live in ``tools/pipeline/`` (see CLAUDE.md anti-spiral rules).

Usage: ``python3 tools/job_worker.py <job_type> <job_id> '<json_args>'``

Runs as a child process so it survives uvicorn restarts (GH #37).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def emit(line: str):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {line}", flush=True)


def run_provision(args: dict) -> None:
    from tools.host_identity import ZONE_DOMAINS
    from tools.pipeline.macro.provision import run
    run(hostname=args["hostname"], virbr0_ip=args["virbr0_ip"],
        project_root=str(PROJECT_ROOT), emit=emit,
        cleanup_cfg=args.get("cleanup_cfg"))
    domain = ZONE_DOMAINS.get(args.get("zone", "development"), "iridium.blue")
    emit(f"── Provision complete — ERPNext at https://{args['hostname']}.{domain} ──")


def run_provision_generic(args: dict) -> None:
    from tools.host_identity import ZONE_DOMAINS
    from tools.pipeline.macro.provision_generic import run
    from tools.pipeline.orchestration.wizard_run import run_wizard
    run(hostname=args["hostname"], virbr0_ip=args["virbr0_ip"],
        project_root=str(PROJECT_ROOT), emit=emit,
        cleanup_cfg=args.get("cleanup_cfg"))
    domain = ZONE_DOMAINS.get(args.get("zone", "development"), "iridium.blue")
    site_url = f"https://{args['hostname']}.{domain}"
    run_wizard(mode=args.get("wizard_mode", "record"),
               hostname=args["hostname"], site_url=site_url,
               arg=args.get("wizard_arg", ""), project_root=PROJECT_ROOT, emit=emit)
    emit(f"── Generic provision complete — {site_url} ──")


def run_refresh(args: dict) -> None:
    from tools.pipeline.macro.refresh import run
    run(hostname=args["hostname"], host_cfg=args["host_cfg"],
        project_root=str(PROJECT_ROOT), emit=emit,
        force=args.get("force", False))
    emit("── Refresh complete ──")


def run_destroy(args: dict) -> None:
    from tools.pipeline.macro.destroy import run
    run(args["hostname"], args["host_cfg"], str(PROJECT_ROOT), emit)


def run_build_template(_args: dict) -> None:
    from tools.pipeline.orchestration.build_template import build_template
    build_template(emit)


RUNNERS = {"provision": run_provision, "provision_generic": run_provision_generic,
           "refresh": run_refresh, "destroy": run_destroy,
           "build_template": run_build_template}


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <job_type> <job_id> '<json_args>'", file=sys.stderr)
        sys.exit(2)
    job_type, job_id, args = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
    status_file = Path(f"/tmp/esacp-job-{job_id}.status")
    runner = RUNNERS.get(job_type)
    if not runner:
        print(f"[ERROR] Unknown job type: {job_type}", file=sys.stderr)
        status_file.write_text("error"); sys.exit(1)
    try:
        runner(args); status_file.write_text("done")
    except Exception as exc:
        emit(f"[ERROR] {exc}"); status_file.write_text("error"); sys.exit(1)


if __name__ == "__main__":
    main()
