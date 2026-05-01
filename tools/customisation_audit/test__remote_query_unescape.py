#!/usr/bin/env python3
"""Tests for _remote_query._unescape — reverse mysql -B batch-mode escaping (#333)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# _remote_query.py is a runner script not part of the package; import by file path.
import importlib.util
_path = Path(__file__).resolve().parent / "_remote_query.py"
_spec = importlib.util.spec_from_file_location("_remote_query", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]


def test_unescape_newline() -> None:
    assert _mod._unescape("a\\nb") == "a\nb"


def test_unescape_tab() -> None:
    assert _mod._unescape("a\\tb") == "a\tb"


def test_unescape_carriage_return() -> None:
    assert _mod._unescape("a\\rb") == "a\rb"


def test_unescape_backslash() -> None:
    assert _mod._unescape("a\\\\b") == "a\\b"


def test_unescape_null() -> None:
    assert _mod._unescape("a\\0b") == "a\0b"


def test_unescape_ctrl_z() -> None:
    assert _mod._unescape("a\\Zb") == "a\x1ab"


def test_unescape_no_escapes_passthrough() -> None:
    assert _mod._unescape("plain text") == "plain text"


def test_unescape_unknown_sequence_kept() -> None:
    """Unrecognised \\X sequences pass through literally — defensive default."""
    assert _mod._unescape("a\\xb") == "a\\xb"


def test_unescape_trailing_backslash_kept() -> None:
    assert _mod._unescape("foo\\") == "foo\\"


def test_unescape_realistic_js_body() -> None:
    raw = "frappe.ui.form.on('X', {\\n\\trefresh: () => {}\\n});"
    expected = "frappe.ui.form.on('X', {\n\trefresh: () => {}\n});"
    assert _mod._unescape(raw) == expected


def test_unescape_double_escaped_backslash_in_js() -> None:
    """`\\\\n` (literal backslash + n) must NOT become a newline."""
    # Source value is two characters: backslash-n  →  encoded by mysql -B as \\n
    # When decoded, must yield single backslash + n (a regex pattern, e.g. /\n/).
    assert _mod._unescape("\\\\n") == "\\n"


if __name__ == "__main__":
    test_unescape_newline()
    test_unescape_tab()
    test_unescape_carriage_return()
    test_unescape_backslash()
    test_unescape_null()
    test_unescape_ctrl_z()
    test_unescape_no_escapes_passthrough()
    test_unescape_unknown_sequence_kept()
    test_unescape_trailing_backslash_kept()
    test_unescape_realistic_js_body()
    test_unescape_double_escaped_backslash_in_js()
    print("OK test__remote_query_unescape")
