"""RAM guard — rejects a VM start that would exceed safe hypervisor memory.

Both entry points return a human-readable rejection string when starting the
VM would leave the host with less than ``_HOST_RAM_RESERVE_KIB`` free, or
``None`` when it is safe to proceed. Pure parsing/formatting lives in
``memory_guard_parse``.
"""

from __future__ import annotations

from tools.pipeline.orchestration.memory_guard_parse import (
    extract_max_memory, format_rejection, parse_nodeinfo_memory)
from tools.pipeline.orchestration.virsh import virsh_ssh

_HOST_RAM_RESERVE_KIB = 2 * 1024 * 1024   # 2 GiB reserve for the host OS


def check_memory(hypervisor: str, hostname: str) -> str | None:
    """Guard starting the already-defined domain *hostname* (reads its
    configured Max memory). Returns a rejection string or ``None``."""
    r_target = virsh_ssh(hypervisor, f"dominfo {hostname}")
    if r_target.returncode != 0:
        return f"Cannot query VM config for '{hostname}': {r_target.stderr.strip()}"
    return check_memory_for_ram(hypervisor, extract_max_memory(r_target.stdout), hostname)


def check_memory_for_ram(hypervisor: str, needed_kib: int, label: str) -> str | None:
    """Guard starting a VM needing *needed_kib* RAM, identified by *label*.

    Used by the template-build path, where the build VM is not yet defined
    so there is no domain to query — the caller supplies the RAM directly.
    """
    r = virsh_ssh(hypervisor, "nodeinfo")
    if r.returncode != 0:
        return f"Cannot query hypervisor memory: {r.stderr.strip()}"
    host_mem_kib = parse_nodeinfo_memory(r.stdout)
    if host_mem_kib == 0:
        return "Could not parse host memory from virsh nodeinfo"

    r_list = virsh_ssh(hypervisor, "list --name")
    if r_list.returncode != 0:
        return f"Cannot list running VMs: {r_list.stderr.strip()}"
    running_vms = [v.strip() for v in r_list.stdout.splitlines() if v.strip()]
    used_kib = sum(_dominfo_max_memory(hypervisor, vm) for vm in running_vms)

    if used_kib + needed_kib > host_mem_kib - _HOST_RAM_RESERVE_KIB:
        return format_rejection(
            label, needed_kib, used_kib, host_mem_kib,
            _HOST_RAM_RESERVE_KIB, running_vms,
        )
    return None


def _dominfo_max_memory(hypervisor: str, vm: str) -> int:
    r = virsh_ssh(hypervisor, f"dominfo {vm}")
    if r.returncode != 0:
        return 0
    return extract_max_memory(r.stdout)
