# Session Minutes — 2026-04-14 1700 UTC

**Objective:** Fix #168 — Cytoscape UI topology not updated after destroy+rebuild

## Completed

1. **Fixed #168** — `_refreshVmState()` now does full topology sync
   - Adds new nodes for hosts that appear in `/api/hosts` but have no graph node
   - Removes stale nodes for hosts no longer in the API response
   - Also tracks `provisioned` state changes (not just `vm_state`)
   - Calls `_updatePromoteButton()` after sync since node count may change
   - PR #170, acceptance test deferred to next destroy+rebuild session

2. **Strategic discussion** — confirmed ESACP has no existing equivalent; Proxmox is not a substitute (it's a hypervisor UI, not an AI-assisted ERP maintenance platform)

3. **Hardcoded values audit** — scanned entire codebase, found 18 violations across 10 files in 5 categories. Filed issues:
   - #171 — hardcoded `saconsole` VM name (~320 occurrences)
   - #172 — hardcoded IPs (192.168.122.x, virbr0 gateway)
   - #173 — hardcoded domain names (iridium.blue, logichem.solutions)
   - #174 — hardcoded passwords in config.py defaults
   - #175 — hardcoded `toshiba` hypervisor fallback

## Issues touched
- #168 — PR #170 (acceptance test pending)
- #171, #172, #173, #174, #175 — opened (planning only)
