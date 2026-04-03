# Agenda — 2026-04-03 09:30 — Jinja2 Template Refactor (GH #89)

## Primary Objective

### Extract differentiate.sh generator from f-string to Jinja2 template

## Pre-flight
1. Run `sync_check.sh` — fix all failures before starting
2. Verify saconsole WG hub has correct peers (dev01, dev02, dev03) — Ansible updates failed during last session's destroy/rebuild cycles
3. Verify dev02 VM is running on toshiba (half-built, H4a incomplete)

## Steps

1. **Plan the template structure** before writing code:
   - Inventory every variable the template needs (hostname, nickname, bench_dir, site_url, erp_user, passwords, API keys, etc.)
   - Identify every section that has quoting complexity (H4a, H4e, apikey.sh writer)
   - Design the vars dict that `_run_provision_erpnext()` will pass to `render()`

2. **Create `platforms/kvm/differentiate.sh.j2`**:
   - Use committed `dev02-differentiate.sh` as the reference output
   - Replace all host-specific values with `{{ var }}` Jinja2 placeholders
   - No f-string escaping, no `${{...}}` hacks — plain bash with Jinja2 variables

3. **Update `tools/api.py`**:
   - Replace the ~400-line f-string template with `jinja2.Template(path).render(vars)`
   - Build the vars dict from `NewErpnextVM` + computed values
   - Add `jinja2` to requirements if not already present

4. **Test end-to-end**: Deploy or Refresh dev02 → all services green → HTTPS responds

## Deferred
- GH #87: Refresh secrets gap (SCP of deploy keys + certs on Refresh)
- dev01 HTTP 502 — investigate separately
- SRI PRUEBAS retry (2026-04-07 agenda item)
