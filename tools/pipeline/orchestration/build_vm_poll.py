"""Polling helpers for VM autoinstall builds — SSH and poweroff detection."""

from __future__ import annotations

import time

from tools.pipeline.stages.common.known_hosts import tcp_port_open
from tools.pipeline.stages.common.types import Emit

from .hypervisor_helpers import start_vm, tcp_probe_via_hypervisor, vm_state


def ensure_running_and_ssh(
    vm: str, virbr0_ip: str, hypervisor: str | None, hyp_user: str, emit: Emit,
) -> None:
    """Poll SSH/poweroff, restart after autoinstall, poll SSH again."""
    state = vm_state(vm, hypervisor)
    if not state:
        raise RuntimeError(f"Cannot determine VM state for {vm}")
    if state not in ("running", "shut off"):
        raise RuntimeError(f"Unexpected VM state: {state!r}")
    if state == "shut off":
        start_vm(vm, hypervisor)

    powered_off = _poll_ssh_or_poweroff(vm, virbr0_ip, hypervisor, hyp_user, emit)
    if powered_off:
        emit(f"  Autoinstall complete — restarting {vm}")
        start_vm(vm, hypervisor)
        _poll_ssh(virbr0_ip, hypervisor, hyp_user, emit, timeout=300, interval=5)


def _poll_ssh_or_poweroff(
    vm: str, virbr0_ip: str, hypervisor: str | None, hyp_user: str, emit: Emit,
    timeout: int = 1800, interval: int = 10,
) -> bool:
    """Poll until SSH opens or VM powers off. Returns True if powered off."""
    start = time.time()
    while time.time() - start < timeout:
        if vm_state(vm, hypervisor) == "shut off":
            return True
        if hypervisor:
            if tcp_probe_via_hypervisor(virbr0_ip, hypervisor, hyp_user):
                return False
        elif tcp_port_open(virbr0_ip):
            return False
        elapsed = int(time.time() - start)
        if elapsed % 60 < interval:
            emit(f"  Waiting for SSH or autoinstall completion... ({elapsed}s)")
        time.sleep(interval)
    raise RuntimeError(f"Timed out after {timeout // 60} min waiting for {vm}")


def _poll_ssh(
    virbr0_ip: str, hypervisor: str | None, hyp_user: str, emit: Emit,
    timeout: int = 300, interval: int = 5,
) -> None:
    """Poll until SSH port opens after reboot."""
    start = time.time()
    while time.time() - start < timeout:
        if hypervisor:
            if tcp_probe_via_hypervisor(virbr0_ip, hypervisor, hyp_user):
                emit(f"  SSH up after reboot ({int(time.time() - start)}s)")
                return
        elif tcp_port_open(virbr0_ip):
            emit(f"  SSH up after reboot ({int(time.time() - start)}s)")
            return
        time.sleep(interval)
    raise RuntimeError(f"SSH did not come up within {timeout // 60} min after reboot")
