#!/usr/bin/env python3
"""Tests for discover_translation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import (  # noqa: E402
    db_query, discover_translation as mod,
)
from tools.customisation_audit._test_support import patched  # noqa: E402
from tools.customisation_audit.audit_config import AuditConfig  # noqa: E402
from tools.customisation_audit.drift import Drift  # noqa: E402


def test_db_only_when_csv_lacks_source() -> None:
    cfg = AuditConfig("x", "x", ["ce_sri"], {})
    rows = [{"name": "trans-1", "language": "es", "source_text": "Custom Phrase",
             "translated_text": "Frase Personalizada"}]
    with patched(db_query, "run_query", lambda *a, **k: rows), \
         patched(mod, "_csv_sources", lambda apps, lang: set()):
        out = mod.run(cfg)
    assert len(out) == 1 and isinstance(out[0], Drift)
    assert out[0].verdict == "db_only"
    assert out[0].promotion_strategy == "app_translations_csv"


if __name__ == "__main__":
    test_db_only_when_csv_lacks_source()
    print("OK test_discover_translation")
