# Session Minutes — 2026-04-16

## Session 1: Phase 1 — Pre-flight validation primitives (#189)

**Objective:** Phase 1 — Pre-flight validation primitives (#189)

### Completed

1. Created branch `fix/189-preflight-primitives` from main
2. Created `tools/pipeline/stages/preflight/` with 5 files:
   - `check_tools.py` (68 lines) — scans PATH for required CLI tools, returns structured ToolStatus
   - `check_files.py` (39 lines) — verifies age key, .sops.yaml, SSH key pair existence
   - `check_keys.py` (75 lines) — SOPS decryption + WireGuard key structure validation
   - `__init__.py` (45 lines) — `run_preflight()` composing all three
   - `verify.py` (73 lines) — colocated acceptance test (7 checks)
3. Replaced esacp.py's `cmd_confirm_prerequisites` and `cmd_validate_keys` with thin dispatchers
4. Deleted REQUIRED_TOOLS, MANUAL_INSTALL_HINTS constants and all business logic from esacp.py
5. Transport-specific UI (apt install prompt, manual hints, file remediation) correctly stays in dispatcher
6. esacp.py reduced by 108 lines (1677 → 1569)
7. All acceptance criteria passed; pre-commit ratchet hook passes
8. PR #200 created, fixes #189

### Decisions

- Remediation UI (Rich interactive prompts for apt install, manual hints, file guidance) stays in dispatcher — it's transport-specific, not business logic
- Pipeline primitives emit plain `[OK]`/`[MISSING]` tags; Rich formatting is dispatcher's job

---

## Session 2: Phase 3 — VM build primitives (#191)

**Objective:** Phase 3 — VM build primitives (#191)
**Branch:** `fix/191-vm-build-primitives`
**PR:** #201 (merged)

### Completed

1. **Mechanical acceptance checks** — all passed:
   - esacp.py reduced from ~1589 to 1011 lines (-578)
   - 7 new pipeline files, all ≤80 lines, emit-only
   - No virsh/ssh subprocess calls in `cmd_build_vm` dispatcher

2. **E2E test — `buildVM dev01`** — revealed pre-existing bugs:
   - Static cloud-init templates had `${CONTROLLER_PUBKEY}` never interpolated
   - Directory naming mismatch: code expects `dev01/`, files at `toshiba-dev01/`
   - Autoinstall path assigns DHCP address instead of configured static IP

3. **Root cause**: `build_vm_seed.py` had a duplicate, broken seed ISO builder. Stage 1's `seed_iso.py` already does this correctly (dynamic generation from hosts_map.yml).

4. **Fix**: Rewired `build_vm.py` to import from stage 1. Deleted broken builder from `build_vm_seed.py`. Net -23 lines.

5. **Issue filed**: #202 — generate cloud-init from template + hosts_map.yml (top priority after Gen 3 phases)

### Commits
- `eb68e18` — `refactor(pipeline): extract VM build primitives into pipeline (#191)`
- `f6b6b07` — `fix(pipeline): reuse stage 1 seed_iso in buildVM — eliminate broken static templates (#191)`

### Blockers
- `buildVM` e2e blocked by #202 (autoinstall static IP). Pre-existing, not a regression. `provisionVM` (template path) unaffected.

### Issues opened
- #202: refactor(kvm): generate cloud-init from template + hosts_map.yml
