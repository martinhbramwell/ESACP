"""H4a: Clear stale __Auth entries and regenerate Administrator API keys.

Runs inside the bench virtualenv on the target VM.
Usage:
    $BENCH_DIR/env/bin/python /tmp/vm_scripts/h4a_apikeys.py \
        --site dev02.iridium.blue \
        --bench-dir /home/erpadm/frappe-bench-D2IRBL
"""

import argparse
from pathlib import Path

import frappe
from frappe.core.doctype.user.user import generate_keys


def main():
    parser = argparse.ArgumentParser(description="Clear __Auth + regenerate API keys")
    parser.add_argument("--site", required=True, help="Frappe site name")
    parser.add_argument("--bench-dir", required=True, help="Bench directory path")
    args = parser.parse_args()

    sites_path = str(Path(args.bench_dir) / "sites")
    frappe.init(site=args.site, sites_path=sites_path)
    frappe.connect()

    count = frappe.db.sql("SELECT COUNT(*) FROM `__Auth`")[0][0]
    frappe.db.sql("DELETE FROM `__Auth`")
    frappe.db.commit()
    print(f"  Cleared {count} stale __Auth entries")

    result = generate_keys("Administrator")
    api_secret = result["api_secret"]
    api_key = frappe.db.get_value("User", "Administrator", "api_key")
    frappe.db.commit()
    print(f"  API_KEY={api_key}")

    apikey_path = Path(args.bench_dir) / "sites" / args.site / "private" / "files" / "apikey.sh"
    apikey_path.write_text(
        f'API_KEY="{api_key}"\n'
        f'API_SECRET="{api_secret}"\n'
        f'KEYS="{api_key}:{api_secret}"\n'
    )
    print("  [OK] apikey.sh written")

    frappe.destroy()


if __name__ == "__main__":
    main()
