#!/usr/bin/env python3
"""Round-trip test: add→remove must leave hosts_map.yml byte-identical.

Run directly: ``./tools/pipeline/orchestration/test_hosts_map_remove.py``
Exit 0 on pass, 1 on fail. No pytest dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.pipeline.orchestration.host_registration_block import (  # noqa: E402
    MARKER, build_host_block,
)
from tools.pipeline.orchestration.hosts_map_remove import (  # noqa: E402
    remove_from_hosts_map,
)

# Frozen inline fixture (#665): the test must NOT couple to the live, evolving
# hosts_map.yml. A real entry that collides with the synthetic host (e.g. the
# now-real `dev01`) breaks the round-trip. This snippet only needs to contain
# the insertion MARKER and be byte-stable across an add→remove cycle.
FROZEN_HOSTS_MAP = (
    "groups:\n"
    "  kvm:\n"
    "    saconsole:\n"
    "      hostname: saconsole\n"
    "      nickname: SACON\n"
    f"{MARKER} (frozen test fixture)\n"
)


def test_round_trip_byte_identical(tmp_path: Path) -> None:
    original_bytes = FROZEN_HOSTS_MAP.encode()

    work = tmp_path / "hosts_map.yml"
    work.write_bytes(original_bytes)

    # Synthetic, non-colliding hostname — must not match any real entry (#665).
    block = build_host_block(
        hostname="zzz_test_host", nickname="ZZZT",
        virbr0_ip="192.168.122.250", wg_ip="10.10.0.250",
        hypervisor="toshiba", vm_role="dev:unspecified",
        backend="kvm", zone="development",
    )
    text = work.read_text()
    assert MARKER in text, f"marker {MARKER!r} must exist in fixture"
    work.write_text(text.replace(MARKER, block + MARKER))

    remove_from_hosts_map("zzz_test_host", work, emit=lambda _m: None)

    assert work.read_bytes() == original_bytes, (
        "hosts_map.yml is not byte-identical after add→remove"
    )


def main() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        test_round_trip_byte_identical(Path(td))
    print("OK  add→remove round-trip is byte-identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
