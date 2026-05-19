# Agenda — Acceptance Run 06 (UI) — dev VM, pseudo-company skeletal ERPNext via setup wizard, backup produced

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove that a dev VM can be built through the Cytoscape UI into a bare ERPNext instance, driven through the ERPNext setup wizard by Playwright, and a post-wizard backup archived — all as one single-command run whose outcome is validated by Playwright. Parity partner: run 03 (CLI); B06 must be equivalent to B03.

## Entry preconditions

- Run 05 complete; minutes committed.
- Saconsole running; the dev VM from run 05 present (this run destroys it first).
- `hosts_map.yml` entry for the target dev VM still pre-registered (same name as run 05 is fine).

## Parameter file

`internal_docs/SessionLogs/acceptance-matrix/params/06-ui-pseudo-wizard.yml`

```yaml
run: "06"
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
backup_output_path: "internal_docs/SessionLogs/acceptance-matrix/artefacts/B06-wizard.sql.gz"
wait_budget_seconds: 1800
```

Values are reused from run 03's param file verbatim — this is the parity check. B06 must be content-equivalent to B03.

## Commands (single destroy, single build)

1. Destroy: Playwright right-clicks the dev VM from run 05 → Destroy → confirms.
2. Build: Playwright drags saconsole → target quadrant → selects "Pseudo-company skeletal (wizard)" → confirms. The Playwright test then continues — post-build it drives the ERPNext setup wizard and triggers the backup.

"One build command" here means the UI's single build action. Everything that follows — wizard completion, backup archival — is part of the same Playwright run, no human input required.

## Playwright test

`prototypes/cytoscape/tests/accept-06-ui-pseudo-wizard.spec.js`

The test:

1. Destroys the run-05 dev VM and waits for the topology to reflect it.
2. Builds the fresh dev VM with the pseudo-wizard option.
3. Navigates to `https://<target_vm>.iridium.blue`, drives the ERPNext setup wizard with values from the param file (reuse helper from run 03).
4. Triggers an ERPNext backup (via the wizard-completion hook or the admin UI, whichever the UI exposes as the "one build" endpoint).
5. Fetches the backup artefact to `backup_output_path`, verifies integrity (file exists, gzip-valid, SQL header present).
6. Asserts the ERPNext instance has company name = `Pseudo-Co` and no company-specific records.

This is the one agenda whose Playwright test will be substantial. Test code is not length-limited; extract helpers shared with run 03 / run 07.

## Acceptance

- Playwright green.
- Backup artefact at `backup_output_path` passes integrity check.
- B06 canary facts match B03 — wizard-backup parity across transports.
- No unexpected mutations in tracked files aside from the artefact and the spec file.

## Exit state (handed to run 07)

Saconsole + dev VM running skeletal ERPNext for "Pseudo-Co". Backup **B06** archived at the path above. Run 07 will consume B06 after destroying this dev VM.

## Findings protocol

Halt + issue. Divergence between B03 and B06 is a high-value parity finding — both transports should produce the same wizard-backup state through the same pipeline.

## Sign-off

Branch `accept/06-ui-pseudo-wizard`; PR; merge. B06 committed alongside the spec.
