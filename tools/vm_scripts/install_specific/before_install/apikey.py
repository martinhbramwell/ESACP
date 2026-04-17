"""Read API key + webserver port from files written by earlier stages."""

import json
import sys
from pathlib import Path


def read_apikey(bd, su):
    """Read key:secret from apikey.sh."""
    apikey_path = Path(bd) / "sites" / su / "private" / "files" / "apikey.sh"
    if not apikey_path.exists():
        print(f"[FAIL] {apikey_path} not found")
        sys.exit(1)
    line = apikey_path.read_text().strip()
    for part in line.replace('"', "=").replace("'", "=").split("="):
        if ":" in part and len(part) > 10:
            return part
    print(f"[FAIL] Could not parse API key from {apikey_path}")
    sys.exit(1)


def read_common_site_config(bd):
    """Read webserver_port from common_site_config.json."""
    csc = Path(bd) / "sites" / "common_site_config.json"
    if csc.exists():
        return json.loads(csc.read_text()).get("webserver_port", "8000")
    return "8000"
