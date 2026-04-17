"""Read + delete the undifferentiated ERPNext template artifact on a hypervisor."""

from __future__ import annotations

import json
import subprocess

METADATA_DIR = "/home/hasan/esacp-packer-output"
METADATA_FILE = f"{METADATA_DIR}/erpnext-v13-latest.json"


def read_template_metadata(hypervisor: str) -> dict:
    """Return template metadata or {image: None, state: "not_built"}."""
    try:
        r = subprocess.run(
            ["ssh", hypervisor, f"cat {METADATA_FILE} 2>/dev/null"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception:
        pass
    return {"image": None, "built_at": None, "state": "not_built"}


def delete_template_metadata(hypervisor: str) -> None:
    """Delete the template qcow2 (libvirt pool) + its metadata JSON.

    Raises RuntimeError if the metadata JSON cannot be removed.
    """
    meta = read_template_metadata(hypervisor)
    image = meta.get("image")
    if image:
        subprocess.run(
            ["ssh", hypervisor,
             f"virsh --connect qemu:///system vol-delete --pool esacp "
             f"'{image}' 2>/dev/null || true"],
            capture_output=True, text=True, timeout=30,
        )
    r = subprocess.run(
        ["ssh", hypervisor, f"rm -f {METADATA_FILE}"],
        capture_output=True, text=True, timeout=10,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"Failed to delete template metadata: {r.stderr.strip()}")
