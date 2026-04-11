"""SCP ddlViews.sql to target VM."""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

VIEWS_DDL_SRC = (
    Path.home() / "projects" / "Logichem" / "ce_sri"
    / "example_srvr_files" / "views.ddl"
)


def _ddl_present(config: Config) -> bool:
    r = ssh_run(config,
                "test -f /tmp/ddlViews.sql && echo y", timeout=10)
    return r.returncode == 0 and "y" in r.stdout


def ensure_ddl_views(config: Config, emit: Emit) -> TaskResult:
    """SCP views.ddl as ddlViews.sql to /tmp/ on the VM."""
    if _ddl_present(config):
        return TaskResult(True, False, "ddlViews.sql already in /tmp/")

    if not VIEWS_DDL_SRC.exists():
        return TaskResult(True, False,
                          f"views.ddl not found at {VIEWS_DDL_SRC} — skipping")

    r = scp_to_vm(config, [str(VIEWS_DDL_SRC)],
                   "/tmp/ddlViews.sql", timeout=30)
    if r.returncode != 0:
        return TaskResult(False, False,
                          f"SCP ddlViews.sql failed: {r.stderr.strip()}")
    return TaskResult(True, True, "ddlViews.sql → /tmp/")
