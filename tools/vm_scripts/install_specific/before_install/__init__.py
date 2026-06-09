"""before_install — File patches (no gunicorn required).

Runs after H4a/H3/H4b/H4c: writes ce_sri.conf, patches site_config.json,
nginx.conf, Procfile, supervisor.conf.
"""

import json
from pathlib import Path

from .._env import bench_dir, site_url, user_home
from .apikey import read_apikey, read_common_site_config
from .cesri_conf import write_cesri_conf
from .common_site_config_patch import patch_common_site_config
from .config_patches import (patch_procfile, patch_site_config,
                             patch_supervisor_conf, verify_p12_cert)
from .nginx_config import patch_nginx_conf


def cmd_before_install():
    bd, su = bench_dir(), site_url()
    print("=== before-install: file patches ===")

    api_key = read_apikey(bd, su)
    port = read_common_site_config(bd)

    parms_path = Path(user_home()) / ".ssh" / "secrets" / "ce_sri_parms.json"
    parms = {}
    if parms_path.exists():
        parms = json.loads(parms_path.read_text())
    else:
        print(f"  [WARN] {parms_path} not found — using defaults")

    cfg = write_cesri_conf(bd, su, api_key, port, parms)
    verify_p12_cert(cfg)
    patch_site_config(bd, su)
    patch_common_site_config(bd)
    patch_nginx_conf(bd, cfg)
    patch_procfile(bd, cfg)
    patch_supervisor_conf(bd, cfg)
    print("=== before-install complete ===")
