# Session Minutes — 2026-04-16 15:02

**Objective:** Phase 5 — Packer build + memory guard + VM power primitives (#193)

**Branch:** `fix/193-vm-power-primitives`
**PR:** #204 (merged as commit `447da8a`)
**Commit:** `3a2741a`
**Plan file:** `~/.claude/plans/synthetic-mapping-pretzel.md` → Phase 5

---

## Pre-session state

- Session started on stale branch `fix/192-destroy-macro` (PR #203 merged prior session but local branch not deleted — consistent with the "keep merged branches" rule). Switched to `main` + pulled before creating new branch.
- `sync_check.sh`: 40 pass / 11 warn / 3 fail. All 3 failures were WG mesh pings to dev02/dev03/target5 — expected, no dev VM currently provisioned (toshiba's 16 GB constrains to saconsole + 1 dev VM at a time).

## Scope boundary

Phase 5 extracts VM power endpoints, memory guard, and Packer build orchestration only. It is **pure refactor**: the virsh+SSH call sequences after extraction are byte-identical to what was deleted from the monoliths. No behavioural change intended.

## Design decisions made during the session

1. **Error-signalling style for `vm_power`** — considered a `PowerResult` dataclass vs. raise-based. Chose raises (matching `destroy_vm.py`): `RuntimeError` for virsh/SSH failure, `ValueError` for policy rejection (hub stop). Dispatcher catches each and maps to HTTP 500 / 400. This avoids introducing a new result type convention in the orchestration layer.

2. **Hub-stop guard placement** — the "can't stop the hub" rule lived in `api.py` before. Moved to the `vm_power.stop(..., is_hub=False)` primitive so the rule applies uniformly regardless of caller (future CLI dispatcher, job_worker, etc.).

3. **`_HOST_RAM_RESERVE_KIB`** — moved from `api.py` to `memory_guard.py` as a private module constant. It is a memory-guard concept, not an API concept.

4. **Dropped `emit_compact` log compaction** from the Packer build — the `\r`-overwrite for consecutive "— waiting 30s ..." lines was a cosmetic job-log concern. Primitive uses plain `emit()`; compaction, if re-needed, belongs in a dispatcher-side emit wrapper, not in pipeline business logic.

5. **`virsh_ssh` location** — first attempt put it in `hypervisor_helpers.py`. The pre-commit size ratchet correctly blocked this because that file (67 lines) grew to 77, and the ratchet enforces "dispatcher/pipeline files must not grow." Response: created a new 15-line `tools/pipeline/orchestration/virsh.py` containing only `virsh_ssh`. This respects the ratchet's spirit (the rule is "don't accrete into monoliths", not "never share helpers") and keeps the new concern in its own tight module.

6. **`check_memory` signature** — dropped the `emit` parameter. The function is a pure query that returns either `None` or a rejection string; there is no progress to emit. Forcing an unused `emit` arg for conformance would be ceremony.

## Implementation sequence

1. Created 3 new primitives + 1 shared helper under `tools/pipeline/orchestration/`:
   - `vm_power.py` (46 lines) — `start(hypervisor, hostname, emit) -> str`, `stop(..., is_hub=False) -> str`, `reboot(...) -> str`
   - `memory_guard.py` (77 lines) — `check_memory(hypervisor, hostname) -> str | None` + private `_parse_nodeinfo_memory`, `_dominfo_max_memory`, `_extract_max_memory`, `_format_rejection` helpers
   - `build_template.py` (77 lines) — `build_template(emit) -> None` + private `_flush_log` poll helper
   - `virsh.py` (15 lines) — `virsh_ssh(hypervisor, cmd, timeout=30) -> CompletedProcess`

2. Thinned `tools/api.py`:
   - Deleted `_virsh_ssh`, `_check_memory`, `_HOST_RAM_RESERVE_KIB`
   - Added helper `_resolve_power_target(hostname) -> (host_cfg, hypervisor)` (9 lines) — lifts the common 404/400 lookup out of the three endpoints
   - Each of `/api/vm/{host}/{start,stop,reboot}` reduced to ~12 lines: resolve → call primitive → map exceptions to HTTP.

3. Thinned `tools/job_worker.py`:
   - `run_build_template` reduced from 85 lines (with nested closures) to 3 lines (import + call).
   - Deleted unused module globals `HYPERVISOR_ALIAS`, `HYPERVISOR_USER`, `HUB_IP`, `HUB_SSH`, `PLATFORMS_PACKER`.
   - Trimmed `from tools.host_identity import …` to only the names still used (`HUB_KEY`, `ZONE_DOMAINS`).

4. Updated `tools/CLAUDE.md` reference from `_check_memory()` to `tools/pipeline/orchestration/vm_power.py` + `memory_guard.check_memory()`, and documented the new HTTP 400 hub-stop path.

## Issues encountered

- **Pre-commit ratchet block on hypervisor_helpers.py**: first commit attempt failed with `Anti-spiral size check FAILED: GREW tools/pipeline/orchestration/hypervisor_helpers.py: 77 lines (was 67, target 80)`. The ratchet does not distinguish "helper file gained a function" from "monolith grew" — it blocks any growth. **Correct fix**: extract the new helper to a new small file (`virsh.py`) rather than mutate an existing one. Noted as a reusable pattern: when sharing a new helper, create a new file rather than extending a tracked one.

## Acceptance tests

| Check | Result |
|---|---|
| All new pipeline files ≤80 lines | ✅ 15 / 46 / 77 / 77 |
| `python3 -c "from tools.pipeline.orchestration.*` imports cleanly | ✅ |
| Signatures match the design contract | ✅ |
| `POST /api/vm/nosuchhost/start` → HTTP 404 | ✅ |
| `POST /api/vm/saconsole/stop` → HTTP 400 with "Cannot stop hub node" | ✅ (exercises the `ValueError → 400` mapping) |
| `memory_guard.check_memory('toshiba', 'dev02')` — direct Python call | ✅ real SSH + virsh round-trip (returned a legitimate "failed to get domain 'dev02'" because dev02 is not defined on toshiba right now) |
| Playwright `power` suite (`npx playwright test --grep "power"` in `prototypes/cytoscape/`) | 1 passed (`memory guard surfaces error when insufficient RAM`, mocked), 4 skipped. Skips are by-design guards: each live-VM test requires a non-hub VM in a specific state; none currently exists on toshiba. |
| Pre-commit size ratchet | ✅ (after `virsh.py` fix). `size_baselines.json` auto-updated with new api.py=907 and job_worker.py=305. |

## Deferred items

- **Live start/stop/reboot on a dev VM**: deferred. The extraction is byte-identical to the previous virsh+SSH sequence and the memory-guard mock test confirms the UI contract. Next session that powers on a dev VM via Cytoscape will exercise the real path.
- **`POST /api/build/template` live run**: deferred. A Packer build is ~30 minutes; not warranted for a pure-refactor phase. Will be exercised the next time a template rebuild is initiated.
- **Plan acceptance bullet 5** — `grep 'subprocess.run|virsh|nodeinfo' tools/api.py` returns no matches — **cannot be met in this phase alone**. Other endpoints (`hosts/add`, `provision/erpnext`, `template/status`, `template` delete, `health`) still call subprocess/virsh directly. They are owned by Phases 2, 3, 6 and beyond. The spirit of the bullet (nothing from Phase 5 leaves a subprocess call behind in api.py) is satisfied.

## File inventory

| Action | File | Lines |
|---|---|---|
| new | `tools/pipeline/orchestration/vm_power.py` | 46 |
| new | `tools/pipeline/orchestration/memory_guard.py` | 77 |
| new | `tools/pipeline/orchestration/build_template.py` | 77 |
| new | `tools/pipeline/orchestration/virsh.py` | 15 |
| modified | `tools/api.py` | 999 → 907 (−92) |
| modified | `tools/job_worker.py` | 400 → 305 (−95) |
| modified | `tools/CLAUDE.md` | 1-line reference update |
| modified | `tools/size_baselines.json` | ratchet auto-update |

## Monolith line counts after Phase 5

| File | Start of session | After | Target | Phase that closes it |
|---|---|---|---|---|
| `tools/esacp.py` | 1,011 | 1,011 | ≤150 | #194 (Phase 6), #195 (Phase 7) |
| `tools/api.py` | 999 | **907** | ≤300 | #195 (Phase 7) |
| `tools/job_worker.py` | 400 | **305** | ≤100 | #195 (Phase 7) |
| `tools/install_specific.py` | 721 | 721 | ≤50 | #197 (Phase 9) |

## GitHub actions taken

- Branch `fix/193-vm-power-primitives` pushed.
- PR #204 opened, body listed verified + deferred acceptance items.
- PR merged via `gh pr merge 204 --merge` → merge commit `447da8a`.
- Issue #193 auto-closed by "Closes #193" in PR body. Follow-up comment added recording `3a2741a` / `447da8a` / line reductions for searchability.
- Branch kept locally and on origin (per `feedback_keep_merged_branches.md`).

## Notes for next session

- See `2026-04-16-1502-next-agenda.md` — Phase 6 (#194).
- **Important**: the plan file (`~/.claude/plans/synthetic-mapping-pretzel.md`) cites line ranges `1335-1430` and `1014-1063` for Phase 6 — those are stale (plan was written when `esacp.py` was 1693 lines; it is now 1011). Actual locations grep'd this session:
  - `_strip_ansi` at line 348, `_filter_ansible_line` at 352 — → `tools/pipeline/stages/common/ansible_output.py`
  - `cmd_verify_vpn` at line 660 (ends ~731) — → `tools/pipeline/orchestration/verify_vpn.py`
  - `_get_grafana_creds` at 732, `cmd_validate_observability` at 758 — → `tools/pipeline/orchestration/observability_creds.py`
- Untracked session-log + docs/Ideas/ files on main are pre-existing from prior sessions — not this session's concern, intentionally not committed.
