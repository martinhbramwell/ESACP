#!/usr/bin/env python3
"""Test: KvmEnv sources its ProxyJump/SCP user from the operator-identity
resolver, not a hardcoded literal (ESACP#591).

Asserts the wiring (config → resolver), the same contract as
test_host_identity.py — so it survives an identity change without edits.

Run directly: ``./tools/pipeline/stages/test_env_kvm.py``
Exit 0 on pass, 1 on fail. No pytest dependency.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.host_identity import hypervisor_user  # noqa: E402
from tools.pipeline.stages.env_kvm import KvmEnv  # noqa: E402


def main() -> int:
    expected = hypervisor_user()
    checks = [
        ("KvmEnv() default", KvmEnv().hypervisor_user),
        ("KvmEnv.from_project_root", KvmEnv.from_project_root(REPO_ROOT).hypervisor_user),
    ]
    ok = True
    for label, got in checks:
        passed = got == expected
        ok = ok and passed
        print(f"  {'✓' if passed else '❌'} {label} = {got!r} (resolver = {expected!r})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
