# Agenda — Acceptance Run 08 (CLI) — dev VM, pseudo-company skeletal ERPNext restored from wizard backup

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove that B07 (the backup produced in run 07) can be used to rebuild an equivalent skeletal ERPNext instance from the CLI, with the UI converging to reflect the result. This is the final run of the matrix.

## Entry preconditions

- Run 07 complete; minutes committed.
- Cytoscape UI running for observation.
- Backup **B07** present.
- Saconsole running; dev VM from run 07 present (this run destroys it first).

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/08-cli-pseudo-restore.yml`

```yaml
run: "08"
transport: cli
target_vm: dev01
variant: pseudo_restore
backup_source: "docs/SessionLogs/acceptance-matrix/artefacts/B07-wizard.sql.gz"
wait_budget_seconds: 1500
topology_convergence_budget_seconds: 300
```

## Commands (single destroy, single build)

1. Destroy: `./tools/esacp.py destroyVM <target_vm>`.
2. Build: `./tools/esacp.py provision --params docs/SessionLogs/acceptance-matrix/params/08-cli-pseudo-restore.yml` (the pipeline is expected to route to the restore variant based on the param file — no separate restore command).

## Playwright test

`prototypes/cytoscape/tests/accept-08-cli-pseudo-restore.spec.js`

The test:

1. Spawns destroy; waits for UI to converge.
2. Spawns build (with restore variant); waits for UI to converge.
3. Navigates to `https://<target_vm>.iridium.blue`.
4. Asserts company = `Pseudo-Co` and canary facts match run 07's exit state (helper reuse).

## Acceptance

- Playwright green.
- Restored instance's canary facts identical to run 07's.

## Exit state (handed to matrix close-out)

Saconsole + dev VM running restored skeletal ERPNext, all eight runs complete.

## Final parity check (matrix close-out)

With all 8 runs signed off, write a close-out note comparing:

- Run 01 vs Run 05 — saconsole rebuild equivalence.
- Run 02 vs Run 06 — full Logichem from backup equivalence.
- Run 03 vs Run 07 — wizard-driven skeletal equivalence (including B03 vs B07 content).
- Run 04 vs Run 08 — restore-from-wizard-backup equivalence.

Equivalence here means functionally indistinguishable endpoints, identical canary facts, topology in both UI- and CLI-driven cases converged within the wait budget.

Record the close-out in `docs/SessionLogs/acceptance-matrix/MATRIX-CLOSEOUT.md` and update `MEMORY.md` with the foundation-solid status so subsequent ERPNext-focused work can start from a trusted baseline.

## Findings protocol

Halt + issue. The final parity check's failures matter more than any single run's — they indicate transport divergence in the shared pipeline primitives, which is exactly what Gen 3 was supposed to prevent.

## Sign-off

Branch `accept/08-cli-pseudo-restore`; PR; merge. Matrix closed.
