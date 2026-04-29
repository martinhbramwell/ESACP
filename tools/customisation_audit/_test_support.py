"""Test helpers used by colocated test_*.py modules.

Each test file MUST add repo root to sys.path itself before importing this
module — otherwise ``from tools.customisation_audit._test_support import …``
fails before ``_test_support`` runs.
"""

from __future__ import annotations

import contextlib


@contextlib.contextmanager
def patched(obj: object, attr: str, value: object):
    """Temporarily replace obj.attr with value; restore on exit."""
    original = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        setattr(obj, attr, original)
