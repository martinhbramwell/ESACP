#!/usr/bin/env python3
"""Pre-commit ratchet hook: dispatcher and pipeline file size enforcement.

Implements the anti-spiral rules from CLAUDE.md (#198).
Files can shrink but never grow beyond their recorded baseline.
New files exceeding their category limit are blocked outright.

Baselines are stored in tools/size_baselines.json and updated
automatically when a file shrinks.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINES_FILE = REPO_ROOT / "tools" / "size_baselines.json"

# Target limits from CLAUDE.md — what files must eventually reach.
TARGET_LIMITS = {
    "tools/esacp.py": 150,
    "tools/job_worker.py": 100,
    "tools/install_specific.py": 50,
}

# Category limits for pattern-matched files.
CATEGORY_LIMITS = {
    "tools/cli/": 80,
    "tools/pipeline/": 80,
    "tools/api/": 80,
}


def get_staged_files():
    """Return list of files staged for commit (added/modified)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    return [f for f in result.stdout.strip().splitlines() if f.endswith(".py")]


def count_lines(filepath):
    """Count lines in a file."""
    full = REPO_ROOT / filepath
    if not full.exists():
        return 0
    return sum(1 for _ in full.open())


def get_limit_for(filepath):
    """Return the category limit for a file, or None if unchecked."""
    if filepath in TARGET_LIMITS:
        return TARGET_LIMITS[filepath]
    for prefix, limit in CATEGORY_LIMITS.items():
        if filepath.startswith(prefix):
            return limit
    return None


def load_baselines():
    """Load recorded baselines from JSON."""
    if BASELINES_FILE.exists():
        return json.loads(BASELINES_FILE.read_text())
    return {}


def save_baselines(baselines):
    """Write baselines back to JSON."""
    BASELINES_FILE.write_text(json.dumps(baselines, indent=2, sort_keys=True) + "\n")


def main():
    staged = get_staged_files()
    if not staged:
        return 0

    baselines = load_baselines()
    violations = []
    baselines_changed = False

    for filepath in staged:
        limit = get_limit_for(filepath)
        if limit is None:
            continue

        lines = count_lines(filepath)
        baseline = baselines.get(filepath)

        if baseline is None:
            # New file — enforce the category limit directly.
            if lines > limit:
                violations.append(
                    f"  NEW  {filepath}: {lines} lines (limit {limit})"
                )
            # Record it as baseline for future commits.
            baselines[filepath] = lines
            baselines_changed = True
        else:
            # Existing file — ratchet: must not grow beyond baseline.
            if lines > baseline:
                violations.append(
                    f"  GREW {filepath}: {lines} lines (was {baseline}, target {limit})"
                )
            elif lines < baseline:
                # File shrank — update the baseline (ratchet down).
                baselines[filepath] = lines
                baselines_changed = True

    if baselines_changed:
        save_baselines(baselines)
        # Auto-stage the updated baselines file so it's included in the commit.
        subprocess.run(
            ["git", "add", str(BASELINES_FILE)],
            cwd=REPO_ROOT,
        )

    if violations:
        print("Anti-spiral size check FAILED:")
        print()
        for v in violations:
            print(v)
        print()
        print("Dispatcher/pipeline files must not grow. Extract logic to")
        print("tools/pipeline/ and delete the old code in the same commit.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
