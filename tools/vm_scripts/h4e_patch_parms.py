"""H4e: Inject API key into ce_sri_parms.json before .env generation.

Reads apikey.sh (written by H4a) to get the freshly generated API_KEY and
API_SECRET, then patches erpnext_api.erpnext_api_key in ce_sri_parms.json.

After this script runs, UPDATE_SRI_SERVICE_PARAMETERS.py can generate
all .env variants without any sed patching.

Usage (on target VM):
    python3 /tmp/vm_scripts/h4e_patch_parms.py \
        --apikey-sh /home/erpadm/frappe-bench/sites/dev02.iridium.blue/private/files/apikey.sh \
        --parms /home/erpadm/.ssh/secrets/ce_sri_parms.json
"""

import argparse
import json
import re
from pathlib import Path


def parse_apikey_sh(apikey_path: Path) -> tuple[str, str]:
    """Extract API_KEY and API_SECRET from apikey.sh."""
    text = apikey_path.read_text()
    key_match = re.search(r'^API_KEY="(.+)"', text, re.MULTILINE)
    secret_match = re.search(r'^API_SECRET="(.+)"', text, re.MULTILINE)
    if not key_match or not secret_match:
        raise ValueError(f"Cannot parse API_KEY/API_SECRET from {apikey_path}")
    return key_match.group(1), secret_match.group(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apikey-sh", required=True,
                        help="Path to apikey.sh (written by H4a)")
    parser.add_argument("--parms", required=True,
                        help="Path to ce_sri_parms.json")
    args = parser.parse_args()

    apikey_path = Path(args.apikey_sh)
    parms_path = Path(args.parms)

    if not apikey_path.exists():
        raise FileNotFoundError(f"apikey.sh not found: {apikey_path}")
    if not parms_path.exists():
        raise FileNotFoundError(f"ce_sri_parms.json not found: {parms_path}")

    api_key, api_secret = parse_apikey_sh(apikey_path)
    print(f"  Read API key from {apikey_path}")

    parms = json.loads(parms_path.read_text())
    parms["erpnext_api"]["erpnext_api_key"] = f"{api_key}:{api_secret}"
    parms_path.write_text(json.dumps(parms, indent=2) + "\n")
    print(f"  Patched erpnext_api_key in {parms_path}")


if __name__ == "__main__":
    main()
