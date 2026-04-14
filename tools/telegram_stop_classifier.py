#!/usr/bin/env python3
"""Classify why Claude stopped and start the appropriate Telegram alert timer.

Called by the Stop hook. Reads hook input from TOOL_INPUT env var,
determines whether Claude finished work or is asking a question,
then delegates to telegram_delayed_alert.sh with the right reason.
"""
import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALERT_SCRIPT = os.path.join(SCRIPT_DIR, "telegram_delayed_alert.sh")
REASON_FILE = "/tmp/.claude-telegram-reason-detail"

DECISION_SIGNALS = ("?", "which ", "choose ", "prefer ", "shall i ", "would you ")
MAX_DETAIL = 120


def extract_question(message):
    """Pull the last sentence ending with '?' as a brief context snippet."""
    for line in reversed(message.strip().splitlines()):
        line = line.strip()
        if line.endswith("?"):
            return line[:MAX_DETAIL]
    return ""


def classify():
    raw = os.environ.get("TOOL_INPUT", "")
    if not raw:
        return "attention", ""

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return "attention", ""

    stop_reason = data.get("stop_reason", "")
    if stop_reason == "user_interrupt":
        return None, ""

    message = data.get("assistant_message", "")
    if any(sig in message.lower() for sig in DECISION_SIGNALS):
        return "decision", extract_question(message)

    return "complete", ""


def main():
    reason, detail = classify()
    if reason:
        # Write detail snippet for the alert script to pick up
        with open(REASON_FILE, "w") as f:
            f.write(detail)
        subprocess.run(["bash", ALERT_SCRIPT, "start", reason], check=False)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let the hook crash block Claude
        pass
