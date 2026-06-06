"""Enable Server Scripts in common_site_config.json (#626)."""

import json
import sys
from pathlib import Path


def patch_common_site_config(bd):
    """Set server_script_enabled=1 in common_site_config.json.

    The tenant relies on DB-resident Server Scripts (e.g. Sales-Partner
    commission DocType events on Sales Invoice). V16's safe_exec reads this
    flag ONLY from common_site_config (per-site config is ignored); without it
    the restored scripts are inert and any document creation that triggers one
    errors with ServerScriptNotEnabled — substrate would not match production.
    """
    ccfg = Path(bd) / "sites" / "common_site_config.json"
    if not ccfg.exists():
        print(f"[FAIL] {ccfg} not found")
        sys.exit(1)
    cfg = json.loads(ccfg.read_text())
    cfg["server_script_enabled"] = 1
    ccfg.write_text(json.dumps(cfg, indent=1))
    print("  [OK] common_site_config.json patched (server_script_enabled)")
