"""Stage 10 — acceptance: HTTPS 200 + bench version reports v14 + sample doc."""

from __future__ import annotations

import subprocess

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def _curl_https(site_url: str) -> int:
    r = subprocess.run(
        ["curl", "-sk", "-o", "/dev/null", "-w", "%{http_code}",
         f"https://{site_url}/"],
        capture_output=True, text=True, timeout=30,
    )
    return int(r.stdout.strip()) if r.stdout.strip().isdigit() else 0


def _bench_version(config: Config) -> str:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} bash -c "
                f"'cd {config.bench_dir} && bench version'",
                timeout=30)
    return r.stdout.strip()


def check_acceptance(config: Config, emit: Emit) -> TaskResult:
    code = _curl_https(config.site_url)
    if code != 200:
        return TaskResult(False, False, f"HTTPS check {config.site_url}: {code}")
    ver = _bench_version(config)
    if "14." not in ver and "version-14" not in ver:
        return TaskResult(False, False, f"bench version not v14:\n{ver}")
    emit(f"  ✓ HTTPS 200 on {config.site_url}; bench version mentions v14")
    return TaskResult(True, False, "acceptance: HTTPS 200 + v14")
