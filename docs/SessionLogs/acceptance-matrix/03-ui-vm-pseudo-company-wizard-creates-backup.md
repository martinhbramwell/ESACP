# Agenda — Acceptance Run 03 (UI) — dev VM, pseudo-company skeletal ERPNext via setup wizard, backup produced

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove that a dev VM can be built through the Cytoscape UI into a bare ERPNext instance, driven through the ERPNext setup wizard by Playwright, and a post-wizard backup archived — all as one single-command run whose outcome is validated by Playwright.

## Entry preconditions

- Run 02 complete; minutes committed.
- Saconsole running; the dev VM from run 02 destroyed (by this run's first action — see below).
- `hosts_map.yml` entry for the target dev VM still pre-registered (same name as run 02 is fine).

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/03-ui-pseudo-wizard.yml`

```yaml
run: "03"
transport: ui
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
```

The wizard fills every required field from this file. No interactive input during the wizard run.

## Commands (single destroy, single build)

1. Destroy: Playwright right-clicks the dev VM from run 02 → Destroy → confirms.
2. Build: Playwright drags saconsole → target quadrant → selects "Pseudo-company skeletal (wizard)" → confirms. The Playwright test then continues — post-build it drives the ERPNext setup wizard and triggers the backup.

"One build command" here means the UI's single build action. Everything that follows — wizard completion, backup archival — is part of the same Playwright run, no human input required.

## Playwright test

`prototypes/cytoscape/tests/accept-03-ui-pseudo-wizard.spec.js`

The test:

1. Destroys the run-02 dev VM and waits for the topology to reflect it.
2. Builds the fresh dev VM with the pseudo-wizard option.
3. Navigates to `https://<target_vm>.iridium.blue`, drives the ERPNext setup wizard with values from the param file.
4. Triggers an ERPNext backup (via the wizard-completion hook or the admin UI, whichever the UI exposes as the "one build" endpoint).
5. Fetches the backup artefact to `backup_output_path`, verifies integrity (file exists, gzip-valid, SQL header present).
6. Asserts the ERPNext instance has company name = `Pseudo-Co` and no Logichem records.

This is the one agenda whose Playwright test will be substantial. Test code is not length-limited; extract helpers when they repeat into runs 04, 07, 08.

## Acceptance

- Playwright green.
- Backup artefact at `backup_output_path` passes integrity check.
- No unexpected mutations in tracked files aside from the artefact and the spec file.

## Exit state (handed to run 04)

Saconsole + dev VM running skeletal ERPNext for "Pseudo-Co". Backup **B03** archived at the path above. Run 04 will consume B03 after destroying this dev VM.

## Findings protocol

Halt + issue. The wizard-automation surface is the most likely source of gaps; if selectors don't exist yet, that is a finding, not a fix-in-place.

## Sign-off

Branch `accept/03-ui-pseudo-wizard`; PR; merge. Backup artefact committed (gzipped SQL dump from a skeletal company is small; safe to track).
