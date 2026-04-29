"""Drift dataclass + stable_id helper. Schema per plan §6."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Drift:
    id: str
    drift_class: str   # serialised as "class" in JSON (Python keyword)
    verdict: str
    doctype: str
    name: str
    owning_app_proposed: str
    fixture_path_proposed: str
    promotion_strategy: str
    row_data: dict[str, Any] = field(default_factory=dict)
    diff: str | None = None
    notes: list[str] = field(default_factory=list)


def stable_id(drift_class: str, name: str, *key_fields: str) -> str:
    """Hash class+name+key-fields → 12-char prefix. Deterministic across runs."""
    blob = "".join((drift_class, name, *key_fields)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]
