"""Route: GET /api/health/{hostname}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from tools.api.helpers import get_host_or_404
from tools.api.jobs import PROJECT_ROOT
from tools.pipeline.orchestration.host_health import check_health
from tools.secrets import load_build_secrets

router = APIRouter()


@router.get("/api/health/{hostname}")
def get_health(hostname: str):
    """Quick SSH health check — {web, app, db} each 'green'|'amber'|'red'."""
    host_cfg = get_host_or_404(hostname)
    wg_ip = host_cfg.get("wg_ip", "")
    if not wg_ip:
        raise HTTPException(400, f"No WireGuard IP for '{hostname}'")

    db_pwd = load_build_secrets(str(PROJECT_ROOT))["db_root_pwd"]
    return check_health(wg_ip, db_pwd)
