#!/usr/bin/env python3
"""Deflection lint (#675) — a seed tripwire for agentless self-reporting.

S116 root cause #3: in my own reports I launder sole-actor agency into agentless
grammar — "the plan didn't foresee", "nobody reconciled", "bit-rot", "drifted
apart". It corrupts the trust channel that is Beaverdam's core promise. The
RELIABLE guardrail is independent judgment (esacp-qa, per qa-contract §9.6); this
is a coarse, evolvable *complement* — it catches recurrence of phrases already
known to be deflection, run over self-report text (commit messages, minutes).

Deliberately conservative: a high-precision curated denylist of multi-word
agentless constructions, NOT broad single words ("drift"/"decay" are skipped —
they have legitimate technical uses like config-drift detection). It surfaces
*candidates*; it never auto-rejects. When esacp-qa's judgment layer catches a
NOVEL deflection, add the phrase here — judgment feeds the mechanical layer.

Exit 1 if any candidate is found (advisory). Run on a file, or pipe via stdin.
"""

import re
import sys
from pathlib import Path

# High-signal agentless / passive-causal phrases. Each almost always launders a
# sole-actor action into a blameless cause in a self-report context. Grown from
# esacp-qa findings — keep entries specific to hold precision.
DENYLIST = [
    r"did ?n[o']t foresee",
    r"the plan did ?n[o']t",
    r"nobody (?:reconciled|noticed|merged|rebased|did|caught|checked)",
    r"bit[- ]rot",
    r"\brot(?:ted|ting)\b",
    r"(?:got|fell|drifted) (?:out of sync|apart)",
    r"never (?:reconciled|got reconciled|reconciling)",
    r"(?:just )?happened to (?:diverge|drift|break)",
    r"somehow (?:diverged|got|ended up|broke)",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in DENYLIST]


def flag_lines(text):
    """Pure core → [(lineno, matched_phrase, line)] per denylisted phrase hit."""
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for rx in _COMPILED:
            m = rx.search(line)
            if m:
                hits.append((lineno, m.group(0), line.strip()))
    return hits


def main():
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text()
    else:
        text = sys.stdin.read()
    hits = flag_lines(text)
    for lineno, phrase, line in hits:
        print(f"  ⚠️  L{lineno}: agentless framing '{phrase}' — name the actor + the action")
        print(f"      {line[:78]}")
    if hits:
        print(f"deflection-lint: {len(hits)} candidate(s) — esacp-qa judges; own agency or cite evidence.")
        return 1
    print("deflection-lint: no candidate agentless framing found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
