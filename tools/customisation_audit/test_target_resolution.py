#!/usr/bin/env python3
"""Tests for target_resolution — module_to_app + resolve_owning_app."""

import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import target_resolution  # noqa: E402
from tools.customisation_audit._test_support import patched  # noqa: E402


def _scaffold(root: Path, app: str, modules: list[str]) -> None:
    inner = root / app / app
    inner.mkdir(parents=True)
    (inner / "modules.txt").write_text("\n".join(modules) + "\n")


def test_module_to_app_builds_mapping() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _scaffold(root, "ce_sri", ["CE-SRI", "Returnable"])
        _scaffold(root, "route_planner", ["Route Planner"])
        with patched(target_resolution, "BESPOKE_ROOT", root):
            mapping = target_resolution.module_to_app(["ce_sri", "route_planner"])
        assert mapping == {"CE-SRI": "ce_sri", "Returnable": "ce_sri", "Route Planner": "route_planner"}


def test_resolve_owning_app_known_and_unknown() -> None:
    mapping = {"CE-SRI": "ce_sri"}
    assert target_resolution.resolve_owning_app("CE-SRI", mapping) == "ce_sri"
    assert target_resolution.resolve_owning_app("ERPNext", mapping) == ""


if __name__ == "__main__":
    test_module_to_app_builds_mapping()
    test_resolve_owning_app_known_and_unknown()
    print("OK test_target_resolution")
