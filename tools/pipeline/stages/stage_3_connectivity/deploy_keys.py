"""SCP GitHub deploy keys + passphrase to target VM."""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

DEPLOY_KEY_DIR = Path.home() / ".ssh"
DEPLOY_KEYS = {
    "ce_sri":        DEPLOY_KEY_DIR / "you_gh_ce_sri",
    "ce_sri_svc":    DEPLOY_KEY_DIR / "you_gh_ce_sri_svc",
    "route_planner": DEPLOY_KEY_DIR / "you_gh_route_planner",
}
DEPLOY_KEY_PASSPHRASE = DEPLOY_KEY_DIR / "you_gh.txt"


def _keys_present_on_vm(config: Config) -> bool:
    r = ssh_run(config,
                f"test -f /home/{config.erp_user}/.ssh/you_gh_ce_sri && echo y",
                timeout=10)
    return r.returncode == 0 and "y" in r.stdout


def ensure_deploy_keys(config: Config, emit: Emit) -> TaskResult:
    """SCP deploy keys + passphrase to /tmp/ on the VM."""
    if _keys_present_on_vm(config):
        return TaskResult(True, False, "Deploy keys already present")

    files: list[str] = []
    for name, path in DEPLOY_KEYS.items():
        if path.exists():
            files.append(str(path))
        else:
            emit(f"  [WARN] {path.name} missing — {name} clone will fail")
    if DEPLOY_KEY_PASSPHRASE.exists():
        files.append(str(DEPLOY_KEY_PASSPHRASE))
    else:
        emit("  [WARN] passphrase missing — private repo clones will fail")

    if not files:
        return TaskResult(False, False, "No deploy key files found")

    r = scp_to_vm(config, files, "/tmp/", timeout=30)
    if r.returncode != 0:
        return TaskResult(False, False,
                          f"SCP deploy keys failed: {r.stderr.strip()}")
    return TaskResult(True, True, f"{len(files)} deploy key files → /tmp/")
