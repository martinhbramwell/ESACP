# Session Minutes — 2026-04-18 22:05 EDT

**Objective:** Verify #227 by running `./rebuild_saconsole.sh teardown`, `bootstrap`, and `verify` against the live hub and confirming post-rebuild `sync_check.sh` reports 5 WG peers + 8 obs containers. If confirmed, close #227 with `332cdff`; otherwise redefine scope.

**Outcome:** Objective delivered. Full destructive rebuild reproduces the 5-peer / 8-obs-container baseline from scratch. #227 was already auto-closed by PR #230's merge at start of session; confirmation comment posted on the closed issue with live evidence. No scope redefinition needed.

---

## What actually happened

### Precondition anomaly

`gh issue view 227` returned `state: CLOSED` — auto-closed by PR #230 at `2026-04-19T00:58:53Z`, which was after the previous session's minutes were written. The agenda's precondition 4 ("confirm OPEN") was stale. Surfaced to user with the options: (1) run the full destructive verification anyway, (2) skip and post a lighter-weight confirmation. User chose **Option 1** explicitly, with "ignore the status of target5" as a scope-narrowing directive.

### Pre-rebuild baseline (captured before teardown)

```
$ ssh you@10.10.0.1 'sudo wg show wg0 | grep -c "^peer:"'
5

$ ssh you@10.10.0.1 'docker ps --format "{{.Names}}"' | sort
alertmanager, cadvisor, grafana, loki, mcp-grafana, node_exporter, prometheus, promtail  (8)

$ bash platforms/kvm/sync_check.sh | tail -2
✅ Passed: 46    ⚠️ Warnings: 8     ❌ Failed: 3   (dev02/dev03/target5 pings — expected)
```

### Rebuild execution

| Phase | Command | Result |
|---|---|---|
| B. Teardown | `platforms/kvm/rebuild_saconsole.sh teardown` | ✅ 2 snapshots deleted, saconsole undefined with storage removed; guard confirmed only saconsole volumes touched |
| C. Bootstrap | `platforms/kvm/rebuild_saconsole.sh bootstrap` | ✅ PLAY RECAP: `ok=138 changed=83 unreachable=0 failed=0 skipped=3` (plays 3/4/5 skipped — no matching hosts, expected on a hub-only rebuild); snapshot `Stage 2.2 Baseline` taken |
| D. Verify | `platforms/kvm/rebuild_saconsole.sh verify` | ✅ Phase D sync_check assertion green — 46/8/3 matches baseline; 8 obs container rows all ✅ |

Bootstrap total ran uninterrupted; no apt-lock races, no unreachable hosts, no failed ansible tasks. The `remote_hub` SSH fix from PR #230 held — Phase D's `accept-new` warming of the post-teardown host key worked on the first attempt.

### Post-rebuild assertion (agenda Step 3)

```
$ ssh you@10.10.0.1 'sudo wg show wg0' | grep -c '^peer:'
5                                                 # target: 5 ✅

$ ssh you@10.10.0.1 'docker ps --format "{{.Names}}:{{.Status}}"' | sort
alertmanager:Up 9 minutes
cadvisor:Up 9 minutes (healthy)
grafana:Up 9 minutes
loki:Up 9 minutes
mcp-grafana:Up 2 minutes
node_exporter:Up 9 minutes
prometheus:Up 9 minutes
promtail:Up 9 minutes                             # target: 8 Up ✅

$ bash platforms/kvm/sync_check.sh
✅ Passed: 46    ⚠️ Warnings: 8     ❌ Failed: 3   # target: 3 ❌ (dev VM pings only) ✅
  ❌ Ping dev02 (10.10.0.12) — unreachable
  ❌ Ping dev03 (10.10.0.14) — unreachable
  ❌ Ping target5 (10.10.0.15) — unreachable
```

All three pass. The `bootstrap_hub.sh` wireguard play re-registers all 5 spokes from inventory during Phase C — no manual re-registration step required, which is exactly what #227 speculated might be missing.

### #227 sign-off

Issue was already CLOSED by `332cdff`. Posted confirmation comment with the live post-rebuild evidence: https://github.com/martinhbramwell/ESACP/issues/227#issuecomment-4274961598

---

## Housekeeping this session

### Safety-net archive deleted

`~/archives/saconsole/saconsole-pre-rebuild-2026-04-18-0757.{qcow2,seed.iso,sha256,xml}` removed (34.9 GB qcow2 + 3 metadata files). The rebuild process is now demonstrably reproducible; the archive's role as "iteration safety net" is discharged.

### MEMORY.md updated

- Acceptance-matrix entry: replaced the Phase E-1/#226/#227 narrative with the closure via PR #230 and a new "Next: Run 01 proper" pointer to `docs/SessionLogs/acceptance-matrix/01-cli-saconsole-rebuild.md`.
- Open-issues list: removed #226 and #227; added closure line with merge commit `332cdff`.
- Added note that no pre-rebuild archive is retained post-discharge.

---

## Audit trail (session-close)

1. **Forward-tense phrases** — all resolved: teardown/bootstrap/verify commands executed; monitor started then stopped; #227 confirmation comment posted (URL durably homed); MEMORY.md edited; archive deleted. No `in_progress` tasks remain.
2. **GH issues with new findings** — #227 received the post-rebuild evidence comment on the issue itself, not only in minutes. #226, #225, #230 referenced only as context; no new findings to post.
3. **PRs opened** — none. No code changes, no branches, no PRs.

---

## Carry-forward

- **Run 01 proper** — the Playwright-observed acceptance test at `docs/SessionLogs/acceptance-matrix/01-cli-saconsole-rebuild.md`. This session's rebuild was pure CLI verification; Run 01 adds the UI-convergence observer (`prototypes/cytoscape/tests/accept-01-cli-saconsole.spec.js`) and the single-command `./rebuild_saconsole.sh` (no sub-arg) launch. That is the next session.
- Open issues unchanged from post-session state: #48, #50, #65, #138, #153, #156, #157, #181, #187, #188, #202, #206, #211, #213, #216, #217, #219, #220, #223, #225.
