#!/usr/bin/env bash
# utils.sh — Shared helpers for VBox platform scripts.
#
# Source this file AFTER PROJECT_ROOT is set:
#   source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"   # WSL scripts
#   source "${PROJECT_ROOT}/platforms/vbox/utils.sh"   # saconsole scripts
#
# Provides:
#   tg_notify <message>  — send Telegram message unless NO_TELEGRAM=1

tg_notify() {
    [[ "${NO_TELEGRAM:-}" == "1" ]] && return 0
    local msg="$1"
    local secrets bot_token chat_id
    secrets=$(sops -d "${PROJECT_ROOT}/ansible/group_vars/all.sops.yml" 2>/dev/null) || return 0
    bot_token=$(awk '/telegram_bot_token:/ {print $2}' <<<"${secrets}")
    chat_id=$(awk '/telegram_chat_id:/ {print $2}' <<<"${secrets}")
    [[ -z "${bot_token}" || -z "${chat_id}" ]] && return 0
    curl -s "https://api.telegram.org/bot${bot_token}/sendMessage" \
        --data-urlencode "chat_id=${chat_id}" \
        --data-urlencode "text=${msg}" > /dev/null || true
}
