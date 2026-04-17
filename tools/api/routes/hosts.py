"""Routes: GET /api/hosts, POST /api/hosts/add."""

from __future__ import annotations

from fastapi import APIRouter

from tools.api.helpers import kvm_hosts, last_octet, load_erp_user
from tools.api.routes._hosts_row import build_host_row
from tools.api_models import NewHost
from tools.api.jobs import PROJECT_ROOT
from tools.host_identity import DEFAULT_HYPERVISOR, virbr0_subnet_prefix
from tools.pipeline.orchestration.host_registration import register_host
from tools.pipeline.orchestration.vm_state_query import query_provisioned

router = APIRouter()


@router.get("/api/hosts")
def get_hosts():
    """Return KVM hosts + suggested next-available IPs.

    provisioned=True  → VM has 'Baseline' snapshot (Ansible-provisioned)
    provisioned=False → in hosts_map.yml but VM not found on hypervisor
    provisioned=None  → hypervisor unreachable, state unknown
    """
    hosts_cfg = kvm_hosts()
    erp_user = load_erp_user()

    vm_cache: dict[str | None, dict | None] = {}
    for h in hosts_cfg.values():
        hv = h.get("hypervisor") or None
        if hv not in vm_cache:
            vm_cache[hv] = query_provisioned(hv)

    hosts, wg_octets, vbr_octets = [], [], []
    for name, h in hosts_cfg.items():
        hosts.append(build_host_row(name, h, vm_cache, erp_user))
        if h.get("wg_ip"):
            wg_octets.append(last_octet(h["wg_ip"]))
        if h.get("virbr0_ip"):
            vbr_octets.append(last_octet(h["virbr0_ip"]))

    hypervisors = [h.get("hypervisor") for h in hosts_cfg.values() if h.get("hypervisor")]
    default_hv  = (max(set(hypervisors), key=hypervisors.count)
                   if hypervisors else DEFAULT_HYPERVISOR)

    return {
        "hosts": hosts,
        "suggestions": {
            "wg_ip":      f"10.10.0.{max(wg_octets, default=0) + 1}",
            "virbr0_ip":  f"{virbr0_subnet_prefix()}.{max(vbr_octets, default=9) + 1}",
            "hypervisor": default_hv,
        },
    }


@router.post("/api/hosts/add")
def add_host(host: NewHost):
    """Append a new KVM host to hosts_map.yml and regenerate inventory."""
    register_host(
        hostname=host.hostname, nickname=host.nickname,
        virbr0_ip=host.virbr0_ip, wg_ip=host.wg_ip,
        hypervisor=host.hypervisor, zone=host.zone, vm_role=host.vm_role,
        backend=host.backend, project_root=str(PROJECT_ROOT),
        emit=lambda _m: None,
    )
    return {"ok": True, "hostname": host.hostname}
