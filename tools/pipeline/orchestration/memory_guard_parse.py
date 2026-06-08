"""Pure parsing + rejection-message formatting for the RAM guard (#655).

Split out of ``memory_guard`` to keep that module under the pipeline size
cap; these functions touch no I/O and are directly unit-testable.
"""

from __future__ import annotations


def parse_nodeinfo_memory(text: str) -> int:
    """Total host memory (KiB) from ``virsh nodeinfo`` output; 0 if absent."""
    for line in text.splitlines():
        if line.startswith("Memory size:"):
            return int(line.split(":")[1].strip().split()[0])
    return 0


def extract_max_memory(dominfo_stdout: str) -> int:
    """A domain's configured Max memory (KiB) from ``virsh dominfo``; 0 if absent."""
    for line in dominfo_stdout.splitlines():
        if line.startswith("Max memory:"):
            return int(line.split(":")[1].strip().split()[0])
    return 0


def format_rejection(
    label: str, needed_kib: int, used_kib: int,
    host_mem_kib: int, reserve_kib: int, running_vms: list[str],
) -> str:
    running_list = ", ".join(running_vms) if running_vms else "(none)"
    return (
        f"Not enough memory on hypervisor — "
        f"{needed_kib // 1024} MiB needed for {label}, "
        f"{used_kib // 1024} MiB already used by [{running_list}], "
        f"host has {host_mem_kib // 1024} MiB total "
        f"({reserve_kib // 1024} MiB reserved for host OS). "
        f"Shut down another VM first."
    )
