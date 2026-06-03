#!/usr/bin/env python3
"""Shared CLI helpers for the per-stage verify scripts.

`parse_verify_args` (and the `VerifyContext` it returns) are re-exported
here so each stage's verify.py __main__ keeps a single import site;
`print_results` renders the pass/fail table and sets the exit code.
"""

from __future__ import annotations

import sys

from tools.pipeline.stages.common.verify_args import parse_verify_args
from tools.pipeline.stages.common.verify_context import VerifyContext

__all__ = ["parse_verify_args", "print_results", "VerifyContext"]


def print_results(
    stage_label: str,
    hostname: str,
    results: list[tuple[bool, str]],
) -> None:
    """Print verification results table and exit 0/1."""
    print(f"\n── {stage_label} verification: {hostname} ──")
    passed = failed = 0
    for ok, msg in results:
        tag = "✅" if ok else "❌"
        print(f"  {tag}  {msg}")
        if ok:
            passed += 1
        else:
            failed += 1
    print(f"\n  {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
