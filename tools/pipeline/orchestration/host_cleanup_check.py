#!/usr/bin/env python3
"""Decide whether an already-registered host needs pre-provision cleanup.

Used by the provisioning endpoints: if a host is in hosts_map.yml but the
hypervisor shows a partial/in-flight VM without a Baseline snapshot, the
caller must clean up residue (storage, WG peer, etc.) before re-provisioning.
If the VM is fully provisioned, the caller must reject with HTTP 409.
"""

from __future__ import annotations

from typing import Callable

from tools.pipeline.orchestration.vm_state_query import query_provisioned

Emit = Callable[[str], None]


class HostAlreadyProvisionedError(Exception):
    """VM exists and has Baseline snapshot. Maps to HTTP 409."""


def check_cleanup_needed(
    *, hostname: str, kvm_hosts: dict, emit: Emit,
) -> tuple[bool, dict | None]:
    """Return ``(already_registered, cleanup_cfg)``.

    * ``already_registered`` — host is present in ``kvm_hosts`` (hosts_map.yml).
    * ``cleanup_cfg`` — ``host_cfg`` dict if residue cleanup is needed before
      rebuilding, otherwise ``None``.

    Raises ``HostAlreadyProvisionedError`` if the hypervisor reports the VM
    as provisioned (Baseline snapshot present).
    """
    if hostname not in kvm_hosts:
        return False, None

    host_cfg = kvm_hosts[hostname]
    vm_map = query_provisioned(host_cfg.get("hypervisor"))
    vm_info = vm_map.get(hostname, {}) if vm_map else {}

    if vm_info.get("provisioned") is True:
        raise HostAlreadyProvisionedError(
            f"'{hostname}' is already provisioned — Destroy it first"
        )

    needs_cleanup = (
        vm_map is not None and hostname in vm_map and not vm_info.get("provisioned")
    )
    if needs_cleanup:
        emit(f"  [NOTE] {hostname} residue detected — will clean before rebuild")
    return True, (host_cfg if needs_cleanup else None)
