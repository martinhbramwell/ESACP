# Agenda — Acceptance Run 07 (UI) — dev VM, pseudo-company skeletal ERPNext restored from wizard backup

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove that the backup produced in run 06 (B06) can be used to rebuild an equivalent skeletal ERPNext instance through the Cytoscape UI, with a single destroy + single build, validated by Playwright. This is the **final run** of the 7-run matrix.

## Entry preconditions

- Run 06 complete; minutes committed.
- Backup **B06** present at the path declared in run 06's param file.
- Saconsole running; dev VM from run 06 still present (this run destroys it as its first action).

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/07-ui-pseudo-restore.yml`

```yaml
run: "07"
transport: ui
target_vm: dev01
variant: pseudo_restore
backup_source: "docs/SessionLogs/acceptance-matrix/artefacts/B06-wizard.sql.gz"
wait_budget_seconds: 1500
```

`backup_source` must match run 06's `backup_output_path` exactly. Confirm before launching.

## Commands (single destroy, single build)

1. Destroy: Playwright right-clicks the dev VM from run 06 → Destroy → confirms.
2. Build: Playwright drags saconsole → target quadrant → selects "Pseudo-company skeletal (restore)" → confirms. Restore source is read from the param file.

## Playwright test

`prototypes/cytoscape/tests/accept-07-ui-pseudo-restore.spec.js`

The test:

1. Destroys the run-06 dev VM.
2. Builds the fresh dev VM with the pseudo-restore option using B06.
3. Navigates to `https://<target_vm>.iridium.blue`.
4. Asserts company = `Pseudo-Co`, wizard flag is set, admin email matches run 06's param file, and no Logichem records exist.
5. Compares canary facts against run 04's exit state (helper reuse) — confirms the UI restore path matches the CLI restore path.

## Acceptance

- Playwright green.
- Canary facts identical to run 04's exit state — UI and CLI restores reproduce the same state.

## Exit state (handed to matrix close-out)

Saconsole + dev VM running restored skeletal ERPNext via UI transport. All 7 runs complete.

## Final parity check (matrix close-out)

With all 7 runs signed off, write a close-out note comparing:

- Run 02 (CLI) vs Run 05 (UI) — full Logichem from golden backup.
- Run 03 (CLI) vs Run 06 (UI) — wizard-driven skeletal (including B03 vs B06 content).
- Run 04 (CLI) vs Run 07 (UI) — restore-from-wizard-backup.

Run 01 (CLI saconsole rebuild) has **no parity partner** — saconsole is CLI-only by design (see `memory/feedback_saconsole_cli_only.md`).

Equivalence here means functionally indistinguishable endpoints, identical canary facts, topology in both UI- and CLI-driven cases converged within the wait budget.

Record the close-out in `docs/SessionLogs/acceptance-matrix/MATRIX-CLOSEOUT.md` and update `MEMORY.md` with the foundation-solid status so subsequent ERPNext-focused work can start from a trusted baseline.

## Findings protocol

Halt + issue. The final parity check's failures matter more than any single run's — they indicate transport divergence in the shared pipeline primitives, which is exactly what Gen 3 was supposed to prevent.

## Sign-off

Branch `accept/07-ui-pseudo-restore`; PR; merge. Matrix closed.
