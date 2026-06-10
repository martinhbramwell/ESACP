# Migration proof-of-delivery ledger

Durable receipts for each step of `internal_docs/MIGRATION_PLAN.md`.

One file per step: `<step-id>.log` (e.g. `S0.log`, `S1.log`). Each contains:

```
STEP: <step-id> — <objective>
DATE: <YYYY-MM-DD>
DELIVERABLE: <named artifact>
PROOF COMMAND: <exact re-runnable command>
--- OUTPUT ---
<the actual, untruncated output>
--- VERDICT ---
PASS  (or FAIL with reason)
COMMIT: <hash>
```

Rules:
- The **proof command is re-runnable** and **cheap** (probe, not the expensive op).
- `tools/migration_status.py` re-executes every committed proof command at session
  start; a DONE step whose proof regresses is reopened.
- Output is **pasted verbatim** — never summarised, never "verified working".
