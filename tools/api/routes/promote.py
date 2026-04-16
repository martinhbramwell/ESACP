"""Route: POST /api/promote (stub)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("/api/promote")
def promote_staging():
    """Stub: initiate Staging → Production promotion.

    Full implementation: validate staging state, send Telegram approval request
    to configured approvers, await 2 confirmations, then execute DNS flip via
    Cloudflare API. Deferred pending v13 staging.
    """
    return {"ok": True, "message": (
        "Promotion initiated — awaiting Telegram approval "
        "(stub; DNS flip not yet implemented)"
    )}
