"""Build + serialise the delta report. Schema per plan §6."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from tools.customisation_audit.drift import Drift

SCHEMA_VERSION = "1"


def _drift_to_dict(d: Drift) -> dict[str, Any]:
    out = asdict(d)
    out["class"] = out.pop("drift_class")
    return out


def emit(drifts: list[Drift], substrate: dict[str, str]) -> dict[str, Any]:
    """Build the report dict. Drifts sorted by id for stable output."""
    sorted_drifts = sorted(drifts, key=lambda d: d.id)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "substrate": substrate,
        "summary": {
            "total_drifts": len(sorted_drifts),
            "by_class": dict(Counter(d.drift_class for d in sorted_drifts)),
            "by_verdict": dict(Counter(d.verdict for d in sorted_drifts)),
        },
        "drifts": [_drift_to_dict(d) for d in sorted_drifts],
    }


def to_json(report: dict[str, Any]) -> str:
    """Stable serialisation: sort_keys ensures byte-identical round-trip."""
    return json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False)
