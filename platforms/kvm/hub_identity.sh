#!/usr/bin/env bash
# hub_identity.sh — Export hub VM identity variables for shell scripts.
#
# Sources config.sh (which runs parse_hosts_map.py) and re-exports the
# hub-specific variables.  Shell scripts that previously hardcoded
# "saconsole" should source this file instead.
#
# Usage:
#   source "$(dirname "${BASH_SOURCE[0]}")/hub_identity.sh"
#
# Exported variables:
#   HUB_KEY, HUB_VM_NAME, HUB_HOSTNAME, HUB_DISPLAY_NAME
#   HUB_VIRBR0_IP, HUB_WG_IP, HUB_USER

# Guard against double-sourcing
[[ -n "${_ESACP_HUB_IDENTITY_LOADED:-}" ]] && return 0
_ESACP_HUB_IDENTITY_LOADED=1

source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

# All variables are already set by config.sh from parse_hosts_map.py output.
# This file exists as the documented entry point for scripts that only need
# hub identity, and as the single place to add hub-specific derived values.
