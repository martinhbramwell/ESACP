#!/usr/bin/env bash
# Send a Telegram message to the ESACP alert chat.
# Usage: telegram_notify.sh "Your message here"
# Credentials from SOPS-encrypted ansible/group_vars/all.sops.yml

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Throttle: skip if last notification was less than 3 minutes ago
STAMP_FILE="/tmp/.claude-telegram-last-notify"
COOLDOWN=180
if [ -f "$STAMP_FILE" ]; then
  LAST=$(cat "$STAMP_FILE")
  NOW=$(date +%s)
  if [ $((NOW - LAST)) -lt $COOLDOWN ]; then
    exit 0
  fi
fi
date +%s > "$STAMP_FILE"

BOT_TOKEN=$(sops -d --extract '["telegram_bot_token"]' "$SCRIPT_DIR/ansible/group_vars/all.sops.yml" 2>/dev/null)
CHAT_ID=$(sops -d --extract '["telegram_chat_id"]' "$SCRIPT_DIR/ansible/group_vars/all.sops.yml" 2>/dev/null)

if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
  echo "ERROR: Could not decrypt Telegram credentials" >&2
  exit 1
fi

MSG="${1:-Claude Code needs your attention}"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" \
  -d text="🤖 ESACP Claude Code: ${MSG}" \
  -d parse_mode="Markdown" > /dev/null 2>&1
