"""Read + delete the undifferentiated ERPNext template artifact on a hypervisor."""

from __future__ import annotations

import json
import subprocess

METADATA_DIR = "/home/hasan/esacp-packer-output"

# Default frappe major when a caller does not specify one (preserves the
# pre-#631 single-template behaviour). Templates are named per-major so the
# v13/v15/v16 lines coexist (dual-template; ESACP #631).
DEFAULT_MAJOR = 13


def metadata_basename(major: int = DEFAULT_MAJOR) -> str:
    """Filename of the per-major template metadata JSON (no directory)."""
    return f"erpnext-v{major}-latest.json"


def metadata_path(major: int = DEFAULT_MAJOR) -> str:
    """Absolute path of the per-major template metadata JSON on the hypervisor."""
    return f"{METADATA_DIR}/{metadata_basename(major)}"


def read_template_metadata(hypervisor: str, major: int = DEFAULT_MAJOR) -> dict:
    """Return template metadata or {image: None, state: "not_built"}."""
    try:
        r = subprocess.run(
            ["ssh", hypervisor, f"cat {metadata_path(major)} 2>/dev/null"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception:
        pass
    return {"image": None, "built_at": None, "state": "not_built"}


def delete_template_metadata(hypervisor: str, major: int = DEFAULT_MAJOR) -> None:
    """Delete the template qcow2 (libvirt pool) + its metadata JSON.

    Raises RuntimeError if the metadata JSON cannot be removed.
    """
    meta = read_template_metadata(hypervisor, major)
    image = meta.get("image")
    if image:
        subprocess.run(
            ["ssh", hypervisor,
             f"virsh --connect qemu:///system vol-delete --pool esacp "
             f"'{image}' 2>/dev/null || true"],
            capture_output=True, text=True, timeout=30,
        )
    r = subprocess.run(
        ["ssh", hypervisor, f"rm -f {metadata_path(major)}"],
        capture_output=True, text=True, timeout=10,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"Failed to delete template metadata: {r.stderr.strip()}")
