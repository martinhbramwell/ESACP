#!/usr/bin/env bash
# telegram_delayed_alert.sh — Delayed Telegram notification for Claude Code.
#
# Usage:
#   telegram_delayed_alert.sh start [reason]  # spawn 3-min timer with reason
#   telegram_delayed_alert.sh cancel          # kill pending timer (user responded)
#
# Reasons: complete | decision | authorization | attention (default)
# "start" kills any existing timer first, then spawns a new one.
# "cancel" just kills and exits silently.
# Detail text: telegram_stop_classifier.py / telegram_permission_handler.py
# write a brief context snippet to /tmp/.claude-telegram-reason-detail.
#
# Credentials: SOPS-encrypted ansible/group_vars/all.sops.yml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="/tmp/.claude-telegram-timer.pid"
REASON_FILE="/tmp/.claude-telegram-reason"
DETAIL_FILE="/tmp/.claude-telegram-reason-detail"
DELAY_SECONDS=180

cancel_timer() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        # Kill the sleep + send subshell if still running
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            # Also kill child processes (the sleep)
            pkill -P "$pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
}

build_message() {
    local reason detail msg
    reason="attention"
    detail=""
    [ -f "$REASON_FILE" ] && reason=$(cat "$REASON_FILE")
    [ -f "$DETAIL_FILE" ] && detail=$(cat "$DETAIL_FILE")

    case "$reason" in
        complete)
            msg="✅ ESACP: All tasks complete — waiting for next instruction"
            ;;
        decision)
            msg="🔀 ESACP: Decision required"
            [ -n "$detail" ] && msg="${msg}
${detail}"
            ;;
        authorization)
            msg="🔐 ESACP: Authorization required"
            [ -n "$detail" ] && msg="${msg}
${detail}"
            ;;
        *)
            msg="🤖 ESACP: Claude Code needs your attention"
            ;;
    esac
    echo "$msg"
}

send_alert() {
    local bot_token chat_id text
    bot_token=$(sops -d --extract '["telegram_bot_token"]' \
        "$SCRIPT_DIR/ansible/group_vars/all.sops.yml" 2>/dev/null)
    chat_id=$(sops -d --extract '["telegram_chat_id"]' \
        "$SCRIPT_DIR/ansible/group_vars/all.sops.yml" 2>/dev/null)

    if [ -z "$bot_token" ] || [ -z "$chat_id" ]; then
        echo "ERROR: Could not decrypt Telegram credentials" >&2
        exit 1
    fi

    text=$(build_message)

    curl -s -X POST "https://api.telegram.org/bot${bot_token}/sendMessage" \
        -d chat_id="$chat_id" \
        -d text="$text" \
        -d parse_mode="Markdown" > /dev/null 2>&1

    # Clean up reason files
    rm -f "$REASON_FILE" "$DETAIL_FILE"
}

ACTION="${1:-start}"
REASON="${2:-attention}"

case "$ACTION" in
    cancel)
        cancel_timer
        rm -f "$REASON_FILE" "$DETAIL_FILE"
        ;;
    start)
        # Always cancel any existing timer first
        cancel_timer

        # Store reason for the deferred send_alert to read
        echo "$REASON" > "$REASON_FILE"

        # Spawn background: sleep then send
        (
            sleep "$DELAY_SECONDS"
            send_alert
            rm -f "$PID_FILE"
        ) </dev/null >/dev/null 2>&1 &
        echo $! > "$PID_FILE"
        # Detach — don't let the hook wait for the background job
        disown
        ;;
    *)
        echo "Usage: $0 {start|cancel} [complete|decision|authorization]" >&2
        exit 1
        ;;
esac
