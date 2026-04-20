#!/usr/bin/env python3
"""Acceptance test for ./tools/esacp.py provisionGeneric — argparse + dispatcher validation.

Covers only the fast-reject paths; the macro (stages 1-9) is NOT invoked.
End-to-end correctness of the macro + wizard_run is covered by Matrix Run 03.

Paths tested:
  1. unknown VM                                  → exit 1 (main() VM_COMMANDS check)
  2. hub VM (wg_role == "hub")                   → exit 1 (dispatcher hub-guard)
  3. --wizard-mode=replay without --wizard-arg   → exit 2 (dispatcher arg-guard)
  4. --wizard-mode=existing without --wizard-arg → exit 2 (dispatcher arg-guard)
  5. --wizard-mode=bogus                         → exit 2 (argparse choices rejection)

Run: ``./tools/cli/verify_provision_generic.py`` → exit 0 on pass.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools.cli._common import PROJECT_ROOT, hub_vm, kvm_hosts, load_config  # noqa: E402

ESACP = str(PROJECT_ROOT / "tools" / "esacp.py")


def _cli(args):
    return subprocess.run([ESACP] + args, capture_output=True, text=True)


def _non_hub_vm(config) -> str:
    for name, info in kvm_hosts(config).items():
        if info.get("wg_role") != "hub":
            return name
    raise RuntimeError("No non-hub VM in hosts_map.yml")


def main() -> int:
    config = load_config()
    hub = hub_vm(config)
    vm = _non_hub_vm(config)
    if not hub:
        print("FAIL: no hub VM in hosts_map.yml"); return 1

    cases = [
        (["provisionGeneric", "nonexistent-vm-xyz"],                                   1, "unknown VM"),
        (["provisionGeneric", hub],                                                    1, "hub rejected"),
        (["provisionGeneric", vm, "--wizard-mode", "replay"],                          2, "replay w/o arg"),
        (["provisionGeneric", vm, "--wizard-mode", "existing"],                        2, "existing w/o arg"),
        (["provisionGeneric", vm, "--wizard-mode", "bogus"],                           2, "invalid wizard-mode"),
    ]
    for i, (argv, want_rc, label) in enumerate(cases, 1):
        r = _cli(argv)
        if r.returncode != want_rc:
            print(f"[{i}/{len(cases)}] FAIL: {label} — got rc={r.returncode} (want {want_rc})")
            print(f"  stdout: {r.stdout}")
            print(f"  stderr: {r.stderr}")
            return 1
        print(f"[{i}/{len(cases)}] OK: {label} (rc={want_rc})")

    print("✓ all fast-reject paths verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
