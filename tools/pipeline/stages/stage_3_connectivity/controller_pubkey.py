"""SCP controller public key to target VM."""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

CONTROLLER_PUBKEY = Path.home() / ".ssh" / "hasan_mighty.pub"


def _pubkey_installed(config: Config) -> bool:
    """Check if the controller pubkey is already in erpadm's authorized_keys."""
    if not CONTROLLER_PUBKEY.exists():
        return False
    key_data = CONTROLLER_PUBKEY.read_text().strip()
    # Use the key blob (second field) for matching
    parts = key_data.split()
    if len(parts) < 2:
        return False
    r = ssh_run(config,
                f"grep -qF '{parts[1]}' "
                f"/home/{config.erp_user}/.ssh/authorized_keys 2>/dev/null "
                f"&& echo y",
                timeout=10)
    return r.returncode == 0 and "y" in r.stdout


def ensure_controller_pubkey(config: Config, emit: Emit) -> TaskResult:
    """SCP hasan_mighty.pub to /tmp/ on the VM."""
    if not CONTROLLER_PUBKEY.exists():
        return TaskResult(False, False,
                          f"{CONTROLLER_PUBKEY} not found")
    if _pubkey_installed(config):
        return TaskResult(True, False, "Controller pubkey already installed")

    r = scp_to_vm(config, [str(CONTROLLER_PUBKEY)], "/tmp/", timeout=30)
    if r.returncode != 0:
        return TaskResult(False, False,
                          f"SCP pubkey failed: {r.stderr.strip()}")
    return TaskResult(True, True, "hasan_mighty.pub → /tmp/")
