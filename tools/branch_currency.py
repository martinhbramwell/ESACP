#!/usr/bin/env python3
"""Branch-base currency gate (#673).

FAIL when an `umbrella/*` branch is behind `origin/main`, or WARN when the
current working branch is. Long-lived branches that silently diverge from main
are the S116 root cause: a sub-branch was cut off an umbrella 30 commits stale,
and the divergence was only discovered live mid-session. CLAUDE.md's
rebase-cadence rule is real but unenforced; this is its mechanical teeth.

One source of truth for two surfaces: `sync_check.sh` §19 (session start) and
the `esacp-qa` verdict layer both invoke it. Pass `--no-fetch` to skip the
`git fetch` — esacp-qa runs read-only and compares against the already-fetched
`origin/main` (the parent / sync_check owns the refresh).

Exit 0 when nothing is behind (or only the current branch is, a WARN); exit 1
when any `umbrella/*` is behind origin/main.
"""

import subprocess
import sys


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def behind_count(branch, base="origin/main"):
    """Commits on *base* not in *branch*; None if the rev-list call fails."""
    cp = _git("rev-list", "--count", f"{branch}..{base}")
    return int(cp.stdout.strip()) if cp.returncode == 0 else None


def classify(name, behind, is_umbrella):
    """Pure verdict → (level, message). level ∈ {ok, warn, fail}.

    An umbrella behind main is a FAIL (umbrella discipline demands currency);
    any other branch behind main is a WARN (rebase before merge, not yet wrong).
    """
    if behind is None:
        return ("warn", f"{name}: currency unknown — rev-list failed")
    if behind == 0:
        return ("ok", f"{name}: current with origin/main")
    if is_umbrella:
        return ("fail", f"{name}: {behind} commit(s) behind origin/main — rebase before use")
    return ("warn", f"{name}: {behind} commit(s) behind origin/main — rebase before merge")


def _umbrella_branches():
    cp = _git("branch", "--list", "umbrella/*", "--format=%(refname:short)")
    return [b for b in cp.stdout.split() if b]


def _current_branch():
    return _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def evaluate():
    """Classify every umbrella + the current branch. Returns list[(level, msg)]."""
    rows = [classify(u, behind_count(u), True) for u in _umbrella_branches()]
    cur = _current_branch()
    if cur and cur != "main" and not cur.startswith("umbrella/"):
        rows.append(classify(cur, behind_count(cur), False))
    return rows


def main():
    # Refresh origin/main so the comparison is against the real remote tip
    # (tolerate offline). `--no-fetch` keeps the run strictly read-only.
    if "--no-fetch" not in sys.argv:
        _git("fetch", "--quiet", "origin", "main")
    rows = evaluate()
    if not rows:
        print("  branch-currency: on main, no umbrellas — nothing to check")
        return 0
    glyph = {"ok": "✅", "warn": "⚠️ ", "fail": "❌"}
    for level, msg in rows:
        print(f"  {glyph[level]} {msg}")
    return 1 if any(level == "fail" for level, _ in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
