"""Environment context: KVM (toshiba hypervisor).

Holds constants and paths specific to the KVM/libvirt environment
that are not per-VM (those go in Config).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class KvmEnv:
    """Immutable KVM environment context."""

    hypervisor_alias: str = "toshiba"
    hypervisor_user: str = "hasan"
    images_dir: str = "/mnt/esacp-disk/var/lib/libvirt/images"
    pool: str = "esacp"

    @property
    def metadata_dir(self) -> str:
        return f"/home/{self.hypervisor_user}/esacp-packer-output"

    # Paths resolved at construction from project root
    project_root: str = ""
    keys_sops: str = ""
    platforms_kvm: str = ""

    @classmethod
    def from_project_root(cls, project_root: str | Path) -> KvmEnv:
        root = Path(project_root)
        return cls(
            project_root=str(root),
            keys_sops=str(root / "config" / "wireguard" / "keys.sops.yml"),
            platforms_kvm=str(root / "platforms" / "kvm"),
        )
