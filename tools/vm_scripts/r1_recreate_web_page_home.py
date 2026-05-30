#!/usr/bin/env python3
"""r1_recreate_web_page_home.py — Recreate Web Page 'home' from tabSingles.

V13->V16 post-migrate fix R1 (ESACP#486, #480 child). The Homepage DocType
was upstream-deleted in V14+; its singleton row in tabSingles survives the
V13->V16 migrate with no V16 render target. Salvages company/tag_line/
description at runtime and INSERTs a Web Page with route='home'.
Idempotent; runtime-reads salvaged values (never hardcoded).
"""
import argparse
import html
from pathlib import Path

import frappe

HOME_ROUTE = "home"
TEMPLATE = (
    '<div class="container py-5">\n  <div class="row">\n'
    '    <div class="col-md-12 text-center">\n'
    '      <h1 class="display-4">{company}</h1>\n'
    '      <h3 class="text-muted my-4">{tag_line}</h3>\n'
    '      <p class="lead">{description}</p>\n    </div>\n  </div>\n</div>'
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--bench-dir", required=True)
    args = parser.parse_args()

    frappe.init(site=args.site, sites_path=str(Path(args.bench_dir) / "sites"))
    frappe.connect()

    existing = frappe.db.exists("Web Page", {"route": HOME_ROUTE})
    if existing:
        print(f"  [OK] Web Page route='{HOME_ROUTE}' already present "
              f"(name={existing})")
        print("  [PROBE] home=present")
        frappe.destroy()
        return

    rows = frappe.db.sql(
        "SELECT field, value FROM tabSingles WHERE doctype = %s",
        ("Homepage",),
    )
    salvaged = {field: value for field, value in rows if value}
    company = salvaged.get("company", "")
    if not company:
        print("  [SKIP] no Homepage singleton with 'company' field")
        print("  [PROBE] homepage=absent")
        frappe.destroy()
        return

    main_section = TEMPLATE.format(
        company=html.escape(company),
        tag_line=html.escape(salvaged.get("tag_line", "")),
        description=html.escape(salvaged.get("description", "")),
    )
    doc = frappe.get_doc({
        "doctype": "Web Page",
        "title": company,
        "route": HOME_ROUTE,
        "published": 1,
        # "Rich Text" renders main_section; "Page Builder" => blank (#456)
        "content_type": "Rich Text",
        "main_section": main_section,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()

    print(f"  [OK] Web Page '{doc.name}' route='{HOME_ROUTE}' "
          f"(was absent, now 1) salvaged company='{company}'")
    print("  [PROBE] home=created")
    frappe.destroy()


if __name__ == "__main__":
    main()
