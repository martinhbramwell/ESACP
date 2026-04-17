"""HTTP helpers — stdlib urllib only, no `requests` dependency.

URLs use localhost (gunicorn binds 127.0.0.1); site name is sent as a
`Host` header for Frappe multi-tenant routing. _HOST_SITE is set by
after_restart._load_globals() before any API call.
"""

import json
from urllib.request import Request, urlopen


_HOST_SITE = None


def set_host_site(site):
    global _HOST_SITE
    _HOST_SITE = site


def _http(method, url, headers, data=None):
    """Low-level HTTP helper. Returns parsed JSON or raises."""
    body = data.encode("utf-8") if data else None
    req = Request(url, data=body, headers=headers, method=method)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _auth_headers(api_key):
    hdrs = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"token {api_key}",
    }
    if _HOST_SITE:
        hdrs["Host"] = _HOST_SITE
    return hdrs


def api_get(url, api_key):
    return _http("GET", url, _auth_headers(api_key))


def api_post(url, api_key, payload):
    return _http("POST", url, _auth_headers(api_key), json.dumps(payload))


def api_put(url, api_key, payload):
    return _http("PUT", url, _auth_headers(api_key), json.dumps(payload))


def api_delete(url, api_key):
    return _http("DELETE", url, _auth_headers(api_key))
