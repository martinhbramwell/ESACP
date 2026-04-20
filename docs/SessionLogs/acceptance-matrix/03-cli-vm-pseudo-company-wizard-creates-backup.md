# Agenda — Acceptance Run 03 (CLI) — dev VM, pseudo-company skeletal ERPNext via setup wizard, backup produced

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove a dev VM can be built from the CLI into a bare ERPNext instance, driven through the ERPNext setup wizard by Playwright, and a post-wizard backup archived — with the UI converging to reflect the new reality. B03 is the reference artefact for the matrix-close parity check against run 06 (UI).

## Entry preconditions

- Run 02 complete; minutes committed.
- Cytoscape UI running for observation.
- Saconsole running; dev VM from run 02 present (this run destroys it first).

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/03-cli-pseudo-wizard.yml`

```yaml
run: "03"
transport: cli
target_vm: dev01
variant: pseudo_wizard
company:
  name: "Pseudo-Co"
  abbr: "PSC"
  country: "Canada"
  currency: "CAD"
  language: "en"
admin_user:
  email: "admin@pseudo-co.example"
backup_output_path: "docs/SessionLogs/acceptance-matrix/artefacts/B03-wizard.sql.gz"
wait_budget_seconds: 1800
topology_convergence_budget_seconds: 300
```

These company values are reused verbatim by run 06 (UI) — B03 and B06 must be equivalent; that is the parity check.

## Commands (single destroy, single build)

1. Destroy: `./tools/esacp.py destroyVM <target_vm>` (exact spelling confirmed at session start).
2. Build: `./tools/esacp.py provisionGeneric <target_vm> --wizard-mode replay --wizard-arg <wizard_recording>` — stages 1–9 produce a skeletal ERPNext, then `replay_wizard.js` drives the recorded Playwright script for company entry, then `handleBackup.sh` archives B03. The spec reads `target_vm` and `wizard_recording` from the param file.

The wizard run and backup-trigger are part of the Playwright test that observes/drives the post-build state — they do not count as additional commands, they're part of the test harness's observation pass.

## Playwright test

`prototypes/cytoscape/tests/accept-03-cli-pseudo-wizard.spec.js`

The test:

1. Spawns destroy; asserts UI converges to saconsole-only within the convergence budget.
2. Spawns build; asserts UI shows dev VM as green within the convergence budget.
3. Navigates to `https://<target_vm>.iridium.blue`, drives the ERPNext setup wizard with run-03 params (helper defined here, reused by run 06).
4. Triggers backup; writes artefact to `backup_output_path`; verifies integrity.
5. Asserts company = `Pseudo-Co`, no company-specific records.

## Acceptance

- Playwright green.
- B03 artefact integrity check passes.
- Canary facts recorded for the close-out parity check against B06.

## Exit state (handed to run 04)

Saconsole + dev VM running skeletal ERPNext for `Pseudo-Co`, backup **B03** archived.

## Findings protocol

Halt + issue. The wizard-automation surface is the most likely source of gaps; if selectors don't exist yet, that is a finding, not a fix-in-place.

## Sign-off

Branch `accept/03-cli-pseudo-wizard`; PR; merge. B03 committed alongside the spec.
