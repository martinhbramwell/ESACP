#!/usr/bin/env python3
"""Preflight validation — compose tool, file, and key checks."""

from __future__ import annotations

from tools.pipeline.stages.common.types import Emit, TaskResult
from tools.pipeline.stages.preflight.check_tools import check_tools
from tools.pipeline.stages.preflight.check_files import check_files
from tools.pipeline.stages.preflight.check_keys import check_keys


def run_preflight(
    project_root: str,
    ssh_key_path: str,
    expected_hosts: list[str],
    hub_name: str,
    emit: Emit,
) -> TaskResult:
    """Run all preflight checks. Returns combined result."""
    emit("── Tool checks ──")
    tool_status = check_tools(emit)

    emit("")
    emit("── File checks ──")
    file_results = check_files(project_root, ssh_key_path, emit)

    emit("")
    emit("── Key validation ──")
    key_result = check_keys(project_root, expected_hosts, hub_name, emit)

    has_tool_issues = bool(tool_status.missing_apt or tool_status.missing_manual)
    has_file_issues = any(not exists for _, _, exists in file_results)
    has_key_issues = not key_result.success

    if has_tool_issues or has_file_issues or has_key_issues:
        parts = []
        if has_tool_issues:
            parts.append("missing tools")
        if has_file_issues:
            parts.append("missing files")
        if has_key_issues:
            parts.append(key_result.message)
        return TaskResult(False, False, "; ".join(parts))

    return TaskResult(True, False, "All prerequisites satisfied")
