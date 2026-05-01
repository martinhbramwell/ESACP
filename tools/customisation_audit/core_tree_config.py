"""Phase 4 substrate config — production-master worktree paths."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CoreTreeConfig:
    substrate_root: str
    apps: list[str] = field(default_factory=lambda: ["frappe", "erpnext"])
    compare_branch: str = "version-13"
