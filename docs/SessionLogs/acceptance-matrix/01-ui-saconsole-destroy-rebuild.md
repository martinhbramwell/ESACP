# Agenda — Acceptance Run 01 (UI) — saconsole destroy + rebuild

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Objective

Prove saconsole can be destroyed and rebuilt entirely through the Cytoscape UI, with a single destroy action and a single build action, validated by a dedicated Playwright test.

## Entry preconditions

- Working tree clean; `main` at HEAD.
- Hypervisor (toshiba) reachable; `sync_check.sh` green except for the expected unprovisioned dev-VM warnings.
- `hosts_map.yml` known-good; saconsole currently running and reachable.
- No in-flight pipeline jobs.

## Parameter file

`docs/SessionLogs/acceptance-matrix/params/01-ui-saconsole.yml`

```yaml
run: "01"
transport: ui
target: saconsole
wait_budget_seconds: 600
```

Confirm this file exists and matches before the run. If missing, create it — that's the only pre-session code change permitted.

## Commands (single destroy, single build)

Both issued through Playwright against the running Cytoscape UI at `http://localhost:5173`:

1. Destroy: right-click the saconsole node → Destroy → confirm.
2. Build: right-click the empty hub quadrant → Build saconsole → confirm.

No further input. The UI's own progress indicators carry the run to completion.

## Playwright test

`prototypes/cytoscape/tests/accept-01-ui-saconsole.spec.js` (create if absent; file a halt issue if the UI lacks the selectors the test needs).

The test:

1. Asserts saconsole is present and green at start.
2. Performs the destroy click path; waits for saconsole to leave the topology.
3. Performs the build click path; waits for saconsole to return to the topology as green.
4. Asserts WireGuard hub responds (backend health endpoint) and the sync_check row for saconsole reports ✅.

## Acceptance

- Playwright test ends green.
- `sync_check.sh` saconsole row ✅.
- `hosts_map.yml` and all other tracked files unchanged (`git status` clean).

## Exit state (handed to run 02)

Saconsole running on a freshly-rebuilt hub VM; no dev/target VMs; WireGuard hub up; topology shows only saconsole.

## Findings protocol

Any failure halts the run. File a GitHub issue with the Playwright trace path and observed state; do not patch the SUT in place. See plan §Findings protocol.

## Sign-off

- Commit minutes + any new files (param file, Playwright spec) on a branch named `accept/01-ui-saconsole`.
- Open PR, merge, close branch.
- Update memory index if the matrix's overall state changed.
