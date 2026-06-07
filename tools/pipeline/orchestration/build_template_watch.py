"""Watch a detached hub build: tail its log + classify its exit sentinel.

Split out of build_template.py so the exit-classification is unit-testable and
both files stay under the size cap (ESACP #637).
"""

from __future__ import annotations

import subprocess
import time

from tools.pipeline.stages.common.types import Emit

# Consecutive *unreachable* polls (× ~5 s) before the watch gives up. The build
# is nohup-detached on the hub, so a transient SSH blip must NOT read as a build
# failure (#637) — only a sustained outage (~5 min) aborts the watch.
_MAX_POLL_MISSES = 60


def parse_exit(returncode: int, stdout: str) -> int | None:
    """Terminal build exit code from one poll, or None if still pending.

    None means "keep waiting": either a transport blip (ssh returncode != 0, or
    empty / non-numeric stdout) or the -1 sentinel (build.sh has not written its
    exit file yet). A non-negative int is terminal (0 = success). A transport
    blip is NEVER turned into a synthesised failure — that was the #637 bug.
    """
    code = stdout.strip()
    if returncode != 0 or not code.lstrip("-").isdigit():
        return None
    val = int(code)
    return None if val < 0 else val


def _flush_log(hub_ssh: list[str], remote_log: str, offset: int, emit: Emit) -> int:
    r = subprocess.run(hub_ssh + [f"tail -c +{offset + 1} {remote_log} 2>/dev/null || true"],
                       capture_output=True, text=True)
    if r.stdout:
        for line in r.stdout.splitlines():
            if line.strip():
                emit(line)
        offset += len(r.stdout.encode("utf-8"))
    return offset


def watch_build(hub_ssh: list[str], remote_log: str, remote_exit: str, emit: Emit) -> None:
    """Poll the detached build until its exit sentinel resolves.

    Returns cleanly on exit code 0. Raises RuntimeError on a real non-zero build
    exit, or after _MAX_POLL_MISSES consecutive unreachable polls.
    """
    offset, misses = 0, 0
    while True:
        time.sleep(5)
        offset = _flush_log(hub_ssh, remote_log, offset, emit)
        r = subprocess.run(hub_ssh + [f"cat {remote_exit} 2>/dev/null || echo -1"],
                           capture_output=True, text=True)
        code = parse_exit(r.returncode, r.stdout)
        if code is None:
            misses = misses + 1 if r.returncode != 0 else 0
            if misses >= _MAX_POLL_MISSES:
                raise RuntimeError("hub unreachable — build watch aborted")
            continue
        _flush_log(hub_ssh, remote_log, offset, emit)
        if code:
            raise RuntimeError(f"build.sh exited with code {code}")
        emit("── Build complete — new image ready on toshiba ──")
        return
