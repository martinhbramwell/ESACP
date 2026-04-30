#!/usr/bin/env python3
"""Tests for auto_rules — matcher dispatch, AND semantics, malformed-skip, precedence."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import auto_rules  # noqa: E402

_THEN_CE_FIX = {"owning_app": "ce_sri", "promotion_strategy": "fixture_json"}
_THEN_CE_PATCH = {"owning_app": "ce_sri", "promotion_strategy": "v14_patch_script"}


def test_like_to_regex_percent_wildcard() -> None:
    assert auto_rules._like_to_regex("PF:%") == "PF:.*"
    assert auto_rules._like_to_regex("%-Form") == "%\\-Form".replace("%", ".*")


def test_dt_in_matches_list_membership() -> None:
    rule = {"class": "custom_field", "when": {"dt_in": ["Sales Order", "Customer"]}, "then": _THEN_CE_FIX}
    amap = {"auto_rules": [rule]}
    assert auto_rules.match(amap, "custom_field", "X", {"dt": "Sales Order"}) == _THEN_CE_FIX
    assert auto_rules.match(amap, "custom_field", "X", {"dt": "Item"}) is None


def test_name_pattern_sql_like() -> None:
    rule = {"class": "client_script", "when": {"name_pattern": "%-Form"}, "then": _THEN_CE_FIX}
    amap = {"auto_rules": [rule]}
    assert auto_rules.match(amap, "client_script", "Address-Form", {}) == _THEN_CE_FIX
    assert auto_rules.match(amap, "client_script", "Address", {}) is None


def test_view_exact_match() -> None:
    rule = {"class": "client_script", "when": {"view": "Form"}, "then": _THEN_CE_FIX}
    amap = {"auto_rules": [rule]}
    assert auto_rules.match(amap, "client_script", "X", {"view": "Form"}) == _THEN_CE_FIX
    assert auto_rules.match(amap, "client_script", "X", {"view": "List"}) is None


def test_standard_exact_match() -> None:
    rule = {"class": "print_format", "when": {"standard": "No"}, "then": _THEN_CE_PATCH}
    amap = {"auto_rules": [rule]}
    assert auto_rules.match(amap, "print_format", "X", {"standard": "No"}) == _THEN_CE_PATCH
    assert auto_rules.match(amap, "print_format", "X", {"standard": "Yes"}) is None


def test_and_semantics_all_must_match() -> None:
    rule = {"class": "client_script", "when": {"name_pattern": "%-Form", "view": "Form"}, "then": _THEN_CE_FIX}
    amap = {"auto_rules": [rule]}
    assert auto_rules.match(amap, "client_script", "Address-Form", {"view": "Form"}) == _THEN_CE_FIX
    assert auto_rules.match(amap, "client_script", "Address-Form", {"view": "List"}) is None
    assert auto_rules.match(amap, "client_script", "Address", {"view": "Form"}) is None


def test_class_filter() -> None:
    rule = {"class": "custom_field", "when": {"dt_in": ["Sales Order"]}, "then": _THEN_CE_FIX}
    amap = {"auto_rules": [rule]}
    assert auto_rules.match(amap, "client_script", "X", {"dt": "Sales Order"}) is None


def test_first_matching_rule_wins() -> None:
    r1 = {"class": "print_format", "when": {"name_pattern": "PF:%"}, "then": _THEN_CE_PATCH}
    r2 = {"class": "print_format", "when": {"name_pattern": "PF:%"}, "then": _THEN_CE_FIX}
    assert auto_rules.match({"auto_rules": [r1, r2]}, "print_format", "PF: O. de V.", {}) == _THEN_CE_PATCH


def test_malformed_rules_skipped() -> None:
    bad = [
        "not a dict",
        {"class": "x"},  # no when, no then
        {"class": "x", "when": {"unknown_matcher": "v"}, "then": _THEN_CE_FIX},  # unknown matcher
        {"class": "x", "when": {"dt_in": ["A"]}, "then": "not a dict"},  # invalid then
        {"class": "x", "when": {"dt_in": ["A"]}, "then": {"owning_app": "y"}},  # missing strategy
    ]
    good = {"class": "x", "when": {"dt_in": ["A"]}, "then": _THEN_CE_FIX}
    assert auto_rules.match({"auto_rules": bad + [good]}, "x", "n", {"dt": "A"}) == _THEN_CE_FIX


def test_no_auto_rules_section() -> None:
    assert auto_rules.match({}, "custom_field", "X", {"dt": "Sales Order"}) is None
    assert auto_rules.match({"auto_rules": None}, "custom_field", "X", {"dt": "Sales Order"}) is None
    assert auto_rules.match({"auto_rules": []}, "custom_field", "X", {"dt": "Sales Order"}) is None


if __name__ == "__main__":
    for n, fn in list(globals().items()):
        if n.startswith("test_") and callable(fn):
            fn()
    print("OK test_auto_rules")
