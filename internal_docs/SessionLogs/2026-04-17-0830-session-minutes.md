# Session Minutes — 2026-04-17 08:30 EDT

**Objective**: Phase 8 — Delete dead Gen 1 dev-quadrant orchestrators (#196)
**Result**: ✅ Complete. PR #212 merged 2026-04-17T12:28:30Z, merge commit `dfcddc9`.

---

## Unfinished Business (carried from prior session)

| Item | Status |
|---|---|
| Phase 8 (#196) — delete dead Gen 1 + extract any trapped logic | ✅ CLOSED — PR #212 merged, `dfcddc9` |
| Pre-session ritual: sync_check, verify_phase7, plan reload | ✅ CLOSED |

---

## New Business

### ✅ CLOSED

1. **WireGuard hub peer drift (second recurrence)** — Investigated root cause. Destroy primitive removes hub peer entry + mutates `hosts_map.yml`/`group_vars/all.yml`/`keys.sops.yml`/inventory; `git restore` of those files declaratively puts the 5 spokes back but **does not** re-apply the hub's live peer list. Filed as **#210** (structural fix options proposed; procedural workaround documented).

2. **Phase 8 — Gen-1 dev-CRUD deletions**:
   - `tools/orchestrator.py` (213 lines) — pure wrapper, deleted
   - `orchestration/provision.py` (327 lines) — VBox-era, superseded by `macro/provision.py`, deleted
   - `orchestration/provision_kvm.py` (350 lines) — autoinstall detection captured in Phase 3, deleted
   - Net diff: **+153 / −903** lines
   - `tools/verify_phase8.py` added (mirrors `verify_phase7.py`)

3. **validate_observability.py decision** — kept as standalone measurement harness (not state-mutation; pure assertion), documented in `tools/CLAUDE.md` under a new "Standalone harnesses" section. Rule recorded: harnesses that only measure may stay single-file; harnesses that mutate state must be pipeline primitives.

4. **Live doc scrub** — `README.md`, `internal_docs/SystemOverview.md`, `internal_docs/BuildOutProcedure.md` swapped stale command references for `./tools/esacp.py provision <host>`. `SETUP_GUIDE.md` got a historical-status banner (Stage 1 / VBox-era body preserved as record). Historical artifacts left untouched (`design_docs/`, `platforms/vbox/`, `Stage 1.5 completion checklist.md`, `internal_docs/SessionLogs/`).

5. **Cytoscape e2e acceptance** — `run-topology-test dev01 lifecycle` passed (~29 min provision + destroy). Jobs `3493734c` (provision) and `4e37318f` (destroy) both completed `done`. Mutated config files (`hosts_map.yml`, `group_vars/all.yml`, `keys.sops.yml`, `inventory/kvm.yml`) restored post-e2e so only the refactor landed.

6. **Orphan orchestration/ audit** — filed **#211** covering `chaos/run_scenario.py`, `fake_attack.py`, `revertToBaseline.py`. Three-possibility framing: obsolete / salvageable / broader-picture. Raises question of a possible 5th quadrant (chaos / red-team / baseline-management) cutting across the current 4-quadrant Cytoscape design.

### 🔄 CARRIED / ⏳ IN PROGRESS

1. **#210 — destroy/restore WG peer drift** — filed this session. The one-liner fix (`--tags wireguard`) worked at the start but did **not** clear the post-e2e drift at session end. This complicates the "procedural workaround" — next session should re-check whether the ansible play needs additional tags or whether the hub needs a different reconciliation strategy.

2. **Phase 9 (#197) — `install_specific.py` decomposition** — next in line per Gen 3 plan. Constraints: runs on VMs (not the controller), uses stdlib only.

---

## Action Points

| # | Action | Owner | Target |
|---:|---|---|---|
| 1 | Investigate why `ansible-playbook --limit saconsole --tags wireguard` didn't reapply dev01 peer post-e2e; update #210 with findings | Next session | Before Phase 9 |
| 2 | Phase 9 (#197): decompose `install_specific.py` (721 → ~30 lines) into `tools/vm_scripts/install_specific/` package; must still work SCP'd as-is on VMs | Next session | Its own PR |
| 3 | At some point: triage #211 (chaos / fake_attack / revertToBaseline) — obsolete vs salvageable vs broader-picture | Backlog | Not blocking Phase 9 |

---

## Notes

- **Architecture alignment confirmed with user** mid-session: goal is complete CRUD over dev-quadrant VMs via both UI and CLI; atomic units; thin choreography; single source of truth. This framing sharpened Phase 8 scope — the three deleted files were dev-CRUD-in-scope; the three parked files (#211) are other-quadrant and don't duplicate pipeline primitives.
- **Measurement vs state-mutation rule** emerged as the criterion for "can this be a standalone script?". Captured in `tools/CLAUDE.md`.
- E2e wall-time vs Playwright reported duration: Playwright reported "29.1m" after what felt like 4 min of dormancy — `ScheduleWakeup` wait was longer than the 270s requested. Worth watching if wakeup timing keeps being unreliable.

---

## Open Issues (post-session)

| # | Title | Relevance |
|---:|---|---|
| 197 | Phase 9 — decompose `install_specific.py` | **Next session** |
| 210 | Destroy strips hub WG peer; git-restore doesn't re-apply | Recurring, procedural fix currently unreliable |
| 211 | Audit orphan orchestration/ files | Backlog |
| 202 | cloud-init template generation | Open |
| 206 | `snapshot_vm.py` subprocess violation (Phase 7 deferral) | Open |
| 187 | `esacp.py` — extract legacy commands into pipeline-backed thin wrappers | Open |
| 188 | Invoke scripts as executables, not via `python` prefix | Open |
| 181, 157, 156, 153, 138, 65, 50, 48 | Longer-term / infrastructure / nice-to-haves | Open |
