#!/usr/bin/env python3
"""
SessionStart hook — domain-aware context loader.

Reads session_focus.txt from the memory directory to determine which
domains are active. Only loads files for active domains + core files.
Runs the KVM sync check only when 'kvm' domain is active.

To change focus: edit memory/session_focus.txt (one domain per line).
Available domains: core, erpnext, kvm, docker, cytoscape
"""

import os
import sys
import subprocess
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bucket_survey import survey_buckets

# CC harness exposes $CLAUDE_PROJECT_DIR when started with a project directory.
# When set, derive the encoded memory-dir path from it. When unset (current
# behaviour in this environment — the var is not exported to child shells),
# fall back to the hard-coded path. The encoded path is frozen to the
# filesystem location at which the CC session first registered, so it does
# not move even if the working directory changes; hence a literal carve-out.
_proj_dir = os.environ.get('CLAUDE_PROJECT_DIR', '')
if _proj_dir:
    _encoded = _proj_dir.replace('/', '-')
    MEMORY_DIR = os.path.expanduser(f'~/.claude/projects/{_encoded}/memory')
else:
    MEMORY_DIR = '/home/hasan/.claude/projects/-home-hasan-projects-Logichem-ESACP/memory'

SYNC_CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sync_check.sh')

# ── Domain → file mapping ──────────────────────────────────────────────────
DOMAINS = {
    'core': [
        # Always loaded: workflow, behavioural rules, mission
        'mission_vision.md',
        'feedback_github_issues.md',
        'feedback_issue_workflow.md',
        'feedback_metacognition.md',
        'feedback_naming_conventions.md',
        'feedback_scc_command.md',
    ],
    'erpnext': [
        # ERPNext production topology, ce_sri scripts, frappe deps
        'project_production_erpnext.md',
        'feedback_envars_secrets_pattern.md',
        'feedback_frappe_v13_deps.md',
        'feedback_lab_passwords.md',
        'feedback_sudo_askpass.md',
    ],
    'kvm': [
        # Hypervisor host, VM lifecycle, SSH gotchas
        'toshiba_environment.md',
        'hypervisor_prep.md',
        'feedback_known_hosts_preclear.md',
        'feedback_non_esacp_hosts.md',
    ],
    'docker': [
        # Observability stack, production topology
        'production_topology.md',
    ],
    'cytoscape': [
        # Empty after S98 purge (stale prototype-era notes removed).
        # Repopulation tracked in ESACP#575.
    ],
}

ALL_DOMAIN_NAMES = list(DOMAINS.keys())

# ── Read active focus ──────────────────────────────────────────────────────
focus_file = os.path.join(MEMORY_DIR, 'session_focus.txt')
active_domains = ['core']
if os.path.exists(focus_file):
    extra = [l.strip() for l in open(focus_file).readlines()
             if l.strip() and not l.strip().startswith('#')]
    active_domains += [d for d in extra if d not in active_domains]

inactive_domains = [d for d in ALL_DOMAIN_NAMES if d not in active_domains]

# ── Collect files to load ──────────────────────────────────────────────────
to_load = []
for dom in active_domains:
    for f in DOMAINS.get(dom, []):
        if f not in to_load:
            to_load.append(f)

# ── Build context ──────────────────────────────────────────────────────────
parts = []
for f in to_load:
    path = os.path.join(MEMORY_DIR, f)
    if os.path.exists(path):
        parts.append('=== ' + f + ' ===\n' + open(path).read())
    else:
        parts.append('=== ' + f + ' === [FILE NOT FOUND]')

# ── Sync check — only when KVM domain is active ────────────────────────────
sync_output = ''
if 'kvm' in active_domains:
    result = subprocess.run(
        ['bash', SYNC_CHECK],
        capture_output=True, text=True
    )
    sync_output = '\n=== Sync Check ===\n' + result.stdout

# ── Bucket surveys — per ESACP #358 Discipline #2 / #369 ───────────────────
buckets_file = os.path.join(MEMORY_DIR, 'session_buckets.txt')
active_buckets = []
if os.path.exists(buckets_file):
    active_buckets = [l.strip() for l in open(buckets_file).readlines()
                      if l.strip() and not l.strip().startswith('#')]
bucket_output = survey_buckets(active_buckets)

ctx = '\n'.join(parts) + sync_output + (('\n' + bucket_output) if bucket_output else '')

# ── Header note ───────────────────────────────────────────────────────────
loaded_summary   = f"domains={active_domains}, buckets={active_buckets}, files={len(to_load)}"
unloaded_summary = (
    f"INACTIVE domains (files NOT loaded): {inactive_domains}. "
    f"To activate, add domain name to memory/session_focus.txt and start a new session. "
    f"WARNING: reading those files mid-session consumes context — restart after if possible."
)

system_msg = f"--- SessionStart: {loaded_summary}. {unloaded_summary}"

print(json.dumps({
    'systemMessage': system_msg,
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': ctx,
    }
}))
