#!/usr/bin/env python3
"""r3_disable_irs_1099_pf.py — Disable orphan IRS 1099 Form Print Format.

V13->V16 post-migrate fix R3 (ESACP#498, #480 child). Jinja template
upstream-deleted long before V16; row persists on restored production
DBs. Sets disabled=1 (reversible). Idempotent; safe if record absent.
"""
import argparse
import json
import os
import subprocess
import sys

PRINT_FORMAT_NAME = "IRS 1099 Form"


def get_db_credentials(bench_dir, site):
    cfg_path = os.path.join(bench_dir, "sites", site, "site_config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)
    return cfg["db_name"], cfg.get("db_password", "")


def run_sql(db_name, db_password, sql):
    result = subprocess.run(
        ["mysql", "-AD", db_name, f"-u{db_name}", f"-p{db_password}",
         "-N", "-B", "-e", sql],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench-dir", required=True)
    parser.add_argument("--site", required=True)
    args = parser.parse_args()

    db_name, db_password = get_db_credentials(args.bench_dir, args.site)

    current = run_sql(
        db_name, db_password,
        f"SELECT disabled FROM `tabPrint Format` "
        f"WHERE name='{PRINT_FORMAT_NAME}';",
    )

    if current == "":
        print(f"  [SKIP] Print Format '{PRINT_FORMAT_NAME}' not present")
        print("  [PROBE] disabled=absent")
        return

    if current == "1":
        print(f"  [OK] Print Format '{PRINT_FORMAT_NAME}' already disabled")
        print("  [PROBE] disabled=1")
        return

    run_sql(
        db_name, db_password,
        f"UPDATE `tabPrint Format` SET disabled=1, "
        f"modified=NOW(), modified_by='Administrator' "
        f"WHERE name='{PRINT_FORMAT_NAME}';",
    )
    print(f"  [OK] Print Format '{PRINT_FORMAT_NAME}' disabled "
          f"(was {current}, now 1)")
    print("  [PROBE] disabled=1")


if __name__ == "__main__":
    main()
