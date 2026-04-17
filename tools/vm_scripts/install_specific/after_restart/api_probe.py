"""API reachability probe — must succeed before any other after-restart step."""

import sys
from urllib.error import HTTPError, URLError

from .._http import api_get


def confirm_api_connection(rsrc_url, api_key):
    """GET /api/resource/Company — verify ERPNext API is reachable."""
    url = f"{rsrc_url}/Company"
    try:
        resp = api_get(url, api_key)
        name = resp["data"][0]["name"]
        print(f"  [OK] ERPNext API connected — company: {name}")
        return True
    except (URLError, HTTPError, KeyError, IndexError) as e:
        print(f"[FAIL] ERPNext API unreachable: {e}")
        sys.exit(1)
