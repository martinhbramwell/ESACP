"""Pipeline type definitions — TaskResult, Config, Emit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

# Log callback — decoupled from the job system.
Emit = Callable[[str], None]


@dataclass(frozen=True)
class TaskResult:
    """Outcome of a single pipeline task."""

    success: bool
    changed: bool
    message: str


@dataclass(frozen=True)
class Config:
    """Immutable configuration for a pipeline run.

    Tasks receive this; they never mutate it.
    ``target_ip`` is set by ``build_config`` — provision uses virbr0_ip,
    refresh uses wg_ip.  Tasks never choose which IP to use.
    """

    hostname: str
    nickname: str
    zone: str
    backend: str
    target_ip: str
    wg_ip: str
    virbr0_ip: str

    site_url: str
    domain: str
    erp_user: str
    erp_user_pwd: str
    db_root_pwd: str

    bench_dir: str
    bench_dir_orig: str

    provision_mode: str  # "restored" or "generic"

    hypervisor: str | None
    ssh_key: str
    ssh_opts: list[str]
    project_root: str
