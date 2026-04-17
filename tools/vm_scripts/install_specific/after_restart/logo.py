"""Upload company logo, set Website Settings + Company branding."""

import base64
from pathlib import Path
from urllib.parse import quote as urlquote

from .._http import api_post, api_put


def install_company_logo(rsrc_url, mthd_url, api_key, cfg):
    logo_dir = cfg.get("environment", "company_logo_location", fallback="")
    logo_file = cfg.get("environment", "company_logo", fallback="")
    if not logo_dir or not logo_file:
        print(f"  [SKIP] Logo config missing (dir={logo_dir!r}, file={logo_file!r})")
        return
    logo_path = Path(logo_dir) / logo_file
    if not logo_path.exists():
        print(f"  [SKIP] Logo not found at {logo_path}")
        return

    logo_name = logo_path.name
    b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

    attach_url = f"{mthd_url}/frappe.client.attach_file"
    api_post(attach_url, api_key, {
        "doctype": "Website Settings",
        "docname": "Website Settings",
        "filename": logo_name,
        "decode_base64": 1,
        "filedata": b64,
    })
    print(f"  [OK] Logo uploaded: {logo_name}")

    ws_url = f"{rsrc_url}/{urlquote('Website Settings')}/{urlquote('Website Settings')}"
    api_put(ws_url, api_key, {
        "banner_image": f"/files/{logo_name}",
        "brand_html": f'<img src="/files/{logo_name}" style="max-height: 80px;">',
    })

    company = cfg.get("environment", "pretty_company_name", fallback="")
    if company:
        co_url = f"{rsrc_url}/Company/{urlquote(company)}"
        api_put(co_url, api_key, {"company_logo": f"/files/{logo_name}"})
    print("  [OK] Website branding installed")
