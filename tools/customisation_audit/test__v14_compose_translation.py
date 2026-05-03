#!/usr/bin/env python3
"""Tests for _v14_compose_translation — DB-side Translation rows."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import _v14_compose_translation as mod  # noqa: E402


def _drift() -> dict:
    return {
        "drift_class": "translation",
        "doctype": "Translation",
        "name": "abc123hash",
        "row_data": {
            "name": "abc123hash",
            "language": "es",
            "source_text": "Gross Year To Date",
            "translated_text": "Año Bruto Hasta La Fecha",
        },
    }


def test_matches_translation() -> None:
    assert mod.matches(_drift()) is True


def test_matches_translation_via_class_only() -> None:
    """JSON-loaded drifts use `class`, not `drift_class`; doctype 'Translation'
    might be missing — class alone must suffice."""
    d = {"class": "translation", "doctype": "(translation_csv)", "row_data": {}}
    assert mod.matches(d) is True


def test_does_not_match_unrelated_class_and_doctype() -> None:
    d = _drift()
    d["drift_class"] = "print_format"
    d["doctype"] = "Print Format"
    assert mod.matches(d) is False


def test_compose_emits_valid_python() -> None:
    ast.parse(mod.compose(_drift()))


def test_compose_uses_language_source_text_guard() -> None:
    src = mod.compose(_drift())
    assert "frappe.db.exists('Translation'" in src
    assert "'language': 'es'" in src
    assert "'source_text': 'Gross Year To Date'" in src


def test_compose_emits_translation_doc() -> None:
    src = mod.compose(_drift())
    assert '"doctype": "Translation"' in src
    assert '"language": "es"' in src
    assert '"translated_text": "A\\u00f1o Bruto Hasta La Fecha"' in src


if __name__ == "__main__":
    test_matches_translation()
    test_matches_translation_via_class_only()
    test_does_not_match_unrelated_class_and_doctype()
    test_compose_emits_valid_python()
    test_compose_uses_language_source_text_guard()
    test_compose_emits_translation_doc()
    print("OK test__v14_compose_translation")
