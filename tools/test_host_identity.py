"""Colocated tests for the operator-SSH-identity resolvers (ESACP#567/#396/#451).

These assert the wiring (config → resolver), not hardcoded operator values, so
they survive an operator change without edits.
"""

import os
from pathlib import Path

import yaml

from tools.host_identity import (
    GROUP_VARS_KVM_PATH,
    HOSTS_MAP_PATH,
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
