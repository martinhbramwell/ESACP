# Agenda — Acceptance Run 01 (CLI) — saconsole rebuild

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove saconsole can be rebuilt from the CLI with a single command, atomically (backup → teardown → bootstrap replacement → mesh reattach), and that the running Cytoscape UI (opened separately by Playwright) converges to reflect the new reality within the wait budget.

saconsole lifecycle is CLI/controller-only by design — there is no UI counterpart for this run. See `memory/feedback_saconsole_cli_only.md` and issue **#222**.

## Prerequisites (from a separate, prior session)

**Issue #222 closed.** `platforms/kvm/rebuild_saconsole.sh` exists on `main`, built step-by-step in a dedicated 1:1:1 session (Session A). This agenda does not build the script — it executes it and tests the outcome.

If the script is not yet on `main`, this run cannot start; resolve the blocker first.

## Entry preconditions

- Clean baseline: hypervisor prepared, `hosts_map.yml` known-good, no dev/target VMs.
- UI running at `http://localhost:5173` so Playwright can observe convergence.
- Saconsole currently running and reachable.
- qcow2 backup archive location on the controller decided and writable (per the `rebuild_saconsole.sh` contract).

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/01-cli-saconsole.yml`

```yaml
run: "01"
transport: cli
target: saconsole
wait_budget_seconds: 600
topology_convergence_budget_seconds: 300
blast_radius: saconsole-only
backup_mode: qcow2_full
preserve_metrics_history: false
```

## Command (single rebuild)

Single atomic rebuild:

```
bash platforms/kvm/rebuild_saconsole.sh
```

The script is responsible for all phases — backup, teardown, bootstrap, mesh reattach. No further input once launched. Dev/target VMs on the hypervisor are left untouched (saconsole-only blast radius).

## Playwright test

`prototypes/cytoscape/tests/accept-01-cli-saconsole.spec.js`

The test:

1. Opens the Cytoscape UI; records the starting topology (saconsole green + hub).
2. Spawns `bash platforms/kvm/rebuild_saconsole.sh` as a subprocess; asserts success exit within the wait budget.
3. Within `topology_convergence_budget_seconds` of command completion, asserts the UI shows saconsole back as green.
4. Asserts the backend health endpoint responds, all MCP endpoints return 200, and `sync_check.sh` saconsole hub rows ✅.
5. Asserts any pre-existing dev/target VMs (if any) are still in the topology — saconsole-only blast radius held.

## Acceptance

- Playwright green (functional + topology convergence).
- `sync_check.sh` saconsole row ✅.
- Metrics history: **not asserted** (fresh hub is expected per issue **#223**).
- Tracked files unchanged outside this run's own param + spec.

## Exit state (handed to run 02)

Saconsole running on a CLI-rebuilt hub; no dev/target VMs created by this run; WireGuard hub up; qcow2 backup of the pre-rebuild saconsole archived (revert-capable).

## Findings protocol

Halt + issue. Topology non-convergence is a real finding — it is the whole point of the observer check for CLI runs. If the backup step fails, halt before teardown (the script must preserve revert capability).

## Sign-off

Branch `accept/01-cli-saconsole`; PR; merge.
