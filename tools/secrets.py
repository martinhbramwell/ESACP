#!/usr/bin/env python3
"""Load build secrets from environment variables or sops.

Priority: ESACP_ERP_USER_PWD / ESACP_DB_ROOT_PWD env vars > sops file.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml

BUILD_SECRETS_SOPS = "config/build_secrets.sops.yml"


def load_build_secrets(project_root: str) -> dict[str, str]:
    """Return dict with keys ``erp_user_pwd`` and ``db_root_pwd``."""
    erp_pwd = os.environ.get("ESACP_ERP_USER_PWD")
    db_pwd = os.environ.get("ESACP_DB_ROOT_PWD")
    if erp_pwd and db_pwd:
        return {"erp_user_pwd": erp_pwd, "db_root_pwd": db_pwd}

    sops_path = Path(project_root) / BUILD_SECRETS_SOPS
    r = subprocess.run(
        ["sops", "-d", str(sops_path)],
        cwd=project_root, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"Cannot load build secrets: sops decrypt failed for {sops_path}: "
            f"{r.stderr.strip()}"
        )
    data = yaml.safe_load(r.stdout)
    return {
        "erp_user_pwd": data["erp_user_pwd"],
        "db_root_pwd": data["db_root_pwd"],
    }
