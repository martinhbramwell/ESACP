"""Route: POST /api/destroy/{hostname}."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from tools.api.helpers import get_host_or_404
from tools.api.jobs import spawn_job

router = APIRouter()


@router.post("/api/destroy/{hostname}")
def start_destroy(hostname: str):
    """Full teardown: WG peer, snapshots, VM, hosts_map, SOPS keys, inventory."""
    host_cfg = get_host_or_404(hostname)
    if host_cfg.get("wg_role") == "hub":
        raise HTTPException(
            400, f"Cannot destroy hub node '{hostname}' — this would break the entire mesh")

    job_id = str(uuid.uuid4())[:8]
    spawn_job("destroy", job_id, {
        "hostname": hostname, "host_cfg": host_cfg,
    }, hostname=hostname)
    return {"job_id": job_id}
