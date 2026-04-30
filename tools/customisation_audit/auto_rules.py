"""Auto-rule pattern matching for customisation_attribution.yml (#319).

Consulted by attribution.resolve() AFTER per-name lookup. Each rule has
a `class`, a `when:` block (matchers), and a `then:` block (resolution).
All matchers in a rule's `when:` must pass (AND). First matching rule wins.

Supported matchers:
  dt_in:        list — row["dt"] must be in the list
  name_pattern: str  — drift name must match SQL LIKE pattern (% → .*)
  view:         str  — exact match on row["view"]
  standard:     str  — exact match on row["standard"]

Malformed rules (missing class/when/then, unknown matcher key) are skipped
silently — preserves audit-time forgiveness; manual count surfaces the gap."""

from __future__ import annotations

import re
from typing import Optional


def _like_to_regex(pattern: str) -> str:
    """Translate SQL LIKE % wildcard to a Python regex."""
    return re.escape(pattern).replace("%", ".*")


_MATCHERS = {
    "dt_in": lambda v, name, row: isinstance(v, list) and row.get("dt") in v,
    "name_pattern": lambda v, name, row: isinstance(v, str) and bool(re.fullmatch(_like_to_regex(v), name)),
    "view": lambda v, name, row: row.get("view") == v,
    "standard": lambda v, name, row: row.get("standard") == v,
}


def _rule_matches(when: dict, name: str, row: dict) -> bool:
    if not when:
        return False
    for key, val in when.items():
        matcher = _MATCHERS.get(key)
        if matcher is None or not matcher(val, name, row):
            return False
    return True


def _valid_then(then: object) -> bool:
    return isinstance(then, dict) and "owning_app" in then and "promotion_strategy" in then


def match(amap: dict, drift_class: str, name: str, row: dict) -> Optional[dict]:
    """First auto-rule whose `class` matches and whose `when` matches the row.
    Returns the rule's `then:` dict, or None."""
    for rule in amap.get("auto_rules") or []:
        if not isinstance(rule, dict) or rule.get("class") != drift_class:
            continue
        if _rule_matches(rule.get("when") or {}, name, row) and _valid_then(rule.get("then")):
            return rule["then"]
    return None
