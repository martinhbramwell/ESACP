#!/usr/bin/env python3
"""Minimal dependency-free test harness (ESACP#663).

Lets a colocated ``test_*.py`` self-run as an executable without pytest:
discover module-level ``test_*`` callables, inject ``monkeypatch`` / ``tmp_path``
shims by parameter name, run each, restore state, return 0/1. House style is
"no pytest"; a module needing a fixture we don't provide fails loudly.
"""

from __future__ import annotations

import inspect
import os
import shutil
import tempfile
from pathlib import Path


def _restore_env(name: str, old: str | None) -> None:
    if old is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = old


class _MonkeyPatch:
    """Subset of pytest's monkeypatch: setattr(obj, name, value) + setenv."""

    def __init__(self) -> None:
        self._undo: list = []

    def setattr(self, target: object, name: str, value: object) -> None:
        old = getattr(target, name)
        self._undo.append(lambda: setattr(target, name, old))
        setattr(target, name, value)

    def setenv(self, name: str, value: str) -> None:
        self._undo.append(lambda old=os.environ.get(name): _restore_env(name, old))
        os.environ[name] = value

    def undo(self) -> None:
        for fn in reversed(self._undo):
            fn()
        self._undo.clear()


def _make_fixture(name: str, teardown: list) -> object:
    if name == "monkeypatch":
        mp = _MonkeyPatch()
        teardown.append(mp.undo)
        return mp
    if name == "tmp_path":
        td = tempfile.mkdtemp(prefix="esacp-testkit-")
        teardown.append(lambda: shutil.rmtree(td, ignore_errors=True))
        return Path(td)
    raise KeyError(f"testkit has no fixture {name!r}")


def run_module_tests(namespace: dict) -> int:
    """Run every ``test_*`` defined in *namespace*; return 0/1 exit code."""
    owner = namespace.get("__name__")
    tests = sorted(
        (n, f) for n, f in namespace.items()
        if n.startswith("test_") and inspect.isfunction(f)
        and getattr(f, "__module__", None) == owner
    )
    failed = 0
    for name, fn in tests:
        teardown: list = []
        try:
            args = [_make_fixture(p, teardown) for p in inspect.signature(fn).parameters]
            fn(*args)
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001 — report, don't abort the run
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
        finally:
            for undo in reversed(teardown):
                undo()
    print(f"— {len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0
