#!/usr/bin/env python3
"""resume_scheduler: both bench subcommands carry --site (V15 regression guard).

V15 dropped the currentsite.txt default-site fallback, so a bare
`bench scheduler resume` exits 1 ("Please specify --site") with the message on
stdout. This guards that BOTH commands pass --site and that a non-zero exit
with empty stderr still surfaces stdout in the failure message.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14.scheduler_resume as scheduler_resume  # noqa: E402
from tools.pipeline.upgrade_v14._test_helpers import make_config, ok, patch_ssh  # noqa: E402


def test_both_commands_pass_site() -> bool:
    captured: list[str] = []

    def fake(_cfg, cmd, *, timeout=30):
        captured.append(cmd)
        return ok()

    orig = patch_ssh(scheduler_resume, fake)
    try:
        result = scheduler_resume.resume_scheduler(make_config(), lambda _: None)
    finally:
        scheduler_resume.ssh_run = orig
    if not result.success:
        print(f"FAIL: {result.message}")
        return False
    if len(captured) != 2:
        print(f"FAIL: expected 2 commands, got {len(captured)}")
        return False
    if not all("scheduler resume" not in c or "--site" in c for c in captured):
        print(f"FAIL: a scheduler command lacks --site: {captured}")
        return False
    if "scheduler resume" not in captured[1] or "--site" not in captured[1]:
        print(f"FAIL: resume command must carry --site: {captured[1]}")
        return False
    print("PASS: set-maintenance + scheduler resume both pass --site")
    return True


def test_failure_surfaces_stdout_when_stderr_empty() -> bool:
    """The V15 error prints to stdout; a stderr-only message would be blank."""
    def fake(_cfg, cmd, *, timeout=30):
        if "scheduler resume" in cmd:
            return SimpleNamespace(returncode=1, stdout="Please specify --site sitename", stderr="")
        return ok()

    orig = patch_ssh(scheduler_resume, fake)
    try:
        result = scheduler_resume.resume_scheduler(make_config(), lambda _: None)
    finally:
        scheduler_resume.ssh_run = orig
    if result.success:
        print("FAIL: stage should fail on rc=1")
        return False
    if "Please specify --site" not in result.message:
        print(f"FAIL: stdout not surfaced in message: {result.message!r}")
        return False
    print("PASS: failure message surfaces stdout when stderr is empty")
    return True


if __name__ == "__main__":
    ok_all = (
        test_both_commands_pass_site()
        and test_failure_surfaces_stdout_when_stderr_empty()
    )
    sys.exit(0 if ok_all else 1)
