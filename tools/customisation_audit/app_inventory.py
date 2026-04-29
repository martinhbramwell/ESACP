"""Parse <app>/<app>/hooks.py:fixtures and enumerate fixture files."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from tools.bespoke_root import BESPOKE_ROOT


def _snake(name: str) -> str:
    """'Custom Field' → 'custom_field'."""
    return re.sub(r"\W+", "_", name).lower()


def app_dir(app_name: str) -> Path:
    return BESPOKE_ROOT / app_name


def fixture_path(app_name: str, doctype: str) -> Path:
    return app_dir(app_name) / app_name / "fixtures" / f"{_snake(doctype)}.json"


def parse_fixtures(app_name: str) -> list[Any]:
    """Read hooks.py and return its fixtures list (literal-only)."""
    hooks = app_dir(app_name) / app_name / "hooks.py"
    if not hooks.exists():
        return []
    tree = ast.parse(hooks.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "fixtures":
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return []
    return []


def load_fixture_file(app_name: str, doctype: str) -> list[dict]:
    p = fixture_path(app_name, doctype)
    if not p.exists():
        return []
    return json.loads(p.read_text())
