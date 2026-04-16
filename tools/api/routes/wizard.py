"""Routes: GET /api/wizard/recordings, /api/wizard/backups."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from tools.api.jobs import PROJECT_ROOT

router = APIRouter()

RECORDINGS_DIR     = PROJECT_ROOT / "prototypes" / "cytoscape" / "recordings" / "wizard"
GOLDEN_BACKUPS_DIR = PROJECT_ROOT / "platforms" / "kvm" / "golden_backups"


@router.get("/api/wizard/recordings")
def list_wizard_recordings():
    """List available Playwright wizard recordings."""
    if not RECORDINGS_DIR.exists():
        return {"recordings": []}
    out = []
    for f in sorted(RECORDINGS_DIR.glob("*.spec.js"), reverse=True):
        stat = f.stat()
        out.append({
            "name": f.name,
            "size_kb": round(stat.st_size / 1024, 1),
            "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
        })
    return {"recordings": out}


@router.get("/api/wizard/backups")
def list_wizard_backups():
    """List available golden backup files."""
    if not GOLDEN_BACKUPS_DIR.exists():
        return {"backups": []}
    out = []
    for f in sorted(GOLDEN_BACKUPS_DIR.glob("*.tgz"), reverse=True):
        stat = f.stat()
        out.append({
            "filename": f.name,
            "size_mb": round(stat.st_size / (1024 * 1024), 1),
            "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
        })
    return {"backups": out}
