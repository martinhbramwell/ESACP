"""Stage 10 — apply the target version's catalogued post-migrate fixups in-leg.

Wraps the shared `v16_post_migrate_fixups` primitive so the automated upgrade
leg runs the fixups belonging to its target version, with no separate manual
dispatcher call. For the V15 leg: #626 server-scripts (enables the tenant's
DB-resident commission Server Scripts), R3 print-format disable, R8 naming-
series probe. The V16 leg additionally runs R1 homepage. Runs after the
scheduler resumes (site reachable) and before acceptance.
"""

from __future__ import annotations

from tools.pipeline.orchestration.v16_post_migrate_fixups import (
    apply_v16_post_migrate_fixups,
)
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def make_fixups_stage(version: int):
    """Build the Stage-10 unit that applies ``version``'s post-migrate fixups."""
    def apply_fixups(config: Config, emit: Emit) -> TaskResult:
        return apply_v16_post_migrate_fixups(config, emit, version)

    return apply_fixups
