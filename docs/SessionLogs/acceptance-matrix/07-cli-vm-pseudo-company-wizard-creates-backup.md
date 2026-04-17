# Agenda — Acceptance Run 07 (CLI) — dev VM, pseudo-company skeletal ERPNext via setup wizard, backup produced

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove a dev VM can be built from the CLI into a bare ERPNext instance, driven through the ERPNext setup wizard by Playwright, and a post-wizard backup archived — with the UI converging to reflect the new reality.

## Entry preconditions

- Run 06 complete; minutes committed.
- Cytoscape UI running for observation.
- Saconsole running; dev VM from run 06 present (this run destroys it first).

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/07-cli-pseudo-wizard.yml`

```yaml
run: "07"
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
backup_output_path: "docs/SessionLogs/acceptance-matrix/artefacts/B07-wizard.sql.gz"
wait_budget_seconds: 1800
topology_convergence_budget_seconds: 300
```

Note the company values are identical to run 03 deliberately — this is the parity check. B07 should be equivalent to B03.

## Commands (single destroy, single build)

1. Destroy: `./tools/esacp.py destroyVM <target_vm>` (exact spelling confirmed at session start).
2. Build: `./tools/esacp.py provision --params docs/SessionLogs/acceptance-matrix/params/07-cli-pseudo-wizard.yml`.

The wizard run and backup-trigger are part of the Playwright test that observes/drives the post-build state — they do not count as additional commands, they're part of the test harness's observation pass.

## Playwright test

`prototypes/cytoscape/tests/accept-07-cli-pseudo-wizard.spec.js`

The test:

1. Spawns destroy; asserts UI converges to saconsole-only within the convergence budget.
2. Spawns build; asserts UI shows dev VM as green within the convergence budget.
3. Navigates to `https://<target_vm>.iridium.blue`, drives the ERPNext setup wizard with run-07 params (reuse helper from run 03).
4. Triggers backup; writes artefact to `backup_output_path`; verifies integrity.
5. Asserts company = `Pseudo-Co`, no Logichem records.

## Acceptance

- Playwright green.
- B07 artefact integrity check passes.
- B07's canary facts match B03's — the CLI path produced an equivalent backup.

## Exit state (handed to run 08)

Saconsole + dev VM running skeletal ERPNext for `Pseudo-Co`, backup **B07** archived.

## Findings protocol

Halt + issue. Divergence between B03 and B07 is a high-value parity finding — both transports are supposed to land at the same state through the same pipeline primitives.

## Sign-off

Branch `accept/07-cli-pseudo-wizard`; PR; merge. B07 committed alongside the spec.
