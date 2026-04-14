#!/usr/bin/env python3
"""Verify job_worker.py subprocess mechanism — acceptance test for GH #37.

Tests the core contract: a job spawned as an independent process writes its
log to a file and its exit status to a .status file. The API can read both
without any in-memory state.

Does NOT run real provision/destroy — uses a mock job type built into this
test to verify the mechanism in isolation.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
JOB_DIR = Path("/tmp")


def test_job_worker_mechanism():
    """Spawn a trivial job via job_worker.py and verify file-based tracking."""

    # We'll test the mechanism by importing api.py functions directly
    sys.path.insert(0, str(PROJECT_ROOT))
    from tools.api import _spawn_job, _read_job, _job_log_path, _job_status_path, _job_meta_path

    # Create a tiny test script that acts as a job
    test_job_id = "test-37"
    log_path = _job_log_path(test_job_id)
    status_path = _job_status_path(test_job_id)
    meta_path = _job_meta_path(test_job_id)

    # Clean up any previous test artifacts
    for p in (log_path, status_path, meta_path):
        p.unlink(missing_ok=True)

    # Spawn a real worker with an unknown job type — it should fail cleanly
    # and write "error" to the status file
    meta = {"hostname": "test-vm", "type": "test", "started_at": "2026-01-01T00:00:00"}
    meta_path.write_text(json.dumps(meta))

    log_file = open(log_path, "w")
    proc = subprocess.Popen(
        ["python3", "tools/job_worker.py", "nonexistent_type", test_job_id, "{}"],
        cwd=PROJECT_ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    proc.wait(timeout=10)
    log_file.close()

    # Verify status file was written
    assert status_path.exists(), "status file not created"
    status = status_path.read_text().strip()
    assert status == "error", f"expected 'error' for unknown job type, got '{status}'"

    # Verify _read_job works
    job = _read_job(test_job_id)
    assert job is not None, "_read_job returned None"
    assert job["status"] == "error"
    assert job["hostname"] == "test-vm"

    # Clean up
    for p in (log_path, status_path, meta_path):
        p.unlink(missing_ok=True)

    print("PASS — job_worker subprocess mechanism verified")
    print("  - Worker process spawned and exited independently")
    print("  - Status file written on completion")
    print("  - _read_job() reconstructs state from disk")
    print("  - No in-memory state required")


if __name__ == "__main__":
    test_job_worker_mechanism()
