"""File-based job tracking — spawn + read (GH #37).

Jobs run as independent OS processes (``tools/job_worker.py``). Metadata + log
+ status are kept in ``/tmp/esacp-job-*.{meta,log,status}`` so the API is fully
stateless across uvicorn restarts.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

JOB_DIR = Path("/tmp")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _job_meta_path(jid: str)   -> Path: return JOB_DIR / f"esacp-job-{jid}.meta"
def _job_log_path(jid: str)    -> Path: return JOB_DIR / f"esacp-job-{jid}.log"
def _job_status_path(jid: str) -> Path: return JOB_DIR / f"esacp-job-{jid}.status"


def spawn_job(
    job_type: str, job_id: str, args: dict, hostname: str,
    job_type_label: str | None = None,
) -> None:
    """Spawn an independent job_worker.py process. Survives uvicorn restarts."""
    meta = {
        "hostname":   hostname,
        "type":       job_type_label or job_type,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    _job_meta_path(job_id).write_text(json.dumps(meta))

    log_file = open(_job_log_path(job_id), "w")
    subprocess.Popen(
        ["python3", "tools/job_worker.py", job_type, job_id, json.dumps(args)],
        cwd=PROJECT_ROOT, stdout=log_file, stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def read_job(job_id: str) -> dict | None:
    """Return job state from disk, or None if no such job."""
    meta_path = _job_meta_path(job_id)
    if not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text())
    log_path = _job_log_path(job_id)
    log_lines = log_path.read_text().splitlines() if log_path.exists() else []
    status_path = _job_status_path(job_id)
    status = status_path.read_text().strip() if status_path.exists() else "running"
    return {
        "status":   status,
        "log":      log_lines,
        "hostname": meta.get("hostname", ""),
        "type":     meta.get("type", ""),
    }
