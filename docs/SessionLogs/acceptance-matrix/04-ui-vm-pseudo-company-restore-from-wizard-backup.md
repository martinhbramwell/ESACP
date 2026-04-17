# Agenda — Acceptance Run 04 (UI) — dev VM, pseudo-company skeletal ERPNext restored from wizard backup

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove that the backup produced in run 03 (B03) can be used to rebuild an equivalent skeletal ERPNext instance through the Cytoscape UI, with a single destroy + single build, validated by Playwright.

## Entry preconditions

- Run 03 complete; minutes committed.
- Backup **B03** present at the path declared in run 03's param file.
- Saconsole running; dev VM from run 03 still present (this run destroys it as its first action).

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/04-ui-pseudo-restore.yml`

```yaml
run: "04"
transport: ui
target_vm: dev01
variant: pseudo_restore
backup_source: "docs/SessionLogs/acceptance-matrix/artefacts/B03-wizard.sql.gz"
wait_budget_seconds: 1500
```

`backup_source` must match run 03's `backup_output_path` exactly. Confirm before launching.

## Commands (single destroy, single build)

1. Destroy: Playwright right-clicks the dev VM from run 03 → Destroy → confirms.
2. Build: Playwright drags saconsole → target quadrant → selects "Pseudo-company skeletal (restore)" → confirms. Restore source is read from the param file.

## Playwright test

`prototypes/cytoscape/tests/accept-04-ui-pseudo-restore.spec.js`

The test:

1. Destroys the run-03 dev VM.
2. Builds the fresh dev VM with the pseudo-restore option using B03.
3. Navigates to `https://<target_vm>.iridium.blue`.
4. Asserts company = `Pseudo-Co`, wizard flag is set, admin email matches run 03's param file, and no Logichem records exist.
5. Compares a small set of canary facts against what the test knows run 03 produced (reuses a helper from run 03).

## Acceptance

- Playwright green.
- Canary facts identical to run 03's exit state — the restore reproduced the wizard's state faithfully.

## Exit state (handed to run 05)

Saconsole + dev VM running restored skeletal ERPNext. Run 05 destroys saconsole, which implicitly collapses this dev VM — a natural reset point between UI and CLI transports.

## Findings protocol

Halt + issue. A mismatch between B03's intent and the restored instance is a real finding — the whole matrix premise is that 04 reproduces 03.

## Sign-off

Branch `accept/04-ui-pseudo-restore`; PR; merge.

**UI transport milestone:** after this run, record in minutes whether runs 01–04 all met acceptance. This is the halfway parity snapshot.
