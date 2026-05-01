#!/usr/bin/env python3
"""Phase 2 dispatcher — promote drifts to bespoke-app fixtures (#327).

Reads delta_report.json, writes bespoke-app fixtures for every drift that
`promotion_dispatch.is_promotable()` returns True for. Operator commits
manually — this tool refuses-if-dirty and stages diffs for review.

Usage: ./tools/correct_bad_customisations.py --delta delta_report.json [--dry-run]
Exit:  0 = success, 2 = source-tree dirty (refuse-to-write), 1 = other error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.customisation_audit import (  # noqa: E402
    promotion_dispatch, source_tree_gate,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 2 promotion (#327)")
    ap.add_argument("--delta", required=True, help="delta_report.json path")
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute targets only; do not write or stage")
    args = ap.parse_args()
    report = json.loads(Path(args.delta).read_text())
    promotable = [d for d in report["drifts"] if promotion_dispatch.is_promotable(d)]
    print(f"{len(promotable)} drifts to promote.")
    targets = [promotion_dispatch.target(d) for d in promotable]
    if args.dry_run:
        for d, t in zip(promotable, targets):
            print(f"  would write: {d['class']}/{d['name'][:60]} → {t}")
        return 0
    source_tree_gate.assert_clean(targets)
    for d in promotable:
        promotion_dispatch.apply(d)
    source_tree_gate.stage_and_print_diff(targets)
    print(f"\n✓ Staged {len(promotable)} promotions across {len(set(t.parts[:5] for t in targets))} repos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
