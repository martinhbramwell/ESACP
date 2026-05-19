# Session Minutes — 2026-04-15 2300

**Objective:** Fix #185 — eliminate SSH key divergence between bootstrap_targets.sh and pipeline

**Platform:** Mighty (Xubuntu controller)

## Sync Check

42 passed, 11 warnings, 4 failures. Failures all expected (dev VMs shut down). Core infrastructure healthy.

## Discussion & Decision

1. Analysed the divergence: `bootstrap_targets.sh` injects hub's `id_ed25519`, pipeline's `seed_iso.py` injects controller's `hasan_mighty`. Mutually exclusive.
2. Considered Option A (retire Phase 3) vs Option B (align keys). User asked about purging both files entirely.
3. Assessed risk: `bootstrap_hub.sh` and `destroy_vms.sh` are irreplaceable (hub lifecycle). `bootstrap_targets.sh` is fully replaced by the pipeline.
4. Aligned on mission: CLI, API, and UI should share the same pipeline logic — not parallel implementations. Bulk target creation is not a real use case (16GB RAM = 1 dev VM at a time).
5. **Decision:** Delete `bootstrap_targets.sh`, slim `rebuild_lab.sh` to hub-only, add `esacp.py provision` and `esacp.py destroy` as thin CLI wrappers over shared pipeline macros.

## Implementation

| File | Change |
|---|---|
| `platforms/kvm/bootstrap_targets.sh` | **Deleted** (404 lines removed) |
| `platforms/kvm/rebuild_lab.sh` | Removed Phase 3, updated header/banner to hub-only |
| `tools/esacp.py` | Added `provision` and `destroy` commands (~120 lines) |
| `platforms/kvm/CLAUDE.md` | Updated bootstrap section, documented unified provisioning |
| `ansible/site-kvm.yml` | Removed stale bootstrap_targets.sh reference |
| `platforms/kvm/bootstrap_hub.sh` | Updated 2 comments |
| 3x cloud-init user-data + saconsole | Updated comments |

## Verification

- `esacp.py --help` shows 12 commands including `provision` and `destroy`
- `provision fakevm` → rejects unknown VM
- `provision saconsole` → rejects hub node
- `destroy saconsole` → rejects hub node
- Python syntax check passes
- E2E provision/destroy deferred (no dev VM running)

## Issues

| # | Action | Description |
|---|---|---|
| #185 | **Closed** | PR #186 merged — bootstrap_targets.sh deleted, unified provision path |
| #187 | **Opened** | refactor: esacp.py legacy commands → pipeline-backed thin wrappers |
| #188 | **Opened** | fix: invoke scripts as executables, not via python prefix |

## Commits

| Hash | Message |
|---|---|
| `fcec86f` | fix(kvm): eliminate SSH key divergence — unified CLI/API provision path |
