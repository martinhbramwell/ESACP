"""after_restart — API work (gunicorn must be running).

URLs use localhost (gunicorn binds 127.0.0.1); site name is sent as
`Host` header via _HOST_SITE for Frappe multi-tenant routing.
"""

import configparser
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

from .._env import bench_dir, site_url
from .._http import set_host_site
from .api_probe import confirm_api_connection
from .logo import install_company_logo
from .naming import get_starting_number, install_naming_series
from .scripts import install_custom_scripts
from .test_data import install_test_data


def _load_globals(bd, su):
    cfg = configparser.ConfigParser()
    conf_path = Path(bd) / "config" / "ce_sri.conf"
    if not conf_path.exists():
        print(f"[FAIL] {conf_path} not found — run before-install first")
        sys.exit(1)
    cfg.read(conf_path)
    site = cfg.get("erpnext_api", "local_site", fallback=su)
    port = cfg.get("erpnext_api", "webserver_port", fallback="8000")
    key = cfg.get("erpnext_api", "erpnext_api_key")
    set_host_site(site)
    base = f"http://localhost:{port}/api"
    return cfg, key, f"{base}/resource", f"{base}/method"


def cmd_after_restart():
    bd, su = bench_dir(), site_url()
    print("=== after-restart: API configuration ===")

    cfg, api_key, rsrc_url, mthd_url = _load_globals(bd, su)
    test_suc_pde = "001-004"

    confirm_api_connection(rsrc_url, api_key)
    install_custom_scripts(bd, rsrc_url, api_key)
    install_company_logo(rsrc_url, mthd_url, api_key, cfg)

    try:
        starting = get_starting_number()
    except (URLError, HTTPError) as e:
        print(f"  [WARN] Could not reach starting number service: {e}")
        starting = 0

    install_naming_series(rsrc_url, mthd_url, api_key, test_suc_pde, starting)
    install_test_data(rsrc_url, api_key, test_suc_pde)
    print("=== after-restart complete ===")
