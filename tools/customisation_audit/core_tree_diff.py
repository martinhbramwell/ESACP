"""Per-app git enumeration: tracked-modified files + diff/before/after vs base."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterator

from tools.customisation_audit.core_tree_config import CoreTreeConfig


def _git(args: list[str], cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), check=True,
        capture_output=True, text=True,
    ).stdout


def tracked_modified(app_dir: Path) -> list[str]:
    return [line[3:].strip()
            for line in _git(["status", "--porcelain"], app_dir).splitlines()
            if len(line) >= 3 and line[1] == "M"]


def file_diff(app_dir: Path, rel: str, base: str) -> str:
    return _git(["diff", base, "--", rel], app_dir)


def file_before(app_dir: Path, rel: str, base: str) -> str:
    try:
        return _git(["show", f"{base}:{rel}"], app_dir)
    except subprocess.CalledProcessError:
        return ""


def iter_modified(config: CoreTreeConfig) -> Iterator[tuple[str, str, str, str, str]]:
    """Yield (app, rel_path, diff, before, after) per tracked-modified file."""
    root = Path(config.substrate_root)
    for app in config.apps:
        app_dir = root / app
        if not (app_dir / ".git").exists():
            continue
        for rel in tracked_modified(app_dir):
            full = app_dir / rel
            after = full.read_text() if full.exists() else ""
            yield (app, rel,
                   file_diff(app_dir, rel, config.compare_branch),
                   file_before(app_dir, rel, config.compare_branch),
                   after)
