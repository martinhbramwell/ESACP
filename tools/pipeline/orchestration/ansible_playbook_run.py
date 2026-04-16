"""Stream ``ansible-playbook`` output through the shared filter.

Returns True on success. Used by ``ansible_provision`` and any other dispatcher
that needs a filtered Ansible run from Python.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tools.pipeline.stages.common.ansible_output import filter_ansible_line
from tools.pipeline.stages.common.types import Emit


def run_playbook(
    vm: str, ansible_dir: Path, ssh_key: str, emit: Emit, check: bool = False,
) -> bool:
    cmd = ["ansible-playbook", "-i", "inventory/kvm.yml",
           "site-kvm.yml", "--limit", vm]
    if check:
        cmd.append("--check")
        emit("[cyan]ℹ️  Check mode — no changes will be made[/cyan]")

    env = {**os.environ,
           "ANSIBLE_CONFIG": str(ansible_dir / "ansible.cfg"),
           "ANSIBLE_PRIVATE_KEY_FILE": ssh_key}
    state: dict = {"current_task": "", "in_recap": False}
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env=env, cwd=str(ansible_dir), bufsize=1,
    )
    for raw in proc.stdout:
        line = filter_ansible_line(raw.rstrip(), state)
        if line is not None:
            emit(line)
    proc.wait()
    if proc.returncode != 0:
        emit(f"[red]❌  Ansible failed (exit {proc.returncode})[/red]")
        return False
    return True
