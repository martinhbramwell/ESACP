# Agenda — Next Session

**Objective:** Phase 4 — macro/destroy.py (#192)

**Pre-requisites:** PR #201 merged, clean working tree on main.

**Plan file:** `~/.claude/plans/synthetic-mapping-pretzel.md` → Phase 4

---

## Step 1: Branch and extract

1. Branch `fix/192-destroy-macro` from main
2. Create `tools/pipeline/macro/destroy.py` — 8-step destroy sequence calling existing `destroy_helpers.py` functions
3. Signature: `run(hostname, host_cfg, project_root, emit)`

## Step 2: Replace dispatchers

1. Replace `cmd_destroy_vm` in `esacp.py` (lines ~265-320) with thin dispatcher calling the new macro
2. Replace destroy logic in `job_worker.py` (lines ~136-211) with call to same macro

## Step 3: Acceptance

1. `POST /api/destroy/<host>` works via Cytoscape UI — full destroy cycle
2. `./tools/esacp.py destroyVM <host>` calls the same macro, identical outcome
3. `wc -l tools/job_worker.py` and `wc -l tools/esacp.py` both show expected reductions
4. `grep -rn 'destroy' tools/job_worker.py` returns only the dispatch entry
5. `tools/pipeline/macro/destroy.py` ≤80 lines, emit-only
6. Colocated verify: destroy a test VM, confirm fully gone
7. Pre-commit ratchet passes
