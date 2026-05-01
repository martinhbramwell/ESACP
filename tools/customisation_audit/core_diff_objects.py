"""Diff-block extraction + JSON helpers shared across rules."""
from __future__ import annotations
import json


def _virtual_close(cur: list[str], out: list[str]) -> None:
    if cur and not cur[-1].strip().endswith("}"):
        cur.append("  }")
    out.append("\n".join(cur))


def scan_added_objects(diff: str) -> list[str]:
    """Extract `+ {...}` JSON additions; virtually close git-truncated blocks."""
    out, cur, in_block = [], [], False
    for line in diff.splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            body, stripped = line[1:], line[1:].strip()
            if not in_block:
                if stripped == "{":
                    cur, in_block = [body], True
                continue
            cur.append(body)
            if stripped in ("},", "}"):
                out.append("\n".join(cur))
                cur, in_block = [], False
        elif in_block:
            _virtual_close(cur, out)
            cur, in_block = [], False
    if in_block:
        _virtual_close(cur, out)
    return out


def parse_object(text: str) -> dict | None:
    try:
        obj = json.loads(text.rstrip().rstrip(","))
    except (json.JSONDecodeError, ValueError):
        return None
    return obj if isinstance(obj, dict) else None


def parent_doctype(text: str) -> str:
    obj = parse_object(text) if text else None
    return obj.get("name", "") if obj else ""


def load_pair(before: str, after: str) -> tuple[dict | None, dict | None]:
    return parse_object(before), parse_object(after)
