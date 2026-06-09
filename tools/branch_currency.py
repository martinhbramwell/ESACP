#!/usr/bin/env python3
"""Branch-base currency gate (#673, #684).

Two measures per branch — conflating them once led me to call branches "stale" on
distance alone (S116). `behind` = how far origin/main is ahead (base-currency: don't
branch/commit/merge off a base behind main; drives the level). `ahead` = commits the
branch has that main LACKS (unmerged work; the retire-safety signal: 0 ⇒ already on
main, >0 ⇒ assess first). behind is a measurement, not a judgement — far-behind can
still hold unmerged work; retiring always needs content assessment + operator sign-off.

Two surfaces: `sync_check.sh` §19 + `esacp-qa`. `--no-fetch` keeps it read-only.
Exit 1 when any `umbrella/*` is behind origin/main.
"""

import subprocess
import sys


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _count(rng):
    cp = _git("rev-list", "--count", rng)
    return int(cp.stdout.strip()) if cp.returncode == 0 else None


def behind_count(branch, base="origin/main"):
    """Commits on *base* not in *branch* (how far behind); None on failure."""
    return _count(f"{branch}..{base}")


def ahead_count(branch, base="origin/main"):
    """Commits on *branch* not in *base* — its unique unmerged work; None on failure."""
    return _count(f"{base}..{branch}")


def _work_note(ahead):
    if ahead is None:
        return "unmerged-work count unknown"
    if ahead == 0:
        return "0 unique commits — content already on main, safe to retire"
    return f"{ahead} unmerged commit(s) not on main — ASSESS before retiring"


def classify(name, behind, ahead, is_umbrella):
    """Pure verdict → (level, message). Level is behind-driven (base-currency);
    the unmerged-work note is always appended so 'behind' is never read as 'obsolete'."""
    work = _work_note(ahead)
    if behind is None:
        return ("warn", f"{name}: base-currency unknown — rev-list failed; {work}")
    if behind == 0:
        return ("ok", f"{name}: current with origin/main; {work}")
    level = "fail" if is_umbrella else "warn"
    return (level, f"{name}: {behind} behind origin/main (rebase before branching off it); {work}")


def _umbrella_branches():
    cp = _git("branch", "--list", "umbrella/*", "--format=%(refname:short)")
    return [b for b in cp.stdout.split() if b]


def _current_branch():
    return _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def evaluate():
    """Classify every umbrella + the current branch. Returns list[(level, msg)]."""
    rows = [classify(u, behind_count(u), ahead_count(u), True) for u in _umbrella_branches()]
    cur = _current_branch()
    if cur and cur != "main" and not cur.startswith("umbrella/"):
        rows.append(classify(cur, behind_count(cur), ahead_count(cur), False))
    return rows


def main():
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
