#!/usr/bin/env python3
"""Tests: host-RAM guard for VM start + template build (ESACP #655 — S110 OOM).
Run directly: ./tools/pipeline/orchestration/test_memory_guard.py (exit 0/1)."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.pipeline.orchestration import memory_guard  # noqa: E402

_GIB = 1024 * 1024   # KiB in a GiB


def _ok(stdout: str) -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def _fail(stderr: str) -> SimpleNamespace:
    return SimpleNamespace(returncode=1, stdout="", stderr=stderr)


def _fake_host(host_gib: int, running: dict[str, int]):
    """Return a virsh_ssh stand-in for a host of *host_gib* GiB with the named
    running domains each sized by *running* (name -> GiB)."""
    def fake(hypervisor: str, cmd: str, timeout: int = 30):
        if cmd == "nodeinfo":
            return _ok(f"Memory size:         {host_gib * _GIB} KiB\n")
        if cmd == "list --name":
            return _ok("\n".join(running) + "\n")
        if cmd.startswith("dominfo "):
            vm = cmd.split(" ", 1)[1]
            return _ok(f"Max memory:     {running.get(vm, 0) * _GIB} KiB\n")
        raise AssertionError(f"unexpected virsh cmd: {cmd}")
    return fake


def test_build_ram_fits_returns_none() -> None:
    # 16 GiB host, 8 GiB in use, 4 GiB build VM: 8+4=12 < 16-2=14 → OK.
    fake = _fake_host(16, {"saconsole": 4, "dev01": 4})
    with mock.patch.object(memory_guard, "virsh_ssh", fake):
        assert memory_guard.check_memory_for_ram("toshiba", 4 * _GIB, "packer-build") is None


def test_build_ram_oversubscribes_is_rejected() -> None:
    # The S110 topology: 15 GiB host, 13 GiB running, +4 GiB build = 17 > 13.
    fake = _fake_host(15, {"saconsole": 4, "dev01": 3, "dev15_01": 6})
    with mock.patch.object(memory_guard, "virsh_ssh", fake):
        msg = memory_guard.check_memory_for_ram("toshiba", 4 * _GIB, "packer-build")
    assert msg is not None and "Not enough memory" in msg
    assert "packer-build" in msg and "saconsole" in msg   # names the culprits


def test_nodeinfo_failure_surfaces_not_masked() -> None:
    def fake(hypervisor, cmd, timeout=30):
        return _fail("ssh: connect: no route to host")
    with mock.patch.object(memory_guard, "virsh_ssh", fake):
        msg = memory_guard.check_memory_for_ram("toshiba", 4 * _GIB, "packer-build")
    assert msg is not None and "Cannot query hypervisor memory" in msg


def test_check_memory_queries_target_domain() -> None:
    # check_memory must read the target's own Max memory then delegate.
    fake = _fake_host(16, {"saconsole": 4, "dev01": 4})
    with mock.patch.object(memory_guard, "virsh_ssh", fake):
        assert memory_guard.check_memory("toshiba", "dev01") is None


def test_check_memory_target_unknown_reports_error() -> None:
    def fake(hypervisor, cmd, timeout=30):
        if cmd.startswith("dominfo "):
            return _fail("error: failed to get domain 'ghost'")
        return _ok("")
    with mock.patch.object(memory_guard, "virsh_ssh", fake):
        msg = memory_guard.check_memory("toshiba", "ghost")
    assert msg is not None and "Cannot query VM config" in msg


def _run() -> int:
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL {name}: {exc}")
    print(f"\n{'OK' if not failures else f'{failures} FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
