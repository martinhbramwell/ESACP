#!/usr/bin/env python3
"""server_scripts_enable_626.py — ensure server_script_enabled=1 (#626).

V13->V15+ post-migrate fixup. The tenant relies on DB-resident Server Scripts
(e.g. Sales-Partner commission DocType events on Sales Invoice). V15/V16
safe_exec reads this flag ONLY from common_site_config (per-site config is
ignored); without it the restored scripts are inert and any document creation
that triggers one errors with ServerScriptNotEnabled — the substrate would not
match production. Bench-level (applies to every site on the bench). Idempotent;
emits the shared [PROBE] contract so the fixups runner can verify it.

This is the post-migrate counterpart of the provision-time setter
(install_specific/before_install/common_site_config_patch.py); the staged
upgrade leg re-asserts it so the migrated bench is self-contained, not reliant
on a provision-time side effect surviving `bench migrate`.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench-dir", required=True)
    parser.add_argument("--site", required=True)  # uniform invocation; unused here
    args = parser.parse_args()

    ccfg = Path(args.bench_dir) / "sites" / "common_site_config.json"
    if not ccfg.exists():
        print(f"  [FAIL] {ccfg} not found", file=sys.stderr)
        sys.exit(1)

    cfg = json.loads(ccfg.read_text())
    current = cfg.get("server_script_enabled")
    if current == 1:
        print("  [OK] server_script_enabled already 1")
        print("  [PROBE] server_scripts=enabled")
        return

    cfg["server_script_enabled"] = 1
    ccfg.write_text(json.dumps(cfg, indent=1))
    prior = "absent" if current is None else current
    print(f"  [OK] server_script_enabled set (was {prior}, now 1)")
    print("  [PROBE] server_scripts=enabled")


if __name__ == "__main__":
    main()
