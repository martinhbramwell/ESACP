#!/usr/bin/env python3
"""Staged ERPNext major-version upgrade orchestrator (Phase 5).

Usage: ./tools/upgrade_to.py --substrate dev01 --target-version 15

Dispatcher only — composes one call to `run_upgrade()` from the
`tools/pipeline/upgrade_v14/` package. Per CLAUDE.md anti-spiral rules,
all logic lives under tools/pipeline/. `--target-version` parameterizes the
staged switch leg (14 → 15 → 16); no default — the destructive switch must
be named explicitly.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.host_identity import resolve_kvm_host  # noqa: E402
from tools.pipeline.stages.common.config import build_config  # noqa: E402
from tools.pipeline.upgrade_v14 import run_upgrade  # noqa: E402


def _load_host(substrate: str) -> tuple[str, dict]:
    """Resolve a substrate (key/hostname/nickname) to (key, host block).

    Routes through ``host_identity.resolve_kvm_host`` — the live hosts_map
    nests hosts under ``groups.kvm.<key>``; the old flat ``hosts[]`` read
    matched nothing and made this dispatcher non-functional.
    """
    key, host_cfg = resolve_kvm_host(substrate)
    if not host_cfg:
        raise SystemExit(f"substrate {substrate!r} not found in hosts_map.yml")
    return key, host_cfg


def _emit(msg: str) -> None:
    print(msg, flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Staged ERPNext major-version upgrade orchestrator")
    ap.add_argument("--substrate", required=True, help="VM hostname or nickname (e.g. dev01)")
    ap.add_argument("--target-version", required=True, type=int, choices=(14, 15, 16),
                    help="Target ERPNext major version to switch+migrate to")
    args = ap.parse_args()
    key, host_cfg = _load_host(args.substrate)
    config = build_config(key, host_cfg, str(REPO_ROOT), use_wg=True)
    try:
        run_upgrade(config, _emit, args.target_version)
    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
