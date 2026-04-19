#!/usr/bin/env python3
"""Acceptance test for ./tools/esacp.py addHost — happy/conflict/invalid.

Uses a disposable hostname with scratch IPs (outside any real range) and
cleans up after the run via the same pipeline primitives used by destroy.
Idempotent — a pre-run cleanup makes repeated execution safe.

Run: ``./tools/cli/verify_add_host.py`` → exit 0 on pass.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools.cli._common import PROJECT_ROOT  # noqa: E402

TMP_HOST   = "verify-add-host-tmp"
TMP_WG_IP  = "10.10.0.250"
TMP_VBR_IP = "192.168.122.250"
ESACP      = str(PROJECT_ROOT / "tools" / "esacp.py")
GUARDED    = [PROJECT_ROOT / "hosts_map.yml",
              PROJECT_ROOT / "ansible" / "inventory" / "kvm.yml"]


def _cli(args):
    return subprocess.run([ESACP] + args, capture_output=True, text=True)


def main() -> int:
    snapshots = {p: p.read_bytes() for p in GUARDED}
    try:
        print("[1/3] happy path — expect exit 0")
        r = _cli(["addHost", TMP_HOST, "--wg-ip", TMP_WG_IP, "--virbr0-ip", TMP_VBR_IP])
        if r.returncode != 0:
            print(f"  FAIL rc={r.returncode}\n  stdout: {r.stdout}\n  stderr: {r.stderr}")
            return 1

        print("[2/3] conflict — re-register same host, expect exit 3")
        r = _cli(["addHost", TMP_HOST, "--wg-ip", TMP_WG_IP, "--virbr0-ip", TMP_VBR_IP])
        if r.returncode != 3:
            print(f"  FAIL rc={r.returncode} (expected 3)")
            return 1

        print("[3/3] invalid hostname (uppercase) — expect exit 2")
        r = _cli(["addHost", "BadHost", "--wg-ip", "10.10.0.251", "--virbr0-ip", "192.168.122.251"])
        if r.returncode != 2:
            print(f"  FAIL rc={r.returncode} (expected 2)")
            return 1

        print("✓ all three paths verified")
        return 0
    finally:
        for p, content in snapshots.items():
            p.write_bytes(content)


if __name__ == "__main__":
    sys.exit(main())
