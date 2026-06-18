#!/usr/bin/env python3
"""Plan-substrate lint (#674).

Verify a plan/agenda's *declared* substrate against *live* state at pickup —
the S116 root cause was accepting an S115 plan ("branch off the umbrella",
"register dev15_01") whose assertions were already stale on main. A plan reads
true-now but is only true-when-written; this makes that difference mechanical.

The agenda declares a `<!-- plan-check ... -->` block (format + rationale in
tools/CLAUDE.md) with:
  base:         a branch the session builds on — must exist + be current (#673).
  creates-host: a host it will register — must NOT already be in hosts_map.yml.
No block => soft pass (legacy agendas). Exit 1 if any declared assertion fails.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.branch_currency import behind_count, _git  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
LOGS = REPO / "internal_docs" / "SessionLogs"
HOSTS_MAP = REPO / "hosts_map.yml"

BLOCK_RE = re.compile(r"<!--\s*plan-check\s*(.*?)-->", re.DOTALL)
KEY_RE = re.compile(r"^\s*([a-z][a-z-]*):\s*(\S.*?)\s*$", re.M)


def parse_block(text):
    """Extract the plan-check block as {key: [values]}; None if absent."""
    m = BLOCK_RE.search(text)
    if not m:
        return None
    out = {}
    for key, val in KEY_RE.findall(m.group(1)):
        out.setdefault(key, []).append(val)
    return out


def check_creates_host(host, hosts_map_text):
    """(level, msg) — a host the plan will create must NOT already be registered."""
    if re.search(rf"^\s*{re.escape(host)}:\s*$", hosts_map_text, re.M):
        return ("fail", f"creates-host '{host}' already in hosts_map — plan is stale")
    return ("ok", f"creates-host '{host}' not yet present — safe to create")


def check_base(branch):
    """(level, msg) — base branch must exist and be current with origin/main."""
    if _git("rev-parse", "--verify", "--quiet", branch).returncode != 0:
        return ("fail", f"base '{branch}' does not exist")
    behind = behind_count(branch)
    if behind is None:
        return ("warn", f"base '{branch}': currency unknown — rev-list failed")
    if behind > 0:
        return ("fail", f"base '{branch}' is {behind} commit(s) behind origin/main — stale plan")
    return ("ok", f"base '{branch}' current with origin/main")


def evaluate(text, hosts_map_text):
    """Run every declared check. Returns (rows, has_block)."""
    block = parse_block(text)
    if block is None:
        return ([], False)
    rows = [check_base(b) for b in block.get("base", [])]
    rows += [check_creates_host(h, hosts_map_text) for h in block.get("creates-host", [])]
    return (rows, True)


def _latest_agenda():
    return max(LOGS.glob("*-next-agenda.md"), key=lambda p: p.name)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else _latest_agenda()
    rows, has_block = evaluate(path.read_text(), HOSTS_MAP.read_text())
    if not has_block:
        print(f"  plan-lint: {path.name} — no plan-check block (legacy/soft-pass)")
        return 0
    glyph = {"ok": "✅", "warn": "⚠️ ", "fail": "❌"}
    for level, msg in rows:
        print(f"  {glyph[level]} {msg}")
    return 1 if any(level == "fail" for level, _ in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
