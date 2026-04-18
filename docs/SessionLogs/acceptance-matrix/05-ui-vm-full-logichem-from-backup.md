# Agenda — Acceptance Run 05 (UI) — dev VM, full Logichem ERPNext from backup

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove that a dev VM can be built through the Cytoscape UI and end up running full Logichem ERPNext, restored from the golden production backup, via a single destroy + single build action validated by Playwright. Parity partner: run 02 (CLI).

## Entry preconditions

- Run 04 complete; minutes committed.
- Saconsole running; dev VM from run 04 present (this run destroys it first — transport transition from CLI to UI).
- Golden production backup available at its known path on the controller (see `project_production_erpnext.md` / `project_prod_repos_ssh.md`).
- `hosts_map.yml` entry for the chosen dev VM name pre-registered.

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/05-ui-full-logichem.yml`

```yaml
run: "05"
transport: ui
target_vm: dev01  # confirm at session start against hosts_map.yml
variant: full_logichem
backup_source: golden_production
wait_budget_seconds: 1800
```

## Commands (single destroy, single build)

1. Destroy: Playwright right-clicks the dev VM from run 04 → Destroy → confirms.
2. Build: Playwright drags saconsole → the target quadrant → selects "Full Logichem from backup" in the pre-provision wizard → confirms. The restore source path is read from the param file, not entered interactively.

## Playwright test

`prototypes/cytoscape/tests/accept-05-ui-full-logichem.spec.js`

The test:

1. Destroys the run-04 dev VM and waits for the topology to reflect it.
2. Performs the drag-and-build path with the `full_logichem` option.
3. Waits (bounded by `wait_budget_seconds`) for the dev VM to appear and turn green.
4. Asserts `https://<target_vm>.iridium.blue` responds with the Logichem ERPNext login page.
5. Queries the same canary Logichem record defined in run 02's helper — parity check against CLI transport.

## Acceptance

- Playwright green.
- `sync_check.sh` ERPNext row for target VM ✅.
- Canary facts identical to run 02's — CLI and UI transports landed at the same state.
- No unexpected mutations in tracked files.

## Exit state (handed to run 06)

Saconsole + dev VM running full Logichem ERPNext, restored from golden backup. Run 06 begins by destroying this dev VM.

## Findings protocol

Halt + issue. Divergence from run 02's observable outcome is a parity finding — it indicates the pipeline primitives are taking different paths under the two transports.

## Sign-off

Branch `accept/05-ui-full-logichem`; PR; merge.
