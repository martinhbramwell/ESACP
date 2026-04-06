# Agenda — Pipeline Error Fixes (Zero-Error Builds)

**Objective:** Fix all differentiation pipeline errors discovered during the dev02 rebuild verification (2026-04-05). Each issue is a 1:1:1 session.

---

## Issues to Address (priority order)

### 1. GH #108 — G2 Custom Field cleanup misses renamed fields
**Why first:** This is the most impactful — causes `bench migrate` to crash during fixture import. Silent data integrity risk if field positioning is wrong.
**Fix:** Add `DELETE FROM tabCustom Field WHERE dt='{dt}' AND fieldname='{fn}'` alongside the existing name-based delete in `g2_clear_fixture_custom_fields.py`.
**Verify:** Rebuild dev02, confirm zero `ValidationError` in migrate output.

### 2. GH #107 — Patch Log seeding runs after first bench migrate
**Why second:** Causes noisy `session_status` crash on every rebuild. Benign but violates zero-error policy.
**Fix:** New `tools/vm_scripts/g1_seed_patch_log.py` script + Step G1 in differentiate template (between G-pre and G). Remove duplicate seeding from G2.
**Verify:** Rebuild, confirm no `ProgrammingError` in Step G output.

### 3. GH #109 — API check before gunicorn ready
**Why third:** Connection refused during ce_sri install. Currently non-fatal but indicates fragile ordering.
**Fix:** Add readiness poll loop (curl `/api/method/ping`, max 60s) as Step H2b between bench restart and H4d.
**Verify:** Rebuild, confirm "gunicorn responding after Ns" in log.

### 4. GH #110 — Deploy erpadm SSH authorized_keys
**Why fourth:** Enhancement, not a build error. Enables direct `ssh dev0N-erp` for all future verification.
**Fix:** New Step A2e in differentiate template — deploy controller pubkey to erpadm's authorized_keys.
**Verify:** After rebuild, `ssh dev02-erp "whoami"` returns `erpadm`.

### 5. GH #111 — UFW blocks SSH after toshiba reboot
**Separate session:** Investigate iptables state after cold boot. May need systemd unit ordering fix.
**First step:** Capture `iptables -L -n` immediately after next reboot, before UFW toggle.

## Pre-requisites

- Only saconsole + target VM running during rebuild (max 2 VMs on 16GB host)
- Shut down idle dev VMs before starting any rebuild session

## Notes

- All fixes go into the differentiate template generator in `tools/api.py` (not just the committed `.sh` artifacts)
- Each fix is a separate branch + PR per 1:1:1 discipline
- After all four pipeline fixes, do a final clean rebuild to verify zero errors end-to-end
