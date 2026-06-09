"""Shared helpers for CLI subcommand modules.

Presentation-only: config loaders, banners, confirmation prompts. No subprocess
calls — infrastructure work belongs in ``tools/pipeline/``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.panel import Panel

from tools.host_identity import guest_vm_user, operator_ssh_key

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ANSIBLE_DIR  = PROJECT_ROOT / "ansible"

console = Console()


def banner(msg: str) -> None:
    console.print(Panel(f"[bold]{msg}[/bold]", expand=False))


def confirm(msg: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    console.print(f"[bold yellow]{msg}[/bold yellow] [{hint}]: ", end="")
    resp = sys.stdin.readline().strip().lower()
    if resp == "":
        return default
    return resp in ("y", "yes")


def load_group_vars(name: str) -> dict:
    path = ANSIBLE_DIR / "group_vars" / f"{name}.yml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_config() -> dict:
    with open(PROJECT_ROOT / "hosts_map.yml") as f:
        hosts = yaml.safe_load(f)
    return {"hosts": hosts, "all": load_group_vars("all"), "kvm": load_group_vars("kvm")}


def kvm_hosts(config: dict) -> dict:
    return config["hosts"].get("groups", {}).get("kvm", {})


def controller_info(config: dict) -> dict:
    return config["hosts"].get("groups", {}).get("controller", {}).get("local", {})


def hub_vm(config: dict) -> Optional[str]:
    for name, info in kvm_hosts(config).items():
        if info.get("wg_role") == "hub":
            return name
    return None


def ssh_key_path() -> str:
    """Operator key path via operator_ssh_key."""
    return operator_ssh_key()


def vm_user(config: dict) -> str:
    """Guest VM user via guest_vm_user (config kept for call-site compat)."""
    return guest_vm_user()
