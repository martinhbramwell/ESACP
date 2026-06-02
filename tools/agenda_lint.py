#!/usr/bin/env python3
"""Agenda-lint: flag bare CLOSED issue-refs in a next-agenda (#560).

Flags any `#N` that is CLOSED in the ESACP tracker yet left bare — no stamp
(`done`/`closed`/`✅`/`~~`) on its line (root cause of #483/#541 drift). Scope
is ESACP-only; cross-repo refs MUST carry their prefix (`LSKB#16`), as REF_RE
skips letter-prefixed refs.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = "martinhbramwell/ESACP"
LOGS = Path(__file__).resolve().parent.parent / "internal_docs" / "SessionLogs"
REF_RE = re.compile(r"(?<![A-Za-z_])#(\d+)")
STAMP_TOKENS = ("done", "closed", "merged", "won't-fix", "wontfix", "✅", "~~")


def bare_closed_refs(text, states):
    """Return [(lineno, number, line)] per bare CLOSED ref (a line bearing any STAMP_TOKEN, case-insensitive, is stamped and skipped)."""
    flagged = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stamped = any(tok in line.lower() for tok in STAMP_TOKENS)
        for m in REF_RE.finditer(line):
            num = int(m.group(1))
            if states.get(num) == "CLOSED" and not stamped:
                flagged.append((lineno, num, line.strip()))
    return flagged


def fetch_states(numbers):
    """Look up live state per ESACP issue → (states, failures); a failed `gh` call is recorded, never silently treated as OPEN."""
    states, failures = {}, []
    for num in sorted(numbers):
        cp = subprocess.run(
            ["gh", "issue", "view", str(num), "--repo", REPO, "--json", "state"],
            capture_output=True, text=True,
        )
        if cp.returncode == 0:
            states[num] = json.loads(cp.stdout)["state"]
        else:
            failures.append(num)
    return states, failures


def latest_agenda():
    return max(LOGS.glob("*-next-agenda.md"), key=lambda p: p.name)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_agenda()
    text = path.read_text()
    states, failures = fetch_states({int(m.group(1)) for m in REF_RE.finditer(text)})
    if failures:
        print(f"agenda-lint: WARNING — gh lookup failed for {failures}; result incomplete.", file=sys.stderr)
    flagged = bare_closed_refs(text, states)
    for lineno, num, line in flagged:
        print(f"  {path.name}:{lineno}  #{num} (CLOSED)  {line[:70]}")
    if flagged:
        print(f"agenda-lint: {path.name} — {len(flagged)} bare CLOSED ref(s).")
    elif not failures:
        print(f"agenda-lint: {path.name} — no bare CLOSED refs.")
    return 1 if flagged else (2 if failures else 0)


if __name__ == "__main__":
    sys.exit(main())
