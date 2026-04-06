#!/usr/bin/env python3
"""Handle Notification hook for permission_prompt events.

Writes the tool name to the detail file, then starts the Telegram
alert timer with reason 'authorization'.
"""
import json
import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALERT_SCRIPT = os.path.join(SCRIPT_DIR, "telegram_delayed_alert.sh")
DETAIL_FILE = "/tmp/.claude-telegram-reason-detail"
MAX_DETAIL = 120


def main():
    raw = os.environ.get("TOOL_INPUT", "")
    detail = ""
    if raw:
        try:
            data = json.loads(raw)
            # Extract tool name or message for context
            tool = data.get("tool_name", "")
            perm = data.get("permission", "")
            detail = perm[:MAX_DETAIL] if perm else tool[:MAX_DETAIL]
        except (json.JSONDecodeError, TypeError):
            pass

    with open(DETAIL_FILE, "w") as f:
        f.write(detail)

    subprocess.run(
        ["bash", ALERT_SCRIPT, "start", "authorization"], check=False
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
