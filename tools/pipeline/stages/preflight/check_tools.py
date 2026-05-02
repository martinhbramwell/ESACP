#!/usr/bin/env python3
"""Check that required tools and Python packages are installed on the controller."""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass
from tools.pipeline.stages.common.types import Emit

# (name, apt-package, kind) — apt-bin/manual via shutil.which; apt-py via importlib.util.find_spec.
REQUIRED_TOOLS = [
    ("virsh",            "libvirt-clients",     "apt-bin"),
    ("virt-install",     "virtinst",            "apt-bin"),
    ("cloud-localds",    "cloud-image-utils",   "apt-bin"),
    ("ansible",          "ansible",             "apt-bin"),
    ("ansible-playbook", "ansible",             "apt-bin"),
    ("wg",               "wireguard-tools",     "apt-bin"),
    ("python3",          "python3",             "apt-bin"),
    ("ssh-keygen",       "openssh-client",      "apt-bin"),
    ("ruamel.yaml",      "python3-ruamel.yaml", "apt-py"),
    ("sops",             "sops",                "manual"),
    ("age",              "age",                 "manual"),
    ("age-keygen",       "age",                 "manual"),
]

MANUAL_INSTALL_HINTS = {
    "sops": (
        "https://github.com/getsops/sops/releases\n"
        "  sudo mv sops-v*.linux.amd64 /usr/local/bin/sops && sudo chmod +x /usr/local/bin/sops"
    ),
    "age": (
        "https://github.com/FiloSottile/age/releases\n"
        "  sudo tar xf age-v*.tar.gz -C /tmp && sudo cp /tmp/age/age /tmp/age/age-keygen /usr/local/bin/"
    ),
}


@dataclass(frozen=True)
class ToolStatus:
    """Result of scanning required tools."""
    tools: list[tuple[str, str, bool]]   # (tool, package, found)
    missing_apt: set[str]
    missing_manual: list[tuple[str, str]]  # (tool, package)


def check_tools(emit: Emit) -> ToolStatus:
    """Scan for each required tool / Python package. Returns structured result."""
    tools: list[tuple[str, str, bool]] = []
    missing_apt: set[str] = set()
    missing_manual: list[tuple[str, str]] = []
    seen: set[str] = set()

    for name, pkg, kind in REQUIRED_TOOLS:
        found = (importlib.util.find_spec(name) is not None
                 if kind == "apt-py" else shutil.which(name) is not None)
        emit(f"  {'[OK]' if found else '[MISSING]'} {name} ({pkg})")
        tools.append((name, pkg, found))
        if not found and pkg not in seen:
            if kind in ("apt-bin", "apt-py"):
                missing_apt.add(pkg)
            else:
                missing_manual.append((name, pkg))
            seen.add(pkg)

    return ToolStatus(tools=tools, missing_apt=missing_apt, missing_manual=missing_manual)
