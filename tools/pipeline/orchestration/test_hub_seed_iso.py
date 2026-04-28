#!/usr/bin/env python3
"""Tests for hub_seed_iso template rendering.

Pure rendering only — no cloud-localds invocation. The ISO-pack step is a
single subprocess that's exercised by the next operator-driven hub rebuild.
"""

from __future__ import annotations

import sys
from pathlib import Path

import jinja2

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.pipeline.orchestration.hub_seed_iso import _render  # noqa: E402


_PARAMS = {
    "hostname": "saconsole",
    "virbr0_ip": "192.168.122.10",
    "gateway": "192.168.122.1",
    "controller_pubkey": "ssh-ed25519 AAAATESTKEY user@test",
}


def test_user_data_substitutes_all_variables() -> None:
    rendered = _render("hub-autoinstall.user-data.j2", _PARAMS)
    assert rendered.startswith("#cloud-config\n")
    assert "autoinstall:" in rendered
    assert "hostname: saconsole" in rendered
    assert "- 192.168.122.10/24" in rendered
    assert "via: 192.168.122.1" in rendered
    assert '- "ssh-ed25519 AAAATESTKEY user@test"' in rendered
    assert "${USER}" not in rendered
    assert "${HOSTNAME}" not in rendered


def test_meta_data_substitutes_hostname() -> None:
    rendered = _render("hub-autoinstall.meta-data.j2", {"hostname": "saconsole"})
    assert rendered == "instance-id: saconsole-01\nlocal-hostname: saconsole\n"


def test_strict_undefined_catches_missing_variables() -> None:
    try:
        _render("hub-autoinstall.user-data.j2", {})
    except jinja2.UndefinedError:
        return
    raise AssertionError("Expected UndefinedError when variables missing")


if __name__ == "__main__":
    test_user_data_substitutes_all_variables()
    test_meta_data_substitutes_hostname()
    test_strict_undefined_catches_missing_variables()
    print("[OK] all tests passed")
