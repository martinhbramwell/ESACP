#!/usr/bin/env python3
"""S0b-bench durable proof — guard the committed V13 structural baseline.

The expensive structural A/B audit runs ONCE against the dev01 V13 prod-data
bench (`migration_status.py --bench dev01 --write …`). Its report is committed
as the baseline. This cheap, offline test asserts that committed artifact still
carries the established structural class/verdict distribution — the reference
every later migration leg (S1-S4) diffs against. A change here is a deliberate
baseline revision, never silent drift.

Per MIGRATION_PLAN.md proof method: the proof command is cheap (loads JSON,
asserts counts) — never a re-run of the SSH audit. See migration_proofs/S0b.log.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASELINE = REPO / "internal_docs" / "migration_proofs" / "delta_report_dev01.json"

# Established V13 prod-data baseline (dev01, frappe 13.58.22). See S0b.log.
EXPECTED_TOTAL = 373
EXPECTED_BY_CLASS = {
    "client_script": 1,
    "custom_docperm": 203,
    "custom_doctype": 4,
    "in_place_core_edit": 31,
    "naming_series": 119,
    "print_format": 4,
    "server_script": 5,
    "translation": 6,
}
EXPECTED_BY_VERDICT = {
    "db_only": 214,
    "discardable_core_edit": 10,
    "enumerate_only": 9,
    "fixture_equivalent_core_edit": 18,
    "human_review_core_edit": 3,
    "informational": 119,
}


def test_baseline_present_and_intact() -> None:
    assert BASELINE.exists(), f"V13 baseline missing: {BASELINE}"
    report = json.loads(BASELINE.read_text())
    assert report["substrate"]["vm"] == "dev01", report["substrate"]
    summary = report["summary"]
    assert summary["total_drifts"] == EXPECTED_TOTAL, summary["total_drifts"]
    assert summary["by_class"] == EXPECTED_BY_CLASS, summary["by_class"]
    assert summary["by_verdict"] == EXPECTED_BY_VERDICT, summary["by_verdict"]
    # the drift list length must agree with the summary total
    assert len(report["drifts"]) == EXPECTED_TOTAL, len(report["drifts"])


if __name__ == "__main__":
    test_baseline_present_and_intact()
    print("OK test_baseline_dev01")
    sys.exit(0)
