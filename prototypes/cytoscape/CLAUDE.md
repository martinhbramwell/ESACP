# Cytoscape Prototype — Claude Code Context

Run: `uvicorn tools.api:app --port 8088 --reload` (project root) + `bash doCytoscape.sh` → http://localhost:5173

## Zone Frames — HTML Overlays (NOT compound nodes)

Compound nodes were abandoned (GH #15). Three fatal bugs:
1. Empty compound zones collapse to zero size at (0,0)
2. Attribute selectors like `node[!provisioned]` bleed onto zone nodes (no VM data → falsy → matched)
3. Phantom anchor selectors lose specificity battles against VM style rules

**Solution**: `<div id="zone-overlay">` with four `.zone-panel` children, absolutely positioned. Position via `_graphToScreen(splitX, splitY)` on every `pan zoom resize` event. Do NOT reintroduce compound nodes for zone frames.

## Zone Geometry — Single Source of Truth

Zone panels, the splitter handle, and `_zoneAtPos()` MUST all derive coordinates from the same `splitX/splitY` via `_graphToScreen()`. Divergence causes VMs to land visually in one zone but be assigned to another. `_updateQuadAnchors()` clamps and writes `splitX/splitY` then calls `_constrainVMsToZones()`.

## Phantom Anchor Nodes

Phantom anchors hold zone corners to prevent zones collapsing. Requirements:
1. Add `provisioned: true` to phantom data — prevents unprovisioned amber-dashed selector matching
2. Add `.phantom` class in `init()`: `cy.$('#' + a.id).addClass('phantom')`
3. Selector: `node.phantom[phantom = "yes"]` (specificity 21) placed AFTER base VM style in CY_STYLE array
4. Anchor nodes must NOT have a `parent` field (no compound nodes)

## VM Power State Display

Nodes reflect libvirt power state (`vm_state` from `/api/hosts`):
- **Running**: full brightness, coloured border, bright label
- **Shut off** (provisioned): grey dotted border (`#556677`), faded icon (`background-opacity: 0.15`), muted label (`#8899aa`), `[shut off]` suffix
- **Unprovisioned**: amber dashed border (`#f0a020`), warm amber label (`#e8c060`), full icon, `[unprovisioned]` suffix — takes precedence over shut-off styling
- Shut-off selector requires `[?provisioned]` so it never overrides unprovisioned nodes
- `_refreshVmState()` polls `/api/hosts` every 30s: patches existing nodes, adds new nodes for hosts that appeared, and removes nodes for hosts that disappeared (full topology sync, no re-layout)
- **Provisioning/Refreshing/Destroying** (active job): blue dashed border (`#4488dd`), cyan label (`#66aaff`), `[provisioning...]`/`[refreshing...]`/`[destroying...]` suffix — overrides unprovisioned amber. Driven by `job_status` node data set by `_attachJobPoller()`.
- **Clicking a provisioning node** shows live job log in the info panel via `_showNodeJobLog()` — fetches full log snapshot from `/api/jobs/{id}`, primary poller continues to append new lines. Clicking away and back re-fetches the snapshot.
- `_refreshVmState()` skips label rebuild for nodes with `job_status === 'running'`
- **Power control buttons**: Start (shut-off VMs), Stop + Reboot (running VMs) — synchronous API calls via `_vmPowerAction()`, immediate `_refreshVmState()` after action, re-renders info panel with updated buttons
- **Memory guard**: Start button may return HTTP 409 with RAM-exceeded message — surfaced as error text in the info panel

## Viewport Initialisation

Never use `cy.fit()` at init — unreliable because phantom positions may be wrong and flex dimensions unsettled. Use `_fitZoneGraph()` inside `requestAnimationFrame()`:

```js
requestAnimationFrame(() => {
  _fitZoneGraph()
  _updateZoneOverlay()
})
```

`_fitZoneGraph()` computes zoom from `ZONE_GRAPH` constants and `cy.width()`/`cy.height()`. Also correct for "Reset View" buttons.

## Selector Syntax

- Use `[!key]` to match nodes where `key` is falsy; `[?key]` for truthy — do NOT use `[?key = false]` or `[key = false]` (silently fails)
- Attribute selectors that should only apply to VM nodes must exclude phantoms: `:not(.phantom):not(.template-node)`
- Use `.not('.phantom')` chained filter (not `':not(.phantom)'` string selector) for external JS access via `div._cyreg.cy`

## INITIAL_POSITIONS Keys

INITIAL_POSITIONS keys must match node ID (hostname), not nickname. The API sets `id: h.hostname`. If INITIAL_POSITIONS uses a nickname (`tgt3` instead of `target3`), the node falls through to `_repositionUnknownNodes()` and stacks on the first dev node.

## api.js Gotchas

- `_syncTemplateState()` must be `await`ed before `_reconnectActiveJob()` in `init()` — race condition otherwise resets tpl-building to tpl-none
- Consecutive "waiting 30s ..." lines compact in-place via `_COMPACT_SUFFIXES` in `emit()`

## Topology UI First (CRITICAL RULE)

Any operation the Cytoscape UI can perform MUST be performed via the browser extension on the topology — not via virsh/CLI. The UI is the product; using it IS the ongoing functional test. CLI only for bootstrap, sync_check, and operations not yet exposed in the UI.

## VM Zones & Roles

- `vm_role`: two-part compound field — `dev:unspecified`, `dev:master`, `dev:slave`, `staging:master`, `staging:slave`, `production:master`, `production:slave`
- `normalizeVmRole()` translates old single-word values on load
- Staging and Production: max 1 master + 1 slave (enforced in UI)
- Production zone is write-protected — promote only via "Promote →" button

## Playwright Tests

Tests live in `prototypes/cytoscape/tests/`. Run from the `prototypes/cytoscape` directory. Shared helpers (`waitForGraph`, `selectNode`, `clickInfoButton`, `waitForJob`, constants) in `tests/helpers.js` — imported by all spec files.

```bash
npx playwright test --grep "inspect"        # read-only, safest
npx playwright test --grep "lifecycle"      # destroy + deploy cycle
npx playwright test --grep "fixture"        # verify ce_sri fixtures post-deploy
npx playwright test --grep "button guards"  # unprovisioned node negative test
npx playwright test --grep "e2e"            # cloud-init provision (real run)
```

Test files:
- `topology-ops.spec.js` — Deploy, Refresh, Destroy, Inspect, Rebuild, Lifecycle, Power, Provisioning state
- `unprovisioned.spec.js` — button guards (negative) + e2e Provision via cloud-init path (#143)

**Prefer Playwright over Chrome extension** for topology operations (Deploy, Refresh, Destroy, Inspect). Cheaper in API credits, more reliable, and produces repeatable regression scripts. Chrome extension remains valid for visual inspection, ad-hoc exploration, and read-only production browsing.

**Architecture**: Claude Code CLI and the Chrome MCP extension must run on the same machine (local MCP/stdio connection). Playwright tests only need Node.js and network access to the target URL — no Chrome extension required for test execution.

**Long-term direction**: Playwright regression suites covering ERPNext business use cases (invoicing, inventory, HR workflows). Tests run against dev/staging instances only — never production. All dev/staging VMs must use `AMBIENTE=1` (Pruebas/test SRI endpoint).

## Stockroom Templates

Two template tiles in the Console quadrant:
- **Restored ERPNext** (`tpl-erpnext-restored`) — provisions a VM and restores a production database clone (stages 1-9, `provision_mode="restored"`)
- **Generic ERPNext** (`tpl-erpnext-generic`) — provisions a blank ERPNext with setup wizard ready (stages 1-9, `provision_mode="generic"`, skips ce_sri/backup/Social Login)

Both share the same Packer base image. `_syncTemplateState()` applies `tpl-ready`/`tpl-none`/`tpl-building` to both tiles simultaneously.

Generic template dialog includes a **Wizard Completion** section with three modes:
1. **Record** — Playwright codegen records wizard input, saves to `recordings/wizard/`
2. **Replay** — runs a previously recorded wizard script
3. **Use existing** — restores from a golden backup (`platforms/kvm/golden_backups/*.tgz`)

After wizard completion (Record/Replay), a golden backup is captured via `handleBackup.sh` and saved to the controller.

### Playwright Recorder Infrastructure

- `recordings/record_wizard.js` — wraps `npx playwright codegen` for headed recording
- `recordings/replay_wizard.js` — replays a saved recording via `@playwright/test`
- Recordings stored in `prototypes/cytoscape/recordings/wizard/*.spec.js`
- This is the training ground for the broader goal: capturing production user workflows for v13-v16 upgrade regression testing

## Inspect / Refresh / Destroy Pipeline

- **Inspect**: 3-box service grid (nginx/frappe+supervisor/mariadb), status from `GET /api/health/{hostname}` via SSH checks
- **Refresh**: `POST /api/refresh/{hostname}` — SCPs saved `{hostname}-differentiate.sh` artifact and runs `sudo bash`
- **Destroy**: remove live WG peer → delete snapshots → virsh destroy+undefine → clean hosts_map.yml + group_vars/all.yml + keys.sops.yml + cloud-init dir → regen inventory → Ansible wireguard on hub
