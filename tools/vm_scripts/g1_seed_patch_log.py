#!/usr/bin/env python3
"""
g1_seed_patch_log.py — Seed tabPatch Log with entries for patches that crash
on a restored production DB (missing tables, schema mismatches).

Must run BEFORE the first `bench migrate` so Frappe skips these patches.

Usage (run as root, before bench migrate):
    python3 /tmp/vm_scripts/g1_seed_patch_log.py \
        --bench-dir /home/erpadm/frappe-bench-D1IRBL \
        --site dev01.iridium.blue
"""
import argparse
import json
import os
import subprocess
import sys

# Patches that crash on restored production DBs.
# Each entry: (patch_name_with_comment, reason)
PATCHES_TO_SKIP = [
    (
        "frappe.patches.v12_0.delete_duplicate_indexes  # 2022-12-15",
        "queries session_status table which doesn't exist in production backup",
    ),
    (
        "erpnext.patches.v16_0.make_workstation_operating_components #1",
        "ESACP#444: upstream doc.save() on submitted Workstation halts V15→V16",
    ),
]


def get_db_credentials(bench_dir, site):
    """Read db_name and db_password from site_config.json."""
    cfg_path = os.path.join(bench_dir, "sites", site, "site_config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)
    return cfg["db_name"], cfg.get("db_password", "")


def run_sql(db_name, db_password, sql):
    """Run a SQL statement against the site DB."""
    result = subprocess.run(
        ["mysql", "-AD", db_name, f"-u{db_name}", f"-p{db_password}", "-e", sql],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def seed_patch_log(db_name, db_password):
    """Insert tabPatch Log entries for patches that must be skipped."""
    for patch_name, reason in PATCHES_TO_SKIP:
        run_sql(
            db_name, db_password,
            "INSERT IGNORE INTO `tabPatch Log` "
            "(name, patch, creation, modified, owner, modified_by) VALUES "
            f"('{patch_name}', '{patch_name}', "
            "NOW(), NOW(), 'Administrator', 'Administrator');",
        )
        print(f"  [OK] Seeded: {patch_name}")
        print(f"        Reason: {reason}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench-dir", required=True)
    parser.add_argument("--site", required=True)
    args = parser.parse_args()

    db_name, db_password = get_db_credentials(args.bench_dir, args.site)
    seed_patch_log(db_name, db_password)


if __name__ == "__main__":
    main()
