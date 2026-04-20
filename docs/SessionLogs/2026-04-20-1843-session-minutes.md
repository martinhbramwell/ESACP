# Session Minutes — Run-04→Run-05 reminder sweep (4 reminders resolved)

**Date:** 2026-04-20 ~18:05–18:43 EDT
**Branches:** `fix/sync-check-dormant-vms`, `docs/housekeeping-post-run-04`
**PRs:** #263 (merged `fc80654` at 22:26:05Z), #264 (merged `b892053` at 22:30:15Z)
**Out-of-repo:** `~/.claude/hooks/memory_md_merge_reminder.py` + `~/.claude/settings.json` SessionEnd entry

## Objective

Resolve the four reminders carried forward from the Run 04 minutes, clearing the queue before Matrix Run 05 (UI transport).

## Outcome — all four resolved

| R | Issue | PR / Artefact | State |
|---|---|---|---|
| 1 — sync_check dormant VMs | **#259** | PR **#263** (`fc80654`) | MERGED |
| 2 — working-tree runtime churn | — (tracked by **#241**, deferred behind **#240**) | No new action; stash-restored on main as expected Run 04 state | Pre-existing |
| 3 — agenda CLI wording drift | **#260** | PR **#264** (`b892053`) | MERGED |
| — amendment to 1:1:1 | **#262** (filed mid-session) | PR **#264** (`b892053`), bundled with #260 | MERGED |
| 4 — MEMORY.md SessionEnd hook | **#261** | Out-of-repo hook + settings.json | CLOSED |

## Mid-session policy shift — 1:1:1 amendment (#262)

User flagged that strict 1:1:1 was slowing the housekeeping queue. Agreed amendment drafted, filed as **#262**, and implemented in the same session as its first example:

- **Substantive** project software changes (pipeline, dispatchers, SUT scripts, Ansible, SOPS-backed config): strict 1:1:1.
- **Housekeeping** bundles (docs, agenda wording, external Claude Code config, `.gitignore`): one branch may close multiple issues, under guardrails (each issue filed; PR titled as sweep; no mixing; per-file size-check ratchet still applies).

PR #264 is the first bundle under the new rule — one branch `docs/housekeeping-post-run-04` closing #260 + #262.

Landed in `CLAUDE.md` Session Protocol and `memory/feedback_issue_branch_session_discipline.md`.

## Commits

| SHA | Branch | Commit |
|---|---|---|
| `2062d1a` | fix/sync-check-dormant-vms | fix(sync_check): distinguish dormant VMs from should-be-up — add expected_state |
| `fc80654` | main | Merge PR #263 |
| `6d1973e` | docs/housekeeping-post-run-04 | docs(sweep): agenda CLI scrub + 1:1:1 amendment for housekeeping bundles |
| `b892053` | main | Merge PR #264 |

## R1 — sync_check dormant VMs (#259 → PR #263)

Added `expected_state: "off"` field to `hosts_map.yml` entries for dev02, dev03, target5 (string-quoted — YAML bare `off` parses as boolean False). `platforms/kvm/sync_check.sh` now parses a `DORMANT_VMS` list and honours it in sections 7 (virsh domstate), 9 (WG ping), 11 (ERPNext HTTPS).

Before: 45 ✅ / 9 ⚠️ / **3 ❌**, exit 1.
After: 44 ✅ / 13 ⚠️ / **0 ❌**, exit 0.

Matrix-spec compatibility preserved: self-check 0b regex `/[✅❌]/` still matches (✅ rows preserved); `REQUIRED_SYNC_ROWS` in accept-01 unaffected (MCP + obs container rows only).

## R3 — agenda CLI wording scrub (#260 → PR #264)

Agendas 02/03/04 referenced the pre-#255 `./tools/esacp.py provision --params <yml>` that never existed in the current SUT. Rewrote each to match the actual spec invocation:

- **02:** `provision <target_vm>` (`Config.provision_mode` defaults to `"restored"`)
- **03:** `provisionGeneric <target_vm> --wizard-mode replay --wizard-arg <wizard_recording>`
- **04:** `provisionGeneric <target_vm> --wizard-mode existing --wizard-arg <backup_tgz_filename>`

Agendas 05/06/07 inspected — no CLI wording present (UI transport). No scrub needed.

Acceptance: `grep -rn 'provision --params' docs/SessionLogs/acceptance-matrix/*.md` → zero hits.

**Scope deviation from #260 body:** issue text said "Do not touch 01–03 agendas (historical, already executed)," but grep showed 02/03 also had the drift, and the acceptance clause was "zero hits." Resolved in favour of the acceptance clause; documented on the issue comment for auditability.

## R4 — MEMORY.md SessionEnd hook (#261, out-of-repo)

`~/.claude/hooks/memory_md_merge_reminder.py` — reads hook payload from stdin; derives per-project auto-memory slug (`path.replace("/", "-")`); if `~/.claude/projects/<slug>/memory/MEMORY.md` exists, compares `git log --merges -1 --format=%ct` against the file's mtime. If merge newer, prints advisory reminder to stderr. Inert outside projects with the memory dir.

`~/.claude/settings.json` — added `hooks.SessionEnd` entry invoking the script; existing `PreToolUse` Bash approval hook preserved.

Tested live against current ESACP state: fires correctly against the post-#263-merge state; silent no-op against `/tmp`.

**Caveat:** settings watcher may not register the new event type until `/hooks` is opened once or the session is restarted. Documented on the issue.

## Session-end state on main

- `b892053` HEAD.
- Working tree: three files modified (Run 04 runtime churn restored post-merge: `ansible/group_vars/all.yml` WG pubkey, `config/wireguard/keys.sops.yml` ciphertext rotation, `hosts_map.yml` dev01 `vm_role: dev:pseudo_restore`). These are overwritten by Run 05's destroy+rebuild; matches Run 02/03/04 discipline. Tracked by #241.
- `sync_check`: 45 ✅ / 12 ⚠️ / 0 ❌.
- Open issues at session close: 28 (down from 28 — closed 4, filed 4, net zero).

## Open issues list (post-session)

#48, #50, #65, #138, #153, #156, #157, #181, #187, #188, #202, #206, #211, #213, #216, #217, #219, #220, #223, #225, #235, #236, #238, #240, #241, #243, #244, #250.

Closed this session: #259, #260, #261, #262.

## Reminders carried into next session

1. **R4 hook activation** — user needs to trigger `/hooks` or restart Claude Code once before the SessionEnd hook actually fires. After that, MEMORY.md freshness will be checked at every session end.
2. **Working-tree churn on main** — same three-file pattern (ansible/group_vars/all.yml, config/wireguard/keys.sops.yml, hosts_map.yml) as every destroy/rebuild session. Long-term fix is #241 (hosts_map.local.yml overlay), deferred behind #240.
3. **Housekeeping-bundle precedent** — PR #264 is the first bundle under the amended 1:1:1 rule. Future bundles should maintain the guardrails (individual issues filed; sweep-titled PR; no substantive code mixed in; per-file size-check ratchet still applies).

## Next

Matrix Run 05 — UI-driven dev VM full company-specific restore from production backup. Agenda: `docs/SessionLogs/acceptance-matrix/05-ui-vm-full-company-specific-from-backup.md`. Destroys dev01 first (currently running B03-restored Pseudo-Co).
