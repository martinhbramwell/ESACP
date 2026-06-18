"""Packer template build — rsync packer dir to hub, run build.sh, tail log."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.host_identity import (  # noqa: E501
    DEFAULT_HYPERVISOR, GUEST_VM_USER, HUB_VIRBR0_IP, operator_ssh_key)
from tools.pipeline.orchestration.build_template_watch import watch_build
from tools.pipeline.orchestration.memory_guard import check_memory_for_ram
from tools.pipeline.stages.common.types import Emit

# RAM the Packer build VM is launched with. Single source of truth: injected
# into build.sh via --build-ram (build.sh's own 4096 is a hand-run fallback).
# Drives the preflight memory guard (#655 — S110 OOM that killed the hub).
_BUILD_VM_RAM_MIB = 4096

_PLATFORMS_PACKER = Path(__file__).resolve().parents[3] / "platforms" / "packer"
_REMOTE_LOG = "/tmp/packer-build-output.log"
_REMOTE_EXIT = "/tmp/packer-build-output.log.exit"
_SSH_OPTS = [
    "-o", f"ProxyJump={DEFAULT_HYPERVISOR}",
    "-o", "StrictHostKeyChecking=no",
    "-i", operator_ssh_key(),
]
_HUB_SSH = ["ssh", *_SSH_OPTS, f"{GUEST_VM_USER}@{HUB_VIRBR0_IP}"]


def build_template(
    emit: Emit, frappe_branch: str = "version-13", erpnext_branch: str = "version-13",
) -> None:
    emit(f"── ERPNext v{frappe_branch.removeprefix('version-')} template build"
         f" (frappe={frappe_branch}, erpnext={erpnext_branch}) ──")

    emit(f"Checking host RAM for the {_BUILD_VM_RAM_MIB} MiB build VM ...")
    rejection = check_memory_for_ram(
        DEFAULT_HYPERVISOR, _BUILD_VM_RAM_MIB * 1024, "packer-build")
    if rejection:
        raise RuntimeError(f"Build aborted before starting build VM — {rejection}")

    emit("Syncing platforms/packer/ to hub ...")
    rsync = subprocess.run(
        ["rsync", "-az", "--delete",
         "-e", "ssh " + " ".join(_SSH_OPTS),
         str(_PLATFORMS_PACKER) + "/",
         f"{GUEST_VM_USER}@{HUB_VIRBR0_IP}:/opt/esacp/platforms/packer/"],
        capture_output=True, text=True,
    )
    if rsync.returncode != 0:
        raise RuntimeError(f"rsync to hub failed: {rsync.stderr.strip()}")

    emit(f"Connecting to hub ({HUB_VIRBR0_IP} via {DEFAULT_HYPERVISOR}) ...")
    subprocess.run(_HUB_SSH + [f"rm -f {_REMOTE_LOG} {_REMOTE_EXIT}"], capture_output=True)
    start_cmd = (
        f"nohup bash -c 'VM_USER={GUEST_VM_USER} bash /opt/esacp/platforms/packer/build.sh"
        f" --frappe-branch {frappe_branch} --erpnext-branch {erpnext_branch}"
        f" --build-ram {_BUILD_VM_RAM_MIB}"
        f" > {_REMOTE_LOG} 2>&1; echo $? > {_REMOTE_EXIT}'"
        f" > /dev/null 2>&1 & echo $!"
    )
    r = subprocess.run(_HUB_SSH + [start_cmd], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Failed to start build on hub: {r.stderr.strip()}")
    emit(f"Build detached on hub (PID {r.stdout.strip()}) — polling log ...")
    watch_build(_HUB_SSH, _REMOTE_LOG, _REMOTE_EXIT, emit)
