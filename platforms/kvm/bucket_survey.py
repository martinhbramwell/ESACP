#!/usr/bin/env python3
"""Bucket-survey helpers for session_start hook (ESACP #358 / #369)."""

import json
import shutil
import subprocess

BUCKETS = {
    'esacp_platform': ['martinhbramwell/ESACP', 'martinhbramwell/BaRe'],
    'logisolu_knowbase': ['martinhbramwell/LogiSoluKnowBase'],
    'ce_sri': ['martinhbramwell/ce_sri', 'martinhbramwell/ce_sri_svc'],
    'tenant_business_apps': [
        'martinhbramwell/route_planner', 'martinhbramwell/BtlMng',
    ],
    'logisolu_memory': ['martinhbramwell/LogiSoluMemory'],
    'logisolu_validations': ['martinhbramwell/LogiSoluValidations'],
}


def _gh(args, timeout=15):
    try:
        r = subprocess.run(['gh'] + args, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return False, '`gh` not on PATH'
    except subprocess.TimeoutExpired:
        return False, 'gh call timed out'
    if r.returncode != 0:
        msg = (r.stderr or r.stdout).strip()
        return False, msg.splitlines()[0] if msg else 'gh error'
    return True, r.stdout


def _survey_repo(repo):
    out = [f'-- {repo} --']
    ok, payload = _gh(['issue', 'list', '--repo', repo, '--state', 'open',
                       '--limit', '5', '--json', 'number,title'])
    if not ok:
        out.append(f'  [survey unavailable: {payload}]')
        return out
    issues = json.loads(payload or '[]')
    ok2, count_out = _gh(['issue', 'list', '--repo', repo, '--state', 'open',
                          '--limit', '100', '--json', 'number', '--jq', 'length'])
    out.append(f'  open issues: {count_out.strip() if ok2 else "?"} (top 5):')
    for i in issues:
        out.append(f'    #{i["number"]} {i["title"]}')
    ok, payload = _gh(['pr', 'list', '--repo', repo, '--state', 'open',
                       '--json', 'number,title,isDraft'])
    if ok:
        prs = json.loads(payload or '[]')
        out.append(f'  open PRs: {len(prs)}')
        for p in prs:
            tag = ' [draft]' if p.get('isDraft') else ''
            out.append(f'    #{p["number"]} {p["title"]}{tag}')
    ok, payload = _gh(['api', f'repos/{repo}/commits', '--jq',
                       '.[0:5] | .[] | "\\(.sha[0:7]) \\(.commit.message | split("\\n") | .[0])"'])
    if ok:
        out.append('  recent commits:')
        for line in payload.strip().split('\n')[:5]:
            if line:
                out.append(f'    {line}')
    ok, payload = _gh(['api', f'repos/{repo}/branches', '--jq',
                       '[.[].name] | join(", ")'])
    if ok:
        out.append(f'  branches: {payload.strip()}')
    return out


def survey_buckets(bucket_keys):
    if not bucket_keys:
        return ''
    if not shutil.which('gh'):
        return '=== Bucket Surveys ===\n[gh not on PATH; surveys skipped]\n'
    parts = ['=== Bucket Surveys ===']
    for key in bucket_keys:
        repos = BUCKETS.get(key)
        if repos is None:
            parts.append(f'[bucket "{key}" unknown — see BUCKETS in platforms/kvm/bucket_survey.py]')
            continue
        parts.append(f'## bucket: {key}')
        for repo in repos:
            parts.extend(_survey_repo(repo))
        parts.append('')
    return '\n'.join(parts) + '\n'


if __name__ == '__main__':
    import sys
    print(survey_buckets(sys.argv[1:] or ['esacp_platform']))
