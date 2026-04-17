"""Install the Sales_Invoice-Form Client Script."""

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote as urlquote

from .._http import api_delete, api_post


def install_custom_scripts(bd, rsrc_url, api_key):
    """DELETE + POST the Sales_Invoice-Form Client Script."""
    dt = "Sales Invoice"
    record = f"{dt}-Form"
    script_type = "Client Script"
    api_url = f"{rsrc_url}/{urlquote(script_type)}"
    encoded_record = urlquote(record)

    js_path = Path(bd) / "apps" / "ce_sri" / "ce_sri" / "frags" / "Sales_Invoice-Form.js"
    if not js_path.exists():
        print(f"  [SKIP] {js_path} not found")
        return

    script_text = js_path.read_text()
    try:
        api_delete(f"{api_url}/{encoded_record}", api_key)
        print(f"  [OK] Deleted previous Client Script '{record}'")
    except (URLError, HTTPError):
        print(f"  [INFO] No previous Client Script '{record}' to delete")

    payload = {"dt": dt, "enabled": 1, "script": script_text, "doctype": script_type}
    resp = api_post(api_url, api_key, payload)
    print(f"  [OK] Created Client Script '{resp['data']['name']}'")
