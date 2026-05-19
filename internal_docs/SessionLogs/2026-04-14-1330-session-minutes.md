# Session Minutes — 2026-04-14 1330 UTC

**Objective:** Fix #37 — decouple jobs from uvicorn process

## Completed

1. **Opened #168** — Cytoscape UI topology not updated after destroy+rebuild without page refresh (separate issue, 1:1:1)

2. **Fixed #37** — Jobs decoupled from uvicorn process
   - Created `tools/job_worker.py` — standalone job runner spawned as independent OS process
   - Created `tools/destroy_helpers.py` — extracted destroy pipeline functions from api.py
   - Rewrote job tracking in `tools/api.py` — file-based (`/tmp/esacp-job-{id}.{log,status,meta}`), fully stateless, no in-memory dict
   - Net -390 lines from api.py
   - Created `tools/verify_job_worker.py` — mechanism acceptance test

3. **Acceptance test** (real, via UI)
   - Refresh job on dev02 via Cytoscape UI — all 9 stages ran successfully
   - Caught and fixed `sys.path` bug during real test (module import failure in subprocess)
   - Killed uvicorn, restarted — job state survived, UI reconnected, full log readable
   - PR #169 merged

## Issues touched
- #37 — closed (PR #169)
- #168 — opened (UI topology refresh)

## Feedback captured
- `feedback_test_real_before_commit.md` — always run the actual feature e2e before declaring ready to commit
