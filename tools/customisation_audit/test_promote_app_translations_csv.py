#!/usr/bin/env python3
"""Tests for promote_app_translations_csv — append CSV row idempotently."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["BESPOKE_ROOT"] = "/tmp/test-bespoke-tx"

from tools.customisation_audit import promote_app_translations_csv as mod  # noqa: E402


def _drift(owning: str = "ce_sri", lang: str = "es",
           src: str = "To Stock", tx: str = "Al Almacén") -> dict:
    return {
        "fixture_path_proposed": "",
        "owning_app_proposed": owning,
        "doctype": "Translation",
        "row_data": {"language": lang, "source_text": src, "translated_text": tx,
                     "name": "abc123"},
    }


def test_target_constructs_from_owning_and_lang() -> None:
    d = _drift(owning="returnable", lang="es-EC")
    assert mod.target(d) == Path("/tmp/test-bespoke-tx/returnable/returnable/translations/es-EC.csv")


def test_compose_appends_new_row_to_empty_file() -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["BESPOKE_ROOT"] = td
        import importlib, tools.bespoke_root as br
        importlib.reload(br); importlib.reload(mod.promote_common); importlib.reload(mod)
        d = _drift()
        out = mod.compose(d)
        assert "To Stock,Al Almacén," in out


def test_compose_appends_to_existing_file() -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["BESPOKE_ROOT"] = td
        import importlib, tools.bespoke_root as br
        importlib.reload(br); importlib.reload(mod.promote_common); importlib.reload(mod)
        d = _drift()
        path = mod.target(d)
        path.parent.mkdir(parents=True)
        path.write_text("Existing,Existente,\n")
        out = mod.compose(d)
        assert "Existing,Existente," in out
        assert "To Stock,Al Almacén," in out


def test_compose_skips_duplicate_source_text() -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["BESPOKE_ROOT"] = td
        import importlib, tools.bespoke_root as br
        importlib.reload(br); importlib.reload(mod.promote_common); importlib.reload(mod)
        d = _drift(src="Make", tx="Fabricar")
        path = mod.target(d)
        path.parent.mkdir(parents=True)
        path.write_text("Make,Fabricar,\n")
        out = mod.compose(d)
        assert out.count("Make") == 1


def test_apply_writes_file() -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["BESPOKE_ROOT"] = td
        import importlib, tools.bespoke_root as br
        importlib.reload(br); importlib.reload(mod.promote_common); importlib.reload(mod)
        d = _drift()
        out = mod.apply(d)
        assert out.exists()
        assert "To Stock" in out.read_text()


if __name__ == "__main__":
    test_target_constructs_from_owning_and_lang()
    test_compose_appends_new_row_to_empty_file()
    test_compose_appends_to_existing_file()
    test_compose_skips_duplicate_source_text()
    test_apply_writes_file()
    print("OK test_promote_app_translations_csv")
