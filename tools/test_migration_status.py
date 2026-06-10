#!/usr/bin/env python3
"""Colocated tests for the migration status probe (S0).

Exercise the pure cores offline — catalogue coverage counting and proof-log
parsing — so the probe's reporting is correct without a live bench or catalogue.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.migration_status import catalogue_coverage, parse_proof_log  # noqa: E402


def test_catalogue_coverage_counts_entries_signoff_and_sections():
    cat = {
        "entries": [
            {"operator_confirmed": False, "business_relevance": "TBD", "suite_section": "A1"},
            {"operator_confirmed": True, "business_relevance": "high", "suite_section": "A1"},
            {"operator_confirmed": False, "business_relevance": "TBD", "suite_section": "E"},
        ]
    }
    cov = catalogue_coverage(cat)
    assert cov["total"] == 3
    assert cov["confirmed"] == 1
    assert cov["tbd"] == 2
    assert cov["sections"] == {"A1": 2, "E": 1}


def test_catalogue_coverage_handles_empty_catalogue():
    cov = catalogue_coverage({})
    assert cov == {"total": 0, "confirmed": 0, "tbd": 0, "sections": {}}


def test_catalogue_coverage_treats_missing_relevance_as_tbd():
    cov = catalogue_coverage({"entries": [{"operator_confirmed": True}]})
    assert cov["tbd"] == 1  # absent business_relevance counts as outstanding


def test_parse_proof_log_extracts_step_command_and_pass():
    text = (
        "STEP: S0a — tooling\n"
        "DATE: 2026-06-10\n"
        "PROOF COMMAND: ./tools/run_tests.py\n"
        "--- OUTPUT ---\nall green\n--- VERDICT ---\nPASS\nCOMMIT: abc123\n"
    )
    rec = parse_proof_log(text)
    assert rec["step"] == "S0a — tooling"
    assert rec["command"] == "./tools/run_tests.py"
    assert rec["verdict"] == "PASS"


def test_parse_proof_log_reports_fail_when_no_pass_line():
    rec = parse_proof_log("STEP: S9\nPROOF COMMAND: false\n--- VERDICT ---\nFAIL: broke\n")
    assert rec["verdict"] == "FAIL"


def test_parse_proof_log_blank_when_fields_absent():
    rec = parse_proof_log("nothing structured here\n")
    assert rec["step"] == "" and rec["command"] == ""


if __name__ == "__main__":
    from tools.testkit import run_module_tests

    raise SystemExit(run_module_tests(globals()))
