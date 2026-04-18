# Agenda — Acceptance Run 04 (CLI) — dev VM, pseudo-company skeletal ERPNext restored from wizard backup

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove that B03 (the backup produced in run 03) can be used to rebuild an equivalent skeletal ERPNext instance from the CLI, with the UI converging to reflect the result. This is the final CLI run of the matrix before the UI transport starts at run 05.

## Entry preconditions

- Run 03 complete; minutes committed.
- Cytoscape UI running for observation.
- Backup **B03** present.
- Saconsole running; dev VM from run 03 present (this run destroys it first).

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/04-cli-pseudo-restore.yml`

```yaml
run: "04"
transport: cli
target_vm: dev01
variant: pseudo_restore
backup_source: "docs/SessionLogs/acceptance-matrix/artefacts/B03-wizard.sql.gz"
wait_budget_seconds: 1500
topology_convergence_budget_seconds: 300
```

## Commands (single destroy, single build)

1. Destroy: `./tools/esacp.py destroyVM <target_vm>`.
2. Build: `./tools/esacp.py provision --params docs/SessionLogs/acceptance-matrix/params/04-cli-pseudo-restore.yml` (the pipeline is expected to route to the restore variant based on the param file — no separate restore command).

## Playwright test

`prototypes/cytoscape/tests/accept-04-cli-pseudo-restore.spec.js`

The test:

1. Spawns destroy; waits for UI to converge.
2. Spawns build (with restore variant); waits for UI to converge.
3. Navigates to `https://<target_vm>.iridium.blue`.
4. Asserts company = `Pseudo-Co` and canary facts match run 03's exit state (helper reuse).

## Acceptance

- Playwright green.
- Restored instance's canary facts identical to run 03's.

## Exit state (handed to run 05)

Saconsole + dev VM running restored skeletal ERPNext. Run 05 destroys this dev VM first (transport transition from CLI to UI).

## CLI-transport milestone

After this run, record in minutes whether runs 01–04 all met acceptance. This is the halfway parity snapshot; the remaining three runs (05–07) re-do runs 02–04 through the UI transport for the final parity comparison.

## Findings protocol

Halt + issue. A mismatch between B03's intent and the restored instance is a real finding — the whole matrix premise is that 04 reproduces 03.

## Sign-off

Branch `accept/04-cli-pseudo-restore`; PR; merge.
