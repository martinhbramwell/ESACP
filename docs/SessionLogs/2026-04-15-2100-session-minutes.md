# Session Minutes — 2026-04-15 21:00

**Objective:** Fix #178 — saconsole SSH config uses unroutable hostname; full rebuild with current codebase

**Branch:** main (direct commits — rebuild required iterative fix-and-retry)

---

## Completed

1. **Pre-rebuild audit** — reviewed all 9 open issues for rebuild relevance; confirmed #178 was the only blocker
2. **Pre-rebuild fixes** (commit `f50cfe0`):
   - `bootstrap_hub.sh`: undefined `${SACONSOLE_IP}` → `${HUB_VIRBR0_IP}` (3 sites)
   - `hosts_map.yml`: target5 duplicate nickname D1IRBL → T5IRBL, added missing `vm_name`
3. **Rebuild Phase 1+2** — destroy all VMs, bootstrap saconsole from scratch. Hub fully provisioned (137 Ansible tasks), both snapshots taken ("Fresh Install", "Stage 2.2 Baseline")
4. **Phase 3 failures exposed 4 more stale-variable bugs**:
   - `rebuild_lab.sh`, `sync_check.sh`, `utils.sh`: undefined `SACONSOLE_USER`/`SACONSOLE_IP`/`PROJECT_ROOT`/`ESACP_SACONSOLE_WG_IP` (commit `e4b3d62`)
   - `config.sh`: `HYPERVISOR_LAN_IP` defaulted to DNS name `toshy.iridium.blue` instead of numeric IP `192.168.1.79` — hub `/etc/hosts` needs numeric first column (commit `6ee2e24`)
   - `bootstrap_targets.sh`: `ESACP_KVM_TARGETS` env override silently overwritten by `config.sh` (commit `beef76d`)
   - `bootstrap_targets.sh`: Ansible `--limit targets` included all VMs in group, not just those being built (commit `0a95a9d`)
5. **dev01 built** via bootstrap_targets.sh (102 Ansible tasks, baseline snapshot) — then **destroyed** because bootstrap_targets.sh injects the hub's SSH key, not the controller's. The provision pipeline (stage 1 `seed_iso.py`) is the correct path and injects `hasan_mighty.pub`.
6. **sync_check post-rebuild**: 44 passed, 3 failures (dev02/03/target5 not built — expected). All 8 observability containers up, WireGuard hub 5 peers, mcp-grafana responding.
7. **#178 closed** with commit hashes. **#185 filed** for bootstrap_targets.sh / pipeline SSH key misalignment.

## Key Discovery

`bootstrap_targets.sh` is legacy — it was designed for the old target1/target2 hub-managed model. The pipeline's stage 1 (`seed_iso.py`) is its replacement for drag-to-provision. `rebuild_lab.sh` Phase 3 should either be retired or aligned with the pipeline (#185).

## Commits (all on main)

| Hash | Description |
|---|---|
| `f50cfe0` | fix(kvm): pre-rebuild cleanup — undefined var, duplicate nickname, missing vm_name |
| `e4b3d62` | fix(kvm): replace remaining undefined SACONSOLE_*/PROJECT_ROOT vars |
| `6ee2e24` | fix(kvm): HYPERVISOR_LAN_IP must be numeric IP, not DNS name |
| `c4c5a12` | ci(kvm): add cloud-init template for dev01 on toshiba |
| `beef76d` | fix(kvm): allow ESACP_KVM_TARGETS env override in bootstrap_targets.sh |
| `0a95a9d` | fix(kvm): Ansible --limit must match TARGETS, not entire group |

## Issues

- **#178** — closed (saconsole rebuild proven)
- **#185** — opened (bootstrap_targets.sh SSH key misalignment with pipeline)
- **Open issues**: #48, #50, #65, #138, #153, #156, #157, #181, #185 (9 open)
