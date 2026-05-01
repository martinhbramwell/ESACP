"""Q4 source-tree mutation gate — refuse-if-dirty + stage+diff+exit. Never commits.

Each touched path must live inside a git repo (a bespoke-app worktree).
`assert_clean` aborts (exit 2) if any target path is dirty *before* writes.
`stage_and_print_diff` stages writes and prints `git diff --cached` for
operator review; the operator commits manually.
"""

from __future__ import annotations

import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def _resolve(path: Path) -> Path:
    """Canonical absolute path; works for paths whose tail dirs don't exist yet."""
    base, tail = path, []
    while not base.exists():
        tail.append(base.name)
        base = base.parent
    return Path(*([base.resolve()] + list(reversed(tail))))


def _repo_root(path: Path) -> Path:
    """Walk up to the nearest existing dir (target may not exist yet)."""
    base = path
    while not base.is_dir():
        base = base.parent
    out = subprocess.run(
        ["git", "-C", str(base), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(out.stdout.strip())


def _group_by_repo(paths: list[Path]) -> dict[Path, list[Path]]:
    by_repo: dict[Path, list[Path]] = defaultdict(list)
    for p in paths:
        resolved = _resolve(p)
        by_repo[_repo_root(resolved)].append(resolved)
    return by_repo


def assert_clean(paths: list[Path]) -> None:
    """Exit 2 if any of `paths` has uncommitted changes in its git repo."""
    for repo, group in _group_by_repo(paths).items():
        rel = [str(p.relative_to(repo)) for p in group]
        out = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain", "--", *rel],
            capture_output=True, text=True, check=True,
        )
        if out.stdout.strip():
            print(f"ERROR: dirty paths in {repo}:\n{out.stdout}", file=sys.stderr)
            sys.exit(2)


def stage_and_print_diff(paths: list[Path]) -> None:
    """`git add` + print `git diff --cached` per repo. Never commits."""
    for repo, group in _group_by_repo(paths).items():
        rel = [str(p.relative_to(repo)) for p in group]
        subprocess.run(["git", "-C", str(repo), "add", "--", *rel], check=True)
        print(f"\n=== {repo} ===")
        subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--stat", "--", *rel])
        subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--", *rel])
