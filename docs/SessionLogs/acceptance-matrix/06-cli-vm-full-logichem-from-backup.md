# Agenda — Acceptance Run 06 (CLI) — dev VM, full Logichem ERPNext from backup

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove a dev VM can be built from the CLI and end up running full Logichem ERPNext restored from the golden production backup, with the UI converging to reflect the new state.

## Entry preconditions

- Run 05 complete; minutes committed.
- Cytoscape UI running for observation.
- Saconsole running; no dev VMs.
- Golden production backup available on the controller.

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/06-cli-full-logichem.yml`

```yaml
run: "06"
transport: cli
target_vm: dev01
variant: full_logichem
backup_source: golden_production
wait_budget_seconds: 1800
topology_convergence_budget_seconds: 300
```

## Commands (single destroy, single build)

1. Destroy: no-op at start (no dev VM present). If one is unexpectedly present, halt.
2. Build: `./tools/esacp.py provision --params docs/SessionLogs/acceptance-matrix/params/06-cli-full-logichem.yml` (exact flag spelling confirmed at session start; must consume the param file without further input).

The `provision` subcommand already performs stages 1–9 as one unit; that satisfies "single build command".

## Playwright test

`prototypes/cytoscape/tests/accept-06-cli-full-logichem.spec.js`

The test:

1. Asserts starting topology (saconsole only).
2. Spawns the build subprocess; asserts success exit.
3. Within `topology_convergence_budget_seconds`, asserts the UI shows the new dev VM as green.
4. Asserts `https://<target_vm>.iridium.blue` serves the Logichem login, and the canary Logichem record is present (helper reused from run 02).

## Acceptance

- Playwright green.
- `sync_check.sh` ERPNext row ✅.
- Tracked files unchanged.

## Exit state (handed to run 07)

Saconsole + dev VM running full Logichem ERPNext via CLI provision. Run 07 destroys this dev VM first.

## Findings protocol

Halt + issue. Any divergence from run 02's observable outcome is a parity finding and must be logged in minutes.

## Sign-off

Branch `accept/06-cli-full-logichem`; PR; merge.
