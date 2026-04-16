#!/usr/bin/env python3
"""Check that required CLI tools are installed on the controller."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from tools.pipeline.stages.common.types import Emit, TaskResult

# (tool, apt-package, install-method: "apt" | "manual")
REQUIRED_TOOLS = [
    ("virsh",            "libvirt-clients",   "apt"),
    ("virt-install",     "virtinst",          "apt"),
    ("cloud-localds",    "cloud-image-utils", "apt"),
    ("ansible",          "ansible",           "apt"),
    ("ansible-playbook", "ansible",           "apt"),
    ("wg",               "wireguard-tools",   "apt"),
    ("python3",          "python3",           "apt"),
    ("ssh-keygen",       "openssh-client",    "apt"),
    ("sops",             "sops",              "manual"),
    ("age",              "age",               "manual"),
    ("age-keygen",       "age",               "manual"),
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
    """Scan PATH for each required tool. Returns structured result."""
    tools: list[tuple[str, str, bool]] = []
    missing_apt: set[str] = set()
    missing_manual: list[tuple[str, str]] = []
    seen_packages: set[str] = set()

    for tool, pkg, method in REQUIRED_TOOLS:
        found = shutil.which(tool) is not None
        tag = "[OK]" if found else "[MISSING]"
        emit(f"  {tag} {tool} ({pkg})")
        tools.append((tool, pkg, found))
        if not found and pkg not in seen_packages:
            if method == "apt":
                missing_apt.add(pkg)
            else:
                missing_manual.append((tool, pkg))
            seen_packages.add(pkg)

    return ToolStatus(
        tools=tools,
        missing_apt=missing_apt,
        missing_manual=missing_manual,
    )
