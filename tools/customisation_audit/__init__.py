"""Customisation discovery library — read-only audit of a dev VM substrate.

Phase 1 of the customisation discovery + promotion + V14 plan
(`~/.claude/plans/customisation-discovery-promotion.md`).

Each per-class `discover_*.py` module exposes ``run(config) -> list[Drift]``.
The package is consumed by the ``tools/identify_bad_customisations.py``
dispatcher; nothing here mutates state on the VM or in the source tree.
"""
