# Session Minutes — 2026-04-16 12:15

**Objective:** Phase 4 — macro/destroy.py (#192)

**Branch:** `fix/192-destroy-macro`
**PR:** #203
**Plan file:** `~/.claude/plans/synthetic-mapping-pretzel.md` → Phase 4

---

## What was done

1. **Sanity check** — verified Gen 3 pipeline is on track: 74 pipeline files (~4600 lines), esacp.py down from 1693→1011 (Phases 1+3), other monoliths untouched until now.

2. **Refined the plan** — original agenda called for reusing `destroy_helpers.py`. Recognised this violates the IoC goal: helpers unpack dicts internally instead of receiving explicit params. Decision: decompose into 8 atomic single-task primitives, delete `destroy_helpers.py` entirely.

3. **Created 8 IoC primitives** in `tools/pipeline/orchestration/`:
   - `wg_pubkey.py` (32 lines) — decrypt SOPS, return pubkey
   - `wg_peer_remove.py` (28 lines) — remove live WG peer from hub
   - `hosts_map_remove.py` (26 lines) — remove host block from hosts_map.yml
   - `group_vars_remove.py` (25 lines) — remove wg_pubkey line
   - `inventory_regen.py` (20 lines) — run generate_inventory.py
   - `ansible_wg_update.py` (36 lines) — Ansible hub WG update
   - `sops_key_remove.py` (73 lines) — remove host keys from SOPS
   - `cloud_init_cleanup.py` (17 lines) — remove cloud-init dir

4. **Created macro** `tools/pipeline/macro/destroy.py` (75 lines) — composes 8 primitives.

5. **Thinned dispatchers:**
   - `job_worker.py:run_destroy` → 3 lines (import + call)
   - `esacp.py:cmd_destroy` → ~25 lines (guards + confirm + call)
   - `job_worker.py` 400→322 (-78), `esacp.py` 1011→939 (-72)

6. **Deleted** `tools/destroy_helpers.py` (209 lines) — fully superseded.

7. **Fixed** `generate_inventory.py` missing +x (pre-existing #188 violation found during test).

8. **E2E test** — `./tools/esacp.py destroy dev01` on toshiba. All 8 steps completed:
   - Step 1: WG peer removed from hub (live)
   - Step 2: VM absent — graceful skip
   - Steps 3-4: hosts_map + group_vars cleaned
   - Step 5: inventory regenerated
   - Step 6: Ansible updated hub wg0.conf (~5 min)
   - Step 7: SOPS keys removed (dev01 + preshared_keys.dev01_saconsole)
   - Step 8: cloud-init dir absent — graceful skip
   - Verified: dev01 gone from all config files, SOPS, hypervisor

## Issues

- **#192**: resolved by this PR
- `generate_inventory.py` missing +x — fixed in this commit (part of broader #188)

## Monolith line counts after Phase 4

| File | Before session | After | Target |
|---|---|---|---|
| `esacp.py` | 1,011 | 939 | ≤150 |
| `job_worker.py` | 400 | 322 | ≤100 |
| `api.py` | 999 | 999 | ≤300 |
| `install_specific.py` | 721 | 721 | ≤50 |
