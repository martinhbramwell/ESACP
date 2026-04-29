"""Controller-side wrapper that runs ``_remote_query.py`` on a dev VM via SSH.

SSH joins argv with spaces and re-parses on the remote shell, so the SQL
must be ``shlex.quote``-d into a single shell-safe token before transport.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

_REMOTE_SCRIPT = Path(__file__).parent / "_remote_query.py"
_REMOTE_PATH = "/tmp/_audit_query.py"


def deploy_runner(ssh_host: str) -> None:
    """SCP _remote_query.py to /tmp on the substrate VM."""
    subprocess.run(
        ["scp", "-q", str(_REMOTE_SCRIPT), f"{ssh_host}:{_REMOTE_PATH}"],
        check=True, capture_output=True, text=True,
    )


def run_query(ssh_host: str, site_config_path: str, sql: str) -> list[dict]:
    """Execute SQL on substrate; return rows as list[dict].

    Raises CalledProcessError if SSH or mysql fails.
    """
    remote_cmd = (
        f"python3 {shlex.quote(_REMOTE_PATH)} "
        f"{shlex.quote(site_config_path)} {shlex.quote(sql)}"
    )
    proc = subprocess.run(
        ["ssh", ssh_host, remote_cmd],
        capture_output=True, text=True, check=True,
    )
    return json.loads(proc.stdout)["rows"]
