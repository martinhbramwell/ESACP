"""SSH-based health checks for an ERPNext VM."""

from __future__ import annotations

import subprocess

from tools.host_identity import GUEST_VM_USER


def _ssh(wg_ip: str, cmd: str, timeout: int = 8) -> str:
    try:
        r = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
             f"{GUEST_VM_USER}@{wg_ip}", cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def check_health(wg_ip: str, db_password: str) -> dict:
    """Return {web, app, db} each 'green'|'amber'|'red'.

    amber = check could not run (SSH timeout, unreachable).
    """
    nginx_state = _ssh(wg_ip, "systemctl is-active nginx 2>/dev/null")
    web = ("green" if nginx_state == "active"
           else ("amber" if not nginx_state else "red"))

    sup_out = _ssh(wg_ip, "sudo supervisorctl status 2>/dev/null")
    if sup_out:
        lines   = [ln for ln in sup_out.splitlines() if ln.strip()]
        total   = len(lines)
        running = sum(1 for ln in lines if "RUNNING" in ln)
        app = ("green" if total > 0 and running == total
               else ("amber" if running > 0 else "red"))
    else:
        app = "amber"

    db_out = _ssh(wg_ip, f"sudo mysql -u root -p{db_password} -e 'SELECT 1' "
                         "2>/dev/null && echo ok")
    db = ("green" if "ok" in db_out
          else ("amber" if not db_out else "red"))

    return {"web": web, "app": app, "db": db}
