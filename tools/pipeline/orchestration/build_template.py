"""Packer template build — rsync packer dir to hub, run build.sh, tail log."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from tools.host_identity import (  # noqa: E501
    DEFAULT_HYPERVISOR, GUEST_VM_USER, HUB_VIRBR0_IP, operator_ssh_key)
from tools.pipeline.stages.common.types import Emit

_PLATFORMS_PACKER = Path(__file__).resolve().parents[3] / "platforms" / "packer"
_REMOTE_LOG = "/tmp/packer-build-output.log"
_REMOTE_EXIT = "/tmp/packer-build-output.log.exit"
_SSH_OPTS = [
    "-o", f"ProxyJump={DEFAULT_HYPERVISOR}",
    "-o", "StrictHostKeyChecking=no",
    "-i", operator_ssh_key(),
]
_HUB_SSH = ["ssh", *_SSH_OPTS, f"{GUEST_VM_USER}@{HUB_VIRBR0_IP}"]


def build_template(emit: Emit) -> None:
    emit("── ERPNext v13 template build ──")
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
        f" > {_REMOTE_LOG} 2>&1; echo $? > {_REMOTE_EXIT}'"
        f" > /dev/null 2>&1 & echo $!"
    )
    r = subprocess.run(_HUB_SSH + [start_cmd], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Failed to start build on hub: {r.stderr.strip()}")
    emit(f"Build detached on hub (PID {r.stdout.strip()}) — polling log ...")

    offset = 0
    while True:
        time.sleep(5)
        offset = _flush_log(offset, emit)
        r = subprocess.run(
            _HUB_SSH + [f"cat {_REMOTE_EXIT} 2>/dev/null || echo -1"],
            capture_output=True, text=True,
        )
        exit_str = r.stdout.strip()
        if exit_str == "-1":
            continue
        _flush_log(offset, emit)
        exit_code = int(exit_str) if exit_str.isdigit() else 1
        if exit_code != 0:
            raise RuntimeError(f"build.sh exited with code {exit_code}")
        emit("── Build complete — new image ready on toshiba ──")
        return


def _flush_log(offset: int, emit: Emit) -> int:
    r = subprocess.run(
        _HUB_SSH + [f"tail -c +{offset + 1} {_REMOTE_LOG} 2>/dev/null || true"],
        capture_output=True, text=True,
    )
    if r.stdout:
        for line in r.stdout.splitlines():
            if line.strip():
                emit(line)
        offset += len(r.stdout.encode("utf-8"))
    return offset
