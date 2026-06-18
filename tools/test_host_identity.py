#!/usr/bin/env python3
"""Colocated tests for the SSH-identity resolvers.

Covers the operator identity (ESACP#567/#396/#451) and the guest VM user
(ESACP#583).  These assert the wiring (config → resolver), not hardcoded
identity values, so they survive an identity change without edits.
"""

import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.host_identity import (  # noqa: E402
    GROUP_VARS_KVM_PATH,
    GUEST_VM_USER,
    HOSTS_MAP_PATH,
    guest_vm_user,
    hypervisor_user,
    operator_pubkey,
    operator_ssh_key,
)


def test_operator_ssh_key_is_absolute_and_fully_expanded():
    key = operator_ssh_key()
    assert os.path.isabs(key)
    assert "{{" not in key and "~" not in key  # no unexpanded HOME/tilde


def test_operator_ssh_key_matches_group_vars_basename():
    kvm = yaml.safe_load(GROUP_VARS_KVM_PATH.read_text())
    configured = kvm["ansible_ssh_private_key_file"]
    assert Path(operator_ssh_key()).name == configured.rsplit("/", 1)[-1]


def test_operator_pubkey_is_private_key_plus_pub():
    assert str(operator_pubkey()) == operator_ssh_key() + ".pub"


def test_hypervisor_user_matches_controller_block():
    hm = yaml.safe_load(HOSTS_MAP_PATH.read_text())
    configured = hm["groups"]["controller"]["local"]["hypervisor_user"]
    assert hypervisor_user() == configured


def test_hypervisor_user_falls_back_to_env_user(monkeypatch):
    import tools.host_identity as hi

    monkeypatch.setattr(hi, "_hosts_map", {"groups": {"controller": {"local": {}}}})
    monkeypatch.setenv("USER", "ci-runner")
    assert hi.hypervisor_user() == "ci-runner"


# ── Guest VM user (ESACP#583) ────────────────────────────────────────────────


def test_guest_vm_user_matches_group_vars_ansible_user():
    kvm = yaml.safe_load(GROUP_VARS_KVM_PATH.read_text())
    assert guest_vm_user() == kvm["ansible_user"]


def test_guest_vm_user_constant_equals_resolver():
    assert GUEST_VM_USER == guest_vm_user()


def test_guest_vm_user_falls_back_to_you(monkeypatch, tmp_path):
    import tools.host_identity as hi

    empty = tmp_path / "kvm.yml"
    empty.write_text("ansible_python_interpreter: /usr/bin/python3\n")
    monkeypatch.setattr(hi, "GROUP_VARS_KVM_PATH", empty)
    assert hi.guest_vm_user() == "you"


if __name__ == "__main__":
    from tools.testkit import run_module_tests
    raise SystemExit(run_module_tests(globals()))
