#!/usr/bin/env bash
# config.sh — Shared configuration for all KVM platform scripts.
#
# Sources hosts_map.yml via parse_hosts_map.py, then layers env-overridable
# defaults for values not in the YAML (SSH alias, username, paths).
#
# Usage (from any KVM platform script):
#   source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
#
# Every variable can be overridden via ESACP_* environment variables.
# See parse_hosts_map.py for the full list of YAML-derived vars.

# Guard against double-sourcing
[[ -n "${_ESACP_CONFIG_LOADED:-}" ]] && return 0
_ESACP_CONFIG_LOADED=1

_CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="${PROJ_ROOT:-$(cd "${_CONFIG_DIR}/../.." && pwd)}"

# ── Derive from hosts_map.yml ────────────────────────────────────────────────
eval "$("${_CONFIG_DIR}/parse_hosts_map.py" "${PROJ_ROOT}/hosts_map.yml")"

# ── Env-overridable defaults (not in hosts_map.yml) ──────────────────────────
HYPERVISOR_ALIAS="${ESACP_HYPERVISOR_ALIAS:-${ESACP_HYPERVISOR}}"
HYPERVISOR_USER="${ESACP_HYPERVISOR_USER:-hasan}"
HYPERVISOR_LAN_IP="${ESACP_HYPERVISOR_LAN_IP:-toshy.iridium.blue}"
REMOTE_IMAGES_DIR="${ESACP_REMOTE_IMAGES_DIR:-/mnt/esacp-disk/var/lib/libvirt/images}"
VM_USER="${ESACP_VM_USER:-you}"
SSH_KEY="${ESACP_SSH_KEY:-${HOME}/.ssh/hasan_mighty}"

# ── Convenience aliases ──────────────────────────────────────────────────────
SACONSOLE_IP="${ESACP_SACONSOLE_VIRBR0_IP}"
SACONSOLE_USER="${VM_USER}"
ANSIBLE_DIR="${PROJ_ROOT}/ansible"
