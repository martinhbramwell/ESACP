"""RAM guard — rejects a VM start that would exceed safe hypervisor memory.

``check_memory`` returns a human-readable rejection string if starting
*hostname* on *hypervisor* would leave the host with less than
``_HOST_RAM_RESERVE_KIB`` free; returns ``None`` when it is safe to proceed.
"""

from __future__ import annotations

from tools.pipeline.orchestration.virsh import virsh_ssh

_HOST_RAM_RESERVE_KIB = 2 * 1024 * 1024   # 2 GiB reserve for the host OS


def check_memory(hypervisor: str, hostname: str) -> str | None:
    r = virsh_ssh(hypervisor, "nodeinfo")
    if r.returncode != 0:
        return f"Cannot query hypervisor memory: {r.stderr.strip()}"
    host_mem_kib = _parse_nodeinfo_memory(r.stdout)
    if host_mem_kib == 0:
        return "Could not parse host memory from virsh nodeinfo"

    r_list = virsh_ssh(hypervisor, "list --name")
    if r_list.returncode != 0:
        return f"Cannot list running VMs: {r_list.stderr.strip()}"
    running_vms = [v.strip() for v in r_list.stdout.splitlines() if v.strip()]
    used_kib = sum(_dominfo_max_memory(hypervisor, vm) for vm in running_vms)

    r_target = virsh_ssh(hypervisor, f"dominfo {hostname}")
    if r_target.returncode != 0:
        return f"Cannot query VM config for '{hostname}': {r_target.stderr.strip()}"
    target_kib = _extract_max_memory(r_target.stdout)

    needed = used_kib + target_kib
    available = host_mem_kib - _HOST_RAM_RESERVE_KIB
    if needed > available:
        return _format_rejection(
            hostname, target_kib, used_kib, host_mem_kib, running_vms,
        )
    return None


def _parse_nodeinfo_memory(text: str) -> int:
    for line in text.splitlines():
        if line.startswith("Memory size:"):
            return int(line.split(":")[1].strip().split()[0])
    return 0


def _dominfo_max_memory(hypervisor: str, vm: str) -> int:
    r = virsh_ssh(hypervisor, f"dominfo {vm}")
    if r.returncode != 0:
        return 0
    return _extract_max_memory(r.stdout)


def _extract_max_memory(dominfo_stdout: str) -> int:
    for line in dominfo_stdout.splitlines():
        if line.startswith("Max memory:"):
            return int(line.split(":")[1].strip().split()[0])
    return 0


def _format_rejection(
    hostname: str, target_kib: int, used_kib: int,
    host_mem_kib: int, running_vms: list[str],
) -> str:
    reserve_mb = _HOST_RAM_RESERVE_KIB // 1024
    running_list = ", ".join(running_vms) if running_vms else "(none)"
    return (
        f"Not enough memory on hypervisor — "
        f"{target_kib // 1024} MiB needed for {hostname}, "
        f"{used_kib // 1024} MiB already used by [{running_list}], "
        f"host has {host_mem_kib // 1024} MiB total "
        f"({reserve_mb} MiB reserved for host OS). "
        f"Shut down another VM first."
    )
