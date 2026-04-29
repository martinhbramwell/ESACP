"""Heuristic: which bespoke app should own a discovered DB row?"""

from __future__ import annotations

from tools.bespoke_root import BESPOKE_ROOT


def module_to_app(app_names: list[str]) -> dict[str, str]:
    """Build module_name → app_name mapping from each app's modules.txt."""
    out: dict[str, str] = {}
    for name in app_names:
        modules_txt = BESPOKE_ROOT / name / name / "modules.txt"
        if not modules_txt.exists():
            continue
        for line in modules_txt.read_text().splitlines():
            mod = line.strip()
            if mod:
                out[mod] = name
    return out


def resolve_owning_app(row_module: str, mapping: dict[str, str]) -> str:
    """Look up the owning app by row's module field; '' if not bespoke."""
    return mapping.get(row_module, "")
