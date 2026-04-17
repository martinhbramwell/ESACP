"""Routes: POST /api/vm/{hostname}/start|stop|reboot."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from tools.api.helpers import get_host_or_404
from tools.pipeline.orchestration import memory_guard, vm_power

router = APIRouter()


def _resolve(hostname: str) -> tuple[dict, str]:
    host_cfg = get_host_or_404(hostname)
    hypervisor = host_cfg.get("hypervisor")
    if not hypervisor:
        raise HTTPException(400, f"No hypervisor configured for '{hostname}'")
    return host_cfg, hypervisor


@router.post("/api/vm/{hostname}/start")
def vm_start(hostname: str):
    """Start a shut-off VM, with a memory guard to prevent OOM."""
    _, hypervisor = _resolve(hostname)
    mem_err = memory_guard.check_memory(hypervisor, hostname)
    if mem_err:
        raise HTTPException(409, mem_err)
    try:
        msg = vm_power.start(hypervisor, hostname, lambda _: None)
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    return {"ok": True, "message": msg}


@router.post("/api/vm/{hostname}/stop")
def vm_stop(hostname: str):
    """Graceful shutdown (virsh shutdown); rejects hub nodes."""
    host_cfg, hypervisor = _resolve(hostname)
    try:
        msg = vm_power.stop(hypervisor, hostname, lambda _: None,
                            is_hub=host_cfg.get("wg_role") == "hub")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    return {"ok": True, "message": msg}


@router.post("/api/vm/{hostname}/reboot")
def vm_reboot(hostname: str):
    """Reboot a running VM (virsh reboot)."""
    _, hypervisor = _resolve(hostname)
    try:
        msg = vm_power.reboot(hypervisor, hostname, lambda _: None)
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    return {"ok": True, "message": msg}
