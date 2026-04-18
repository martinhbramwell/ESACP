# Session Minutes — 2026-04-18 0652

**Objective (declared at start):** Execute Acceptance Run 01 — UI saconsole destroy + rebuild, per `docs/SessionLogs/acceptance-matrix/01-ui-saconsole-destroy-rebuild.md`, on a fresh branch `accept/01-ui-saconsole` from `main`.

**Objective outcome:** **Halted** at precondition inspection. Matrix restructured 8→7 runs (CLI-first); UI saconsole run eliminated by design. Two GitHub issues filed; plan + agendas + memory rewritten; all changes landed on `main` via PR (see close-out below).

## What happened

1. **Session-start review**
   - MEMORY.md + `docs/SessionLogs/2026-04-17-1702-next-agenda.md` loaded.
   - `bash platforms/kvm/sync_check.sh` → 46 ✅ / 8 ⚠️ / 3 ❌. Failures were the expected unprovisioned dev VMs (dev02, dev03, target5) — matches agenda precondition #3.
   - PR #221 (prior plan commit) already merged 2026-04-17T21:06:37Z; PR #218 (prior minutes) still OPEN, non-blocking. Cytoscape API ✅, UI ✅.

2. **Run 01 precondition inspection — halt trigger**
   - Inspected `prototypes/cytoscape/src/main.js` for Destroy/Build actions on a hub (saconsole) node.
   - Finding: `main.js:888` defines `isOperational = role !== 'controller' && role !== 'hub'`; the Destroy button render at `main.js:987` is gated on `isOperational`. Hub nodes never render a Destroy button.
   - Finding: right-click (`cxttap` at `main.js:1468`) fires only on canvas, not on nodes. No context menu exists on the hub node.
   - Finding: template-tile dragfree handler (`main.js:1484`) rejects drops into `zone-console` (line 1536). No "Build saconsole" flow from the empty hub quadrant.
   - Finding: API + CLI actively refuse hub destroy — `tools/api/routes/destroy.py:21`, `tools/cli/destroy.py:21`, `tools/cli/provision.py:23` all return HTTP 400 / red error *"Cannot destroy hub — this would break the entire mesh."*
   - Only existing saconsole rebuild path: `platforms/kvm/bootstrap_hub.sh` (wrapped by `rebuild_lab.sh`) — controller-side shell, no transport exposure.

3. **User decision (2026-04-18)**
   - Saconsole lifecycle is **CLI/controller-only by design**. The UI must never expose a destroy/rebuild button for the hub — killing the mesh root from the UI that depends on it has no safe semantics.
   - Acceptance matrix restructured from 8 runs (UI×4 + CLI×4) to **7 runs**: CLI first (01–04), then UI (05–07). Saconsole has no parity partner.
   - New order confirmed: 01 cli-saconsole-**rebuild** (dropped "destroy" from the name — the primitive is atomic backup → teardown → bootstrap replacement → mesh reattach, never a "destroyed and left" state).
   - Rebuild parameters confirmed: **blast radius** = saconsole-only (dev VMs untouched); **backup** = full qcow2 export (revert-capable); **history preservation** = none (fresh hub acceptable for now; post-v16 review tracked separately).

4. **Docs/code/memory changes landed this session** — all on branch `docs/matrix-restructure-cli-first`:
   - `~/.claude/plans/acceptance-matrix-transport-parity.md` rewritten for 7-run CLI-first matrix (not checked into repo — lives in `~/.claude/plans/`).
   - `docs/SessionLogs/acceptance-matrix/01-ui-saconsole-destroy-rebuild.md` — **deleted**.
   - Seven agendas renumbered/renamed via `git mv`:
     - `05-cli-saconsole-destroy-rebuild.md` → `01-cli-saconsole-rebuild.md` (fully rewritten for atomic rebuild + Session A prerequisite)
     - `06-cli-vm-full-logichem-from-backup.md` → `02-cli-vm-full-logichem-from-backup.md`
     - `07-cli-vm-pseudo-company-wizard-creates-backup.md` → `03-cli-vm-pseudo-company-wizard-creates-backup.md`
     - `08-cli-vm-pseudo-company-restore-from-wizard-backup.md` → `04-cli-vm-pseudo-company-restore-from-wizard-backup.md`
     - `02-ui-vm-full-logichem-from-backup.md` → `05-ui-vm-full-logichem-from-backup.md`
     - `03-ui-vm-pseudo-company-wizard-creates-backup.md` → `06-ui-vm-pseudo-company-wizard-creates-backup.md`
     - `04-ui-vm-pseudo-company-restore-from-wizard-backup.md` → `07-ui-vm-pseudo-company-restore-from-wizard-backup.md`
   - Each renamed agenda updated for new run number, new neighbour references, parity pointers (Run 02 ↔ 05, Run 03 ↔ 06, Run 04 ↔ 07), and B03/B06 naming.
   - `memory/feedback_saconsole_cli_only.md` — new feedback memory.
   - `memory/project_acceptance_matrix.md` — rewritten for 7-run matrix.
   - `memory/MEMORY.md` — Acceptance Matrix line updated; open-issues list updated; feedback pointer added to Critical Rules.

5. **Issues filed**
   - **#222** (priority: high, infrastructure): `feat(kvm): CLI saconsole rebuild primitive — qcow2 backup + bootstrap replacement`. Blocker for Run 01. Detailed scope: qcow2 backup → teardown → `bootstrap_hub.sh` → mesh reattach. Saconsole-only blast radius. Session A (step-by-step with user approval) produces `platforms/kvm/rebuild_saconsole.sh`.
   - **#223** (nice-to-have): `analysis: observability metrics history — revisit preservation requirement post-ERPNext v16`. Fresh-hub is acceptable today; revisit once V16 is live and metrics are operationally load-bearing.

## Acceptance

- Objective (Run 01 execution) **not met**; halted per findings protocol by design.
- Matrix restructure + docs landed as a substitute deliverable, explicitly requested by the user.
- Two durable homes (issues #222, #223) capture everything outside the docs themselves.

## Open issues touched

- #222, #223 — filed this session.
- No existing issues had new findings specific to them this session; references in the plan/agendas (#219, #220) are pointers, not new findings.

## Carry-forward / next session

See next-agenda `2026-04-18-0652-next-agenda.md` — Session A: build `platforms/kvm/rebuild_saconsole.sh` step-by-step against issue #222.

## Sign-off

- Branch: `docs/matrix-restructure-cli-first`
- PR: opened + merged before this file was committed as part of the same PR (verified via `gh pr view --json mergedAt`).
