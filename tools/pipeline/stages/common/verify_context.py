#!/usr/bin/env python3
"""VerifyContext model shared by the per-stage verify scripts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerifyContext:
    hostname: str
    host_cfg: dict
    project_root: str
    use_wg: bool
    target_ip: str
    ssh_opts: list[str]
    ssh_key: str
    hypervisor: str
    virbr0_ip: str
    wg_ip: str
    erp_user: str
    nickname: str
    bench_dir: str
    bench_dir_orig: str
    site_url: str
    domain: str
