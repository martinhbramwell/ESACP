# Agenda — Acceptance Run 02 (CLI) — dev VM, full company-specific ERPNext from backup

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove a dev VM can be built from the CLI and end up running full company-specific ERPNext restored from the golden production backup, with the UI converging to reflect the new state.

## Entry preconditions

- Run 01 complete; minutes committed.
- Cytoscape UI running for observation.
- Saconsole running; no dev VMs.
- Golden production backup available on the controller.

## Parameter file

`internal_docs/SessionLogs/acceptance-matrix/params/02-cli-full-company-specific.yml`

```yaml
run: "02"
transport: cli
target_vm: dev01
variant: full_company_specific
backup_source: golden_production
wait_budget_seconds: 1800
topology_convergence_budget_seconds: 300
```

## Commands (single destroy, single build)

1. Destroy: no-op at start (no dev VM present). If one is unexpectedly present, halt.
2. Build: `./tools/esacp.py provision <target_vm>` — `Config.provision_mode` defaults to `"restored"`; stages 1–9 pull the golden production backup. The spec reads `target_vm` from the param file.

The `provision` subcommand already performs stages 1–9 as one unit; that satisfies "single build command".

## Playwright test

`prototypes/cytoscape/tests/accept-02-cli-full-company-specific.spec.js`

The test:

1. Asserts starting topology (saconsole only).
2. Spawns the build subprocess; asserts success exit.
3. Within `topology_convergence_budget_seconds`, asserts the UI shows the new dev VM as green.
4. Asserts `https://<target_vm>.iridium.blue` serves the company-specific login, and the canary company-specific record is present (helper defined here, reused by run 05).

## Acceptance

- Playwright green.
- `sync_check.sh` ERPNext row ✅.
- Tracked files unchanged.

## Exit state (handed to run 03)

Saconsole + dev VM running full company-specific ERPNext via CLI provision. Run 03 destroys this dev VM first.

## Findings protocol

Halt + issue. Canary-helper content here is the parity reference for run 05 (UI).

## Sign-off

Branch `accept/02-cli-full-company-specific`; PR; merge.
