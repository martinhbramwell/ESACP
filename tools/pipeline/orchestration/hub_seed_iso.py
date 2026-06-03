#!/usr/bin/env python3
"""Build hub autoinstall seed ISO from Jinja2 templates + hosts_map.yml (#202).

Hub uses subiquity (autoinstall: schema); targets use cloud-config — the two
formats are structurally incompatible, so this is a separate renderer from
stage_1_vm_creation.seed_iso.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import jinja2

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.host_identity import GUEST_VM_USER, operator_pubkey, virbr0_gateway  # noqa: E402
from tools.pipeline.stages.common.types import Emit  # noqa: E402

_TEMPLATES = Path(__file__).resolve().parents[3] / "platforms" / "kvm" / "cloud-init"


def _render(template_name: str, params: dict) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES)),
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )
    return env.get_template(template_name).render(**params)


def build_hub_seed_iso(hostname: str, virbr0_ip: str, platforms_kvm: str, emit: Emit) -> Path:
    """Render hub autoinstall artifacts and pack them into a cloud-localds ISO."""
    pubkey_path = operator_pubkey()
    if not pubkey_path.exists():
        raise FileNotFoundError(f"Controller pubkey not found: {pubkey_path}")
    params = {
        "hostname": hostname,
        "virbr0_ip": virbr0_ip,
        "gateway": virbr0_gateway(virbr0_ip),
        "controller_pubkey": pubkey_path.read_text().strip(),
        "vm_user": GUEST_VM_USER,
    }
    user_data = _render("hub-autoinstall.user-data.j2", params)
    meta_data = _render("hub-autoinstall.meta-data.j2", params)

    work_dir = Path(tempfile.mkdtemp())
    try:
        (work_dir / "user-data").write_text(user_data)
        (work_dir / "meta-data").write_text(meta_data)
        seed_iso = Path(platforms_kvm) / f"{hostname}-seed.iso"
        r = subprocess.run(
            ["cloud-localds", str(seed_iso),
             str(work_dir / "user-data"), str(work_dir / "meta-data")],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"cloud-localds failed: {r.stderr.strip()}")
        emit(f"  [OK] Hub seed ISO: {seed_iso.name}")
        return seed_iso
    finally:
        shutil.rmtree(work_dir)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Build hub autoinstall seed ISO")
    p.add_argument("hostname"); p.add_argument("virbr0_ip"); p.add_argument("platforms_kvm")
    args = p.parse_args()
    try:
        build_hub_seed_iso(args.hostname, args.virbr0_ip, args.platforms_kvm, print)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); sys.exit(1)
