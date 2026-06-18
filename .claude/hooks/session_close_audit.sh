#!/usr/bin/env bash
# Session-close audit hook. Fires on UserPromptSubmit; if the user's
# prompt contains a session-close signal (SCC?, session flip, wrap up,
# close out, sign off, session close/end), injects an audit reminder
# into the assistant's context BEFORE it responds.
#
# Motivation: Phase 8 post-mortem (2026-04-17). See
# memory/feedback_narration_not_action.md for the rule this enforces.

set -euo pipefail

PROMPT="$(jq -r '.prompt // ""')"

SIGNAL_RE='\bSCC\?|session[- ](flip|close|end)|\bwrap[- ]?up\b|\bclose[- ]out\b|sign(ing)?[- ]off|\bsession[- ]close[- ]audit\b'

if ! printf '%s' "$PROMPT" | grep -iqE "$SIGNAL_RE"; then
    exit 0
fi

cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "SESSION-CLOSE AUDIT — run this BEFORE writing minutes or declaring anything DONE.\n\n1. Grep this session's own outputs for forward-tense / lip-service phrases: \"I'll X\", \"I will X\", \"should X\", \"next we need to X\", \"noted for next session\", \"lesson noted\", \"lesson learned\", \"going forward I'll X\". For each, confirm one of:\n   (a) the tool call in this session that executed it,\n   (b) the URL / file path where it was committed to a durable home (gh issue comment, code file, memory file), or\n   (c) an open task with in_progress status.\n   \"Noted in the minutes\" is NOT a valid resolution — minutes reference durable homes, they do not replace them. SPECIAL CASE — a behavioural LESSON (\"lesson noted\", \"lesson learned\", \"going forward I'll\") has exactly ONE valid home: a created or updated memory file WITH its MEMORY.md pointer. A GH issue, a minutes entry, or a bare in-text acknowledgement does NOT satisfy a lesson; if no memory-file write for it appears in this session's tool calls, flag it as unrecorded. (ESACP #650)\n\n2. For every GH issue referenced this session: confirm any new findings about it have been posted as a comment on the issue itself (not just the minutes).\n\n3. For every PR opened this session: run `gh pr view <N> --json mergedAt` and confirm it is non-null before writing \"DONE\" anywhere.\n\n4. Scan for unresolved concerns or doubts the operator expressed during the session. Surface only those still needing the operator's decision or awareness — silent on items already resolved in-session or durably homed in a carry-forward.\n\nRun the audit internally. Report ONLY the hits with their corrective actions (commit hash, comment URL, task ID), plus any prong-4 items still needing operator attention. Everything that resolved cleanly collapses into one final line — no tables, no enumeration of pass-through items. If the audit truly finds nothing: \"Session-end audit: clean.\" Rationale: memory/feedback_session_end_audit_brevity.md. Minutes describe what happened, not what you intended to happen."
  }
}
JSON
