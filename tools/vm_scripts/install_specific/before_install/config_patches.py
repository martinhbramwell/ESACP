"""Patches to site_config.json, Procfile, supervisor.conf; P12 cert verify."""

import json
import sys
from pathlib import Path

from .._env import erp_user, user_home


def patch_site_config(bd, su):
    """Set developer_mode and ce_sri_url in site_config.json."""
    scfg = Path(bd) / "sites" / su / "site_config.json"
    if not scfg.exists():
        print(f"[FAIL] {scfg} not found")
        sys.exit(1)
    cfg = json.loads(scfg.read_text())
    cfg["developer_mode"] = 1
    cfg["ce_sri_url"] = f"http://{su}:5000"
    scfg.write_text(json.dumps(cfg, indent=1))
    print("  [OK] site_config.json patched (developer_mode, ce_sri_url)")


def patch_procfile(bd, cfg):
    """Add ce_sri_svc line to Procfile if missing."""
    procfile = Path(bd) / "Procfile"
    if not procfile.exists():
        print("  [SKIP] Procfile not found")
        return
    locator = cfg.get("nodejs_service", "nodejs_service_locator",
                       fallback="ce_sri_svc")
    content = procfile.read_text()
    if locator in content:
        print("  [SKIP] Procfile already contains ce_sri_svc")
        return
    line = f"\n# {locator}: apps/ce_sri/services/{locator}/go.sh\n"
    procfile.write_text(content + line)
    print("  [OK] Procfile patched")


def patch_supervisor_conf(bd, cfg):
    """Add ce_sri_svc program section to supervisor.conf if missing."""
    conf = Path(bd) / "config" / "supervisor.conf"
    if not conf.exists():
        print("  [SKIP] config/supervisor.conf not found")
        return
    content = conf.read_text()
    if "electronic_vouchers-service" in content:
        print("  [SKIP] supervisor.conf already patched")
        return
    nickname = cfg.get("environment", "local_site_nickname", fallback="GENERIC")
    svc_dir = str(Path(bd) / "apps" / "ce_sri" / "services" / "ce_sri_svc")
    section = (
        f"\n[program:electronic_vouchers-service-{nickname}]\n"
        f"command={svc_dir}/go.sh\n"
        f"priority=3\nautostart=true\nautorestart=true\n"
        f"stdout_logfile={bd}/logs/ce_sri_svc.log\n"
        f"stderr_logfile={bd}/logs/ce_sri_svc.error.log\n"
        f"user={erp_user()}\ndirectory={svc_dir}\n\n"
    )
    if "[program:" in content:
        content = content.replace("[program:", f"{section}[program:", 1)
    else:
        content += section
    conf.write_text(content)
    print("  [OK] supervisor.conf patched")


def verify_p12_cert(cfg):
    """Check the P12 certificate exists."""
    cert_path = cfg.get("electronic_signature", "certificate_location",
                        fallback=str(Path(user_home()) / ".ssh" / "secrets"))
    cert_name = cfg.get("electronic_signature", "sri_p12_cert", fallback="")
    if not cert_name:
        print("  [SKIP] no sri_p12_cert configured")
        return
    full = Path(cert_path) / cert_name
    if full.exists():
        print(f"  [OK] P12 cert found: {full}")
    else:
        print(f"  [WARN] P12 cert not found: {full}")
