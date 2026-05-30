"""Routes: POST /api/provision/erpnext, /api/provision/erpnext-generic, /api/refresh/{host}."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from tools.api.helpers import get_host_or_404, kvm_hosts
from tools.api.jobs import PROJECT_ROOT, spawn_job
from tools.api_models import NewErpnextVM, NewGenericErpnextVM
from tools.pipeline.orchestration.host_cleanup_check import check_cleanup_needed
from tools.pipeline.orchestration.host_registration import register_host

router = APIRouter()


def _ensure_registered(vm, kvm: dict) -> dict | None:
    already, cleanup_cfg = check_cleanup_needed(
        hostname=vm.hostname, kvm_hosts=kvm, emit=lambda _m: None)
    if not already:
        register_host(
            hostname=vm.hostname, nickname=vm.nickname,
            virbr0_ip=vm.virbr0_ip, wg_ip=vm.wg_ip,
            hypervisor=vm.hypervisor, zone=vm.zone, vm_role=vm.vm_role,
            backend="kvm", project_root=str(PROJECT_ROOT), emit=lambda _m: None)
    return cleanup_cfg


@router.post("/api/provision/erpnext")
def start_provision_erpnext(vm: NewErpnextVM):
    """Register a VM (if new) and start a template-based provisioning job."""
    cleanup_cfg = _ensure_registered(vm, kvm_hosts())
    job_id = str(uuid.uuid4())[:8]
    spawn_job("provision", job_id, {
        "hostname": vm.hostname, "virbr0_ip": vm.virbr0_ip,
        "cleanup_cfg": cleanup_cfg,
    }, hostname=vm.hostname, job_type_label="provision_erpnext")
    return {"job_id": job_id, "hostname": vm.hostname}


@router.post("/api/provision/erpnext-generic")
def start_provision_erpnext_generic(vm: NewGenericErpnextVM):
    """Register + start a generic ERPNext provisioning job (no prod data)."""
    if vm.wizard_mode not in ("record", "replay", "existing"):
        raise HTTPException(400,
            f"wizard_mode must be record, replay, or existing (got '{vm.wizard_mode}')")
    if vm.wizard_mode == "replay" and not vm.wizard_arg:
        raise HTTPException(400, "wizard_mode=replay requires wizard_arg (recording script name)")
    if vm.wizard_mode == "existing" and not vm.wizard_arg:
        raise HTTPException(400, "wizard_mode=existing requires wizard_arg (backup filename)")

    cleanup_cfg = _ensure_registered(vm, kvm_hosts())
    job_id = str(uuid.uuid4())[:8]
    spawn_job("provision_generic", job_id, {
        "hostname": vm.hostname, "virbr0_ip": vm.virbr0_ip, "zone": vm.zone,
        "cleanup_cfg": cleanup_cfg,
        "wizard_mode": vm.wizard_mode, "wizard_arg": vm.wizard_arg,
    }, hostname=vm.hostname, job_type_label="provision_generic")
    return {"job_id": job_id, "hostname": vm.hostname}


@router.post("/api/refresh/{hostname}")
def start_refresh(hostname: str, force: bool = False):
    """Re-run stages 3–9 on an existing VM via WireGuard.

    ``force=True`` bypasses per-stage presence-based verify-skip gates so
    template-only edits actually redeploy (#492).
    """
    host_cfg = get_host_or_404(hostname)
    if not host_cfg.get("wg_ip"):
        raise HTTPException(400, f"No WireGuard IP configured for '{hostname}'")

    job_id = str(uuid.uuid4())[:8]
    spawn_job("refresh", job_id, {
        "hostname": hostname, "host_cfg": host_cfg, "force": force,
    }, hostname=hostname)
    return {"job_id": job_id}
