#!/usr/bin/env python3
"""Interactive attribution review for unresolved promotable drifts.

Walks each drift in delta_report.json with promotable strategy + empty
owning_app, displays full context (diff hunk for in_place; row data for
DB-side), and writes the operator's answer into customisation_attribution.yml.
Resumable — re-runs skip drifts already resolved in the YAML.

Usage: ./tools/review_attribution.py [--delta /tmp/delta_phase2.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.customisation_audit import attribution, review_display  # noqa: E402

PROMOTABLE = {"fixture_json", "fixtures_custom_scripts",
              "app_translations_csv", "v14_patch_script"}
APP_KEYS = {"c": "ce_sri", "r": "returnable",
            "p": "route_planner", "n": "not_ours"}
# `k` (in_core) means: lives in frappe/erpnext core, typically with paired
# Python controller code that can't be expressed as a bespoke-app fixture.
# Mapped to `v14_patch_script` strategy → Phase 5 generates a runtime patch
# that re-applies the customisation post-V14. NEVER manual.
IN_CORE_KEY = "k"
IN_CORE_OWNING = "in_core"
IN_CORE_STRATEGY = "v14_patch_script"


def _todo(report: dict, amap: dict) -> list[dict]:
    out = []
    for d in report["drifts"]:
        if d["promotion_strategy"] not in PROMOTABLE:
            continue
        if d["owning_app_proposed"]:
            continue
        if attribution.lookup(amap, d["class"], d["name"]):
            continue
        out.append(d)
    return out


def _ask() -> str | None:
    """Return owning_app, None for skip, 'QUIT' for quit. `k` returns IN_CORE_OWNING."""
    while True:
        prompt = ("  Owning app? [c=ce_sri r=returnable p=route_planner "
                  "k=in_core n=not_ours s=skip q=quit] ▸ ")
        ans = input(prompt).strip().lower()
        if ans in ("", "c"):
            return "ce_sri"
        if ans == IN_CORE_KEY:
            return IN_CORE_OWNING
        if ans in APP_KEYS:
            return APP_KEYS[ans]
        if ans == "s":
            return None
        if ans == "q":
            return "QUIT"
        print(f"  ?  unrecognised: {ans!r}; pick c/r/p/k/n/s/q or Enter for ce_sri")


def main() -> int:
    ap = argparse.ArgumentParser(description="Interactive attribution review")
    ap.add_argument("--delta", default="/tmp/delta_phase2.json",
                    help="Delta report JSON path (default: /tmp/delta_phase2.json)")
    ap.add_argument("--attribution", default="config/customisation_attribution.yml")
    args = ap.parse_args()

    yml_path = REPO_ROOT / args.attribution
    report = json.loads(Path(args.delta).read_text())
    amap = attribution.load(yml_path)
    todo = _todo(report, amap)
    print(f"\n{len(todo)} unresolved promotable drifts to review.")
    print(f"(Already resolved entries in {args.attribution} are skipped.)\n")

    for i, drift in enumerate(todo, 1):
        print(f"\n{'='*78}")
        print(f"[{i}/{len(todo)}]  {review_display.summary(drift)}")
        print('='*78)
        print(review_display.context(drift))
        print()
        ans = _ask()
        if ans == "QUIT":
            print("\n↪ Saving progress and exiting. Re-run to resume.")
            break
        if ans is None:
            print("  ↪ skipped")
            continue
        # in_core → v14_patch_script (Phase 5 generates automated runtime patch).
        strategy = (IN_CORE_STRATEGY if ans == IN_CORE_OWNING
                    else drift["promotion_strategy"])
        attribution.append_resolved(
            yml_path, drift["class"], drift["name"], ans, strategy,
        )
        print(f"  ✓ {drift['class']}/{drift['name'][:60]} → {ans} ({strategy})")

    print(f"\n{args.attribution} updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
