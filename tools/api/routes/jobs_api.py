"""Routes: GET /api/jobs, GET /api/jobs/{job_id}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from tools.api.jobs import JOB_DIR, read_job

router = APIRouter()


@router.get("/api/jobs")
def list_jobs():
    """Return all jobs (reads /tmp/esacp-job-*.meta — survives restarts)."""
    result = {}
    for meta_file in JOB_DIR.glob("esacp-job-*.meta"):
        jid = meta_file.stem.replace("esacp-job-", "")
        j = read_job(jid)
        if j:
            result[jid] = {"status": j["status"], "hostname": j["hostname"]}
    return result


@router.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Poll a job's status + log (from disk; survives uvicorn restarts)."""
    j = read_job(job_id)
    if j is None:
        raise HTTPException(404, "job not found")
    return {"status": j["status"], "log": j["log"], "hostname": j["hostname"]}
