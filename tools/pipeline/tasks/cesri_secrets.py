"""Decrypt + patch ce_sri secrets, SCP to target VM."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.pipeline.ssh import scp_to_vm
from tools.pipeline.types import Config, Emit, TaskResult

CE_SRI_SECRETS_DIR = Path.home() / ".ssh" / "secrets"
CE_SRI_P12_CERT = CE_SRI_SECRETS_DIR / (
    "PRESIDENTE_DANIEL_LEONARD_WILD_STAPEL_1709470171_171224162014.p12"
)
LOGICHEM_DIR = Path.home() / "projects" / "Logichem"
CE_SRI_LOGO = LOGICHEM_DIR / "ce_sri" / "example_srvr_files" / "docType_Logo.png"
CE_SRI_SOCIALS = LOGICHEM_DIR / "ce_sri" / "example_srvr_files" / "socials_google.json"


def _collect_static_files(emit: Emit) -> list[str]:
    files: list[str] = []
    for label, path in [("P12 cert", CE_SRI_P12_CERT),
                        ("company logo", CE_SRI_LOGO),
                        ("socials_google.json", CE_SRI_SOCIALS)]:
        if path.exists():
            files.append(str(path))
        else:
            emit(f"  [WARN] {label} not found at {path}")
    return files


def _decrypt_and_patch(config: Config) -> Path | None:
    sops_path = Path(config.project_root) / "config" / "ce_sri_parms.sops.json"
    if not sops_path.exists():
        return None
    r = subprocess.run(
        ["sops", "-d", str(sops_path)],
        capture_output=True, text=True, timeout=15,
    )
    if r.returncode != 0:
        raise RuntimeError(f"sops decrypt failed: {r.stderr.strip()}")
    parms = json.loads(r.stdout)
    parms["erpnext_api"]["local_site"] = config.site_url
    parms["erpnext_api"]["api_protocol"] = "https"
    parms["erpnext_api"]["api_port"] = "443"
    cert_dir = f"/home/{config.erp_user}/.ssh/secrets"
    parms["electronic_signature"]["certificate_location"] = cert_dir
    parms["electronic_signature"]["sri_p12_cert"] = CE_SRI_P12_CERT.name
    parms["environment"]["local_site_nickname"] = config.nickname
    parms["environment"]["company_logo_location"] = cert_dir
    parms["revenue_service"]["test_or_production_mode"] = "1"
    out = Path("/tmp") / f"ce_sri_parms_{config.nickname}.json"
    out.write_text(json.dumps(parms, indent=2))
    return out


def ensure_cesri_secrets(config: Config, emit: Emit) -> TaskResult:
    """SOPS-decrypt, patch per-VM, SCP secrets to /tmp/."""
    files = _collect_static_files(emit)
    try:
        patched = _decrypt_and_patch(config)
    except RuntimeError as exc:
        return TaskResult(False, False, str(exc))
    if patched:
        files.append(str(patched))
    else:
        emit("  [WARN] ce_sri_parms.sops.json not found — skipping parms")
    if not files:
        return TaskResult(True, False, "No ce_sri files to send")
    r = scp_to_vm(config, files, "/tmp/", timeout=30)
    if r.returncode != 0:
        return TaskResult(False, False,
                          f"SCP ce_sri secrets failed: {r.stderr.strip()}")
    return TaskResult(True, True, f"{len(files)} ce_sri secret files → /tmp/")
