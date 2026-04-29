"""Operator-curated attribution map. Read-only at audit time; --write-stubs
appends TODO placeholders. Schema in config/customisation_attribution.yml."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Optional

import yaml

DEFAULT_PATH = "config/customisation_attribution.yml"
TODO_TOKEN = "TODO"


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def lookup(amap: dict, drift_class: str, name: str) -> Optional[dict]:
    """Return entry only when both fields are operator-resolved (not TODO)."""
    entry = (amap.get(drift_class) or {}).get(name)
    if not entry or TODO_TOKEN in (entry.get("owning_app"), entry.get("promotion_strategy")):
        return None
    return entry


def append_stubs(path: Path, drift_class: str, names: list[str]) -> int:
    amap = load(path)
    cls = amap.setdefault(drift_class, {}) or {}
    new = [n for n in names if n not in cls]
    for n in new:
        cls[n] = {"owning_app": TODO_TOKEN, "promotion_strategy": TODO_TOKEN}
    amap[drift_class] = cls
    path.write_text(yaml.safe_dump(amap, sort_keys=True))
    return len(new)


def stub_unmapped_from_report(path: Path, report: dict) -> dict[str, int]:
    """Append TODO stubs for every (class, name) the report flagged unmapped."""
    by_class: dict[str, list[str]] = defaultdict(list)
    for d in report["drifts"]:
        if d["promotion_strategy"] == "manual" and d["owning_app_proposed"] == "":
            by_class[d["class"]].append(d["name"])
    return {cls: append_stubs(path, cls, sorted(set(ns))) for cls, ns in by_class.items()}
