# Agenda — Acceptance Run 02 (UI) — dev VM, full Logichem ERPNext from backup

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove that a dev VM can be built through the Cytoscape UI and end up running full Logichem ERPNext, restored from the golden production backup, via a single destroy + single build action validated by Playwright.

## Entry preconditions

- Run 01 complete; minutes committed.
- Saconsole running; no dev/target VMs.
- Golden production backup available at its known path on the controller (see `project_production_erpnext.md` / `project_prod_repos_ssh.md`).
- `hosts_map.yml` entry for the chosen dev VM name pre-registered.

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/02-ui-full-logichem.yml`

```yaml
run: "02"
transport: ui
target_vm: dev01  # confirm at session start against hosts_map.yml
variant: full_logichem
backup_source: golden_production
wait_budget_seconds: 1800
```

## Commands (single destroy, single build)

1. Destroy: no-op at start of run 02 (no dev VM present from run 01's exit state). If a dev VM is unexpectedly present, that's a finding — halt.
2. Build: Playwright drags saconsole → the target quadrant → selects "Full Logichem from backup" in the pre-provision wizard → confirms. The restore source path is read from the param file, not entered interactively.

## Playwright test

`prototypes/cytoscape/tests/accept-02-ui-full-logichem.spec.js`

The test:

1. Asserts starting state (saconsole only).
2. Performs the drag-and-build path with the `full_logichem` option.
3. Waits (bounded by `wait_budget_seconds`) for the dev VM to appear and turn green.
4. Asserts `https://<target_vm>.iridium.blue` responds with the Logichem ERPNext login page.
5. Queries a known stable Logichem record (canary lookup defined in the helpers) to confirm the restore delivered real data, not a blank install.

## Acceptance

- Playwright green.
- `sync_check.sh` ERPNext row for target VM ✅.
- No unexpected mutations in tracked files.

## Exit state (handed to run 03)

Saconsole + dev VM running full Logichem ERPNext, restored from golden backup. Run 03 begins by destroying this dev VM.

## Findings protocol

Halt + issue, per plan. Production backups are read-only — a damaged backup on-disk is itself a finding.

## Sign-off

Branch `accept/02-ui-full-logichem`; PR; merge.
