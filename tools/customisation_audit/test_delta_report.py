#!/usr/bin/env python3
"""Tests for delta_report.emit + to_json — round-trip stability."""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit.delta_report import emit, to_json  # noqa: E402
from tools.customisation_audit.drift import Drift  # noqa: E402


def _sample_drifts() -> list[Drift]:
    return [
        Drift(id="zzz", drift_class="custom_field", verdict="db_only",
              doctype="Sales Invoice", name="A", owning_app_proposed="ce_sri",
              fixture_path_proposed="", promotion_strategy="fixture_json"),
        Drift(id="aaa", drift_class="workflow", verdict="db_only",
              doctype="Workflow", name="B", owning_app_proposed="",
              fixture_path_proposed="", promotion_strategy="manual"),
    ]


def test_round_trip_byte_identical() -> None:
    substrate = {"vm": "dev01", "frappe_version": "13.x", "erpnext_version": "13.x"}
    report = emit(_sample_drifts(), substrate)
    s1 = to_json(report)
    s2 = to_json(json.loads(s1))
    assert s1 == s2, "round-trip not byte-identical"


def test_drifts_sorted_by_id() -> None:
    report = emit(_sample_drifts(), {"vm": "dev01"})
    ids = [d["id"] for d in report["drifts"]]
    assert ids == sorted(ids), f"drifts not sorted by id: {ids}"


def test_summary_counts_correct() -> None:
    report = emit(_sample_drifts(), {"vm": "dev01"})
    assert report["summary"]["total_drifts"] == 2
    assert report["summary"]["by_class"] == {"custom_field": 1, "workflow": 1}


if __name__ == "__main__":
    test_round_trip_byte_identical()
    test_drifts_sorted_by_id()
    test_summary_counts_correct()
    print("OK test_delta_report")
