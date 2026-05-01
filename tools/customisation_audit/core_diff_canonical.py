"""JSON canonicalisation + business-state semantics for v14 migration safety."""
from __future__ import annotations

_NOISE_KEYS = {"modified", "field_order"}
_DEFAULT_VALUES = (0, "", None, [], {})


def canonicalize(v):
    if isinstance(v, dict):
        out = {}
        for k, val in v.items():
            if k in _NOISE_KEYS:
                continue
            cv = canonicalize(val)
            if cv in _DEFAULT_VALUES:
                continue
            out[k] = cv
        return out
    if isinstance(v, list):
        return [canonicalize(x) for x in v]
    return v


def _deletion_dominant(diff: str) -> bool:
    added = sum(len(l) for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    removed = sum(len(l) for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
    return removed > 2 * added


def has_new_business(before: dict, after: dict, diff: str = "") -> bool:
    br = {p.get("role") for p in before.get("permissions", []) if isinstance(p, dict)}
    ar = {p.get("role") for p in after.get("permissions", []) if isinstance(p, dict)}
    if ar - br:
        return True
    if _deletion_dominant(diff):
        return False
    if any(k not in before for k in after if k not in {"permissions", "fields"}):
        return True
    bf = {f.get("fieldname") for f in before.get("fields", []) if isinstance(f, dict)}
    af = {f.get("fieldname") for f in after.get("fields", []) if isinstance(f, dict)}
    return bool(af - bf)
