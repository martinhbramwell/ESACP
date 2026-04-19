# Session Minutes — 2026-04-18 21:05 EDT

**Objective:** Add Phase E-1 to `platforms/kvm/rebuild_saconsole.sh` to bring up the observability stack on a fresh hub and assert all 8 expected containers are healthy. Close #226.

**Outcome:** Objective re-scoped mid-session and delivered. PR #230 merged (commit `332cdff`); #226 closed with merge SHA. Two false-negative bugs in `sync_check.sh` fixed at root cause; Phase D now asserts 8 obs container rows.

---

## What actually happened

### Discovery (Step 1 of agenda)

Live inspection of the post-Session-A hub via `ssh you@10.10.0.1 'docker ps'` showed **all 8 observability containers already running** ("Up 4 hours") — `prometheus`, `grafana`, `loki`, `promtail`, `alertmanager`, `node_exporter`, `cadvisor`, `mcp-grafana`. The Ansible role `ansible/roles/observability/tasks/main.yml:118-124` already does `docker-compose up -d --force-recreate` followed by Grafana/Prometheus/Loki health waits during Phase C bootstrap.

### Root-cause analysis

`sync_check.sh` was reporting all 8 containers + the WG peer drift row as failures. Traced to `sync_check.sh:47-49`:

- `remote_hub` used `BatchMode=yes` without `StrictHostKeyChecking=accept-new`.
- `rebuild_saconsole.sh` Phase D correctly clears `~/.ssh/known_hosts` for `HUB_VIRBR0_IP=192.168.122.10`.
- First `remote_hub` SSH after a rebuild died silently with "Host key verification failed" (swallowed by `2>/dev/null || true`).
- Empty `OBS_CONTAINERS` → 8 false negatives. Empty `LIVE_PEERS` → 1 false negative ("hub has 0 WG peers").

Reproduced by manually warming the host key with `accept-new` — sync_check immediately went from 12 ❌ → 3 ❌.

### Decision (re-scope)

Building a `phase_e1_servicesup` to call `docker-compose up -d` would have been redundant with the Ansible role and would have masked the SSH bug. Per the agenda's Carry-forward clause ("Don't silently patch") and global rule "Root cause over symptoms", the user approved **Option B** — re-scope #226 in place to fix the SSH-warming bug and tighten Phase D's assertion.

### Edits delivered (PR #230)

| File | Change |
|---|---|
| `platforms/kvm/sync_check.sh:47-50` | Added `-o StrictHostKeyChecking=accept-new` to `remote_hub` |
| `platforms/kvm/rebuild_saconsole.sh` Phase D | Broadened required-row list from 3 hub-critical rows to also include all 8 observability container rows (this is the agenda's Step 5 promoted to the primary edit) |
| `platforms/kvm/rebuild_saconsole.sh` header | Removed stale "Phase E-1 PENDING" callout; documented that obs bring-up lives in the Ansible role |

**Diff stats:** 2 files, +27/-13. GPG-signed by RSA `9C6BCEA8...04E8`.

### Verification

With `~/.ssh/known_hosts` deliberately cleared for `192.168.122.10` (simulating fresh rebuild):

```
✅ Passed: 44    ⚠️ Warnings: 10    ❌ Failed: 3
```

3 failures are the 3 unprovisioned dev VMs (`dev02`, `dev03`, `target5` — out of scope, related to #138 phone-home work).

### Lifecycle

- Branch `feat/226-phase-e1-observability` from `main` at `ad0a2f1`.
- Commit `d2618a9` GPG-signed.
- PR [#230](https://github.com/martinhbramwell/ESACP/pull/230) opened.
- Squash-merged: commit `332cdff82176b09dbbe50d2b7cfce24abc0dc303`, `mergedAt: 2026-04-19T00:58:51Z`.
- #226 closed (auto by `fixes #226` trailer); closing comment added with merge SHA.

---

## Carry-forward findings

### #227 likely moot (comment posted)

Live `wg show wg0` on the hub reports **5 peers configured** with active handshakes from the controller (`10.10.0.2`) and `dev01` (`10.10.0.13`). The other 3 are configured peers waiting for VMs to come up. The `bootstrap_hub.sh` wireguard role already re-registers all spokes from inventory during Phase C — there is no missing step.

Posted as comment on #227 (https://github.com/martinhbramwell/ESACP/issues/227#issuecomment-4274903247). Recommendation: a short next session that runs `./rebuild_saconsole.sh all` end-to-end and confirms the 5-peer state holds. If yes, close #227 with `332cdff`. If not, redefine scope with concrete evidence at that point.

### Real remaining failure

The 3 unprovisioned dev VMs — `dev02` (10.10.0.12), `dev03` (10.10.0.14), `target5` (10.10.0.15). Out of scope here; addressed by manual provision (CLI/UI) or by #138 (phone-home agent).

---

## Audit trail (session-close)

- Forward-tense phrases all resolved (executed / durably homed in PR + comments).
- Every GH issue with new findings (#226, #227) had findings posted as comments, not just minutes.
- PR #230 `mergedAt` confirmed non-null before this minute file was written.
- No tasks left in `in_progress`.

---

## Memory updates

None proposed. The substantive lessons (observability is brought up by Ansible, sync_check is now robust to fresh-hub state, Phase D is the honest gate) are encoded in code + commit messages, not memory. Existing memories (`feedback_no_monolith_patching.md`, `feedback_plan_before_code.md`, `feedback_pr_merge_before_session_close.md`) all held up cleanly.
