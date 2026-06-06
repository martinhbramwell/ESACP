"""Routes: GET /api/template/status, DELETE /api/template, POST /api/build/template."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from tools.api.jobs import JOB_DIR, read_job, spawn_job
from tools.api_models import BuildTemplateReq
from tools.host_identity import DEFAULT_HYPERVISOR
from tools.pipeline.orchestration.template_metadata import (
    delete_template_metadata, read_template_metadata,
)

router = APIRouter()


@router.get("/api/template/status")
def get_template_status():
    """Return template metadata, or {image: None, state: 'not_built'}."""
    return read_template_metadata(DEFAULT_HYPERVISOR)


@router.delete("/api/template")
def delete_template():
    """Delete the undifferentiated ERPNext template artifact on the hypervisor."""
    try:
        delete_template_metadata(DEFAULT_HYPERVISOR)
    except RuntimeError as exc:
        raise HTTPException(500, str(exc))
    except Exception as exc:
        raise HTTPException(500, str(exc))
    return {"ok": True, "message": "Template artifact deleted — state reset to not_built"}


@router.post("/api/build/template")
def start_build_template(req: BuildTemplateReq = BuildTemplateReq()):
    """Start a background Packer build on the hub (one at a time).

    Body selects the frappe/erpnext line (defaults to the v13 line, preserving
    pre-#631 behaviour); the major names the resulting template.
    """
    for meta_file in JOB_DIR.glob("esacp-job-*.meta"):
        jid = meta_file.stem.replace("esacp-job-", "")
        j = read_job(jid)
        if j and j.get("type") == "build_template" and j["status"] == "running":
            raise HTTPException(409, "A template build is already in progress")

    job_id = str(uuid.uuid4())[:8]
    spawn_job(
        "build_template", job_id,
        {"frappe_branch": req.frappe_branch, "erpnext_branch": req.erpnext_branch},
        hostname="template",
    )
    return {"job_id": job_id}
