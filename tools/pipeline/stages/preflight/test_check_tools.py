#!/usr/bin/env python3
"""Tests for check_tools detection paths (apt-bin / apt-py / manual).

Run: ./tools/pipeline/stages/preflight/test_check_tools.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tools.pipeline.stages.preflight.check_tools import check_tools  # noqa: E402

MOD = "tools.pipeline.stages.preflight.check_tools"


def test_missing_apt_py_ruamel() -> tuple[bool, str]:
    """Missing python3-ruamel.yaml surfaces at preflight, not at audit runtime."""
    emitted: list[str] = []
    with patch(f"{MOD}.importlib.util.find_spec",
               side_effect=lambda n: None if n == "ruamel.yaml" else object()):
        status = check_tools(emit=emitted.append)

    line = any("[MISSING] ruamel.yaml (python3-ruamel.yaml)" in l for l in emitted)
    in_apt = "python3-ruamel.yaml" in status.missing_apt
    not_manual = all(p != "python3-ruamel.yaml" for _, p in status.missing_manual)
    return (line and in_apt and not_manual,
            f"line={line} apt={in_apt} not_manual={not_manual}")


def test_missing_apt_bin_regression() -> tuple[bool, str]:
    """Renamed 'apt' → 'apt-bin' must keep CLI-missing routing to apt bucket."""
    with patch(f"{MOD}.shutil.which",
               side_effect=lambda n: None if n == "virsh" else f"/usr/bin/{n}"):
        status = check_tools(emit=lambda _: None)
    ok = "libvirt-clients" in status.missing_apt
    return (ok, f"missing virsh → libvirt-clients in missing_apt: {ok}")


def test_missing_manual_regression() -> tuple[bool, str]:
    """'manual' kind unchanged, must still route to missing_manual."""
    with patch(f"{MOD}.shutil.which",
               side_effect=lambda n: None if n == "sops" else f"/usr/bin/{n}"):
        status = check_tools(emit=lambda _: None)
    in_manual = any(n == "sops" for n, _ in status.missing_manual)
    not_apt = "sops" not in status.missing_apt
    return (in_manual and not_apt, f"manual={in_manual} not_apt={not_apt}")


if __name__ == "__main__":
    print("── check_tools tests ──")
    fails = 0
    for fn in (test_missing_apt_py_ruamel,
               test_missing_apt_bin_regression,
               test_missing_manual_regression):
        ok, msg = fn()
        print(f"  {'✅' if ok else '❌'}  {fn.__name__}: {msg}")
        if not ok:
            fails += 1
    print(f"\n  {3 - fails} passed, {fails} failed")
    sys.exit(0 if fails == 0 else 1)
