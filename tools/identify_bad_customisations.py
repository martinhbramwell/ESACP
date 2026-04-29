#!/usr/bin/env python3
"""Phase 1 dispatcher — read-only customisation discovery (#315; plan §5).

Usage: ./tools/identify_bad_customisations.py --substrate dev01 [--output FILE] [--write-stubs]
Exit:  0 = success, 1 = substrate/pipeline failure, 2 = invalid args (argparse).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.customisation_audit import attribution, delta_report  # noqa: E402
from tools.customisation_audit.runner import run_audit  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Customisation discovery (Phase 1, #315)")
    ap.add_argument("--substrate", required=True, help="VM hostname (e.g. dev01)")
    ap.add_argument("--output", default="delta_report.json", help="Output JSON path")
    ap.add_argument("--write-stubs", action="store_true",
                    help=f"Append TODO entries for unmapped names to {attribution.DEFAULT_PATH}")
    args = ap.parse_args()
    try:
        report = run_audit(args.substrate, str(REPO_ROOT))
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    Path(args.output).write_text(delta_report.to_json(report))
    s = report["summary"]
    print(f"Wrote {args.output}\n  total_drifts: {s['total_drifts']}")
    for cls, n in sorted(s["by_class"].items()):
        print(f"  {cls}: {n}")
    if args.write_stubs:
        added = attribution.stub_unmapped_from_report(REPO_ROOT / attribution.DEFAULT_PATH, report)
        print(f"\nAppended {sum(added.values())} stubs to {attribution.DEFAULT_PATH}: {dict(added)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
