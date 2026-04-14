# Session Minutes — 2026-04-14 2300

**Objective:** Merge PR #176 (#171), then implement and test #172–#175 (hardcoded values audit)

**Branch:** `refactor/172-175-eliminate-hardcoded-values`

---

## Completed

1. **Merged PR #176** — decoupled saconsole VM name (#171). Smoke-tested: `HUB_KEY`, `HUB_VM_NAME`, `HUB_VIRBR0_IP` resolve correctly in both Python and shell.

2. **Implemented #172–#175 as a single PR #177** (29 files, 283+/144-):
   - **#172 (IPs)**: `virbr0_gateway()`, `virbr0_subnet_prefix()` in `host_identity.py`. Shell scripts source `hub_identity.sh`. No hardcoded `192.168.122.x` in active code.
   - **#173 (domains)**: `zone_domains` mapping in `hosts_map.yml`. `ZONE_DOMAINS` exported from `host_identity.py`. Duplicate dicts deleted from `api.py` and `config.py`. All pipeline stages, verify scripts, `sync_check.sh` use centralised mapping.
   - **#174 (passwords)**: New `tools/secrets.py` loads from env vars or `config/build_secrets.sops.yml`. No hardcoded password defaults.
   - **#175 (hypervisor)**: `DEFAULT_HYPERVISOR` derived from hosts_map. All `"toshiba"` literals replaced. `generate_inventory.py` uses truthiness check with dynamic ProxyJump.

3. **A-to-Z acceptance test**: Shut down dev02, provisioned dev01 from scratch via `POST /api/provision/erpnext`. All 9 pipeline stages passed. ERPNext live at `https://dev01.iridium.blue`. ~29 minutes total (dominated by `tabScheduled Job Log` import).

4. **Merged PR #177** to main. Issues #172–#175 auto-closed.

## Notes

- 1:1:1 rule overridden for this session — 4 issues bundled because changes were deeply interleaved across the same files.
- PR #170 (fix #168 — topology refresh) is still open; not reviewed this session.
- dev01 is running; dev02 is shut off (freed RAM for provisioning).
