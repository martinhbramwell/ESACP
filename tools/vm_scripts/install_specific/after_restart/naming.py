"""SRI-mandated Sales Invoice naming series + shared starting counter."""

import json
from urllib.parse import quote as urlquote
from urllib.request import Request, urlopen

from .._http import api_get, api_post


def get_starting_number():
    """Fetch + increment the shared invoice counter."""
    url = "https://json.extendsclass.com/bin/2ac2f4154c43"
    headers = {"Security-key": "4ba0d416-d78f-11ec-b943-0242ac110002"}
    req = Request(url, headers=headers)
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    starting = data["nxt"]
    body = json.dumps({"nxt": starting + 1}).encode()
    put_req = Request(url, data=body, headers={**headers,
                      "Content-Type": "application/json"}, method="PUT")
    urlopen(put_req, timeout=15)
    print(f"  [OK] Starting number: {starting}")
    return starting


def install_naming_series(rsrc_url, mthd_url, api_key, test_suc_pde, starting):
    srvr_url = f"{mthd_url}/runserverobj"

    ns_url = f"{rsrc_url}/{urlquote('Naming Series')}/{urlquote('Naming Series')}"
    resp = api_get(ns_url, api_key)
    modified = resp["data"]["modified"]

    series = test_suc_pde
    api_post(srvr_url, api_key, {
        "method": "update_series",
        "docs": {
            "name": "Naming Series", "prefix": "001-001-.#########",
            "doctype": "Naming Series",
            "select_doc_for_series": "Sales Invoice",
            "set_options": f"001-001-.#########\n{series}-.#########",
            "modified": modified,
        },
    })
    print(f"  [OK] Naming series '{series}' created")

    api_post(srvr_url, api_key, {
        "method": "update_series_start",
        "docs": {
            "name": "Naming Series", "doctype": "Naming Series",
            "select_doc_for_series": "Sales Invoice",
            "prefix": f"{series}-.#########",
            "current_value": starting,
            "modified": modified,
        },
    })
    print(f"  [OK] Series start value set to {starting}")
