"""Pipeline runner — iterate tasks, stop on first failure."""

from __future__ import annotations

from typing import Callable

from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def run_pipeline(
    tasks: list[Callable[[Config, Emit], TaskResult]],
    config: Config,
    emit: Emit,
) -> list[TaskResult]:
    """Execute *tasks* in order.  Stop on first failure."""
    results: list[TaskResult] = []
    for task in tasks:
        name = task.__name__
        emit(f"── {name} ──")
        result = task(config, emit)
        results.append(result)
        if not result.success:
            emit(f"  [FAIL] {name}: {result.message}")
            break
        tag = "[CHANGED]" if result.changed else "[OK]"
        emit(f"  {tag} {result.message}")
    return results
