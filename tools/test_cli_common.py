#!/usr/bin/env python3
"""Colocated tests for CLI shared helpers."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cli import _common  # noqa: E402


def test_ssh_key_path_has_no_ignored_config_parameter():
    assert list(inspect.signature(_common.ssh_key_path).parameters) == []


def test_ssh_key_path_delegates_to_operator_identity(monkeypatch):
    monkeypatch.setattr(_common, "operator_ssh_key", lambda: "/tmp/operator-key")

    assert _common.ssh_key_path() == "/tmp/operator-key"


if __name__ == "__main__":
    from tools.testkit import run_module_tests

    raise SystemExit(run_module_tests(globals()))
