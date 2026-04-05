#!/usr/bin/env python3
"""
g2_clear_fixture_custom_fields.py — Clear fixture-defined Custom Fields from
the restored production DB so bench migrate reimports them from app fixtures.

Problem: when a production DB is restored, its tabCustom Field records carry
insert_after values that match the production layout (Developer Mode edits).
bench migrate won't overwrite them if the DB record's `modified` is >= the
fixture file's `modified`. Deleting the records lets migrate recreate them
from the fixture with correct positioning.

Usage (run as ERP_USER from bench dir):
    python3 /tmp/vm_scripts/g2_clear_fixture_custom_fields.py \
        --bench-dir /home/erpadm/frappe-bench-D1IRBL \
        --site dev01.iridium.blue
"""
import argparse
import json
import os
import subprocess
import sys


def get_db_credentials(bench_dir, site):
    """Read db_name and db_password from site_config.json."""
    cfg_path = os.path.join(bench_dir, "sites", site, "site_config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)
    return cfg["db_name"], cfg.get("db_password", "")


def collect_fixture_custom_fields(bench_dir):
    """Scan all installed apps for Custom Field fixtures; return list of dicts."""
    apps_txt = os.path.join(bench_dir, "sites", "apps.txt")
    with open(apps_txt) as f:
        apps = [line.strip() for line in f if line.strip()]

    seen = set()
    records = []
    for app in apps:
        fixture_path = os.path.join(
            bench_dir, "apps", app, app, "fixtures", "custom_field.json"
        )
        if not os.path.exists(fixture_path):
            continue
        with open(fixture_path) as f:
            data = json.load(f)
        for rec in data:
            name = rec.get("name", "")
            if rec.get("doctype") == "Custom Field" and name and name not in seen:
                seen.add(name)
                records.append({
                    "name": name,
                    "dt": rec.get("dt", ""),
                    "fieldname": rec.get("fieldname", ""),
                })
    return records


def run_sql(db_name, db_password, sql):
    """Run a SQL statement against the site DB."""
    result = subprocess.run(
        ["mysql", "-AD", db_name, f"-u{db_name}", f"-p{db_password}", "-e", sql],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def clear_fields(db_name, db_password, fixture_records):
    """Delete Custom Field records AND colliding DocField entries from the DB."""
    if not fixture_records:
        print("  No fixture-defined Custom Fields found — nothing to clear")
        return

    names = {r["name"] for r in fixture_records}
    dt_fn_pairs = [(r["dt"], r["fieldname"]) for r in fixture_records]

    # 1. Delete fixture Custom Fields so migrate reimports with correct values
    quoted = ", ".join(f"'{n}'" for n in sorted(names))
    run_sql(db_name, db_password,
            f"DELETE FROM `tabCustom Field` WHERE name IN ({quoted});")
    print(f"  [OK] Cleared {len(names)} Custom Fields from tabCustom Field")

    # 2. Delete colliding DocField entries (production Developer Mode edits
    #    stored as standard fields — block fixture Custom Field insertion)
    for dt, fn in dt_fn_pairs:
        run_sql(db_name, db_password,
                f"DELETE FROM `tabDocField` WHERE parent='{dt}' "
                f"AND fieldname='{fn}';")
    print(f"  [OK] Cleared colliding DocField entries ({len(dt_fn_pairs)} checked)")

    # 3. Seed tabPatch Log for delete_duplicate_indexes (comment-format mismatch
    #    causes re-run → crash on missing performance_schema tables)
    run_sql(db_name, db_password,
            "INSERT IGNORE INTO `tabPatch Log` "
            "(name, patch, creation, modified, owner, modified_by) VALUES "
            "('frappe.patches.v12_0.delete_duplicate_indexes  # 2022-12-15', "
            "'frappe.patches.v12_0.delete_duplicate_indexes  # 2022-12-15', "
            "NOW(), NOW(), 'Administrator', 'Administrator');")
    print("  [OK] Seeded tabPatch Log for delete_duplicate_indexes")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench-dir", required=True)
    parser.add_argument("--site", required=True)
    args = parser.parse_args()

    db_name, db_password = get_db_credentials(args.bench_dir, args.site)
    records = collect_fixture_custom_fields(args.bench_dir)
    clear_fields(db_name, db_password, records)


if __name__ == "__main__":
    main()
