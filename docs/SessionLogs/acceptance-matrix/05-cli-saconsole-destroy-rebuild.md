# Agenda — Acceptance Run 05 (CLI) — saconsole destroy + rebuild

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove saconsole can be destroyed and rebuilt from the CLI with a single destroy + single build command, and that the running Cytoscape UI (opened separately by Playwright) converges to reflect the new reality within the wait budget.

## Entry preconditions

- Run 04 complete; minutes committed.
- UI still running at `http://localhost:5173` so Playwright can observe convergence.
- Saconsole and the run-04 dev VM currently present (they will be torn down by this run's destroy command, since destroying saconsole collapses everything that depends on it).

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/05-cli-saconsole.yml`

```yaml
run: "05"
transport: cli
target: saconsole
wait_budget_seconds: 600
topology_convergence_budget_seconds: 300
```

## Commands (single destroy, single build)

1. Destroy: `./tools/esacp.py destroy saconsole` (exact subcommand name confirmed at session start from `./tools/esacp.py --help`; substitute whichever shipping subcommand destroys the hub).
2. Build: `bash platforms/kvm/bootstrap_hub.sh` — the saconsole rebuild script. Exempt from the ≤~100-line rule for this matrix (see plan §Exempt SUT files; issue **#220**).

Both commands run to completion without further input.

## Playwright test

`prototypes/cytoscape/tests/accept-05-cli-saconsole.spec.js`

The test:

1. Opens the Cytoscape UI; records the starting topology.
2. Spawns the destroy command as a subprocess, asserts success exit.
3. Within `topology_convergence_budget_seconds`, asserts the UI has removed saconsole from the topology.
4. Spawns the build command as a subprocess, asserts success exit.
5. Within `topology_convergence_budget_seconds` of command completion, asserts the UI shows saconsole back as green.
6. Asserts backend health endpoint and `sync_check.sh` saconsole row ✅.

## Acceptance

- Playwright green (functional + topology convergence).
- `sync_check.sh` saconsole row ✅.
- Tracked files unchanged.

## Exit state (handed to run 06)

Saconsole running on a CLI-rebuilt hub; no dev/target VMs; WireGuard hub up.

## Findings protocol

Halt + issue. Topology non-convergence is a real finding — it is the whole point of the observer check for CLI runs.

## Sign-off

Branch `accept/05-cli-saconsole`; PR; merge.
